"""Applique dans Notion les actions faites dans l'application Radar Emploi (sans serveur).

Lancé par .github/workflows/notion-action.yml, que l'application déclenche avec la clé GitHub
personnelle de l'utilisateur. Les actions arrivent chiffrées (AES-256-GCM) avec la clé RADAR_SYNC_KEY,
que seuls l'appareil de l'utilisateur et ce robot connaissent : le dépôt étant public, rien de lisible
(favoris, candidatures…) n'apparaît dans GitHub. Le journal n'affiche que des nombres.

Garde-fous : seules les deux bases du Radar sont modifiables, chaque page visée est relue et son parent
vérifié, et seules certaines propriétés sont acceptées.
"""
import base64, json, os, re, sys, urllib.error, urllib.request

OFFERS_DS = os.environ.get("NOTION_DATA_SOURCE_ID", "7d5552ba-961d-4a01-a94d-af4343774545")
SOURCES_DS = os.environ.get("NOTION_SOURCES_DATA_SOURCE_ID", "cb83dfc0-dd8f-4afa-a84c-a544bff96be3")
ALLOWED_DS = {OFFERS_DS, SOURCES_DS}
MAX_OPS = 50

# Propriétés que l'application peut écrire (format « à plat » du connecteur Notion de claude.ai).
SELECTS = {
    "Statut": {"Nouveau", "Favori", "À regarder", "Candidaté", "Écarté"},
    "Contrat": {"CDI", "CDD"},
    "Niveau": {"Junior", "Confirmé", "Senior / Cadre", "Technicien"},
    "Langue": {"Français", "Anglais", "Bilingue"},
    "Source": {"Ajout manuel"},
    "Type": {"Site employeur", "Job board", "Réseau / association", "Public"},
}
OFFER_UPDATE = {"Statut", "date:Date de candidature:start"}
OFFER_CREATE = {"Poste", "Lien", "Source", "Statut", "À compléter", "Entreprise", "Lieu", "Région", "Contrat", "Niveau",
                "Domaine", "date:Date de publication:start", "Langue", "Salaire", "Résumé"}
SOURCE_UPDATE = {"Active"}
SOURCE_CREATE = {"Nom", "userDefined:URL", "Type", "Active", "Notes"}
TITLE = {"Poste", "Nom"}
TEXT = {"Entreprise", "Lieu", "Salaire", "Résumé", "Notes"}
URLS = {"Lien": "Lien", "userDefined:URL": "URL"}
CHECKBOX = {"À compléter", "Active"}
DATES = {"date:Date de candidature:start": "Date de candidature", "date:Date de publication:start": "Date de publication"}
REGIONS = {"Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne", "Centre-Val de Loire", "Corse", "Grand Est", "Hauts-de-France",
           "Île-de-France", "Normandie", "Nouvelle-Aquitaine", "Occitanie", "Pays de la Loire", "Provence-Alpes-Côte d'Azur", "Outre-mer",
           "Télétravail / National"}
DOMAINES = {"Biodiversité", "Marin & littoral", "Forêt", "Eau & milieux aquatiques", "Énergies renouvelables", "Climat & adaptation",
            "Agriculture & sols", "Déchets & économie circulaire", "Air & pollutions", "Éducation à l'environnement",
            "Aménagement & espaces naturels"}


class Refused(Exception):
    pass


def decrypt(blob, key_b64):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = base64.b64decode(key_b64)
    if len(key) != 32:
        raise Refused("clé RADAR_SYNC_KEY invalide (32 octets attendus)")
    raw = base64.b64decode(blob)
    try:
        return json.loads(AESGCM(key).decrypt(raw[:12], raw[12:], None).decode("utf-8"))
    except Exception as e:  # mauvaise clé ou message altéré
        raise Refused("message illisible : la clé de l'application ne correspond pas à RADAR_SYNC_KEY") from e


def page_id(v):
    s = str(v or "").split("?")[0]
    m = re.search(r"([0-9a-f]{32})$", s, re.I) or re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$", s, re.I)
    if not m:
        raise Refused("identifiant de page invalide")
    h = m.group(1).replace("-", "").lower()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"


def safe_url(u):
    u = str(u or "").strip()
    return u if re.match(r"^https?://[^\s/]+\.[^\s]+$", u, re.I) and len(u) <= 2000 else ""


