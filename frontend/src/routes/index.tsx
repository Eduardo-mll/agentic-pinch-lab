import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Activity, ArrowDown, ArrowRight, ArrowUpRight, BookOpen, Check, ChevronDown, ChevronRight, Cpu, FlaskConical, Lightbulb, LineChart as LineIcon, Play, ShieldCheck, Sparkles, Target, Thermometer, Waves, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { activity, experiments, pipeline, reference, streams, sweep } from "@/lib/pinch-data";
import { apiConfigured, discoveryApi, isVerifiedEngineResult, type DiscoveryRun } from "@/lib/discovery-api";
import heroImage from "@/assets/pinch-hero.jpg.asset.json";
import networkImage from "@/assets/thermal-network.jpg";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [
    { title: "Agentic Pinch Lab — Scientific Workspace" },
    { name: "description", content: "Explore the Agentic Pinch Lab scientific workspace for heat exchange network optimization and AI-guided Pinch Analysis." },
    { property: "og:title", content: "Agentic Pinch Lab — Scientific Workspace" },
    { property: "og:description", content: "A scientific workspace for evidence, experiments, Pinch Analysis results, and interpretation." },
    { property: "og:type", content: "website" },
    { name: "twitter:card", content: "summary_large_image" },
  ] }),
  component: Dashboard,
});

const stageIcons = [BookOpen, Lightbulb, FlaskConical, Cpu, LineIcon];
const stageDetails = [
  { input: "Four-stream network (H1, H2, C1, C2) and sample scientific references.", output: "Evidence summary · 4 sources in the sample workspace.", provenance: "Evidence-backed · AI-generated summary; source verification is not connected." },
  { input: "Evidence summary and the objective to reduce external utility demand.", output: "H-001: Reducing ΔTmin is expected to increase heat recovery and decrease utility demand.", provenance: "AI-generated hypothesis · evidence-backed in the sample narrative, not independently verified." },
  { input: "Hypothesis H-001 and the four-stream network.", output: "AI-proposed experiment E-003 · sweep ΔTmin from 5 to 30 °C in six points.", provenance: "AI-proposed plan · parameters shown are illustrative." },
  { input: "Proposed ΔTmin sweep and the H1, H2, C1, C2 stream configuration.", output: "At 10 °C: 490 kW recovery, 100 kW heating, 95 kW cooling; hot/cold pinch 80 / 70 °C.", provenance: "Deterministic calculation · Calculated by Python · Physics-based result. These are sample values; the engine is not connected." },
  { input: "Sample sweep results from the Python-engine output area and hypothesis H-001.", output: "Sample interpretation: lower ΔTmin favors recovery; next proposed experiment E-004 adds an area cost model.", provenance: "AI-generated interpretation · not a calculated result or a connected agent response." },
] as const;

function SectionLabel({ children, ai = false }: { children: React.ReactNode; ai?: boolean }) {
  return <span className={`section-label ${ai ? "text-ai" : "text-primary"}`}><span className={`inline-block h-1.5 w-1.5 rounded-full ${ai ? "bg-ai" : "bg-primary"}`} />{children}</span>;
}

