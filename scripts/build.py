"""Génère site/index.html (Radar Emploi Nature) à partir de la base Notion.

Utilise l'API officielle de Notion avec le secret d'intégration NOTION_TOKEN.
Lancé chaque matin par GitHub Actions (voir .github/workflows/radar.yml).
"""
import base64, datetime, gzip, json, os, pathlib, sys, urllib.request, urllib.error

DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "650d2e7e59c74a239cfe04291fbcfed5")
DATA_SOURCE_ID = os.environ.get("NOTION_DATA_SOURCE_ID", "7d5552ba-961d-4a01-a94d-af4343774545")
ROOT = pathlib.Path(__file__).resolve().parent.parent


def call(url, body, version, token):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers={
        "Authorization": f"Bearer {token}", "Notion-Version": version, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def fetch_pages(token):
    """Lit toutes les lignes, d'abord via l'API « data sources » (2025), sinon via l'API « databases » (2022)."""
    attempts = [
        (f"https://api.notion.com/v1/data_sources/{DATA_SOURCE_ID}/query", "2025-09-03"),
        (f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", "2022-06-28"),
    ]
    last = None
    for url, version in attempts:
        try:
            pages, cursor = [], None
            while True:
                body = {"page_size": 100, **({"start_cursor": cursor} if cursor else {})}
                res = call(url, body, version, token)
                pages += res.get("results", [])
                if not res.get("has_more"):
                    return pages
                cursor = res.get("next_cursor")
        except urllib.error.HTTPError as e:
            last = f"{e.code} {e.read().decode(errors='replace')[:300]}"
            print(f"Échec {url} ({version}) : {last}", file=sys.stderr)
    sys.exit("Impossible de lire la base Notion. Vérifiez NOTION_TOKEN et que l'intégration est connectée à la base. " + (last or ""))


def text(prop):
    if not prop:
        return ""
    t = prop.get("type")
    if t in ("title", "rich_text"):
        return "".join(x.get("plain_text", "") for x in prop.get(t) or [])
    if t == "select":
        return (prop.get("select") or {}).get("name", "")
    if t == "url":
        return prop.get("url") or ""
    if t == "created_time":
        return prop.get("created_time") or ""
    if t == "date":
        return ((prop.get("date") or {}).get("start") or "")[:10]
    return ""


def to_offer(page):
    p = page.get("properties", {})
    dom = [x["name"] for x in (p.get("Domaine", {}).get("multi_select") or [])]
    o = {"p": text(p.get("Poste")), "e": text(p.get("Entreprise")), "l": text(p.get("Lieu")), "r": text(p.get("Région")),
         "c": text(p.get("Contrat")), "d": dom, "n": text(p.get("Niveau")), "pub": text(p.get("Date de publication")),
         "s": text(p.get("Source")), "u": text(p.get("Lien")), "res": text(p.get("Résumé")), "sal": text(p.get("Salaire")),
         "st": text(p.get("Statut")), "aj": text(p.get("Ajouté le")) or page.get("created_time", "")}
    return {k: v for k, v in o.items() if v}


def build(pages, out_dir):
    offres = [to_offer(pg) for pg in pages if not pg.get("in_trash") and not pg.get("archived")]
    offres = [o for o in offres if o.get("p")]
    data = {"genere": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "offres": offres}
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode()
    gz = base64.b64encode(gzip.compress(raw, 9)).decode()
    html = (ROOT / "radar-template.html").read_text(encoding="utf-8").replace("__OFFRES_GZ_B64__", gz)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    (out_dir / ".nojekyll").write_text("")
    print(f"{len(offres)} offres -> {out_dir / 'index.html'} ({len(html.encode()) // 1024} Kio)")


if __name__ == "__main__":
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        sys.exit("Variable NOTION_TOKEN manquante (secret GitHub).")
    build(fetch_pages(token), ROOT / "site")
