"""Durcit le projet Android généré par Capacitor (mobile/android/).

- aucune sauvegarde des données de l'app (CV, clé API mémorisée) : ni sauvegarde Google,
  ni transfert vers un autre téléphone, ni « adb backup » ;
- pas de trafic HTTP non chiffré.
Lancé par « npm run android » après « cap add android ». Sans effet s'il est relancé.
"""
import pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
MANIFEST = HERE / "android/app/src/main/AndroidManifest.xml"
RULES = HERE / "android/app/src/main/res/xml/data_extraction_rules.xml"
BACKUP = HERE / "android/app/src/main/res/xml/backup_rules.xml"

if not MANIFEST.exists():
    sys.exit("Projet Android absent : lancez d'abord « npx cap add android ».")

RULES.parent.mkdir(parents=True, exist_ok=True)
RULES.write_text("""<?xml version="1.0" encoding="utf-8"?>
<data-extraction-rules>
    <cloud-backup>
        <exclude domain="root" path="." />
        <exclude domain="file" path="." />
        <exclude domain="database" path="." />
        <exclude domain="sharedpref" path="." />
        <exclude domain="external" path="." />
    </cloud-backup>
    <device-transfer>
        <exclude domain="root" path="." />
        <exclude domain="file" path="." />
        <exclude domain="database" path="." />
        <exclude domain="sharedpref" path="." />
        <exclude domain="external" path="." />
    </device-transfer>
</data-extraction-rules>
""", encoding="utf-8")
BACKUP.write_text("""<?xml version="1.0" encoding="utf-8"?>
<full-backup-content>
    <exclude domain="root" path="." />
    <exclude domain="file" path="." />
    <exclude domain="database" path="." />
    <exclude domain="sharedpref" path="." />
    <exclude domain="external" path="." />
</full-backup-content>
""", encoding="utf-8")

xml = MANIFEST.read_text(encoding="utf-8")
m = re.search(r"<application\b[^>]*>", xml, re.S)
if not m:
    sys.exit("Balise <application> introuvable dans AndroidManifest.xml.")
tag = m.group(0)
wanted = {
    "android:allowBackup": "false",
    "android:fullBackupContent": "@xml/backup_rules",
    "android:dataExtractionRules": "@xml/data_extraction_rules",
    "android:usesCleartextTraffic": "false",
}
new = tag
for attr, value in wanted.items():
    if re.search(rf'{attr}="[^"]*"', new):
        new = re.sub(rf'{attr}="[^"]*"', f'{attr}="{value}"', new)
    else:
        new = new.replace("<application", f'<application\n        {attr}="{value}"', 1)
MANIFEST.write_text(xml.replace(tag, new, 1), encoding="utf-8")
print("Android durci : sauvegardes désactivées, HTTP non chiffré refusé.")