function Dashboard() {
  const [running, setRunning] = useState(false);
  const [selected, setSelected] = useState(reference.dTmin);
  const [expandedStage, setExpandedStage] = useState<number | null>(0);
  const [discovery, setDiscovery] = useState<DiscoveryRun | null>(null);
  const [runIndex, setRunIndex] = useState(0);
  const [runError, setRunError] = useState<string | null>(null);
  const liveRecords = discovery?.experiments ?? [];
  const liveRecord = liveRecords[runIndex];
  const livePoints = liveRecords.filter(isVerifiedEngineResult).map(record => ({
    id: record.experiment.experiment_id, dTmin: record.result.delta_t_min,
    heatingUtility: record.result.heating_utility_kw, coolingUtility: record.result.cooling_utility_kw,
    heatRecovery: record.result.heat_recovery_kw, hotPinch: record.result.hot_pinch_c,
    coldPinch: record.result.cold_pinch_c, status: record.result.status,
  }));
  const chartPoints = discovery ? livePoints : sweep;
  const current = discovery ? livePoints.find(point => point.id === liveRecord?.experiment.experiment_id) : sweep.find(point => point.dTmin === selected) ?? reference;
  const hasVerifiedSelection = !discovery || (liveRecord ? isVerifiedEngineResult(liveRecord) : false);
  const run = async () => {
    if (!apiConfigured) { setRunError("Connect the discovery API to run a scientific cycle. The displayed results are demonstration data."); return; }
    setRunning(true); setRunError(null);
    try { const response = await discoveryApi.run(); if (response.status !== "ok" || !response.experiments.length) throw new Error("The discovery API did not return completed experiments."); setDiscovery(response); setRunIndex(0); }
    catch (error) { setRunError(error instanceof Error ? error.message : "Unable to run the scientific cycle."); }
    finally { setRunning(false); }
  };
  const showLive = Boolean(discovery);
  const displayStages = pipeline.map((stage, index) => ({ ...stage, state: showLive ? (index === 3 && liveRecord && !isVerifiedEngineResult(liveRecord) ? "pending" : "completed") : stage.state,
    output: !liveRecord ? stage.output : [
      `${liveRecord.evidence?.items.length ?? liveRecord.evidence_ids?.length ?? 0} evidence records`,
      liveRecord.hypothesis.id,
      `${liveRecord.experiment.experiment_id} · ΔTmin ${liveRecord.experiment.proposed_value} °C`,
      `${liveRecord.result.status} · ${liveRecord.result.generated_by}`,
      liveRecord.analysis.status,
    ][index] ?? stage.output,
  }));
  const liveDetails = liveRecord ? [
    { input: liveRecord.question ?? "Scientific question", output: liveRecord.evidence?.items.map(item => `${item.evidence_id}: ${item.title}`).join(" · ") || liveRecord.evidence?.message || "No evidence records returned.", provenance: `Evidence IDs: ${liveRecord.evidence_ids?.join(", ") || "not provided"}` },
    { input: liveRecord.evidence?.items.map(item => item.evidence_id).join(", ") || "Evidence review", output: liveRecord.hypothesis.text, provenance: `AI-generated hypothesis ${liveRecord.hypothesis.id} · ${liveRecord.hypothesis.status}` },
    { input: liveRecord.hypothesis.text, output: `${liveRecord.experiment.experiment_id}: ${liveRecord.experiment.variable} ${liveRecord.experiment.proposed_value} °C. ${liveRecord.experiment.reason ?? ""}`, provenance: "AI-proposed experiment · parameter choice is not an engine result" },
    { input: `${liveRecord.experiment.variable} = ${liveRecord.experiment.proposed_value} °C`, output: isVerifiedEngineResult(liveRecord) ? `Recovery ${liveRecord.result.heat_recovery_kw} kW · heating ${liveRecord.result.heating_utility_kw} kW · cooling ${liveRecord.result.cooling_utility_kw} kW · hot/cold pinch ${liveRecord.result.hot_pinch_c} / ${liveRecord.result.cold_pinch_c} °C` : `No verified Pinch values (${liveRecord.result.status}).`, provenance: `${liveRecord.result.generated_by} · validation ${liveRecord.validation.status} · ${isVerifiedEngineResult(liveRecord) ? "Calculated by Python" : "Not a verified Python calculation"}` },
    { input: `${liveRecord.experiment.experiment_id} · ${liveRecord.result.status}`, output: liveRecord.analysis.learning, provenance: `AI-generated interpretation · ${liveRecord.analysis.status} · next: ${liveRecord.next_decision.reason}` },
  ] : stageDetails;

  return <div className="min-h-screen overflow-x-hidden bg-background text-foreground">
    <header className="absolute inset-x-0 top-0 z-20 border-b border-border/40 bg-background/60 backdrop-blur-xl">
      <div className="mx-auto flex h-20 max-w-[1500px] items-center justify-between gap-4 px-5 sm:px-8 lg:px-12">
        <a href="#top" className="flex shrink-0 items-center gap-3" aria-label="Agentic Pinch Lab, back to top"><span className="brand-symbol grid h-10 w-10 place-items-center rounded-sm border border-primary/50"><Activity className="h-5 w-5 text-primary" /></span><span className="text-sm font-bold leading-tight sm:text-base">AGENTIC<br /><span className="text-primary">PINCH LAB</span></span></a>
        <nav aria-label="Main navigation" className="hidden items-center gap-7 text-xs font-semibold uppercase text-muted-foreground md:flex"><a className="nav-link" href="#workflow">Workflow</a><a className="nav-link" href="#objective">Objective</a><a className="nav-link" href="#experiment">Experiment</a><a className="nav-link" href="#analysis">Analysis</a></nav>
        <Button variant="cycle" size="sm" onClick={run} disabled={running} className="h-10 rounded-sm px-4 font-semibold sm:px-5"><Play className="h-3.5 w-3.5 fill-current" />{running ? "Running…" : "Run cycle"}</Button>
      </div>
    </header>

    <main id="top">
      <section className="hero-stage relative isolate min-h-[650px] overflow-hidden border-b border-border/60">
        <img src={heroImage.url} alt="Illuminated industrial heat exchanger in a dark laboratory" width={1920} height={1080} className="absolute inset-0 -z-20 h-full w-full object-cover object-[63%_center]" />
        <div className="hero-shade absolute inset-0 -z-10" />
        <div className="mx-auto flex min-h-[650px] max-w-[1500px] flex-col justify-end px-5 pb-8 pt-32 sm:px-8 lg:px-12">
          <div className="mb-auto mt-8 flex items-center gap-2 font-mono text-[10px] uppercase text-primary/90"><span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse-dot" /> Scientific workspace <span className="mx-2 text-border">/</span> {showLive ? `${liveRecord?.experiment.experiment_id ?? "Discovery"} · API results` : "E-003 · sample cycle"} {running ? "running" : "ready"}</div>
          <div className="max-w-[820px] pb-12 lg:pb-16">
            <p className="mb-5 font-mono text-[11px] font-semibold uppercase text-primary sm:text-xs">Heat exchange network optimization <span className="mx-2 text-border">/</span> AI-guided Pinch Analysis</p>
            <h1 className="hero-title font-heading text-[clamp(4rem,9vw,9rem)] font-black uppercase leading-[0.82] text-foreground">AGENTIC<br /><span className="gradient-text">PINCH LAB</span></h1>
            <p className="mt-7 max-w-lg text-sm leading-relaxed text-muted-foreground sm:text-base">From scientific evidence to engineering insight. Explore how a four-stream network trades heat recovery against utility demand.</p>
            <div className="mt-8 flex flex-wrap items-center gap-4"><Button variant="cycle" size="lg" onClick={run} disabled={running} className="h-14 rounded-sm px-7 text-sm font-bold uppercase shadow-glow"><Play className="fill-current" />{running ? "Running cycle…" : "Run Scientific Cycle"}<ArrowUpRight /></Button><a className="inline-flex h-12 items-center gap-2 border-b border-primary/70 px-1 text-xs font-semibold uppercase text-foreground transition-colors hover:text-primary" href="#workflow">Explore the workflow <ArrowDown className="h-4 w-4" /></a></div>
          </div>
          {runError && <p role="alert" className="mb-4 max-w-lg border-l-2 border-ai bg-background/80 px-4 py-3 text-sm text-foreground">{runError}</p>}
          <div className="flex flex-wrap gap-x-8 gap-y-3 border-t border-border/70 pt-5 font-mono text-[10px] uppercase text-muted-foreground sm:gap-x-12"><span><strong className="mr-2 text-base text-foreground">04</strong> process streams</span><span><strong className="mr-2 text-base text-foreground">{showLive ? String(liveRecords.length).padStart(2, "0") : "06"}</strong> {showLive ? "discovery experiments" : "sweep points"}</span><span><strong className="mr-2 text-base text-foreground">05</strong> workflow stages</span><span className="text-ai">{showLive ? "API response · provenance shown below" : "Sample workspace · engine not connected"}</span></div>
        </div>
      </section>

      <section id="workflow" className="section-band border-b border-border/60 py-20 sm:py-24">
        <div className="page-wrap">
          <div className="mb-11 flex flex-wrap items-end justify-between gap-5"><div><SectionLabel>01 / The process</SectionLabel><h2 className="section-title mt-4">Scientific <span className="gradient-text">workflow.</span></h2></div><p className="max-w-sm text-sm leading-relaxed text-muted-foreground">Follow the evidence through to interpretation. Select a stage to inspect its input, output, status, and provenance.</p></div>
          <p className="mb-6 max-w-3xl text-sm leading-relaxed text-muted-foreground">{showLive ? "This cycle is the Python discovery loop. Pinch numbers come from the engine. Omnigent, when used, calls these same tools and does not replace this loop." : "The six-point chart below is sample data. Run cycle starts the Python discovery loop, not a separate Omnigent session."}</p>
          <div className="mb-6 flex flex-wrap gap-x-6 gap-y-2 font-mono text-[10px] uppercase"><span className="flex items-center gap-2 text-ai"><span className="h-2 w-2 bg-ai" /> AI-generated reasoning</span><span className="flex items-center gap-2 text-primary"><span className="h-2 w-2 bg-primary" /> Python calculation area</span><span className="text-muted-foreground">{showLive ? `Python discovery loop · ${liveRecord?.run_id ?? "—"}` : "Sample six-point sweep · not the live loop"}</span></div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5" aria-label="Scientific workflow stages">
            {displayStages.map((stage, i) => { const Icon = stageIcons[i] ?? Cpu; const open = expandedStage === i; const engine = stage.kind === "engine"; return <div key={stage.id} className="relative min-w-0">
              <Button variant="ghost" type="button" onClick={() => setExpandedStage(open ? null : i)} aria-expanded={open} aria-controls="workflow-detail" className={`stage-card group relative flex h-full min-h-[245px] w-full flex-col items-stretch justify-start overflow-hidden rounded-sm border p-5 text-left text-foreground whitespace-normal transition-transform duration-300 hover:-translate-y-1 hover:text-foreground focus-visible:ring-2 ${engine ? "border-primary/50 bg-engine hover:bg-engine focus-visible:ring-primary" : "border-ai/25 bg-card/80 hover:bg-card focus-visible:ring-ai"} ${open ? engine ? "ring-1 ring-primary" : "ring-1 ring-ai" : ""}`}>
                <span className="flex w-full items-center justify-between font-mono text-[10px] text-muted-foreground"><span>{stage.id} / 05</span><span className={engine ? "text-primary" : "text-ai"}>{engine ? "PYTHON ENGINE" : "AI AGENT"}</span></span>
                <span className={`mt-8 grid h-12 w-12 place-items-center rounded-sm border ${engine ? "border-primary/40 bg-primary/10 text-primary" : "border-ai/40 bg-ai/10 text-ai"}`}><Icon className="h-6 w-6" /></span>
                <span className="mt-6 block text-base font-semibold leading-tight">{stage.name}</span><span className="mt-2 block font-mono text-[11px] text-muted-foreground">{stage.output}</span>
                <span className={`mt-auto flex w-full items-center justify-between border-t pt-4 font-mono text-[10px] uppercase ${engine ? "border-primary/20 text-primary" : "border-ai/20 text-ai"}`}><span>{engine ? "Deterministic calculation" : i === 0 ? "Evidence-backed" : i === 2 ? "AI-proposed" : "AI-generated"}</span><ChevronDown className={`h-4 w-4 shrink-0 transition-transform ${open ? "rotate-180" : ""}`} /></span>
              </Button>
              {i < pipeline.length - 1 && <><ArrowDown aria-hidden="true" className="absolute -bottom-[15px] left-1/2 z-10 h-4 w-4 -translate-x-1/2 text-primary sm:hidden" /><ArrowRight aria-hidden="true" className="absolute -right-[18px] top-1/2 z-10 hidden h-5 w-5 -translate-y-1/2 text-primary lg:block" /></>}
            </div>; })}
          </div>
          {expandedStage !== null && (() => { const stage = displayStages[expandedStage]; const detail = liveDetails[expandedStage]; if (!stage || !detail) return null; const engine = stage.kind === "engine"; return <div id="workflow-detail" className={`mt-4 border-l-2 ${engine ? "border-primary bg-engine" : "border-ai bg-card/70"}`}>
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 px-5 py-4 sm:px-7"><div className="flex flex-wrap items-center gap-3"><span className={`font-mono text-[11px] ${engine ? "text-primary" : "text-ai"}`}>{stage.id} / 05</span><h3 className="text-lg font-semibold">{stage.name}</h3></div><span className={`font-mono text-[10px] uppercase ${engine ? "text-primary" : "text-ai"}`}>{engine ? "Deterministic calculation" : "AI-generated reasoning"}</span></div>
            <dl className="grid gap-6 p-5 sm:grid-cols-2 sm:p-7 lg:grid-cols-4">{[
              { label: "Input", value: detail.input },
              { label: "Output", value: detail.output },
              { label: "Status", value: showLive ? stage.state : `${stage.state} · sample workflow, not a live run` },
              { label: "Provenance", value: detail.provenance },
            ].map(item => <div key={item.label} className="min-w-0"><dt className={`mb-2 font-mono text-[10px] font-semibold uppercase ${engine ? "text-primary" : "text-ai"}`}>{item.label}</dt><dd className="text-sm leading-relaxed text-foreground/85">{item.value}</dd></div>)}</dl>
          </div>; })()}
          <p className="mt-5 font-mono text-[10px] text-muted-foreground">{showLive ? `Discovery run ${liveRecord?.run_id ?? "—"} · engine provenance ${liveRecord?.result.generated_by ?? "unknown"}` : "Illustrative workflow status · no live cycle is connected"}</p>
        </div>
      </section>

      <section id="objective" className="border-b border-border/60 py-20 sm:py-28">
        <div className="page-wrap grid items-center gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:gap-16">
          <div><SectionLabel>02 / The mission</SectionLabel><h2 className="section-title mt-5">Find the energy<br /><span className="gradient-text">trade-off.</span></h2><p className="mt-6 max-w-lg text-base leading-relaxed text-muted-foreground">Study how <span className="font-mono text-foreground">ΔTmin</span> affects maximum heat recovery and external heating and cooling needs in a four-stream network.</p>
            <div className="mt-8 flex items-center gap-3"><Target className="h-5 w-5 text-primary" /><span className="font-mono text-xs uppercase text-foreground">Scientific objective / HEN optimization</span></div>
            <div className="mt-9 border-l-2 border-ai pl-5"><SectionLabel ai>Active hypothesis / {liveRecord?.hypothesis.id ?? "H-001"}</SectionLabel><blockquote className="mt-4 max-w-lg text-lg leading-relaxed text-foreground sm:text-xl">“{liveRecord?.hypothesis.text ?? "Reducing ΔTmin is expected to increase maximum heat recovery and decrease external utility requirements."}”</blockquote><div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-ai"><span className="inline-flex items-center gap-2"><ShieldCheck className="h-4 w-4" /> Evidence-backed · {showLive ? `${liveRecord?.evidence?.items.length ?? 0} records` : "4 sources (sample)"}</span><span className="border border-ai/40 px-2 py-1 font-mono text-[10px] uppercase">{liveRecord?.hypothesis.status ?? "Testing"}</span></div></div>
          </div>
          <div className="relative min-h-[330px] overflow-hidden rounded-sm border border-border sm:min-h-[460px]"><img src={networkImage} alt="Hot and cold streams crossing through an industrial heat exchanger" loading="lazy" width={1400} height={900} className="absolute inset-0 h-full w-full object-cover" /><div className="absolute inset-x-0 bottom-0 flex flex-wrap items-center justify-between gap-3 bg-background/85 px-5 py-4 backdrop-blur-md"><span className="font-mono text-[10px] uppercase text-muted-foreground">Four-stream network / illustrative visual</span><div className="flex gap-2">{streams.map(s => <span key={s} className={`border px-2 py-1 font-mono text-xs ${s.startsWith("H") ? "border-heat/50 text-heat" : "border-cool/50 text-cool"}`}>{s}</span>)}</div></div></div>
        </div>
      </section>

      <section id="experiment" className="section-band border-b border-border/60 py-20 sm:py-28"><div className="page-wrap">
        <div className="mb-10 flex flex-wrap items-end justify-between gap-6"><div><SectionLabel>03 / {showLive ? "Discovery experiments" : "E-003 · ΔTmin sweep"}</SectionLabel><h2 className="section-title mt-4">Experiment <span className="gradient-text">results.</span></h2></div><span className="inline-flex items-center gap-2 border border-primary/30 px-3 py-2 font-mono text-[10px] uppercase text-primary"><Cpu className="h-3.5 w-3.5" /> {showLive ? "API results · verified entries only" : "Engine-format sample data"}</span></div>
        <div className="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)] xl:grid-cols-[315px_minmax(0,1fr)]">
          <div className="border-t-2 border-primary bg-card/70 p-6"><div className="flex items-center gap-2 text-primary"><FlaskConical className="h-4 w-4" /><span className="section-label">Current experiment</span></div><div className="mt-6 font-mono text-4xl text-foreground">{liveRecord?.experiment.experiment_id ?? "E-003"}</div><p className="mt-3 text-sm text-muted-foreground">{liveRecord?.experiment.reason ?? "Vary the minimum temperature approach across six points."}</p><dl className="mt-8 space-y-4 text-xs">{[["Independent variable", liveRecord?.experiment.variable ?? "ΔTmin"], ["Range", showLive ? `${liveRecord?.experiment.proposed_value ?? "—"} °C` : "5 – 30 °C"], ["Runs", showLive ? `${liveRecords.length} API experiments` : "6 sample points"], ["Status", liveRecord?.validation.status ?? "Illustrative"]].map(([label, value]) => <div key={label} className="flex justify-between gap-3 border-b border-border pb-3"><dt className="text-muted-foreground">{label}</dt><dd className="font-mono text-foreground">{value}</dd></div>)}</dl><div className="mt-9 font-mono text-[11px] uppercase text-muted-foreground">{showLive ? "Inspect experiment" : "Inspect ΔTmin / °C"}</div><div className="mt-3 grid grid-cols-6 gap-1 lg:grid-cols-3">{showLive ? liveRecords.map((record, index) => <Button key={`${record.run_id}-${record.experiment.experiment_id}`} variant={runIndex === index ? "default" : "outline"} size="sm" aria-label={`Inspect ${record.experiment.experiment_id}`} aria-pressed={runIndex === index} onClick={() => setRunIndex(index)} className="h-10 min-w-0 rounded-sm px-0 font-mono text-xs">{record.experiment.proposed_value}</Button>) : sweep.map(s => <Button key={s.dTmin} variant={selected === s.dTmin ? "default" : "outline"} size="sm" aria-label={`Inspect ΔTmin ${s.dTmin} degrees Celsius`} aria-pressed={selected === s.dTmin} onClick={() => setSelected(s.dTmin)} className="h-10 min-w-0 rounded-sm px-0 font-mono text-xs">{s.dTmin}</Button>)}</div></div>
          <div className="min-w-0 border border-border bg-engine/75"><div className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-5 py-4"><div><div className="font-mono text-xs font-semibold uppercase text-primary">Energy Performance vs ΔTmin</div><p className="mt-1 text-[11px] text-muted-foreground">{showLive ? "Verified engine results from the discovery API" : "Sample visualization · awaiting Python engine connection"}</p></div><span className="flex items-center gap-1.5 font-mono text-[10px] uppercase text-primary"><Cpu className="h-3.5 w-3.5" /> Python Pinch Engine · {showLive ? "API" : "sample"}</span></div><div className="chart-grid h-[345px] p-3 pt-5 sm:h-[440px] sm:p-6">{chartPoints.length ? <ResponsiveContainer width="100%" height="100%"><LineChart data={chartPoints} margin={{ top: 10, right: 18, left: 0, bottom: 12 }}><CartesianGrid stroke="var(--border)" strokeDasharray="3 5" /><XAxis dataKey="dTmin" tick={{ fontFamily: "IBM Plex Mono", fontSize: 10, fill: "var(--muted-foreground)" }} label={{ value: "ΔTmin (°C)", position: "insideBottom", offset: -5, fontSize: 10, fill: "var(--muted-foreground)" }} /><YAxis tick={{ fontFamily: "IBM Plex Mono", fontSize: 10, fill: "var(--muted-foreground)" }} label={{ value: "Energy (kW)", angle: -90, position: "insideLeft", fontSize: 10, fill: "var(--muted-foreground)" }} /><Tooltip contentStyle={{ background: "var(--popover)", color: "var(--popover-foreground)", border: "1px solid var(--border)", borderRadius: 2, fontSize: 12 }} /><Legend verticalAlign="top" height={32} iconType="plainline" wrapperStyle={{ fontSize: 11 }} />{(!showLive || current) && <ReferenceLine x={current?.dTmin ?? selected} stroke="var(--primary)" strokeDasharray="4 4" />}<Line type="monotone" dataKey="heatRecovery" name="Heat recovery" stroke="var(--recovery)" strokeWidth={2.5} dot={{ r: 4, fill: "var(--recovery)" }} isAnimationActive={false} /><Line type="monotone" dataKey="heatingUtility" name="Heating utility" stroke="var(--heat)" strokeWidth={2} dot={{ r: 3, fill: "var(--heat)" }} isAnimationActive={false} /><Line type="monotone" dataKey="coolingUtility" name="Cooling utility" stroke="var(--cool)" strokeWidth={2} dot={{ r: 3, fill: "var(--cool)" }} isAnimationActive={false} /></LineChart></ResponsiveContainer> : <div className="flex h-full items-center justify-center text-sm text-muted-foreground">No validated Python results were returned.</div>}</div></div>
        </div>
        <div className="mt-10 flex flex-wrap items-center justify-between gap-3"><SectionLabel>Selected point / ΔTmin {current?.dTmin ?? "—"} °C</SectionLabel><span className="flex items-center gap-1.5 font-mono text-[10px] uppercase text-primary"><Cpu className="h-3.5 w-3.5" /> {showLive ? hasVerifiedSelection ? "Calculated by Python Pinch Engine · API result" : "Unverified result · engineering values hidden" : "Calculated by Python Pinch Engine · sample values, not live calculations"}</span></div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{[
          { label: "Maximum Heat Recovery", value: current?.heatRecovery ?? "—", unit: "kW", icon: Waves, color: "text-recovery" },
          { label: "Minimum Heating Utility", value: current?.heatingUtility ?? "—", unit: "kW", icon: Zap, color: "text-heat" },
          { label: "Minimum Cooling Utility", value: current?.coolingUtility ?? "—", unit: "kW", icon: Thermometer, color: "text-cool" },
          { label: "Hot / Cold Pinch Temperature", value: current ? `${current.hotPinch} / ${current.coldPinch}` : "—", unit: "°C", icon: Target, color: "text-primary" },
        ].map(item => { const Icon = item.icon; return <div key={item.label} className="flex min-w-0 flex-col rounded-sm border border-border bg-card/65 p-5"><div className="flex items-center justify-between gap-2"><span className="text-xs text-muted-foreground">{item.label}</span><Icon className={`h-4 w-4 shrink-0 ${item.color}`} /></div><div className={`mt-6 whitespace-nowrap font-mono text-2xl sm:text-3xl ${item.color}`}>{item.value}<span className="ml-1.5 text-xs text-muted-foreground">{item.unit}</span></div><div className="mt-auto flex flex-wrap items-center justify-between gap-2 border-t border-border pt-3"><span className="flex items-center gap-1.5 font-mono text-[9px] uppercase text-primary"><Cpu className="h-3 w-3" /> {showLive ? current ? "Calculated by Python Pinch Engine" : "No verified calculation" : "Calculated by Python Pinch Engine · sample"}</span>{!showLive && selected === reference.dTmin && <span className="font-mono text-[9px] uppercase text-muted-foreground">Baseline</span>}</div></div>; })}</div>
        {showLive && <div className="mt-6 border-l-2 border-primary bg-card/65 px-5 py-4 text-sm"><span className="font-mono text-xs uppercase text-primary">Reference baseline / 10 °C</span><p className="mt-2 text-muted-foreground">490 kW recovery · 100 kW heating · 95 kW cooling · hot/cold pinch 80 / 70 °C <span className="text-ai">(reference, not this run)</span></p>{current && <p className="mt-2 font-mono text-xs text-foreground">Vs baseline: recovery {current.heatRecovery - 490 > 0 ? "+" : ""}{current.heatRecovery - 490} kW · heating {current.heatingUtility - 100 > 0 ? "+" : ""}{current.heatingUtility - 100} kW · cooling {current.coolingUtility - 95 > 0 ? "+" : ""}{current.coolingUtility - 95} kW</p>}</div>}
        <div className="mt-14">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3"><SectionLabel>{showLive ? "Discovery experiment timeline" : "Experiment comparison / full sweep"}</SectionLabel><span className="flex items-center gap-1.5 font-mono text-[10px] uppercase text-primary"><Cpu className="h-3.5 w-3.5" /> {showLive ? "API provenance per result" : "Calculated by Python Pinch Engine · sample"}</span></div>
          <div className="overflow-x-auto border border-border bg-engine/75">
            <table className="w-full min-w-[920px] border-collapse text-left">
              <caption className="sr-only">Pinch analysis results for each ΔTmin point of experiment E-003</caption>
              <thead><tr className="border-b border-border">{["Experiment", "ΔTmin (°C)", "Heating Utility (kW)", "Cooling Utility (kW)", "Heat Recovery (kW)", "Hot Pinch (°C)", "Cold Pinch (°C)", "Status"].map(h => <th key={h} scope="col" className="whitespace-nowrap px-4 py-3 font-mono text-[10px] font-semibold uppercase text-muted-foreground">{h}</th>)}</tr></thead>
              <tbody>{(showLive ? liveRecords.map(record => ({ id: record.experiment.experiment_id, dTmin: record.experiment.proposed_value, heatingUtility: isVerifiedEngineResult(record) ? record.result.heating_utility_kw : "—", coolingUtility: isVerifiedEngineResult(record) ? record.result.cooling_utility_kw : "—", heatRecovery: isVerifiedEngineResult(record) ? record.result.heat_recovery_kw : "—", hotPinch: isVerifiedEngineResult(record) ? record.result.hot_pinch_c : "—", coldPinch: isVerifiedEngineResult(record) ? record.result.cold_pinch_c : "—", status: isVerifiedEngineResult(record) ? "VALID" : record.result.status, baseline: false })) : experiments).map((row, index) => { const baseline = row.baseline; return <tr key={row.id} onClick={() => showLive ? setRunIndex(index) : setSelected(row.dTmin)} className={`cursor-pointer border-b border-border/60 transition-colors last:border-0 hover:bg-primary/5 ${baseline ? "bg-primary/10" : ""}`}>
                <th scope="row" className={`whitespace-nowrap px-4 py-3 font-mono text-xs font-semibold ${baseline ? "text-primary" : "text-foreground"}`}>{row.id}{baseline && <span className="ml-2 border border-primary/50 px-1.5 py-0.5 font-mono text-[9px] uppercase text-primary">Baseline</span>}</th>
                <td className="px-4 py-3 font-mono text-sm text-foreground">{row.dTmin}</td>
                <td className="px-4 py-3 font-mono text-sm text-heat">{row.heatingUtility}</td>
                <td className="px-4 py-3 font-mono text-sm text-cool">{row.coolingUtility}</td>
                <td className="px-4 py-3 font-mono text-sm text-recovery">{row.heatRecovery}</td>
                <td className="px-4 py-3 font-mono text-sm text-foreground">{row.hotPinch}</td>
                <td className="px-4 py-3 font-mono text-sm text-foreground">{row.coldPinch}</td>
                <td className="px-4 py-3"><span className="inline-flex items-center gap-1.5 whitespace-nowrap font-mono text-[10px] uppercase text-success"><Check className="h-3 w-3" /> {row.status}</span></td>
              </tr>; })}</tbody>
            </table>
          </div>
          <p className="mt-3 font-mono text-[10px] text-muted-foreground">{showLive ? "Select a row to inspect the complete experiment · unverified results show —" : "Select a row to inspect that ΔTmin point above · sample values shaped for a future engine API response"}</p>
        </div>
      </div></section>

      <section id="analysis" className="border-b border-border/60 py-20 sm:py-28"><div className="page-wrap"><SectionLabel ai>04 / AI interpretation</SectionLabel><h2 className="section-title mt-4">What the results <span className="gradient-text">suggest.</span></h2><div className="mt-10 grid gap-10 lg:grid-cols-[1.25fr_0.75fr] lg:gap-16">
        <div className="border-t-2 border-ai bg-card/50 p-6 sm:p-8"><div className="flex flex-wrap items-center justify-between gap-3"><span className="flex items-center gap-2 font-mono text-xs uppercase text-ai"><Sparkles className="h-4 w-4" /> Analysis agent / {showLive ? "API" : "sample"}</span><span className="font-mono text-[10px] text-muted-foreground">{liveRecord?.hypothesis.id ?? "H-001"}</span></div><h3 className="mt-8 flex items-center gap-3 text-2xl font-semibold">{showLive ? `Hypothesis ${liveRecord?.analysis.status.toLowerCase() ?? "unknown"}` : "Hypothesis supported"} {(!showLive || liveRecord?.analysis.status === "SUPPORTED") && <Check className="h-5 w-5 text-success" />}</h3><div className="mt-9 grid gap-8 sm:grid-cols-2"><div><h4 className="font-mono text-xs uppercase text-ai">{showLive ? "Evidence" : "Observed trend"}</h4><p className="mt-3 text-sm leading-relaxed text-muted-foreground">{showLive ? liveRecord?.evidence?.items.map(item => `${item.evidence_id}: ${item.title}`).join(" · ") || "No evidence items were returned." : <>Each +5 °C in ΔTmin reduces recovery by <span className="font-mono text-foreground">12.5 kW</span> and raises both utilities equally in this sample.</>}</p></div><div><h4 className="font-mono text-xs uppercase text-ai">{showLive ? "Learning" : "Engineering interpretation"}</h4><p className="mt-3 text-sm leading-relaxed text-muted-foreground">{liveRecord?.analysis.learning ?? "Lower ΔTmin cuts energy cost but requires more exchanger area — a capital versus operating trade-off."}</p></div></div><div className="mt-9 border-l-2 border-ai bg-ai-soft px-5 py-5"><h4 className="font-mono text-xs uppercase text-ai">Next {showLive ? "decision" : "experiment / E-004"}</h4><p className="mt-2 text-sm">{liveRecord?.next_decision.reason ?? "Add an area cost model and explore the optimal ΔTmin in the 8–14 °C range."}</p>{liveRecord?.next_decision.experiment && <p className="mt-2 font-mono text-xs text-ai">Proposed ΔTmin {liveRecord.next_decision.experiment.delta_t_min} °C</p>}</div>{discovery && <div className="mt-5 border border-ai/40 px-4 py-3 font-mono text-xs text-ai"><span className="font-semibold">Experiment #2 changed after result #1: {discovery.agentic_proof.second_changed ? "YES" : "NO"}</span><span className="mt-1 block text-muted-foreground">ΔTmin {discovery.agentic_proof.first_delta_t_min} °C → {discovery.agentic_proof.second_delta_t_min} °C · API proof</span></div>}<p className="mt-5 font-mono text-[10px] text-muted-foreground">{showLive ? `AI interpretation · run ${liveRecord?.run_id ?? "—"}` : "Sample interpretation · not generated by a connected agent"}</p></div>
        <div className="border-t border-border pt-6"><div className="flex items-center justify-between"><span className="font-mono text-xs uppercase text-foreground">{showLive ? "Discovery timeline" : "Activity stream"}</span><span className="font-mono text-[10px] text-muted-foreground">{showLive ? `${liveRecords.length} experiments / API` : "E-003 / sample"}</span></div><ol className="mt-7 space-y-6">{showLive ? liveRecords.map((record, index) => <li key={`${record.run_id}-${record.experiment.experiment_id}`} className="border-l-2 border-ai pl-5"><div className="font-mono text-[10px] text-ai">EXPERIMENT {index + 1} / {record.experiment.experiment_id}</div><div className="mt-1 text-sm font-semibold">ΔTmin {record.experiment.proposed_value} °C · {record.analysis.status}</div><p className="mt-1 text-xs text-muted-foreground">{record.analysis.learning}</p><p className="mt-1 text-xs text-muted-foreground">Next decision: {record.next_decision.reason}</p><p className="mt-2 font-mono text-[10px] text-primary">{isVerifiedEngineResult(record) ? `Engine: ${record.result.heat_recovery_kw} kW recovery · ${record.result.heating_utility_kw} kW heating · ${record.result.cooling_utility_kw} kW cooling` : `Unverified: ${record.result.generated_by}`}</p></li>) : activity.map(a => <li key={a.t} className={`border-l-2 pl-5 ${a.kind === "engine" ? "border-primary" : "border-ai"}`}><div className="flex items-center gap-3 font-mono text-[10px] text-muted-foreground"><span>{a.t}</span><span className={a.kind === "engine" ? "text-primary" : "text-ai"}>{a.kind === "engine" ? "ENGINE" : "AI AGENT"}</span></div><div className="mt-1 text-sm font-semibold">{a.who}</div><p className="mt-1 text-xs text-muted-foreground">{a.msg}</p></li>)}</ol></div>
      </div></div></section>

      <section className="closing-band relative overflow-hidden py-16 sm:py-20"><div className="page-wrap relative flex flex-wrap items-center justify-between gap-8"><div><SectionLabel>Continue the cycle</SectionLabel><h2 className="mt-4 text-3xl font-bold sm:text-5xl">The next insight starts here.</h2><p className="mt-3 text-sm text-muted-foreground">Scientific reasoning and calculated results, kept clearly apart.</p></div><Button variant="cycle" size="lg" onClick={run} disabled={running} className="h-14 rounded-sm px-7 text-sm font-bold uppercase shadow-glow"><Play className="fill-current" />{running ? "Running cycle…" : "Run Scientific Cycle"}<ChevronRight /></Button></div></section>
    </main>
    <footer className="border-t border-border bg-engine py-7"><div className="page-wrap flex flex-wrap items-center justify-between gap-3 font-mono text-[10px] uppercase text-muted-foreground"><span>Agentic Pinch Lab / Scientific workspace</span><span>{showLive ? "Discovery API response · engine provenance shown per run" : "Prototype · sample data · engine not connected"}</span></div></footer>
  </div>;
}
