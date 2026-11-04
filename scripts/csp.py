"""Politique de sécurité (CSP) de la page générée.

- Le modèle autorise 'unsafe-inline' pour rester utilisable ouvert tel quel. À la génération, on le
  remplace par l'empreinte SHA-256 de chaque script intégré : un script injecté (par exemple via une
  offre piégée) ne pourrait pas s'exécuter, ni lire le CV.
- L'application native lit la liste publiée sur GitHub Pages : cette adresse est ajoutée aux connexions autorisées.
"""
import base64, hashlib, json, re, urllib.parse

INLINE = re.compile(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>", re.S)
CONNECT = "connect-src 'self' https://api.github.com"


def harden(html):
    hashes = []
    for m in INLINE.finditer(html):
        attrs = m.group("attrs")
        if "src=" in attrs or 'type="text/plain"' in attrs:
            continue
        digest = base64.b64encode(hashlib.sha256(m.group("body").encode("utf-8")).digest()).decode()
        hashes.append(f"'sha256-{digest}'")
    old = "script-src 'self' 'unsafe-inline'"
    if old not in html:
        raise SystemExit("CSP introuvable (script-src) dans la page.")
    return html.replace(old, "script-src 'self' " + " ".join(dict.fromkeys(hashes)), 1)


def with_data_url(html, url):
    """Application native : indique où relire la liste publiée et autorise cette adresse (https uniquement)."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or not parts.netloc:
        raise SystemExit(f"Adresse de la liste invalide : {url}")
    if CONNECT + ";" not in html:
        raise SystemExit("CSP introuvable (connect-src) dans la page.")
    html = html.replace(CONNECT + ";", f"{CONNECT} https://{parts.netloc};", 1)
    marker = "<script>\n// La page ne doit pas"
    if marker not in html:
        raise SystemExit("Script principal introuvable dans la page.")
    return html.replace(marker, f"<script>window.RADAR_DATA_URL = {json.dumps(url)};</script>\n{marker}", 1)