def rich(s, limit):
    s = str(s or "")[:limit]
    return [{"type": "text", "text": {"content": s[i:i + 1900]}} for i in range(0, len(s), 1900)]


def to_props(flat, allowed):
    props = {}
    for key, value in (flat or {}).items():
        if key.endswith(":is_datetime"):
            continue
        if key not in allowed:
            raise Refused(f"propriété non autorisée : {key}")
        if key in TITLE:
            props[key] = {"title": rich(value, 200)}
        elif key in TEXT:
            props[key] = {"rich_text": rich(value, 1500)}
        elif key in URLS:
            props[URLS[key]] = {"url": safe_url(value) or None}
        elif key in CHECKBOX:
            props[key] = {"checkbox": value is True or value == "__YES__"}
        elif key in DATES:
            v = str(value or "")
            if v and not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
                raise Refused(f"date invalide : {key}")
            props[DATES[key]] = {"date": {"start": v} if v else None}
        elif key == "Région":
            props[key] = {"select": {"name": value} if value in REGIONS else None}
        elif key == "Domaine":
            props[key] = {"multi_select": [{"name": d} for d in (value or []) if d in DOMAINES][:5]}
        elif key in SELECTS:
            if value not in SELECTS[key]:
                raise Refused(f"valeur non autorisée pour {key}")
            props[key] = {"select": {"name": value}}
        else:
            raise Refused(f"propriété non gérée : {key}")
    return props


class Notion:
    def __init__(self, token, opener=urllib.request.urlopen):
        self.token, self.open = token, opener

    def call(self, method, path, body=None):
        req = urllib.request.Request("https://api.notion.com/v1" + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Authorization": f"Bearer {self.token}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"})
        with self.open(req, timeout=60) as r:
            return json.load(r)

    def guarded(self, pid):
        page = self.call("GET", f"/pages/{page_id(pid)}")
        ds = (page.get("parent") or {}).get("data_source_id")
        if ds not in ALLOWED_DS:
            raise Refused("page hors des bases du Radar")
        return page["id"], ds


def apply(actions, notion):
    if not isinstance(actions, list) or len(actions) > MAX_OPS:
        raise Refused("liste d'actions invalide")
    done = {"update": 0, "create": 0, "delete": 0}
    errors = 0
    for a in actions:
        try:
            op = a.get("op")
            if op == "update":
                pid, ds = notion.guarded(a.get("id"))
                props = to_props(a.get("props"), OFFER_UPDATE if ds == OFFERS_DS else SOURCE_UPDATE)
                notion.call("PATCH", f"/pages/{pid}", {"properties": props})
            elif op == "create":
                ds = a.get("ds")
                if ds not in ALLOWED_DS:
                    raise Refused("base non autorisée")
                props = to_props(a.get("props"), OFFER_CREATE if ds == OFFERS_DS else SOURCE_CREATE)
                notion.call("POST", "/pages", {"parent": {"type": "data_source_id", "data_source_id": ds}, "properties": props})
            elif op == "delete":
                pid, _ = notion.guarded(a.get("id"))
                notion.call("PATCH", f"/pages/{pid}", {"in_trash": True})
            else:
                raise Refused("action inconnue")
            done[op] += 1
        except (Refused, urllib.error.HTTPError, KeyError, TypeError, AttributeError) as e:
            errors += 1
            # Jamais de contenu dans le journal (dépôt public) : seulement le type d'erreur.
            print(f"::warning::Action ignorée ({type(e).__name__}{': ' + str(e) if isinstance(e, Refused) else ''})")
    return done, errors


if __name__ == "__main__":
    token, key, blob = os.environ.get("NOTION_TOKEN"), os.environ.get("RADAR_SYNC_KEY"), os.environ.get("ACTIONS", "")
    if not token or not key:
        sys.exit("Secrets NOTION_TOKEN et RADAR_SYNC_KEY nécessaires (voir LISEZMOI.md).")
    try:
        done, errors = apply(decrypt(blob, key), Notion(token))
    except Refused as e:
        sys.exit(f"Refusé : {e}")
    print(f"Notion mis à jour : {done['update']} modification(s), {done['create']} ajout(s), {done['delete']} retrait(s), {errors} erreur(s).")
    sys.exit(1 if errors else 0)
