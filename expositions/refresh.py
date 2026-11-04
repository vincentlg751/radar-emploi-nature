"""Renouvelle la base des expositions et détecte les nouvelles.

Sources :
  1. API Open Data de la Ville de Paris, jeu « Que faire à Paris ? » (sans clé).
  2. expositions/data/selection.json : sélection tenue à la main (grandes expos, lieux hors API).

Étapes :
  - lit les deux sources et les ramène au même modèle (voir MODELE.md) ;
  - retire les expositions terminées ;
  - compare à la base précédente : les nouvelles reçoivent « vu_le » = aujourd'hui ;
  - écrit data/expositions.json (la base) et ajoute une ligne à data/journal.json.

Si l'API ne répond pas, les fiches API de la base précédente sont gardées (sauf celles terminées).
Lancé chaque jour par .github/workflows/expositions.yml. Aucune dépendance hors bibliothèque standard.
"""
import datetime, json, os, pathlib, re, sys, unicodedata, urllib.error, urllib.parse, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data"
BASE = DATA / "expositions.json"
SELECTION = DATA / "selection.json"
JOURNAL = DATA / "journal.json"
API = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/que-faire-a-paris-/exports/json"
MAX_BYTES = 80 * 2**20  # taille maximale acceptée pour la réponse de l'API
FIELDS = ("id,url,title,lead_text,date_start,date_end,date_description,cover_url,tags,qfap_tags,"
          "address_name,address_street,address_zipcode,address_city,lat_lon,price_type,price_detail,"
          "access_link,access_type,pmr")

# Thématiques normalisées : (nom affiché, mots-clés cherchés dans les tags, le titre et le chapeau)
THEMES = [
    ("Photographie", ["photo"]),
    ("Art contemporain", ["art contemporain", "contemporain", "installation", "video", "numerique", "digital"]),
    ("Beaux-arts", ["peinture", "peintre", "beaux-arts", "beaux arts", "sculpture", "dessin", "gravure", "impressionn",
                    "maitre", "chef-d'oeuvre", "retrospective"]),
    ("Histoire & patrimoine", ["histoire", "patrimoine", "archeolog", "memoire", "guerre", "antique", "egypt", "siecle"]),
    ("Sciences & nature", ["science", "nature", "biodiversite", "climat", "ecolog", "animal", "plante", "jardin",
                           "environnement", "ocean", "espace"]),
    ("Design, mode & arts déco", ["design", "mode", "couture", "bijou", "arts decoratifs", "artisanat", "metiers d'art"]),
    ("Architecture & ville", ["architecture", "urbanisme", "ville", "paysage"]),
    ("Street art & BD", ["street art", "graffiti", "bande dessinee", "bd", "illustration", "manga"]),
    ("Société & monde", ["societe", "monde", "voyage", "citoyen", "droits", "feminis", "migration", "cultures"]),
    ("Jeunesse", ["enfant", "famille", "jeune public", "jeunesse"]),
]


def plain(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s)


def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", str(s or ""))
    return re.sub(r"\s+", " ", s).strip()


def safe_url(v):
    """Garde seulement une adresse web http(s) valide ; complète « www.… » ; sinon None.
    Empêche qu'un lien « javascript:… » ou mal formé venu de la source arrive dans l'app."""
    v = str(v or "").strip()
    if v.lower().startswith("www."):
        v = "https://" + v
    try:
        u = urllib.parse.urlsplit(v)
    except ValueError:
        return None
    if u.scheme not in ("http", "https") or not u.netloc or any(c in v for c in "\"'<>`\\ \n\r\t"):
        return None
    return v


