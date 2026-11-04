// Relais Notion du Radar Emploi Nature.
//
// L'application d'origine (artifact claude.ai) parle à Notion par le connecteur MCP de claude.ai,
// avec des propriétés « à plat » : "date:Date de publication:start", "Domaine": [...],
// "À compléter": "__YES__", "userDefined:URL"… Ce module reproduit exactement ces quatre outils
// (lecture d'une vue, mise à jour, création, mise à la corbeille) avec l'API officielle de Notion,
// pour que l'application garde le même code.
//
// Sécurité : seules les deux bases du Radar sont accessibles. Toute page visée est relue et son
// parent vérifié avant modification ; aucune autre page de l'espace Notion ne peut être touchée.

export const OFFERS_DS = "7d5552ba-961d-4a01-a94d-af4343774545";
export const SOURCES_DS = "cb83dfc0-dd8f-4afa-a84c-a544bff96be3";
// Vues utilisées par l'application -> base correspondante (les deux vues ne filtrent rien).
export const VIEWS = {
  "view://bfcfcb20-ba5e-487c-af58-c94131515e21": OFFERS_DS,
  "view://c83f1989-7d12-4c18-acec-3124570670e8": SOURCES_DS,
};
const ALLOWED_DS = new Set([OFFERS_DS, SOURCES_DS]);
const NOTION_VERSION = "2025-09-03";
const API = "https://api.notion.com/v1";

export class ToolError extends Error {
  constructor(code, message, status = 400) { super(message); this.code = code; this.status = status; }
}

