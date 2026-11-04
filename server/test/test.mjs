// Tests du serveur avec un faux Notion et un faux Claude : node test/test.mjs
import assert from "node:assert/strict";
import { makeNotion, pageIdOf, OFFERS_DS, SOURCES_DS } from "../src/notion.js";
import { makeClaude, parseJSON } from "../src/claude.js";
import worker from "../src/index.js";

let failed = 0;
async function test(name, fn) {
  try { await fn(); console.log("ok   ", name); } catch (e) { failed++; console.log("ÉCHEC", name, "\n     ", e.message); }
}

// ---------- faux Notion ----------
const PAGE_ID = "40704136fa7481aaa399cd6896ce1062";
const OTHER_ID = "11111111222233334444555566667777";
const SCHEMA = {
  Poste: { type: "title" }, Entreprise: { type: "rich_text" }, Statut: { type: "select" }, Domaine: { type: "multi_select" },
  "Date de candidature": { type: "date" }, "Date de publication": { type: "date" }, Lien: { type: "url" },
  "À compléter": { type: "checkbox" }, "Ajouté le": { type: "created_time" }, Source: { type: "select" }, Résumé: { type: "rich_text" },
};
const SRC_SCHEMA = { Nom: { type: "title" }, URL: { type: "url" }, Type: { type: "select" }, Active: { type: "checkbox" }, Notes: { type: "rich_text" } };
const page = (id, ds, extra = {}) => ({
  object: "page", id, url: `https://www.notion.so/Offre-${id.replace(/-/g, "")}`, created_time: "2026-11-01T05:40:00.000Z", in_trash: false,
  parent: { type: "data_source_id", data_source_id: ds, database_id: "650d2e7e-59c7-4a23-9cfe-04291fbcfed5" },
  properties: {
    Poste: { type: "title", title: [{ plain_text: "Chargé·e d'études faune" }] },
    Entreprise: { type: "rich_text", rich_text: [{ plain_text: "LPO" }] },
    Statut: { type: "select", select: { name: "Favori" } },
    Domaine: { type: "multi_select", multi_select: [{ name: "Biodiversité" }, { name: "Forêt" }] },
    "Date de publication": { type: "date", date: { start: "2026-10-30", end: null } },
    "Date de candidature": { type: "date", date: null },
    Lien: { type: "url", url: "https://example.org/offre" },
    "À compléter": { type: "checkbox", checkbox: true },
    "Ajouté le": { type: "created_time", created_time: "2026-11-01T05:40:00.000Z" },
    ...extra,
  },
});
function fakeNotion() {
  const calls = [];
  const f = async (url, init) => {
    const u = new URL(url), body = init.body ? JSON.parse(init.body) : null;
    calls.push({ method: init.method, path: u.pathname, body });
    const ok = d => new Response(JSON.stringify(d), { status: 200 });
    if (init.method === "GET" && u.pathname === `/v1/data_sources/${OFFERS_DS}`) return ok({ properties: SCHEMA });
    if (init.method === "GET" && u.pathname === `/v1/data_sources/${SOURCES_DS}`) return ok({ properties: SRC_SCHEMA });
    if (init.method === "POST" && u.pathname === `/v1/data_sources/${OFFERS_DS}/query`) {
      if (!body.start_cursor) return ok({ results: [page(PAGE_ID, OFFERS_DS), { ...page("aa".repeat(16), OFFERS_DS), in_trash: true }], has_more: true, next_cursor: "c2" });
      return ok({ results: [page("bb".repeat(16), OFFERS_DS)], has_more: false });
    }
    if (init.method === "POST" && u.pathname === `/v1/data_sources/${SOURCES_DS}/query`) {
      return ok({ results: [{ ...page("cc".repeat(16), SOURCES_DS), properties: { Nom: { type: "title", title: [{ plain_text: "OFB" }] }, URL: { type: "url", url: "https://ofb.gouv.fr" }, Active: { type: "checkbox", checkbox: false } } }], has_more: false });
    }
    if (init.method === "GET" && u.pathname.startsWith("/v1/pages/")) {
      const id = u.pathname.split("/").pop();
      if (id.replace(/-/g, "") === OTHER_ID) return ok(page(id, "99999999-9999-9999-9999-999999999999"));
      return ok(page(id, OFFERS_DS));
    }
    if (init.method === "PATCH" && u.pathname.startsWith("/v1/pages/")) return ok(page(u.pathname.split("/").pop(), OFFERS_DS));
    if (init.method === "POST" && u.pathname === "/v1/pages") return ok({ id: "new", url: "https://www.notion.so/Nouvelle-" + "dd".repeat(16) });
    return new Response(JSON.stringify({ message: "inconnu" }), { status: 404 });
  };
  return { f, calls };
}

await test("identifiant de page depuis une URL Notion", () => {
  assert.equal(pageIdOf(`https://www.notion.so/Offre-${PAGE_ID}`), "40704136-fa74-81aa-a399-cd6896ce1062");
  assert.equal(pageIdOf(`https://app.notion.com/p/${PAGE_ID}?pvs=204`), "40704136-fa74-81aa-a399-cd6896ce1062");
  assert.throws(() => pageIdOf("javascript:alert(1)"));
});

