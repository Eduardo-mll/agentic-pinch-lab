import { z } from "zod";

// Match the backend handoff. Keep API wire names here so the UI never guesses
// scientific values or rewrites the backend's provenance.
const evidenceItem = z.object({
  evidence_id: z.string(),
  title: z.string(),
  source_type: z.string().optional(),
  claim_supported: z.string().optional(),
  confidence: z.string().optional(),
  approved: z.boolean().optional(),
});

export const experimentRecord = z.object({
  run_id: z.string(),
  timestamp: z.string().optional(),
  question: z.string().optional(),
  evidence_ids: z.array(z.string()).optional(),
  evidence: z.object({ status: z.string(), message: z.string().optional(), items: z.array(evidenceItem) }).optional(),
  hypothesis: z.object({ id: z.string(), text: z.string(), status: z.string(), expected_effect: z.string().optional(), direction: z.string().optional() }),
  experiment: z.object({ experiment_id: z.string(), variable: z.string(), baseline_value: z.number(), proposed_value: z.number(), expected_effect: z.string().optional(), reason: z.string().optional() }),
  validation: z.object({ status: z.string() }),
  result: z.object({
    generated_by: z.string(), status: z.string(), delta_t_min: z.number(),
    heat_recovery_kw: z.number(), heating_utility_kw: z.number(), cooling_utility_kw: z.number(),
    hot_pinch_c: z.number(), cold_pinch_c: z.number(), message: z.string().optional(),
  }),
  analysis: z.object({ status: z.string(), learning: z.string() }),
  next_decision: z.object({ reason: z.string(), experiment: z.object({ delta_t_min: z.number() }).optional() }),
});

export const discoveryRun = z.object({
  status: z.string(), steps: z.number(), experiments: z.array(experimentRecord),
  agentic_proof: z.object({ first_delta_t_min: z.number(), second_delta_t_min: z.number(), second_changed: z.boolean() }),
});
const latestResponse = z.object({ status: z.string(), record: experimentRecord.nullable() });
const historyResponse = z.object({ experiments: z.array(z.object({
  run_id: z.string(), experiment_id: z.string(), delta_t_min: z.number(), analysis_status: z.string(),
  hypothesis_id: z.string().optional(), evidence_ids: z.array(z.string()).optional(), path: z.string().optional(),
})) });
const evidenceResponse = z.object({ status: z.string(), count: z.number(), evidence: z.array(evidenceItem) });

export type ExperimentRecord = z.infer<typeof experimentRecord>;
export type DiscoveryRun = z.infer<typeof discoveryRun>;
export type EvidenceItem = z.infer<typeof evidenceItem>;

export function isVerifiedEngineResult(record: ExperimentRecord): boolean {
  return record.validation.status === "PASS" && record.result.status === "VALID" && record.result.generated_by === "SCIENCE_PINCH_ENGINE";
}

export const apiBaseUrl = (import.meta.env['VITE_API_BASE_URL'] ?? "").trim().replace(/\/+$/, "");
export const apiConfigured = Boolean(apiBaseUrl);

async function request<T>(path: string, schema: z.ZodType<T>, init?: RequestInit): Promise<T> {
  if (!apiConfigured) throw new Error("Discovery API is not configured.");
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, { ...init, headers: { Accept: "application/json", ...init?.headers } });
  } catch {
    throw new Error("Cannot reach the discovery API. Check its address and browser access.");
  }
  if (!response.ok) throw new Error(`Discovery API returned HTTP ${response.status}.`);
  const data: unknown = await response.json();
  const parsed = schema.safeParse(data);
  if (!parsed.success) throw new Error("Discovery API returned data that does not match the handoff contract.");
  return parsed.data;
}

export const discoveryApi = {
  run: () => request("/discovery/run", discoveryRun, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ steps: 2 }) }),
  latest: () => request("/discovery/latest", latestResponse),
  history: () => request("/discovery/history", historyResponse),
  evidence: () => request("/evidence", evidenceResponse),
  pinch: (deltaTmin: number) => request(`/pinch?delta_t_min=${encodeURIComponent(deltaTmin)}`, z.unknown()),
};