const hex = s => String(s || "").replace(/-/g, "").toLowerCase();
const dashed = h => `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;

/** Identifiant de page à partir d'une URL Notion ou d'un identifiant (avec ou sans tirets). */
export function pageIdOf(v) {
  const s = String(v || "").split("?")[0];
  const m = s.match(/([0-9a-f]{32})$/i) || s.match(/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$/i);
  if (!m) throw new ToolError("tool_error", "Identifiant de page Notion invalide.");
  return dashed(hex(m[1]));
}

export function makeNotion(token, fetchImpl = fetch) {
  async function call(method, path, body) {
    let res;
    try {
      res = await fetchImpl(API + path, {
        method,
        headers: { Authorization: `Bearer ${token}`, "Notion-Version": NOTION_VERSION, "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      });
    } catch {
      throw new ToolError("server_unavailable", "Notion ne répond pas.", 502);
    }
    const data = await res.json().catch(() => ({}));
    if (res.ok) return data;
    if (res.status === 401) throw new ToolError("needs_reauth", "La clé Notion du serveur est refusée.", 502);
    if (res.status === 404) throw new ToolError("tool_error", "Page ou base introuvable : l'intégration Notion est-elle connectée aux bases « Veille offres emploi écologie » et « Sources de recherche » ?", 502);
    if (res.status === 429 || res.status >= 500) throw new ToolError("server_unavailable", "Notion est momentanément indisponible.", 502);
    throw new ToolError("tool_error", String(data.message || `Erreur Notion ${res.status}`).slice(0, 300), 400);
  }

  const schemas = new Map();
  async function schema(ds) {
    if (!schemas.has(ds)) {
      const d = await call("GET", `/data_sources/${ds}`);
      schemas.set(ds, d.properties || {});
    }
    return schemas.get(ds);
  }

  // Le connecteur claude.ai renomme les propriétés qui portent le nom d'une colonne réservée.
  const keyOf = name => (/^(url|id|createdtime)$/i.test(name) ? `userDefined:${name}` : name);
  const nameOf = key => key.replace(/^userDefined:/, "");

  function plain(rt) { return (rt || []).map(x => x.plain_text ?? x.text?.content ?? "").join(""); }
  function rich(s) {
    const text = String(s ?? "");
    const parts = [];
    for (let i = 0; i < text.length; i += 1900) parts.push({ type: "text", text: { content: text.slice(i, i + 1900) } });
    return parts;
  }

  /** Page Notion -> ligne « à plat », au format du connecteur claude.ai. */
  function toRow(page) {
    const row = { url: page.url, createdTime: page.created_time };
    for (const [name, p] of Object.entries(page.properties || {})) {
      const k = keyOf(name);
      switch (p.type) {
        case "title": case "rich_text": row[k] = plain(p[p.type]); break;
        case "select": row[k] = p.select?.name ?? null; break;
        case "status": row[k] = p.status?.name ?? null; break;
        case "multi_select": row[k] = (p.multi_select || []).map(x => x.name); break;
        case "url": row[k] = p.url ?? null; break;
        case "checkbox": row[k] = p.checkbox ? "__YES__" : "__NO__"; break;
        case "created_time": row[k] = p.created_time; break;
        case "number": row[k] = p.number; break;
        case "date":
          row[`date:${name}:start`] = p.date?.start ?? null;
          row[`date:${name}:end`] = p.date?.end ?? null;
          row[`date:${name}:is_datetime`] = p.date?.start ? (p.date.start.length > 10 ? 1 : 0) : null;
          break;
        default: break;
      }
    }
    return row;
  }

  /** Propriétés « à plat » -> propriétés de l'API Notion, d'après le schéma de la base. */
  async function toProps(ds, flat) {
    const sch = await schema(ds);
    const out = {}, dates = {};
    for (const [key, value] of Object.entries(flat || {})) {
      const dm = key.match(/^date:(.+):(start|end|is_datetime)$/);
      if (dm) { (dates[dm[1]] ||= {})[dm[2]] = value; continue; }
      const name = nameOf(key), def = sch[name];
      if (!def) throw new ToolError("tool_error", `Propriété inconnue : ${name}`);
      const empty = value == null || value === "";
      switch (def.type) {
        case "title": out[name] = { title: rich(value) }; break;
        case "rich_text": out[name] = { rich_text: empty ? [] : rich(value) }; break;
        case "select": out[name] = { select: empty ? null : { name: String(value) } }; break;
        case "status": out[name] = { status: empty ? null : { name: String(value) } }; break;
        case "multi_select": {
          const arr = Array.isArray(value) ? value : (() => { try { return JSON.parse(value || "[]"); } catch { return []; } })();
          out[name] = { multi_select: arr.map(n => ({ name: String(n) })) }; break;
        }
        case "url": out[name] = { url: empty ? null : String(value) }; break;
        case "checkbox": out[name] = { checkbox: value === true || value === "__YES__" }; break;
        case "number": out[name] = { number: empty ? null : Number(value) }; break;
        default: throw new ToolError("tool_error", `Propriété non modifiable : ${name}`);
      }
    }
    for (const [name, d] of Object.entries(dates)) {
      if (sch[name]?.type !== "date") throw new ToolError("tool_error", `Propriété date inconnue : ${name}`);
      out[name] = { date: d.start ? { start: String(d.start), ...(d.end ? { end: String(d.end) } : {}) } : null };
    }
    return out;
  }

  /** Relit la page et vérifie qu'elle appartient à l'une des deux bases du Radar. */
  async function guardedPage(idOrUrl) {
    const id = pageIdOf(idOrUrl);
    const page = await call("GET", `/pages/${id}`);
    const ds = page.parent?.data_source_id || page.parent?.database_id;
    const ok = page.parent?.data_source_id ? ALLOWED_DS.has(page.parent.data_source_id) : false;
    if (!ok) throw new ToolError("not_in_manifest", "Cette page n'appartient pas aux bases du Radar.", 403);
    return { id, ds, page };
  }

  const tools = {
    async "notion-query-data-sources"(args) {
      const data = args?.data || {};
      const ds = VIEWS[data.view_url] || (ALLOWED_DS.has(data.data_source_id) ? data.data_source_id : null);
      if (!ds) throw new ToolError("not_in_manifest", "Vue non autorisée.", 403);
      const results = [];
      let cursor = data.start_cursor || undefined, n = 0;
      do {
        const r = await call("POST", `/data_sources/${ds}/query`, { page_size: 100, ...(cursor ? { start_cursor: cursor } : {}) });
        for (const p of r.results || []) if (!p.in_trash && !p.archived) results.push(toRow(p));
        cursor = r.has_more ? r.next_cursor : undefined;
      } while (cursor && ++n < 40);
      return { results, has_more: false, next_cursor: null };
    },

    async "notion-update-page"(args) {
      if (args?.command !== "update_properties") throw new ToolError("tool_error", "Commande non prise en charge.");
      const { id, ds } = await guardedPage(args.page_id);
      const properties = await toProps(ds, args.properties);
      const page = await call("PATCH", `/pages/${id}`, { properties });
      return { url: page.url, id: page.id };
    },

    async "notion-create-pages"(args) {
      const ds = args?.parent?.data_source_id;
      if (!ALLOWED_DS.has(ds)) throw new ToolError("not_in_manifest", "Base non autorisée.", 403);
      const pages = Array.isArray(args.pages) ? args.pages.slice(0, 10) : [];
      const out = [];
      for (const p of pages) {
        const properties = await toProps(ds, p.properties);
        const page = await call("POST", "/pages", { parent: { type: "data_source_id", data_source_id: ds }, properties });
        out.push({ url: page.url, id: page.id });
      }
      return { pages: out };
    },

    async "notion-delete-pages"(args) {
      const ids = Array.isArray(args?.page_ids) ? args.page_ids.slice(0, 20) : [];
      const done = [];
      for (const v of ids) {
        const { id } = await guardedPage(v);
        await call("PATCH", `/pages/${id}`, { in_trash: true });
        done.push(id);
      }
      return { deleted: done };
    },
  };

  return {
    async run(tool, args) {
      const fn = tools[tool];
      if (!fn) throw new ToolError("not_in_manifest", "Outil non autorisé.", 403);
      return fn(args);
    },
  };
}