await test("lecture de la vue des offres : format du connecteur, pagination, corbeille exclue", async () => {
  const { f } = fakeNotion();
  const r = await makeNotion("t", f).run("notion-query-data-sources", { data: { mode: "view", view_url: "view://bfcfcb20-ba5e-487c-af58-c94131515e21" } });
  assert.equal(r.results.length, 2);
  const row = r.results[0];
  assert.equal(row.Poste, "Chargé·e d'études faune");
  assert.deepEqual(row.Domaine, ["Biodiversité", "Forêt"]);
  assert.equal(row["date:Date de publication:start"], "2026-10-30");
  assert.equal(row["date:Date de candidature:start"], null);
  assert.equal(row["À compléter"], "__YES__");
  assert.equal(row["Ajouté le"], "2026-11-01T05:40:00.000Z");
  assert.match(row.url, /^https:\/\/www\.notion\.so\//);
});

await test("lecture des sources : la propriété URL devient userDefined:URL", async () => {
  const { f } = fakeNotion();
  const r = await makeNotion("t", f).run("notion-query-data-sources", { data: { view_url: "view://c83f1989-7d12-4c18-acec-3124570670e8" } });
  assert.equal(r.results[0]["userDefined:URL"], "https://ofb.gouv.fr");
  assert.equal(r.results[0].Active, "__NO__");
});

await test("vue inconnue refusée", async () => {
  const { f } = fakeNotion();
  await assert.rejects(makeNotion("t", f).run("notion-query-data-sources", { data: { view_url: "view://autre" } }), { code: "not_in_manifest" });
});

await test("passage en Candidaté avec date", async () => {
  const { f, calls } = fakeNotion();
  await makeNotion("t", f).run("notion-update-page", { page_id: `https://www.notion.so/Offre-${PAGE_ID}`, command: "update_properties",
    properties: { Statut: "Candidaté", "date:Date de candidature:start": "2026-11-03", "date:Date de candidature:is_datetime": 0 } });
  const patch = calls.find(c => c.method === "PATCH");
  assert.deepEqual(patch.body.properties, { Statut: { select: { name: "Candidaté" } }, "Date de candidature": { date: { start: "2026-11-03" } } });
});

await test("modification d'une page hors des bases du Radar refusée", async () => {
  const { f, calls } = fakeNotion();
  await assert.rejects(makeNotion("t", f).run("notion-update-page", { page_id: OTHER_ID, command: "update_properties", properties: { Statut: "Favori" } }), { code: "not_in_manifest" });
  await assert.rejects(makeNotion("t", f).run("notion-delete-pages", { page_ids: [OTHER_ID] }), { code: "not_in_manifest" });
  assert.equal(calls.filter(c => c.method === "PATCH").length, 0);
});

await test("création d'une offre par lien (propriétés de l'artifact)", async () => {
  const { f, calls } = fakeNotion();
  const r = await makeNotion("t", f).run("notion-create-pages", { parent: { data_source_id: OFFERS_DS }, pages: [{ properties: {
    Poste: "Écologue", Lien: "https://example.org/x", Source: "Ajout manuel", Statut: "Favori", "À compléter": "__YES__", Domaine: ["Forêt"],
    "date:Date de publication:start": "2026-11-01", "date:Date de publication:is_datetime": 0, Résumé: "x".repeat(4500) } }] });
  assert.match(r.pages[0].url, /notion\.so/);
  const post = calls.find(c => c.method === "POST" && c.path === "/v1/pages");
  assert.equal(post.body.parent.data_source_id, OFFERS_DS);
  assert.equal(post.body.properties["À compléter"].checkbox, true);
  assert.equal(post.body.properties.Résumé.rich_text.length, 3); // découpé en blocs de 1900 caractères
  assert.deepEqual(post.body.properties.Domaine.multi_select, [{ name: "Forêt" }]);
});

await test("création dans une autre base refusée", async () => {
  const { f } = fakeNotion();
  await assert.rejects(makeNotion("t", f).run("notion-create-pages", { parent: { data_source_id: "autre" }, pages: [{ properties: {} }] }), { code: "not_in_manifest" });
});

await test("ajout d'une source (userDefined:URL, Active)", async () => {
  const { f, calls } = fakeNotion();
  await makeNotion("t", f).run("notion-create-pages", { parent: { data_source_id: SOURCES_DS }, pages: [{ properties: { Nom: "OFB", "userDefined:URL": "https://ofb.gouv.fr", Type: "Public", Active: "__YES__" } }] });
  const post = calls.find(c => c.path === "/v1/pages");
  assert.deepEqual(post.body.properties.URL, { url: "https://ofb.gouv.fr" });
  assert.deepEqual(post.body.properties.Active, { checkbox: true });
});

await test("suppression = corbeille Notion", async () => {
  const { f, calls } = fakeNotion();
  await makeNotion("t", f).run("notion-delete-pages", { page_ids: [`https://www.notion.so/x-${PAGE_ID}`], user_confirmed: true });
  assert.deepEqual(calls.find(c => c.method === "PATCH").body, { in_trash: true });
});

await test("outil inconnu refusé", async () => {
  await assert.rejects(makeNotion("t", fakeNotion().f).run("notion-search", {}), { code: "not_in_manifest" });
});

// ---------- faux Claude ----------
await test("JSON extrait d'une réponse avec bloc de code", () => {
  assert.deepEqual(parseJSON('```json\n{"a":1}\n```'), { a: 1 });
  assert.deepEqual(parseJSON('Voici : [{"i":0}] fin'), [{ i: 0 }]);
  assert.throws(() => parseJSON("pas de json"), { code: "invalid_json" });
});

await test("niveaux : Opus 5.5 avec repli de sécurité, Haiku 5.5 pour la lecture rapide", async () => {
  const seen = [];
  const fake = {
    beta: { messages: { create: async p => { seen.push(p); return { stop_reason: "end_turn", content: [{ type: "thinking", thinking: "" }, { type: "text", text: '{"ok":true}' }] }; } } },
    messages: { create: async p => { seen.push(p); return { stop_reason: "end_turn", content: [{ type: "text", text: '{"poste":"x"}' }] }; } },
  };
  const c = makeClaude("k", fake);
  assert.deepEqual(await c.json("analyse", "default"), { ok: true });
  assert.deepEqual(await c.json("annonce", "quick"), { poste: "x" });
  assert.equal(seen[0].model, "claude-opus-5-5");
  assert.equal(seen[0].fallbacks, "default");
  assert.deepEqual(seen[0].betas, ["server-side-fallback-2026-07-01"]);
  assert.equal(seen[1].model, "claude-haiku-5-5");
  assert.equal(seen[1].fallbacks, undefined);
});

await test("refus de Claude signalé", async () => {
  const fake = { beta: { messages: { create: async () => ({ stop_reason: "refusal", content: [] }) } } };
  await assert.rejects(makeClaude("k", fake).json("x"), { code: "refused" });
});

// ---------- serveur complet ----------
const ENV = { APP_PASSWORD: "un-mot-de-passe-assez-long-42", NOTION_TOKEN: "t", ANTHROPIC_API_KEY: "k", ALLOWED_ORIGINS: "https://vincentlg751.github.io" };
const req = (path, { method = "POST", pass = ENV.APP_PASSWORD, origin = "https://vincentlg751.github.io", body, ip = "1.2.3.4" } = {}) =>
  new Request("https://radar-emploi.exemple.workers.dev" + path, { method, headers: { ...(pass ? { Authorization: "Bearer " + pass } : {}), Origin: origin, "Content-Type": "application/json", "CF-Connecting-IP": ip }, body: body ? JSON.stringify(body) : undefined });

await test("mot de passe exigé", async () => {
  assert.equal((await worker.fetch(req("/ping", { method: "GET", pass: null }), ENV)).status, 401);
  assert.equal((await worker.fetch(req("/ping", { method: "GET", pass: "faux" }), ENV)).status, 401);
  const ok = await worker.fetch(req("/ping", { method: "GET" }), ENV);
  assert.equal(ok.status, 200);
  assert.equal(ok.headers.get("Access-Control-Allow-Origin"), "https://vincentlg751.github.io");
});

await test("origine inconnue : pas d'en-tête CORS (le navigateur bloque la réponse)", async () => {
  const r = await worker.fetch(req("/ping", { method: "GET", origin: "https://pirate.example" }), ENV);
  assert.equal(r.headers.get("Access-Control-Allow-Origin"), null);
  const pre = await worker.fetch(new Request("https://x/ping", { method: "OPTIONS", headers: { Origin: "https://pirate.example" } }), ENV);
  assert.equal(pre.status, 403);
  const app = await worker.fetch(new Request("https://x/ping", { method: "OPTIONS", headers: { Origin: "capacitor://localhost" } }), ENV);
  assert.equal(app.status, 204);
});

await test("essais de mot de passe freinés après 10 échecs", async () => {
  for (let i = 0; i < 10; i++) await worker.fetch(req("/ping", { method: "GET", pass: "faux", ip: "9.9.9.9" }), ENV);
  assert.equal((await worker.fetch(req("/ping", { method: "GET", ip: "9.9.9.9" }), ENV)).status, 429);
});

await test("mot de passe trop court refusé par le serveur", async () => {
  assert.equal((await worker.fetch(req("/ping", { method: "GET", pass: "court" }), { ...ENV, APP_PASSWORD: "court" })).status, 500);
});

await test("seul le serveur Notion est relayé", async () => {
  const r = await worker.fetch(req("/mcp", { body: { server: "Claude Docs", tool: "batch", args: {} } }), ENV);
  assert.equal(r.status, 403);
});

console.log(failed ? `\n${failed} test(s) en échec` : "\nTous les tests passent.");
process.exit(failed ? 1 : 0);
