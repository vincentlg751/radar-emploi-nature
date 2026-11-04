// Relais Claude du Radar Emploi Nature.
//
// Remplace `claude.use("sample").json(prompt, { modelTier })` de l'artifact claude.ai :
// l'application envoie le prompt (inchangé), le serveur appelle l'API Claude avec la clé
// gardée côté serveur et renvoie l'objet JSON produit.
import Anthropic from "@anthropic-ai/sdk";

const MODELS = {
  // Analyses (CV, lettre, indice, conversation « Mes expériences »).
  default: { model: "claude-opus-5-5", effort: "medium", fallback: true },
  // Lecture rapide d'une annonce collée.
  quick: { model: "claude-haiku-5-5", effort: "low", fallback: false },
};
const MAX_PROMPT_CHARS = 200_000;
const SYSTEM = "Tu réponds uniquement avec le JSON demandé, sans texte avant ni après et sans bloc de code.";

export class SampleError extends Error {
  constructor(code, message, status = 400) { super(message); this.code = code; this.status = status; }
}

/** Extrait le premier objet ou tableau JSON d'un texte (tolère un bloc ```json). */
export function parseJSON(text) {
  const t = String(text || "").trim().replace(/^```(?:json)?\s*/i, "").replace(/```\s*$/, "").trim();
  try { return JSON.parse(t); } catch {}
  const start = t.search(/[\[{]/);
  if (start < 0) throw new SampleError("invalid_json", "Réponse sans JSON.", 502);
  const open = t[start], close = open === "{" ? "}" : "]";
  const end = t.lastIndexOf(close);
  if (end > start) { try { return JSON.parse(t.slice(start, end + 1)); } catch {} }
  throw new SampleError("invalid_json", "JSON illisible.", 502);
}

export function makeClaude(apiKey, client = new Anthropic({ apiKey, maxRetries: 2 })) {
  return {
    async json(prompt, tier = "default") {
      prompt = String(prompt || "");
      if (!prompt.trim()) throw new SampleError("invalid_request", "Prompt vide.");
      if (prompt.length > MAX_PROMPT_CHARS) throw new SampleError("prompt_too_large", "Prompt trop long.", 413);
      const cfg = MODELS[tier] || MODELS.default;
      const params = {
        model: cfg.model,
        max_tokens: 16000,
        system: SYSTEM,
        output_config: { effort: cfg.effort },
        messages: [{ role: "user", content: prompt }],
      };
      let res;
      try {
        // Si un filtre de sécurité refuse la demande, l'API la relance d'elle-même sur un autre modèle.
        res = cfg.fallback
          ? await client.beta.messages.create({ ...params, betas: ["server-side-fallback-2026-07-01"], fallbacks: "default" })
          : await client.messages.create(params);
      } catch (e) {
        if (e instanceof Anthropic.RateLimitError) throw new SampleError("rate_limited", "Trop de demandes.", 429);
        if (e instanceof Anthropic.AuthenticationError) throw new SampleError("sampling_disabled", "Clé API Claude refusée par Anthropic.", 502);
        if (e instanceof Anthropic.PermissionDeniedError) throw new SampleError("sampling_disabled", "Clé API Claude sans accès à ce modèle.", 502);
        if (e instanceof Anthropic.BadRequestError) {
          const tooLong = /prompt is too long|too many tokens|context/i.test(e.message || "");
          throw new SampleError(tooLong ? "prompt_too_large" : "invalid_request", String(e.message || "Requête refusée").slice(0, 300), 400);
        }
        if (e instanceof Anthropic.APIConnectionError) throw new SampleError("upstream_error", "Claude ne répond pas.", 502);
        if (e instanceof Anthropic.APIError) throw new SampleError("upstream_error", `Erreur Claude ${e.status ?? ""}`.trim(), 502);
        throw e;
      }
      if (res.stop_reason === "refusal") throw new SampleError("refused", "Claude a refusé cette demande.", 422);
      const text = (res.content || []).filter(b => b.type === "text").map(b => b.text).join("");
      if (res.stop_reason === "max_tokens") throw new SampleError("invalid_json", "Réponse tronquée.", 502);
      return parseJSON(text);
    },
  };
}
