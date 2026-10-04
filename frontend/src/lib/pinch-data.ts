// Mock data for UI visualization only. Replace with values returned by the
// Python Pinch Analysis Engine (same shape) when the backend is connected.

export type PinchResult = {
  dTmin: number;
  heatingUtility: number; // kW
  coolingUtility: number; // kW
  heatRecovery: number; // kW
  hotPinch: number; // °C
  coldPinch: number; // °C
};

export const sweep: PinchResult[] = [5, 10, 15, 20, 25, 30].map((dT) => ({
  dTmin: dT,
  heatingUtility: 75 + 2.5 * dT,
  coolingUtility: 70 + 2.5 * dT,
  heatRecovery: 515 - 2.5 * dT,
  hotPinch: 75 + dT / 2,
  coldPinch: 75 - dT / 2,
}));

export const reference = sweep[1]!;

// Comparison-table rows for the UI. Built from the same engine-shaped
// PinchResult values; swap `experiments` for an API response later.
export type ExperimentRow = PinchResult & {
  id: string; // run id, e.g. "E-003.1"
  baseline: boolean; // reference sweep point (ΔTmin = 10 °C)
  status: "Completed";
};

export const experiments: ExperimentRow[] = sweep.map((r, i) => ({
  ...r,
  id: `E-003.${i + 1}`,
  baseline: r.dTmin === reference.dTmin,
  status: "Completed",
}));

export type StageState = "completed" | "active" | "pending";

export const pipeline: {
  id: string;
  name: string;
  role: string;
  kind: "ai" | "engine";
  state: StageState;
  output: string;
}[] = [
  { id: "01", name: "Evidence Agent", role: "Evidence", kind: "ai", state: "completed", output: "4 sources validated" },
  { id: "02", name: "Hypothesis Agent", role: "Hypothesis", kind: "ai", state: "completed", output: "H-001 created" },
  { id: "03", name: "Experiment Planner", role: "Experiment", kind: "ai", state: "completed", output: "ΔTmin sweep · 6 runs" },
  { id: "04", name: "Python Pinch Engine", role: "Calculation", kind: "engine", state: "completed", output: "E-003 · 6/6 solved" },
  { id: "05", name: "Analysis Agent", role: "Analysis", kind: "ai", state: "active", output: "Interpreting trend…" },
];

export const activity = [
  { t: "14:02:11", who: "Evidence Agent", kind: "ai", msg: "4 sources validated" },
  { t: "14:02:48", who: "Hypothesis Agent", kind: "ai", msg: "Hypothesis H-001 created" },
  { t: "14:03:05", who: "Experiment Planner", kind: "ai", msg: "ΔTmin sweep generated" },
  { t: "14:03:41", who: "Python Engine", kind: "engine", msg: "Experiment E-003 completed" },
  { t: "14:03:58", who: "Analysis Agent", kind: "ai", msg: "Hypothesis supported" },
] as const;

export const streams = ["H1", "H2", "C1", "C2"];
