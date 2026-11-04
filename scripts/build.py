"""Génère le site publié par GitHub Pages (dossier site/) : l'application Radar Emploi Nature
et la liste des offres (offres.json), lue dans Notion chaque matin.

Comme l'app « Expositions » : pas de serveur. Le robot GitHub (.github/workflows/radar.yml) lit la base
Notion avec le secret NOTION_TOKEN et publie la liste ; l'application la lit et garde sur l'appareil
les favoris, candidatures, offres retirées ou ajoutées.

Ne sont jamais publiés : le statut des offres et la date de candidature (données personnelles),
les offres « Écarté » et la clé de dédoublonnage.
"""
import datetime, json, os, pathlib, shutil, sys, urllib.error, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import csp  # noqa: E402

OFFERS_DS = os.environ.get("NOTION_DATA_SOURCE_ID", "7d5552ba-961d-4a01-a94d-af4343774545")
SOURCES_DS = os.environ.get("NOTION_SOURCES_DATA_SOURCE_ID", "cb83dfc0-dd8f-4afa-a84c-a544bff96be3")
PRIVATE = {"Statut", "Date de candidature", "Clé dédoublonnage"}
EXCLUDED_STATUSES = {"Écarté"}


def query(ds, token):
    pages, cursor = [], None
    while True:
        body = {"page_size": 100, **({"start_cursor": cursor} if cursor else {})}
        req = urllib.request.Request(f"https://api.notion.com/v1/data_sources/{ds}/query", data=json.dumps(body).encode(), method="POST",
                                     headers={"Authorization": f"Bearer {token}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            res = json.load(r)
        pages += [p for p in res.get("results", []) if not p.get("in_trash") and not p.get("archived")]
        if not res.get("has_more"):
            return pages
        cursor = res.get("next_cursor")


def safe_url(u):
    """Ne garde que les liens http(s) absolus (pas de javascript:, data:, etc.)."""
    u = (u or "").strip()
    try:
        parts = urllib.parse.urlsplit(u)
    except ValueError:
        return ""
    return u if parts.scheme.lower() in ("http", "https") and parts.netloc else ""


def to_row(page, skip=()):
    """Page Notion -> ligne « à plat », au format du connecteur Notion de claude.ai (lu tel quel par l'application)."""
    row = {"url": safe_url(page.get("url"))}
    for name, p in (page.get("properties") or {}).items():
        if name in skip:
            continue
        key = f"userDefined:{name}" if name.lower() in ("url", "id", "createdtime") else name
        t = p.get("type")
        if t in ("title", "rich_text"):
            row[key] = "".join(x.get("plain_text", "") for x in p.get(t) or [])
        elif t == "select":
            row[key] = (p.get("select") or {}).get("name")
        elif t == "multi_select":
            row[key] = [x["name"] for x in p.get("multi_select") or []]
        elif t == "url":
            row[key] = safe_url(p.get("url"))
        elif t == "checkbox":
            row[key] = "__YES__" if p.get("checkbox") else "__NO__"
        elif t == "created_time":
            row[key] = p.get("created_time")
        elif t == "date":
            row[f"date:{name}:start"] = (p.get("date") or {}).get("start")
    return {k: v for k, v in row.items() if v not in (None, "", [])}


def status(page):
    return ((page.get("properties", {}).get("Statut") or {}).get("select") or {}).get("name")


def fetch(token):
    offres = [to_row(p, PRIVATE) for p in query(OFFERS_DS, token) if status(p) not in EXCLUDED_STATUSES]
    offres = [o for o in offres if o.get("Poste") and o.get("url")]
    try:
        sources = [to_row(p) for p in query(SOURCES_DS, token)]
    except urllib.error.HTTPError as e:
        print(f"::warning::Base « Sources de recherche » illisible ({e.code}) : connectez-y l'intégration Notion.", file=sys.stderr)
        sources = []
    return {"genere": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "offres": offres, "sources": sources}


def build(out_dir, data=None):
    out_dir.mkdir(parents=True, exist_ok=True)
    html = csp.harden((ROOT / "radar-template.html").read_text(encoding="utf-8"))
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    (out_dir / ".nojekyll").write_text("")
    if data is not None:
        (out_dir / "offres.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    app = ROOT / "radar-app"
    shutil.copy2(app / "manifest.webmanifest", out_dir / "manifest.webmanifest")
    shutil.copy2(app / "sw.js", out_dir / "sw.js")
    (out_dir / "icons").mkdir(exist_ok=True)
    for icon in ("icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png"):
        shutil.copy2(app / "icons" / icon, out_dir / "icons" / icon)
    shutil.copytree(app / "vendor", out_dir / "vendor", dirs_exist_ok=True)
    n = len(data["offres"]) if data else 0
    print(f"Application et {n} offres -> {out_dir}")


if __name__ == "__main__":
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        sys.exit("Variable NOTION_TOKEN manquante (secret GitHub).")
    try:
        data = fetch(token)
    except urllib.error.HTTPError as e:
        sys.exit(f"Lecture Notion impossible ({e.code}) : vérifiez NOTION_TOKEN et que l'intégration est connectée à la base. {e.read()[:300]!r}")
    build(ROOT / "site", data)
