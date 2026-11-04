"""Durcit la Content-Security-Policy de la page générée.

Le modèle autorise 'unsafe-inline' pour rester utilisable ouvert tel quel. À la génération, on le
remplace par l'empreinte SHA-256 de chaque script intégré : un script injecté (par exemple via une
offre piégée) ne pourrait alors pas s'exécuter, ni lire la clé API ou le CV.
"""
import base64, hashlib, re

INLINE = re.compile(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>", re.S)


def harden(html):
    hashes = []
    for m in INLINE.finditer(html):
        attrs = m.group("attrs")
        if "src=" in attrs or 'type="text/plain"' in attrs:
            continue  # scripts externes (couverts par 'self') et données non exécutées
        digest = base64.b64encode(hashlib.sha256(m.group("body").encode("utf-8")).digest()).decode()
        hashes.append(f"'sha256-{digest}'")
    old = "script-src 'self' 'unsafe-inline'"
    if old not in html:
        raise SystemExit("CSP introuvable (script-src) dans la page.")
    return html.replace(old, "script-src 'self' " + " ".join(dict.fromkeys(hashes)), 1)
