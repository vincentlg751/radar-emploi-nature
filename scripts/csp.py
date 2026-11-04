"""Politique de sécurité (CSP) de la page générée.

- Le modèle autorise 'unsafe-inline' pour rester utilisable ouvert tel quel. À la génération, on le
  remplace par l'empreinte SHA-256 de chaque script intégré : un script injecté (par exemple via une
  offre piégée) ne pourrait pas s'exécuter, ni lire le mot de passe du serveur ou le CV.
- Si le serveur personnel n'est pas sur *.workers.dev (domaine personnalisé), son adresse est ajoutée
  aux connexions autorisées.
"""
import base64, hashlib, re, urllib.parse

INLINE = re.compile(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>", re.S)
CONNECT = "connect-src 'self' https://*.workers.dev"


def server_origin(url):
    """Origine https du serveur personnel, ou "" (adresse absente ou invalide)."""
    parts = urllib.parse.urlsplit((url or "").strip())
    if parts.scheme != "https" or not parts.netloc or parts.path not in ("", "/"):
        return ""
    return f"https://{parts.netloc}"


def harden(html, server=""):
    origin = server_origin(server)
    if origin and not origin.endswith(".workers.dev"):
        if CONNECT not in html:
            raise SystemExit("CSP introuvable (connect-src) dans la page.")
        html = html.replace(CONNECT, f"{CONNECT} {origin}", 1)
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


def with_server(html, server):
    """Pré-remplit l'adresse du serveur personnel (variable RADAR_SERVER), avant le script principal."""
    origin = server_origin(server)
    if not origin:
        return html
    tag = f'<script>window.RADAR_SERVER = "{origin}";</script>\n'
    marker = "<script>\n// La page ne doit pas"
    if marker not in html:
        raise SystemExit("Script principal introuvable dans la page.")
    return html.replace(marker, tag + marker, 1)