def coord(v, lo, hi):
    """Nombre dans [lo, hi], sinon None."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if lo <= f <= hi else None


def as_list(v):
    if not v:
        return []
    if isinstance(v, list):
        return [str(x) for x in v if x]
    return [x.strip() for x in re.split(r"[;,]", str(v)) if x.strip()]


def themes_for(*texts):
    t = " " + plain(" ".join(texts)) + " "
    found = [name for name, keys in THEMES if any(re.search(r"\b" + re.escape(k), t) for k in keys)]
    return found or ["Autres"]


def tarif_type(price_type):
    p = plain(price_type)
    if "condition" in p:
        return "gratuit_sous_condition"
    if "gratuit" in p:
        return "gratuit"
    if "payant" in p:
        return "payant"
    return "inconnu"


def prix_min(detail):
    """Plus petit montant en euros cité dans le détail du tarif (0 ignoré), ou None."""
    nums = [float(n.replace(",", ".")) for n in re.findall(r"(\d+(?:[.,]\d{1,2})?)\s*(?:€|euros?)", str(detail or ""))]
    nums = [n for n in nums if n > 0]
    return min(nums) if nums else None


# Événements autour d'une expo (visites, ateliers, vernissages…) : ce ne sont pas des expositions.
SIDE_EVENTS = re.compile(
    r"^(atelier|visites?|spectacle|vernissage|taxitram|soiree|boum|philo|conference|balade|dedicace|workshop|"
    r"rencontre|performance|stage|concert|projection|lecture|finissage|table ronde|masterclass|jeu|parcours conte)\b"
    r"|visite (guidee|contee|commentee)|vernissage|finissage")


def is_side_event(title):
    return bool(SIDE_EVENTS.search(plain(strip_html(title)).lstrip(" \"'«[(-")))


def title_key(title):
    return re.sub(r"[^a-z0-9]+", " ", plain(title)).strip()


def is_expo(r):
    tags = plain(" ".join(as_list(r.get("qfap_tags")) + as_list(r.get("tags")) + as_list(r.get("universe_tags"))))
    if is_side_event(r.get("title")):
        return False
    return "expo" in tags or plain(r.get("title")).startswith("expo")


def from_api(r, today):
    ll = r.get("lat_lon") or {}
    if isinstance(ll, str) and "," in ll:  # « lat,lon »
        la, lo = ll.split(",", 1)
        ll = {"lat": la, "lon": lo}
    elif isinstance(ll, list) and len(ll) == 2:
        ll = {"lat": ll[0], "lon": ll[1]}
    if not isinstance(ll, dict):
        ll = {}
    detail = strip_html(r.get("price_detail"))
    t = tarif_type(r.get("price_type"))
    tags = as_list(r.get("qfap_tags")) + as_list(r.get("tags"))
    return {
        "id": f"qfap-{r.get('id')}",
        "titre": strip_html(r.get("title")),
        "resume": strip_html(r.get("lead_text"))[:400],
        "debut": (r.get("date_start") or "")[:10],
        "fin": (r.get("date_end") or "")[:10],
        "horaires": strip_html(r.get("date_description"))[:300],
        "lieu": strip_html(r.get("address_name")),
        "adresse": ", ".join(x for x in [strip_html(r.get("address_street")),
                                         " ".join(x for x in [r.get("address_zipcode"), r.get("address_city")] if x)] if x),
        "lat": coord(ll.get("lat"), -90, 90), "lon": coord(ll.get("lon"), -180, 180),
        "thematiques": themes_for(" ".join(tags), r.get("title") or "", r.get("lead_text") or ""),
        "tarif": {"type": t, "detail": detail[:300], "prix_min": prix_min(detail) if t == "payant" else 0 if t.startswith("gratuit") else None,
                  "reservation": plain(r.get("access_type")) in ("reservation", "conseillee", "obligatoire") or None,
                  "billetterie": safe_url(r.get("access_link"))},
        "image": safe_url(r.get("cover_url")),
        "lien": safe_url(r.get("url")),
        "accessible": bool(r.get("pmr")) or None,
        "source": "Que faire à Paris (Open Data Ville de Paris)",
    }


def fetch_api(today):
    """Interroge l'API ; si une requête est refusée (champ ou filtre inconnu), réessaie plus simplement
    et filtre ici. Le motif du refus est affiché dans le journal du robot."""
    attempts = [
        {"select": FIELDS, "where": f'date_end >= "{today}"'},
        {"where": f'date_end >= "{today}"'},
        {},
    ]
    last = None
    for params in attempts:
        url = API + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "radar-expositions/1.0 (GitHub Actions)"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                raw = r.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError(f"Réponse de plus de {MAX_BYTES // 2**20} Mo, ignorée")
            rows = json.loads(raw)
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code} : {exc.read().decode(errors='replace')[:300]}"
            print(f"Requête refusée ({', '.join(params) or 'sans filtre'}) -> {last}", file=sys.stderr)
            continue
        if not isinstance(rows, list):
            raise ValueError(f"Réponse inattendue : {str(rows)[:200]}")
        expos = []
        for x in rows:
            try:
                if isinstance(x, dict) and is_expo(x):
                    expos.append(from_api(x, today))
            except Exception as exc:  # une fiche mal formée ne bloque pas toute la mise à jour
                print(f"Fiche ignorée ({x.get('id') if isinstance(x, dict) else '?'}) : {exc}", file=sys.stderr)
        print(f"API : {len(rows)} événements reçus, {len(expos)} expositions retenues")
        return expos
    raise RuntimeError(last or "API injoignable")


def clean(e):
    e = {k: v for k, v in e.items() if v not in (None, "", [], {})}
    if "tarif" in e:
        e["tarif"] = {k: v for k, v in e["tarif"].items() if v not in (None, "")}
    return e


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def main():
    today = os.environ.get("EXPOS_TODAY") or datetime.date.today().isoformat()
    previous = {e["id"]: e for e in load(BASE, {}).get("expositions", [])}
    selection = load(SELECTION, {}).get("expositions", [])
    for e in selection:
        e.setdefault("source", "Sélection manuelle")
        for f in ("titre", "resume", "lieu", "adresse", "horaires"):
            if e.get(f):
                e[f] = strip_html(e[f])
        for f in ("lien", "image"):
            e[f] = safe_url(e.get(f))
        if isinstance(e.get("tarif"), dict):
            e["tarif"]["billetterie"] = safe_url(e["tarif"].get("billetterie"))
        e["lat"], e["lon"] = coord(e.get("lat"), -90, 90), coord(e.get("lon"), -180, 180)
        if not e.get("thematiques"):
            e["thematiques"] = themes_for(e.get("titre", ""), e.get("resume", ""))

    api_ok, api_error = True, None
    try:
        api = fetch_api(today)
        print(f"API Que faire à Paris : {len(api)} expositions en cours ou à venir")
    except Exception as exc:  # réseau, quota, format : on garde la base précédente
        api_ok, api_error = False, f"{type(exc).__name__}: {exc}"
        api = [e for e in previous.values() if e["id"].startswith("qfap-")]
        print(f"::warning::API Que faire à Paris indisponible ({api_error}). Base précédente conservée.", file=sys.stderr)

    # Une expo de la sélection manuelle déjà présente dans l'API n'est gardée qu'une fois :
    # la fiche manuelle prime, complétée par l'image et le lien de l'API.
    sel_keys = {title_key(e["titre"]): e for e in selection if e.get("titre")}
    dedup = []
    for e in api:
        k = title_key(e.get("titre", ""))
        twin = next((v for sk, v in sel_keys.items() if sk and (sk in k or k in sk)), None)
        if twin is None:
            dedup.append(e)
            continue
        for f in ("image", "lien", "horaires"):
            if e.get(f) and not twin.get(f):
                twin[f] = e[f]
    api = dedup

    merged = {}
    for e in api + selection:  # la sélection manuelle prime sur l'API pour un même id
        if e.get("fin") and e["fin"] < today:
            continue
        if not e.get("titre"):
            continue
        merged[e["id"]] = clean(e)

    added, kept = [], 0
    for id_, e in merged.items():
        old = previous.get(id_)
        if old and old.get("vu_le"):
            e["vu_le"] = old["vu_le"]
            kept += 1
        else:
            e["vu_le"] = today
            added.append(id_)
    removed = [id_ for id_ in previous if id_ not in merged]

    expos = sorted(merged.values(), key=lambda e: (e.get("fin") or "9999", e["titre"]))
    counts = {t: sum(1 for e in expos if e.get("tarif", {}).get("type") == t)
              for t in ("gratuit", "gratuit_sous_condition", "payant", "inconnu")}
    base = {"genere": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "jour": today, "api_ok": api_ok, "total": len(expos), "par_tarif": counts,
            "nouvelles": added, "expositions": expos}
    DATA.mkdir(parents=True, exist_ok=True)
    BASE.write_text(json.dumps(base, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    journal = load(JOURNAL, [])
    journal = [j for j in journal if j.get("jour") != today]
    journal.append({"jour": today, "total": len(expos), "ajoutees": len(added), "retirees": len(removed),
                    "api_ok": api_ok, **({"erreur": api_error} if api_error else {}),
                    "titres_ajoutes": [merged[i]["titre"] for i in added][:50]})
    JOURNAL.write_text(json.dumps(journal[-90:], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    lines = [f"## Expositions — {today}", "",
             f"- Total : **{len(expos)}** (gratuites {counts['gratuit'] + counts['gratuit_sous_condition']}, payantes {counts['payant']}, tarif inconnu {counts['inconnu']})",
             f"- Nouvelles : **{len(added)}** · retirées (terminées) : {len(removed)} · API : {'OK' if api_ok else 'indisponible'}", ""]
    lines += [f"  - {merged[i]['titre']} — {merged[i].get('lieu', '')}" for i in added[:40]]
    report = "\n".join(lines)
    print(report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(report + "\n")


if __name__ == "__main__":
    main()
