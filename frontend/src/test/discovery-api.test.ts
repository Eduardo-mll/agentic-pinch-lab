import { describe, expect, it } from "vitest";
import { discoveryRun, experimentRecord, isVerifiedEngineResult } from "@/lib/discovery-api";

const record = {
  run_id: "RUN-001", evidence_ids: ["EVID-001"],
  evidence: { status: "OK", items: [{ evidence_id: "EVID-001", title: "Process baseline" }] },
  hypothesis: { id: "HYP-001", text: "Reduce utility demand", status: "TESTED" },
  experiment: { experiment_id: "EXP-001", variable: "delta_t_min", baseline_value: 10, proposed_value: 7.5 },
  validation: { status: "PASS" },
  result: { generated_by: "SCIENCE_PINCH_ENGINE", status: "VALID", delta_t_min: 7.5, heat_recovery_kw: 502.5, heating_utility_kw: 87.5, cooling_utility_kw: 82.5, hot_pinch_c: 77.5, cold_pinch_c: 70 },
  analysis: { status: "SUPPORTED", learning: "Results support the hypothesis" },
  next_decision: { reason: "Explore 6 degrees", experiment: { delta_t_min: 6 } },
};

describe("discovery API contract", () => {
  it("accepts handoff-shaped records and verifies only Python calculations", () => {
    const parsed = experimentRecord.parse(record);
    expect(isVerifiedEngineResult(parsed)).toBe(true);
    expect(isVerifiedEngineResult({ ...parsed, result: { ...parsed.result, generated_by: "FAKE_EXPERIMENT" } })).toBe(false);
    expect(isVerifiedEngineResult({ ...parsed, validation: { status: "REJECTED" } })).toBe(false);
  });

  it("rejects missing calculation values instead of showing invented values", () => {
    expect(experimentRecord.safeParse({ ...record, result: { ...record.result, heat_recovery_kw: undefined } }).success).toBe(false);
  });

  it("accepts a two-step discovery run and its agentic proof", () => {
    const run = discoveryRun.parse({ status: "ok", steps: 2, experiments: [record, { ...record, experiment: { ...record.experiment, experiment_id: "EXP-002", proposed_value: 6 } }], agentic_proof: { first_delta_t_min: 7.5, second_delta_t_min: 6, second_changed: true } });
    expect(run.agentic_proof.second_changed).toBe(true);
    expect(run.experiments[1]?.experiment.proposed_value).toBe(6);
  });
});