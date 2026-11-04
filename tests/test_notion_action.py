"""Tests du robot Radar Emploi → Notion (scripts/notion_action.py) : python3 tests/test_notion_action.py"""
import base64, io, json, os, pathlib, subprocess, sys, unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import notion_action as na  # noqa: E402

KEY = base64.b64encode(bytes(range(32))).decode()
OFFER = "40e04136fa74810d9a9dc4bdecc2f4d3"
OTHER = "11111111222233334444555566667777"


def js_seal(obj):
    """Chiffre comme la page (WebCrypto AES-GCM) pour vérifier la compatibilité avec le robot."""
    code = """
const [k, msg] = process.argv.slice(1);
(async () => {
  const key = await crypto.subtle.importKey("raw", Buffer.from(k, "base64"), "AES-GCM", false, ["encrypt"]);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, new TextEncoder().encode(msg)));
  process.stdout.write(Buffer.concat([Buffer.from(iv), Buffer.from(ct)]).toString("base64"));
})();"""
    return subprocess.run(["node", "-e", code, KEY, json.dumps(obj)], capture_output=True, text=True, check=True).stdout


class FakeNotion:
    def __init__(self):
        self.calls = []

    def __call__(self, req, timeout=60):
        body = json.loads(req.data) if req.data else None
        path = req.full_url.replace("https://api.notion.com/v1", "")
        self.calls.append((req.get_method(), path, body))
        if req.get_method() == "GET" and path.startswith("/pages/"):
            pid = path.split("/")[-1]
            ds = "99999999-9999-9999-9999-999999999999" if pid.replace("-", "") == OTHER else na.OFFERS_DS
            return io.BytesIO(json.dumps({"id": pid, "parent": {"type": "data_source_id", "data_source_id": ds}}).encode())
        return io.BytesIO(b"{}")


class Tests(unittest.TestCase):
    def run_actions(self, actions):
        fake = FakeNotion()
        done, errors = na.apply(na.decrypt(js_seal(actions), KEY), na.Notion("t", fake))
        return fake, done, errors

    def test_chiffrement_page_vers_robot(self):
        fake, done, errors = self.run_actions([{"op": "update", "id": f"https://app.notion.com/p/{OFFER}", "props": {"Statut": "Candidaté", "date:Date de candidature:start": "2026-11-04"}}])
        self.assertEqual((done["update"], errors), (1, 0))
        self.assertEqual(fake.calls[-1][2], {"properties": {"Statut": {"select": {"name": "Candidaté"}}, "Date de candidature": {"date": {"start": "2026-11-04"}}}})

    def test_mauvaise_cle_refusee(self):
        with self.assertRaises(na.Refused):
            na.decrypt(js_seal([]), base64.b64encode(bytes(32)).decode())

    def test_page_hors_des_bases_refusee(self):
        fake, done, errors = self.run_actions([{"op": "delete", "id": OTHER}, {"op": "update", "id": OTHER, "props": {"Statut": "Favori"}}])
        self.assertEqual(errors, 2)
        self.assertFalse([c for c in fake.calls if c[0] != "GET"])

    def test_propriete_non_autorisee_refusee(self):
        fake, done, errors = self.run_actions([{"op": "update", "id": OFFER, "props": {"Résumé": "piraté"}}, {"op": "update", "id": OFFER, "props": {"Statut": "Supprimé"}}])
        self.assertEqual(errors, 2)

    def test_suppression_corbeille(self):
        fake, done, errors = self.run_actions([{"op": "delete", "id": OFFER}])
        self.assertEqual(fake.calls[-1], ("PATCH", f"/pages/40e04136-fa74-810d-9a9d-c4bdecc2f4d3", {"in_trash": True}))

    def test_ajout_offre_et_source(self):
        fake, done, errors = self.run_actions([
            {"op": "create", "ds": na.OFFERS_DS, "props": {"Poste": "Garde du littoral", "Lien": "https://example.org/x", "Source": "Ajout manuel", "Statut": "Favori", "À compléter": "__YES__",
                                                          "Domaine": ["Marin & littoral", "Inconnu"], "Région": "Bretagne", "date:Date de publication:start": "2026-11-03"}},
            {"op": "create", "ds": na.SOURCES_DS, "props": {"Nom": "OFB", "userDefined:URL": "https://ofb.gouv.fr/emplois", "Type": "Public", "Active": "__YES__"}},
            {"op": "create", "ds": "autre-base", "props": {"Poste": "x"}}])
        self.assertEqual((done["create"], errors), (2, 1))
        offer = fake.calls[0][2]
        self.assertEqual(offer["parent"]["data_source_id"], na.OFFERS_DS)
        self.assertEqual(offer["properties"]["Domaine"], {"multi_select": [{"name": "Marin & littoral"}]})
        self.assertEqual(offer["properties"]["À compléter"], {"checkbox": True})
        self.assertEqual(fake.calls[1][2]["properties"]["URL"], {"url": "https://ofb.gouv.fr/emplois"})

    def test_lien_javascript_neutralise(self):
        fake, done, errors = self.run_actions([{"op": "create", "ds": na.OFFERS_DS, "props": {"Poste": "x", "Lien": "javascript:alert(1)"}}])
        self.assertEqual(fake.calls[0][2]["properties"]["Lien"], {"url": None})

    def test_trop_d_actions(self):
        with self.assertRaises(na.Refused):
            na.apply([{"op": "delete", "id": OFFER}] * 51, na.Notion("t", FakeNotion()))


if __name__ == "__main__":
    unittest.main(verbosity=1)
