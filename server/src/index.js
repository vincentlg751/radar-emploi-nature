// Serveur personnel de Radar Emploi Nature (Cloudflare Worker).
//
//   POST /mcp     { server: "Notion", tool, args }  -> { payload }   (lecture / écriture des deux bases du Radar)
//   POST /sample  { prompt, tier }                  -> { result }    (appel à Claude, réponse JSON)
//   GET  /ping                                      -> { ok: true }  (vérifie le mot de passe)
//
// Toutes les routes exigent « Authorization: Bearer <APP_PASSWORD> ».
// Secrets (Cloudflare) : NOTION_TOKEN, ANTHROPIC_API_KEY, APP_PASSWORD.
// Variable : ALLOWED_ORIGINS (adresses autorisées à appeler le serveur, séparées par des virgules).
import { makeNotion, ToolError } from "./notion.js";
import { makeClaude, SampleError } from "./claude.js";

const MAX_BODY = 400_000;
const DEFAULT_ORIGINS = ["https://localhost", "capacitor://localhost", "http://localhost"];

function origins(env) {
  return new Set([...DEFAULT_ORIGINS, ...String(env.ALLOWED_ORIGINS || "").split(",").map(s => s.trim()).filter(Boolean)]);
}

function cors(req, env) {
  const o = req.headers.get("Origin");
  if (!o || !origins(env).has(o)) return {};
  return {
    "Access-Control-Allow-Origin": o,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}

function json(data, status, headers) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", ...headers },
  });
}

async function sha256(s) {
  return new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)));
}
/** Comparaison en temps constant (sur les empreintes, de longueur fixe). */
async function samePassword(given, expected) {
  const [a, b] = await Promise.all([sha256(given), sha256(expected)]);
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

// Freine les essais de mot de passe (par adresse IP, au mieux : la mémoire est propre à chaque instance).
const failures = new Map();
function tooManyFailures(ip) {
  const f = failures.get(ip);
  return f && f.n >= 10 && Date.now() - f.t < 15 * 60e3;
}
function noteFailure(ip) {
  const f = failures.get(ip);
  const fresh = !f || Date.now() - f.t > 15 * 60e3;
  failures.set(ip, { n: fresh ? 1 : f.n + 1, t: fresh ? Date.now() : f.t });
  if (failures.size > 5000) failures.clear();
}

export default {
  async fetch(req, env) {
    const h = cors(req, env);
    if (req.method === "OPTIONS") return new Response(null, { status: h["Access-Control-Allow-Origin"] ? 204 : 403, headers: h });
    const { pathname } = new URL(req.url);

    if (!env.APP_PASSWORD || env.APP_PASSWORD.length < 16) return json({ code: "server_config", message: "Mot de passe du serveur absent ou trop court (16 caractères minimum)." }, 500, h);
    const ip = req.headers.get("CF-Connecting-IP") || "?";
    if (tooManyFailures(ip)) return json({ code: "auth", message: "Trop d'essais. Réessayez dans 15 minutes." }, 429, h);
    const auth = req.headers.get("Authorization") || "";
    const given = auth.startsWith("Bearer ") ? auth.slice(7) : "";
    if (!given || !(await samePassword(given, env.APP_PASSWORD))) { noteFailure(ip); return json({ code: "auth", message: "Mot de passe incorrect." }, 401, h); }
    failures.delete(ip);

    if (req.method === "GET" && pathname === "/ping") return json({ ok: true }, 200, h);
    if (req.method !== "POST") return json({ code: "not_found" }, 404, h);

    const raw = await req.text();
    if (raw.length > MAX_BODY) return json({ code: "prompt_too_large", message: "Requête trop volumineuse." }, 413, h);
    let body;
    try { body = JSON.parse(raw); } catch { return json({ code: "invalid_request", message: "JSON invalide." }, 400, h); }

    try {
      if (pathname === "/mcp") {
        if (body.server !== "Notion") return json({ code: "not_in_manifest", message: "Seul Notion est disponible." }, 403, h);
        if (!env.NOTION_TOKEN) return json({ code: "server_not_connected", message: "Clé Notion absente du serveur." }, 500, h);
        const payload = await makeNotion(env.NOTION_TOKEN).run(String(body.tool || ""), body.args || {});
        return json({ payload }, 200, h);
      }
      if (pathname === "/sample") {
        if (!env.ANTHROPIC_API_KEY) return json({ code: "sampling_disabled", message: "Clé API Claude absente du serveur." }, 500, h);
        const result = await makeClaude(env.ANTHROPIC_API_KEY).json(body.prompt, body.tier === "quick" ? "quick" : "default");
        return json({ result }, 200, h);
      }
      return json({ code: "not_found" }, 404, h);
    } catch (e) {
      if (e instanceof ToolError || e instanceof SampleError) return json({ code: e.code, message: e.message }, e.status, h);
      console.error(e);
      return json({ code: "server_error", message: "Erreur interne du serveur." }, 500, h);
    }
  },
};
