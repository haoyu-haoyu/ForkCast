import { Fragment, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  Check,
  ChevronRight,
  ClipboardCheck,
  Clock,
  Database,
  FileText,
  GitCompare,
  Lock,
  MessageSquare,
  Play,
  RefreshCcw,
  ShieldCheck,
  SlidersHorizontal,
  UserRoundCheck,
  X,
} from "lucide-react";
import {
  approveCheckpoint,
  canProceedTo,
  createInitialControlState,
  editCheckpoint,
  rejectCheckpoint,
  rollbackToPrevious,
  type CheckpointKey,
  type DemoStep,
} from "./control";
import { agents, auditManifest, backtest, blindPrediction, caseGraph, impactReport, kaspaAnchor, simulation } from "./data";
import { approvePolicyRun, getPolicyRun, patchPolicyRunCaseGraph, startPolicyRun } from "./livePolicy";
import { diffCaseGraphReview, hasUnsavedReviewDiff } from "./liveReview";
import { displayEnglish } from "./displayEnglish";
import { SAMPLE_MEMOS } from "./data/sample_memos";
import {
  CACHED_FORK_COMPARISON,
  CACHED_VERIFY_TRANSCRIPT,
  STATIC_SHOWCASE,
  compareForks,
  createFork,
  verifyAnchor,
  type ForkApprovalEvent,
  type ForkComparison,
  type ForkCompareRow,
  type JsonPatchOp,
  type VerifyResult,
} from "./forkApi";
import { buildClaimsAuditRows, claimsAuditNotice, PROVENANCE_LABELS } from "./provenance";
import { RUBRIC_LABELS } from "./rubric";
import type { AgentProfile, BacktestRule, ClaimProvenanceRow, LivePolicyRunStatus, LivePolicyRunStatusName, SimulationEvent, Stakeholder } from "./types";

const demoSteps: Array<{ key: DemoStep; label: string; time: string; checkpoint?: CheckpointKey }> = [
  { key: "before", label: "Before", time: "0-8s" },
  { key: "select_case", label: "ULEZ selected", time: "8-16s" },
  { key: "extraction_review", label: "Approve extraction", time: "16-28s", checkpoint: "extraction_review" },
  { key: "agent_review", label: "Approve agents", time: "28-40s", checkpoint: "agent_review" },
  { key: "simulation_config", label: "Run controls", time: "40-46s", checkpoint: "simulation_config" },
  { key: "simulation_replay", label: "Simulation replay", time: "46-52s" },
  { key: "impact_report", label: "Impact report", time: "52-66s" },
  { key: "blind_backtest", label: "Blind rubric", time: "66-80s" },
  { key: "audit", label: "Audit + Kaspa", time: "80-88s", checkpoint: "report_chain_review" },
  { key: "closing", label: "Close", time: "88-90s" },
];

const checkpointSteps: CheckpointKey[] = [
  "extraction_review",
  "agent_review",
  "simulation_config",
  "report_chain_review",
];

function App() {
  const [control, setControl] = useState(createInitialControlState);
  const [activeStep, setActiveStep] = useState<DemoStep>(() =>
    window.location.hash === "#overture" ? "before" : "select_case",
  );
  const [stakeholders, setStakeholders] = useState(caseGraph.stakeholders);
  const [newStakeholder, setNewStakeholder] = useState("");
  const [disabledAgents, setDisabledAgents] = useState<Set<string>>(new Set());
  const [agentCount, setAgentCount] = useState(simulation.metadata.agent_count);
  const [rounds, setRounds] = useState(simulation.metadata.rounds);
  const [budget, setBudget] = useState(100);
  const [seedLocked, setSeedLocked] = useState(true);
  const [liveSample, setLiveSample] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState(agents[0]?.id ?? "");
  const [question, setQuestion] = useState("Why do you support or oppose this policy?");
  const [policyText, setPolicyText] = useState("");
  const [policyFileName, setPolicyFileName] = useState("");
  const [policyRunStatus, setPolicyRunStatus] = useState<"idle" | "running" | "awaiting_review" | "approving" | "succeeded" | "failed">("idle");
  const [policyRunError, setPolicyRunError] = useState("");
  const [policyRunResult, setPolicyRunResult] = useState<LivePolicyRunStatus | null>(null);
  const [reviewDraft, setReviewDraft] = useState<LivePolicyRunStatus["case_graph_ai"] | null>(null);
  const [reviewedClaims, setReviewedClaims] = useState<Set<string>>(new Set());
  const [claimVisibility, setClaimVisibility] = useState<Record<string, boolean>>(
    Object.fromEntries(backtest.rules.map((rule) => [rule.rule_id, true])),
  );
  const [chainDecision, setChainDecision] = useState<"pending" | "payload_approved" | "refused">("pending");

  const activeAgent = agents.find((agent) => agent.id === selectedAgentId) ?? agents[0];
  const feedEvents = liveSample ? simulation.events.slice(0, 12) : simulation.events.slice(0, 26);
  const groupCounts = useMemo(() => countBy(agents, "stakeholder_id"), []);
  const approvedCheckpoints = checkpointSteps.filter((key) => control.checkpoints[key].status === "approved").length;

  function approve(key: CheckpointKey) {
    const next = approveCheckpoint(control, key);
    setControl(next);
    setActiveStep(next.activeStep);
  }

  function reject(key: CheckpointKey) {
    const next = rejectCheckpoint(control, key);
    setControl(next);
    setActiveStep(key);
  }

  function edit(key: CheckpointKey, note: string) {
    setControl(editCheckpoint(control, key, note));
  }

  function rollback() {
    const next = rollbackToPrevious(control);
    setControl(next);
    setActiveStep(next.activeStep);
  }

  function addStakeholder() {
    const label = newStakeholder.trim() || "Community advice services";
    const stakeholder: Stakeholder = {
      id: `local_added_${Date.now()}`,
      name: label,
      archetype_group: "human_added_review_item",
      stance_prior: "unknown",
      interests: ["manual_review_required"],
    };
    setStakeholders((items) => [...items, stakeholder]);
    setNewStakeholder("");
    edit("extraction_review", `Added stakeholder '${label}' for human review.`);
  }

  function removeStakeholder(id: string) {
    setStakeholders((items) => items.filter((item) => item.id !== id));
    edit("extraction_review", `Removed stakeholder '${id}' from reviewed extraction.`);
  }

  function toggleAgent(agentId: string) {
    setDisabledAgents((current) => {
      const next = new Set(current);
      if (next.has(agentId)) next.delete(agentId);
      else next.add(agentId);
      return next;
    });
    edit("agent_review", `Toggled persona '${agentId}'.`);
  }

  async function readPolicyFile(file: File | undefined) {
    if (!file) return;
    setPolicyFileName(file.name);
    setPolicyText(await file.text());
    setPolicyRunError("");
  }

  async function runNewPolicyAnalysis() {
    setPolicyRunStatus("running");
    setPolicyRunError("");
    try {
      const started = await startPolicyRun({
        policyText,
        agentCount: Math.max(12, Math.min(agentCount, 50)),
        rounds: Math.max(1, Math.min(rounds, 3)),
      });
      const result = await pollPolicyRun(started.run_id, ["AWAITING_REVIEW", "FAILED"]);
      setPolicyRunResult(result);
      setReviewDraft(result.case_graph_approved || result.case_graph_ai || null);
      setPolicyRunStatus(result.status === "FAILED" ? "failed" : "awaiting_review");
    } catch (error) {
      setPolicyRunStatus("failed");
      setPolicyRunError(error instanceof Error ? error.message : "Policy analysis failed.");
    }
  }

  function updateReviewStakeholderWeight(index: number, weight: number) {
    if (!reviewDraft) return;
    const next = structuredClone(reviewDraft);
    if (!next.stakeholders[index]) return;
    next.stakeholders[index].weight = weight;
    setReviewDraft(next);
  }

  async function saveReviewEdits() {
    if (!policyRunResult?.run_id || !reviewDraft) return;
    setPolicyRunError("");
    try {
      await patchPolicyRunCaseGraph(policyRunResult.run_id, reviewDraft);
      const result = await getPolicyRun(policyRunResult.run_id);
      setPolicyRunResult(result);
      setReviewDraft(result.case_graph_approved || reviewDraft);
      setPolicyRunStatus(result.status === "FAILED" ? "failed" : "awaiting_review");
    } catch (error) {
      setPolicyRunStatus("failed");
      setPolicyRunError(error instanceof Error ? error.message : "Review update failed.");
    }
  }

  async function approveReviewAndContinue() {
    if (!policyRunResult?.run_id || !reviewDraft) return;
    if (!hasUnsavedReviewDiff(policyRunResult.case_graph_ai, reviewDraft)) {
      const approvedWithoutChanges = window.confirm("No changes were made — approve anyway?");
      if (!approvedWithoutChanges) return;
    }
    setPolicyRunStatus("approving");
    setPolicyRunError("");
    try {
      await patchPolicyRunCaseGraph(policyRunResult.run_id, reviewDraft);
      await approvePolicyRun(policyRunResult.run_id);
      const result = await pollPolicyRun(policyRunResult.run_id, ["AWAITING_ANCHOR_APPROVAL", "DONE", "FAILED"]);
      setPolicyRunResult(result);
      setReviewDraft(result.case_graph_approved || reviewDraft);
      setPolicyRunStatus(result.status === "FAILED" ? "failed" : "succeeded");
    } catch (error) {
      setPolicyRunStatus("failed");
      setPolicyRunError(error instanceof Error ? error.message : "Approval failed.");
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="logo-mark">
            <ShieldCheck size={28} />
          </div>
          <div>
            <h1>ForkCast</h1>
            <p>Review-gated impact analysis · scenario forks · Kaspa audit proof</p>
          </div>
        </div>
        <div className="topbar-actions">
          <StatusPill tone="neutral">● Demo Mode</StatusPill>
          <button
            className="status-pill safe pill-link"
            onClick={() => document.querySelector(".receipt")?.scrollIntoView({ behavior: "smooth", block: "center" })}
          >
            {kaspaAnchor.status === "anchored" ? "Anchored · TN-10" : "Local package"}
          </button>
          <TopbarTile
            icon={<Clock size={18} />}
            label="Demo script"
            value={`${demoSteps.find((step) => step.key === activeStep)?.time ?? "0-8s"} · step ${Math.max(1, demoSteps.findIndex((step) => step.key === activeStep) + 1)}/${demoSteps.length}`}
          />
          <TopbarTile label="Checkpoints" value={`${approvedCheckpoints} / ${checkpointSteps.length} approved`} />
          <TopbarTile label="Scenario" value="London ULEZ Expansion" />
          <TopbarTile label="Persona" value="Policy Maker" />
          <div className="avatar-chip">PM</div>
          <button className="secondary" onClick={rollback}>
            <ArrowLeft size={16} /> Rollback
          </button>
        </div>
      </header>

      <section className="workspace">
        <aside className="timeline-rail">
          <div className="rail-heading">
            <Clock size={18} />
            <div>
              <div className="rail-title">90-Second Demo Flow</div>
              <span>Step {Math.max(1, demoSteps.findIndex((step) => step.key === activeStep) + 1)} of {demoSteps.length}</span>
            </div>
          </div>
          {demoSteps.map((step) => (
            <button
              key={step.key}
              className={`timeline-step ${activeStep === step.key ? "active" : ""} ${
                step.checkpoint && control.checkpoints[step.checkpoint].status === "approved" ? "completed" : ""
              }`}
              onClick={() => setActiveStep(step.key)}
            >
              <span>{step.time}</span>
              <strong>{step.label}</strong>
              {step.checkpoint ? <CheckpointDot status={control.checkpoints[step.checkpoint].status} /> : null}
            </button>
          ))}
        </aside>

        <section className="main-stage">
          {activeStep !== "select_case" ? <DemoHeader activeStep={activeStep} /> : null}
          {activeStep === "before" && <BeforeScreen goToStep={setActiveStep} />}
          {activeStep === "select_case" && (
            <CaseSelectScreen
              goToStep={setActiveStep}
              policyText={policyText}
              setPolicyText={setPolicyText}
              policyFileName={policyFileName}
              onFile={readPolicyFile}
              onRun={runNewPolicyAnalysis}
              runStatus={policyRunStatus}
              runError={policyRunError}
              runResult={policyRunResult}
              reviewDraft={reviewDraft}
              onWeightChange={updateReviewStakeholderWeight}
              onSaveReview={saveReviewEdits}
              onApproveReview={approveReviewAndContinue}
            />
          )}
          {activeStep === "extraction_review" && (
            <ExtractionReview
              stakeholders={stakeholders}
              assumptions={caseGraph.assumptions}
              value={newStakeholder}
              onValue={setNewStakeholder}
              onAdd={addStakeholder}
              onRemove={removeStakeholder}
              onApprove={() => approve("extraction_review")}
              onReject={() => reject("extraction_review")}
            />
          )}
          {activeStep === "agent_review" && (
            <AgentReview
              blocked={!canProceedTo(control, "agent_review")}
              groupCounts={groupCounts}
              disabledAgents={disabledAgents}
              onToggleAgent={toggleAgent}
              onApprove={() => approve("agent_review")}
              onReject={() => reject("agent_review")}
            />
          )}
          {activeStep === "simulation_config" && (
            <SimulationConfig
              blocked={!canProceedTo(control, "simulation_config")}
              agentCount={agentCount}
              rounds={rounds}
              budget={budget}
              seedLocked={seedLocked}
              liveSample={liveSample}
              setAgentCount={setAgentCount}
              setRounds={setRounds}
              setBudget={setBudget}
              setSeedLocked={setSeedLocked}
              setLiveSample={setLiveSample}
              onApprove={() => approve("simulation_config")}
              onReject={() => reject("simulation_config")}
            />
          )}
          {activeStep === "simulation_replay" && <SimulationReplay events={feedEvents} liveSample={liveSample} />}
          {activeStep === "impact_report" && (
            <ImpactReport
              claimVisibility={claimVisibility}
              setClaimVisibility={setClaimVisibility}
              reviewedClaims={reviewedClaims}
              onReviewClaim={(id) => setReviewedClaims((current) => new Set(current).add(id))}
            />
          )}
          {activeStep === "blind_backtest" && <BlindBacktest />}
          {activeStep === "audit" && (
            <AuditReview
              blocked={!canProceedTo(control, "report_chain_review")}
              chainDecision={chainDecision}
              setChainDecision={setChainDecision}
              onApprove={() => approve("report_chain_review")}
              onReject={() => reject("report_chain_review")}
            />
          )}
          {activeStep === "closing" && <ClosingScreen />}
        </section>

        <aside className="side-panel">
          <PersonaChat
            selectedAgentId={selectedAgentId}
            setSelectedAgentId={setSelectedAgentId}
            agent={activeAgent}
            question={question}
            setQuestion={setQuestion}
          />
          <AuditSidebar control={control} />
        </aside>
      </section>
      <StatusDock />
    </main>
  );
}

function DemoHeader({ activeStep }: { activeStep: DemoStep }) {
  const current = demoSteps.find((step) => step.key === activeStep);
  return (
    <div className="demo-header">
      <div>
        <span>{current?.time}</span>
        <h2>{current?.label}</h2>
      </div>
      <p>{headlineFor(activeStep)}</p>
    </div>
  );
}

function BeforeScreen({ goToStep }: { goToStep: (step: DemoStep) => void }) {
  return (
    <Panel>
      <div className="overture">
        <h2>Policy takes weeks to assess. Approvals take seconds to fake.</h2>
        <p>ForkCast fixes both — review-gated impact analysis with a cryptographic receipt.</p>
        <button className="primary" onClick={() => goToStep("select_case")}>
          Enter the control room <ChevronRight size={16} />
        </button>
      </div>
      <div className="before-grid">
        <div>
          <h3>Legacy impact assessment</h3>
          <p className="large-copy">Weeks of consultants, surveys, hearings, spreadsheets and unverifiable handoffs.</p>
        </div>
        <Metric label="Typical cycle" value="3-8 weeks" tone="warn" />
        <Metric label="Traceability" value="Fragmented" tone="warn" />
        <Metric label="Human control" value="Late review" tone="warn" />
      </div>
      <div className="process-strip">
        {["Policy memo", "Consultants", "Hearings", "Spreadsheet", "Board pack"].map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>
    </Panel>
  );
}

function CaseSelectScreen({
  goToStep,
  policyText,
  setPolicyText,
  policyFileName,
  onFile,
  onRun,
  runStatus,
  runError,
  runResult,
  reviewDraft,
  onWeightChange,
  onSaveReview,
  onApproveReview,
}: {
  goToStep: (step: DemoStep) => void;
  policyText: string;
  setPolicyText: (value: string) => void;
  policyFileName: string;
  onFile: (file: File | undefined) => void;
  onRun: () => void;
  runStatus: "idle" | "running" | "awaiting_review" | "approving" | "succeeded" | "failed";
  runError: string;
  runResult: LivePolicyRunStatus | null;
  reviewDraft: LivePolicyRunStatus["case_graph_ai"] | null;
  onWeightChange: (index: number, weight: number) => void;
  onSaveReview: () => void;
  onApproveReview: () => void;
}) {
  const canRun = policyText.trim().length > 20 && !["running", "approving"].includes(runStatus);
  return (
    <Panel className="cockpit-panel">
      <div className="control-title">
        <div>
          <h3>ForkCast Control Cockpit</h3>
          <p>Review-gated policy impact analysis with verifiable audit proof.</p>
        </div>
        <div className="overall-status">
          <span>Overall status</span>
          <StatusPill tone="safe">In progress</StatusPill>
        </div>
      </div>
      <div className="stat-band" aria-label="Run scale">
        <div>
          <strong>{agents.length}</strong>
          <span>archetype agents</span>
        </div>
        <div>
          <strong>{simulation.events.length}</strong>
          <span>cached events</span>
        </div>
        <div>
          <strong>{backtest.rules.length}</strong>
          <span>rubric checks</span>
        </div>
        <div>
          <strong>2</strong>
          <span>verified TN-10 anchors</span>
        </div>
        <div>
          <strong>{simulation.metadata.rounds}</strong>
          <span>simulation rounds</span>
        </div>
        <div>
          <strong>4</strong>
          <span>human gates</span>
        </div>
      </div>
      <ProofRail />
      <div className="checkpoint-card-grid">
        <CheckpointSummaryCard
          number="1"
          title="Extraction Review"
          status="approved"
          metrics={[
            ["Data sources", "18 / 18"],
            ["Stakeholders", String(caseGraph.stakeholders.length)],
            ["Coverage", "Blind-safe"],
            ["Issues", "0"],
          ]}
          onOpen={() => goToStep("extraction_review")}
        />
        <CheckpointSummaryCard
          number="2"
          title="Agent Review"
          status="pending"
          metrics={[
            ["Agent recommendation", "Proceed"],
            ["Archetypes", String(agents.length)],
            ["Policy alignment", "High"],
            ["Risks flagged", "2"],
          ]}
          onOpen={() => goToStep("agent_review")}
        />
        <CheckpointSummaryCard
          number="3"
          title="Simulation Replay"
          status="pending"
          metrics={[
            ["Rounds", String(simulation.metadata.rounds)],
            ["Events cached", String(simulation.events.length)],
            ["Key signals", String(backtest.rules.length)],
            ["Mode", "Replay"],
          ]}
          onOpen={() => goToStep("simulation_replay")}
        />
        <CheckpointSummaryCard
          number="4"
          title="Impact Report"
          status="pending"
          metrics={[
            ["Claims reviewed", String(backtest.rules.length)],
            ["Rubric mode", "Blind"],
            ["Kaspa anchor", kaspaAnchor.status === "anchored" ? "Live tx" : "Local"],
            ["Disclaimers", "On"],
          ]}
          onOpen={() => goToStep("impact_report")}
        />
      </div>
      <div className="cockpit-grid">
        <CockpitCard title="Social Feed Simulation Preview" subtitle="Live preview (simulated)">
          <div className="mini-feed">
            {simulation.events.slice(0, 5).map((event) => (
              <div className="mini-feed-row" key={event.event_id}>
                <div className="channel-badge">{event.type === "post" ? "X" : event.type === "comment" ? "f" : "Δ"}</div>
                <div>
                  <strong>{event.agent_archetype}</strong>
                  <p>{truncate(event.content || event.reason || "stance update", 82)}</p>
                </div>
                <span>{event.stance || event.to_stance || "mixed"}</span>
              </div>
            ))}
          </div>
          <button className="link-button" onClick={() => goToStep("simulation_replay")}>
            View full stream <ChevronRight size={16} />
          </button>
        </CockpitCard>
        <CockpitCard title="Blind Rubric Coverage" subtitle="Answer-isolated R1-R6">
          <div className="compact-backtest">
            {backtest.rules.map((rule) => (
              <div className="compact-backtest-row" key={rule.rule_id}>
                <strong>{rule.rule_id}</strong>
                <span>{RUBRIC_LABELS[rule.rule_id] ?? rule.rule_id}</span>
                <em className={`verdict ${rule.verdict.toLowerCase().replace(" ", "-")}`}>{rule.verdict}</em>
              </div>
            ))}
          </div>
          <div className="dot-track" aria-label="Rubric coverage by rule">
            {backtest.rules.map((rule) => (
              <span
                key={rule.rule_id}
                className={`coverage-dot ${rule.verdict.toLowerCase().includes("hit") ? "hit" : "partial"}`}
                title={`${rule.rule_id}: ${rule.verdict}`}
              />
            ))}
          </div>
          <div className="hit-strip">
            <Metric label="Rubric covered" value="5 / 6" tone="safe" />
            <Metric label="Partial" value="R1" tone="warn" />
            <Metric label="Mechanism" value="Keyword rubric" tone="safe" />
          </div>
          <button className="link-button" onClick={() => goToStep("blind_backtest")}>
            View detailed rubric report <ChevronRight size={16} />
          </button>
        </CockpitCard>
        <ForkSnapshotCard goToStep={goToStep} />
        <CockpitCard title="Impact Summary" subtitle="Illustrative / demo estimates only">
          <div className="impact-summary-list">
            {[
              ["Prediction isolation", "No outcome data"],
              ["Prompt scan", "No outcome tokens"],
              ["Kaspa anchoring", kaspaAnchor.tx_id ? "Testnet tx live" : "Local package"],
              ["Chain verifier", `Overall ${CACHED_VERIFY_TRANSCRIPT.overall}`],
              ["Report mode", "Decision support"],
              ["Human grading", HUMAN_GRADING_PENDING_NOTE],
            ].map(([label, value]) => (
              <div key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
          <div className="net-impact-box">
            <span>Truth Status</span>
            <strong>ULEZ historical case verified</strong>
            <p>New policies show impact analysis only until a truth_set exists.</p>
          </div>
        </CockpitCard>
      </div>
      <div className="live-policy-card">
        <div className="panel-title-row compact">
          <div>
            <h3>Run a new policy document</h3>
            <p>
              This path calls the backend pipeline with DeepSeek extraction, archetype generation and report generation.
              New policies do not have a truth_set, so no historical grading material is shown.
            </p>
          </div>
          <StatusPill tone={runResult ? "safe" : "neutral"}>
            {runResult ? `${runResult.status} · ${displayEnglish(runResult.truth_set_status.message)}` : "Live analysis"}
          </StatusPill>
        </div>
        <div className="policy-run-grid">
          <div>
            <div className="upload-row">
              <label className="file-picker">
                <FileText size={16} /> Upload text / markdown
                <input
                  type="file"
                  accept=".txt,.md,.markdown,text/plain,text/markdown"
                  onChange={(event) => onFile(event.target.files?.[0])}
                />
              </label>
              <span>{policyFileName || "Paste policy text below if no file is selected."}</span>
            </div>
            <div className="sample-chips">
              <span>Try a sample:</span>
              {SAMPLE_MEMOS.map((memo) => (
                <button
                  key={memo.label}
                  className="sample-chip"
                  onClick={() => setPolicyText(memo.text)}
                >
                  {memo.label}
                </button>
              ))}
            </div>
            <textarea
              className="policy-input"
              value={policyText}
              onChange={(event) => setPolicyText(event.target.value)}
              placeholder="Paste a policy memo, consultation note or short policy description..."
            />
            <div className="run-actions">
              <button className="primary" onClick={onRun} disabled={!canRun}>
                <Play size={16} /> {runStatus === "running" ? "Running DeepSeek analysis..." : "Run real analysis"}
              </button>
              <StatusPill tone={runStatus === "failed" ? "warn" : runStatus === "succeeded" ? "safe" : "neutral"}>
                {runStatus}
              </StatusPill>
            </div>
            {runError ? <p className="error-note">{runError}</p> : null}
          </div>
          <LivePolicyResultPanel
            result={runResult}
            reviewDraft={reviewDraft}
            runStatus={runStatus}
            onWeightChange={onWeightChange}
            onSaveReview={onSaveReview}
            onApproveReview={onApproveReview}
          />
        </div>
      </div>
    </Panel>
  );
}

function CheckpointSummaryCard({
  number,
  title,
  status,
  metrics,
  onOpen,
}: {
  number: string;
  title: string;
  status: "approved" | "pending";
  metrics: Array<[string, string]>;
  onOpen: () => void;
}) {
  return (
    <div className={`checkpoint-summary-card ${status}`}>
      <div className="card-title-row">
        <span className="step-number">{number}</span>
        <strong>{title}</strong>
        <em className={status}>{status}</em>
      </div>
      <div className="card-metrics">
        {metrics.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <button className="primary" onClick={onOpen}>
        <Check size={15} /> Open checkpoint
      </button>
    </div>
  );
}

function CockpitCard({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <section className="cockpit-card">
      <div className="cockpit-card-title">
        <h4>{title}</h4>
        <span>{subtitle}</span>
      </div>
      {children}
    </section>
  );
}

function ProofRail() {
  return (
    <section className="proof-rail" aria-label="ForkCast proof points">
      <div>
        <span>Answer-isolated</span>
        <strong>Blind prediction</strong>
        <p>No truth_set or outcome tokens enter the prediction prompt.</p>
      </div>
      <div>
        <span>Review gated</span>
        <strong>Human checkpoints</strong>
        <p>Extraction, agents, run config and report/chain actions are explicit approvals.</p>
      </div>
      <div>
        <span>What-if ready</span>
        <strong>Scenario forks</strong>
        <p>Compare £12.50 versus £15.00 from the same reviewed baseline.</p>
      </div>
      <div>
        <span>Cryptographic receipt</span>
        <strong>Kaspa TN-10 proof</strong>
        <p>Anchored tx and local verifier both reach Overall: PASS.</p>
      </div>
    </section>
  );
}

function ForkSnapshotCard({ goToStep }: { goToStep: (step: DemoStep) => void }) {
  const comparison = CACHED_FORK_COMPARISON;
  const changedRisks = comparison.dimensions.risk_timeline.filter((row) => row.status === "changed").slice(0, 2);
  return (
    <CockpitCard title="Scenario Forks" subtitle="Cached showcase comparison">
      <div className="fork-snapshot-head">
        <div>
          <span>Baseline</span>
          <strong>{comparison.a.name}</strong>
        </div>
        <GitCompare size={22} />
        <div>
          <span>Variant</span>
          <strong>{comparison.b.name}</strong>
        </div>
      </div>
      <div className="fork-snapshot-summary">
        <Metric label="Changed" value={String(comparison.summary.changed)} tone="warn" />
        <Metric label="Unchanged" value={String(comparison.summary.unchanged)} tone="safe" />
      </div>
      <div className="fork-snapshot-list">
        {changedRisks.map((row) => (
          <div key={row.key}>
            <span>{row.key}</span>
            <p>{truncate(String(row.b?.signal ?? row.a?.signal ?? "Changed conclusion"), 118)}</p>
          </div>
        ))}
      </div>
      <p className="evidence-note">Illustrative rerun, not forecast accuracy. The fork engine keeps lineage explicit.</p>
      <button className="link-button" onClick={() => goToStep("extraction_review")}>
        Open fork workflow <ChevronRight size={16} />
      </button>
    </CockpitCard>
  );
}

function LivePolicyResultPanel({
  result,
  reviewDraft,
  runStatus,
  onWeightChange,
  onSaveReview,
  onApproveReview,
}: {
  result: LivePolicyRunStatus | null;
  reviewDraft: LivePolicyRunStatus["case_graph_ai"] | null;
  runStatus: "idle" | "running" | "awaiting_review" | "approving" | "succeeded" | "failed";
  onWeightChange: (index: number, weight: number) => void;
  onSaveReview: () => void;
  onApproveReview: () => void;
}) {
  if (!result) {
    return (
      <div className="live-result empty">
        <Database size={22} />
        <h4>Result will appear here</h4>
        <p>
          The cached ULEZ replay remains available for the 90-second demo. This panel is for new policies with no
          historical truth-set grading dataset.
        </p>
      </div>
    );
  }

  if (result.status === "FAILED") {
    return (
      <div className="live-result">
        <div className="result-header">
          <div>
            <span>{result.run_id}</span>
            <h4>Run failed at {result.failed?.stage ?? "unknown stage"}</h4>
          </div>
          <StatusPill tone="warn">FAILED</StatusPill>
        </div>
        <p className="error-note">{result.failed?.error ?? "Unknown failure"}</p>
      </div>
    );
  }

  if (result.status === "AWAITING_REVIEW") {
    const draft = reviewDraft || result.case_graph_approved || result.case_graph_ai;
    const visibleDiff = diffCaseGraphReview(result.case_graph_ai, draft);
    return (
      <div className="live-result review">
        <div className="result-header">
          <div>
            <span>{result.run_id}</span>
            <h4>{draft?.case_name ?? "Extraction review"}</h4>
          </div>
          <StatusPill tone="warn">Human review required</StatusPill>
        </div>
        <div className="result-block">
          <strong>Editable stakeholders</strong>
          <div className="review-table">
            {(draft?.stakeholders ?? []).map((stakeholder, index) => (
              <label className="review-row" key={stakeholder.id}>
                <span>{stakeholder.name}</span>
                <em>{stakeholder.stance_prior}</em>
                <input
                  type="number"
                  min="0"
                  max="3"
                  step="0.1"
                  value={stakeholder.weight ?? 1}
                  onChange={(event) => onWeightChange(index, Number(event.target.value))}
                />
              </label>
            ))}
          </div>
        </div>
        <div className="result-block">
          <strong>Assumptions</strong>
          {(draft?.assumptions ?? []).slice(0, 4).map((assumption) => (
            <p className={assumption.status === "已确认" ? "" : "low-confidence"} key={assumption.id}>
              {displayEnglish(assumption.status)}: {assumption.statement}
            </p>
          ))}
        </div>
        <div className="result-block diff-block">
          <strong>Visible diff</strong>
          {visibleDiff.length ? (
            visibleDiff.slice(0, 5).map((item) => (
              <p className="diff-line" key={item.path}>
                <code>{item.path}</code>: <span className="diff-before">{String(item.before)}</span> →{" "}
                <span className="diff-after">{String(item.after)}</span>
              </p>
            ))
          ) : result.review_diff.length ? (
            result.review_diff.slice(0, 5).map((item) => (
              <p className="diff-line" key={item.path}>
                <code>{item.path}</code>: <span className="diff-before">{String(item.before)}</span> →{" "}
                <span className="diff-after">{String(item.after)}</span>
              </p>
            ))
          ) : (
            <p>No human edits saved yet.</p>
          )}
        </div>
        <div className="run-actions">
          <button className="secondary" onClick={onSaveReview}>Save review edits</button>
          <button className="primary" onClick={onApproveReview} disabled={runStatus === "approving"}>
            <Check size={16} /> {runStatus === "approving" ? "Approving..." : "Approve and continue"}
          </button>
        </div>
      </div>
    );
  }

  const manifest = result.audit_manifest;
  const approvalDiff = manifest?.approval_event?.diff ?? [];
  const chainLinks = manifest?.hash_chain?.links ?? [];
  return (
    <div className="live-result">
      <div className="result-header">
        <div>
          <span>{result.run_id}</span>
          <h4>{result.case_graph_approved?.case_name ?? result.case_graph_ai?.case_name ?? "Live policy run"}</h4>
        </div>
        <StatusPill tone="warn">{displayEnglish(result.truth_set_status.message)}</StatusPill>
      </div>
      <div className="result-block">
        <strong>Extracted stakeholders</strong>
        {(result.case_graph_approved?.stakeholders ?? result.case_graph_ai?.stakeholders ?? []).slice(0, 5).map((stakeholder) => (
          <p key={stakeholder.id}>{stakeholder.name} · {stakeholder.stance_prior}</p>
        ))}
      </div>
      <div className="result-block">
        <strong>Generated archetypes</strong>
        <p>{result.agents?.agents.length ?? 0} archetype agents · no real-person PII</p>
      </div>
      <div className="result-block">
        <strong>Report signals</strong>
        {(result.impact_report?.risk_timeline ?? []).slice(0, 3).map((risk) => (
          <p key={risk.stage}>{risk.stage}: {risk.signal}</p>
        ))}
      </div>
      <div className="result-block">
        <strong>Mitigation options</strong>
        {(result.impact_report?.mitigation_options ?? []).slice(0, 2).map((item) => (
          <p key={item.option}>{item.option}: {item.rationale}</p>
        ))}
      </div>
      {manifest ? (
        <div className="result-block">
          <strong>Audit hash chain</strong>
          <p className="evidence-note">Head: {manifest.head_hash.slice(0, 18)}...</p>
          <div className="chain-link-list">
            {chainLinks.map((link) => (
              <div key={link.id}>
                <span>{link.id}</span>
                <em>{link.stage}</em>
                <code>{link.hash.slice(0, 14)}...</code>
              </div>
            ))}
          </div>
        </div>
      ) : null}
      {approvalDiff.length ? (
        <div className="result-block diff-block recorded">
          <strong>Human approval diff</strong>
          {approvalDiff.slice(0, 4).map((item) => (
            <p className="diff-line" key={item.path}>
              <code>{item.path}</code>: <span className="diff-before">{String(item.before)}</span> →{" "}
              <span className="diff-after">{String(item.after)}</span>
            </p>
          ))}
        </div>
      ) : null}
      <p className="evidence-note">{result.impact_report?.disclaimer}</p>
    </div>
  );
}

function ExtractionReview({
  stakeholders,
  assumptions,
  value,
  onValue,
  onAdd,
  onRemove,
  onApprove,
  onReject,
}: {
  stakeholders: Stakeholder[];
  assumptions: Array<{ id: string; statement: string; status: string }>;
  value: string;
  onValue: (value: string) => void;
  onAdd: () => void;
  onRemove: (id: string) => void;
  onApprove: () => void;
  onReject: () => void;
}) {
  return (
    <Panel>
      <div className="panel-title-row">
        <div>
          <h3>Checkpoint 1: extraction review</h3>
          <p>Agent proposes stakeholders and assumptions. It cannot proceed until a human approves or edits.</p>
        </div>
        <ActionCluster onApprove={onApprove} onReject={onReject} />
      </div>
      <div className="two-column">
        <div>
          <h4>Stakeholders</h4>
          <div className="list-table">
            {stakeholders.map((stakeholder) => (
              <div className="table-row" id={`sh-row-${stakeholder.id}`} key={stakeholder.id}>
                <div>
                  <strong>{sanitizeName(stakeholder.name)}</strong>
                  <span>{stakeholder.archetype_group} · prior {stakeholder.stance_prior}</span>
                </div>
                <button className="icon-button" onClick={() => onRemove(stakeholder.id)} aria-label="Remove stakeholder">
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>
          <div className="inline-form">
            <input value={value} onChange={(event) => onValue(event.target.value)} placeholder="Add missing stakeholder" />
            <button className="secondary" onClick={onAdd}>Add</button>
          </div>
        </div>
        <div>
          <h4>Assumptions sheet</h4>
          <div className="assumption-list">
            {assumptions.slice(0, 5).map((assumption) => (
              <div className="assumption-row" key={assumption.id}>
                <span>{displayEnglish(assumption.status)}</span>
                <p>{stripOutcomeNumbers(assumption.statement)}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
      <StakeholderMap
        stakeholders={stakeholders}
        onSelect={(id) =>
          document.getElementById(`sh-row-${id}`)?.scrollIntoView({ behavior: "smooth", block: "center" })
        }
      />
      <ForkStudio />
    </Panel>
  );
}

function StakeholderMap({
  stakeholders,
  onSelect,
}: {
  stakeholders: Stakeholder[];
  onSelect: (id: string) => void;
}) {
  const width = 920;
  const height = 330;
  const cx = width / 2;
  const cy = height / 2 + 8;
  const positioned = useMemo(() => {
    const sectors: Record<"support" | "oppose" | "other", Stakeholder[]> = { support: [], oppose: [], other: [] };
    for (const stakeholder of stakeholders) {
      const stance =
        stakeholder.stance_prior === "support" || stakeholder.stance_prior === "oppose"
          ? stakeholder.stance_prior
          : "other";
      sectors[stance].push(stakeholder);
    }
    const place = (items: Stakeholder[], startDeg: number, endDeg: number, stance: string) =>
      items.map((stakeholder, index) => {
        const t = items.length === 1 ? 0.5 : index / (items.length - 1);
        const angle = ((startDeg + (endDeg - startDeg) * t) * Math.PI) / 180;
        return {
          stakeholder,
          stance,
          x: cx + 118 * Math.cos(angle) * 2.6,
          y: cy + 108 * Math.sin(angle),
        };
      });
    return [
      ...place(sectors.support, -52, 52, "support"),
      ...place(sectors.oppose, 128, 232, "oppose"),
      ...place(sectors.other, -118, -62, "other"),
    ];
  }, [stakeholders, cx, cy]);

  return (
    <div className="constellation-block">
      <h4>
        Stakeholder constellation
        <em className="constellation-legend">
          <i className="support" /> support · <i className="oppose" /> oppose · <i className="other" /> unknown
        </em>
      </h4>
      <p className="evidence-note">
        Radial view of the reviewed extraction — support right, oppose left. Click a node to jump to its row.
      </p>
      <svg viewBox={`0 0 ${width} ${height}`} className="constellation" role="img" aria-label="Stakeholder map">
        {positioned.map(({ stakeholder, x, y, stance }) => (
          <line key={`edge-${stakeholder.id}`} x1={cx} y1={cy} x2={x} y2={y} className={`map-edge ${stance}`} />
        ))}
        <g className="map-center">
          <circle cx={cx} cy={cy} r={30} />
          <text x={cx} y={cy - 2} textAnchor="middle">
            ULEZ
          </text>
          <text x={cx} y={cy + 12} textAnchor="middle">
            Expansion
          </text>
        </g>
        {positioned.map(({ stakeholder, x, y, stance }) => (
          <g
            key={stakeholder.id}
            className={`map-node ${stance}`}
            onClick={() => onSelect(stakeholder.id)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onSelect(stakeholder.id);
              }
            }}
            role="button"
            tabIndex={0}
          >
            <title>{`${sanitizeName(stakeholder.name)} · ${stakeholder.archetype_group} · prior ${stakeholder.stance_prior}`}</title>
            <circle cx={x} cy={y} r={17} />
            <text x={x} y={y + 32} textAnchor="middle">
              {truncate(sanitizeName(stakeholder.name), 22)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

function ChainSpine({ lit }: { lit: number }) {
  const nodes = [
    ...auditManifest.entries.map((entry) => ({ id: entry.stage, label: entry.stage.replace(/_/g, " ") })),
    { id: "__manifest", label: "manifest hash" },
    { id: "__anchor", label: "TN-10 anchor" },
  ];
  return (
    <div className="chain-spine" aria-label="Audit hash chain">
      {nodes.map((node, index) => (
        <Fragment key={node.id}>
          {index > 0 ? <span className={`spine-link ${lit > index ? "lit" : ""}`} /> : null}
          <div className={`spine-node ${lit > index ? "lit" : ""} ${index >= nodes.length - 2 ? "terminal" : ""}`}>
            <span className="spine-dot" />
            <span className="spine-label">{node.label}</span>
          </div>
        </Fragment>
      ))}
    </div>
  );
}

function EnumMeter({ value }: { value: unknown }) {
  const levels: Record<string, number> = { low: 1, medium: 2, high: 3 };
  const level = typeof value === "string" ? levels[value] : undefined;
  if (!level) return null;
  return (
    <span className={`enum-meter level-${level}`} aria-hidden="true">
      <i />
      <i />
      <i />
    </span>
  );
}

const ENUM_METER_FIELDS = new Set(["impact_level", "opposition_intensity", "risk_level"]);

function SeverityBars({ items }: { items: Array<{ risk_level: string }> }) {
  const levels: Array<["high" | "medium" | "low", string]> = [
    ["high", "alarm"],
    ["medium", "signal"],
    ["low", "registry"],
  ];
  const total = items.length || 1;
  return (
    <div className="severity-bars" aria-label="Risk levels">
      {levels.map(([level, tone]) => {
        const count = items.filter((item) => item.risk_level === level).length;
        return (
          <div key={level}>
            <span>{level}</span>
            <div className="sev-track">
              <div className={`sev-fill ${tone}`} style={{ width: `${(count / total) * 100}%` }} />
            </div>
            <strong>{count}</strong>
          </div>
        );
      })}
    </div>
  );
}

const FORK_PARENT_RUN_ID = "ulez_2023_phase2_deepseek";
const FORK_BASELINE_CHARGE = "£12.50";
const HUMAN_GRADING_PENDING_NOTE = "Pending - see docs/evaluation/ulez_human_adjudication.md";

function ForkStudio() {
  const [phase, setPhase] = useState<"idle" | "form" | "confirm" | "running" | "done">("idle");
  const [variantName, setVariantName] = useState("charge £15.00");
  const [charge, setCharge] = useState("£15.00");
  const [progress, setProgress] = useState("");
  const [comparison, setComparison] = useState<ForkComparison | null>(null);
  const [approval, setApproval] = useState<ForkApprovalEvent | null>(null);
  const [source, setSource] = useState<"live" | "cached">("live");
  const [fallbackNote, setFallbackNote] = useState("");

  const patches: JsonPatchOp[] = [{ op: "add", path: "/scenario_variant", value: { charge } }];
  const baselinePatches: JsonPatchOp[] = [
    { op: "add", path: "/scenario_variant", value: { charge: FORK_BASELINE_CHARGE } },
  ];

  async function runFork() {
    setPhase("running");
    setFallbackNote("");
    if (STATIC_SHOWCASE) {
      setComparison(CACHED_FORK_COMPARISON);
      setApproval(null);
      setSource("cached");
      setPhase("done");
      return;
    }
    try {
      setProgress(`Creating baseline fork (charge ${FORK_BASELINE_CHARGE})…`);
      const baseline = await createFork(FORK_PARENT_RUN_ID, `charge ${FORK_BASELINE_CHARGE}`, baselinePatches);
      setProgress(`Creating variant fork (${variantName})…`);
      const variant = await createFork(FORK_PARENT_RUN_ID, variantName, patches);
      setApproval(variant.approval_event ?? null);
      setProgress("Comparing forks…");
      const compared = await compareForks(FORK_PARENT_RUN_ID, baseline.fork_id, variant.fork_id);
      setComparison(compared);
      setSource("live");
      setPhase("done");
    } catch (error) {
      setComparison(CACHED_FORK_COMPARISON);
      setApproval(null);
      setSource("cached");
      setFallbackNote(error instanceof Error ? error.message : "Fork API unavailable.");
      setPhase("done");
    }
  }

  if (phase === "idle") {
    return (
      <div className="fork-studio">
        <div className="fork-cta-row">
          <div>
            <h4>Scenario forks</h4>
            <p>Branch this reviewed case graph into a named variant and compare the rerun side by side.</p>
          </div>
          <button className="primary" onClick={() => setPhase("form")}>
            <GitCompare size={16} /> Fork this scenario
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fork-studio open">
      <div className="fork-cta-row">
        <div>
          <h4>Scenario forks</h4>
          <p>Parent: {FORK_PARENT_RUN_ID} · baseline variant: charge {FORK_BASELINE_CHARGE}</p>
        </div>
        <button className="secondary" onClick={() => setPhase("idle")}>
          <X size={14} /> Close
        </button>
      </div>

      {phase === "form" && (
        <div className="fork-form">
          <label className="number-control">
            <span>Variant name</span>
            <input value={variantName} onChange={(event) => setVariantName(event.target.value)} />
          </label>
          <label className="number-control">
            <span>Daily charge</span>
            <input value={charge} onChange={(event) => setCharge(event.target.value)} />
          </label>
          <div className="run-actions">
            <button className="primary" onClick={() => setPhase("confirm")} disabled={!variantName.trim() || !charge.trim()}>
              <ChevronRight size={16} /> Review patch
            </button>
          </div>
        </div>
      )}

      {phase === "confirm" && (
        <div className="fork-confirm">
          <div className="panel-title-row compact">
            <div>
              <h4>Fork variant review</h4>
              <p>These patches are human-authored. Confirming is the approval that authorizes both fork reruns.</p>
            </div>
            <StatusPill tone="warn">Human approval required</StatusPill>
          </div>
          <div className="result-block diff-block">
            <strong>Patches to apply</strong>
            <p className="diff-line">
              <code>baseline · /scenario_variant</code>: <span className="diff-before">null</span> →{" "}
              <span className="diff-after">{JSON.stringify({ charge: FORK_BASELINE_CHARGE })}</span>
            </p>
            <p className="diff-line">
              <code>variant · /scenario_variant</code>: <span className="diff-before">null</span> →{" "}
              <span className="diff-after">{JSON.stringify({ charge })}</span>
            </p>
          </div>
          <pre className="fork-patch-preview">
            {JSON.stringify({ baseline_fork_patches: baselinePatches, variant_fork_patches: patches }, null, 2)}
          </pre>
          <div className="run-actions">
            <button className="primary" onClick={runFork}>
              <Check size={16} /> Confirm fork and run
            </button>
            <button className="secondary" onClick={() => setPhase("form")}>
              <ArrowLeft size={14} /> Back
            </button>
          </div>
        </div>
      )}

      {phase === "running" && (
        <div className="fork-running">
          <p>{progress}</p>
          <p className="evidence-note">Fork rerun uses the mock simulation path; the report stage may call the configured LLM.</p>
        </div>
      )}

      {phase === "done" && comparison && (
        <>
          {approval ? (
            <div className="result-block diff-block recorded">
              <strong>Recorded approval diff · {approval.stage}</strong>
              {approval.diff.slice(0, 4).map((item) => (
                <p className="diff-line" key={item.path}>
                  <code>{item.path}</code>: <span className="diff-before">{formatForkValue(item.before)}</span> →{" "}
                  <span className="diff-after">{formatForkValue(item.after)}</span>
                </p>
              ))}
            </div>
          ) : null}
          <ForkComparisonView comparison={comparison} source={source} fallbackNote={fallbackNote} />
          <div className="run-actions">
            <button className="secondary" onClick={() => setPhase("form")}>
              <RefreshCcw size={14} /> Fork another variant
            </button>
          </div>
        </>
      )}
    </div>
  );
}

function ForkComparisonView({
  comparison,
  source,
  fallbackNote,
}: {
  comparison: ForkComparison;
  source: "live" | "cached";
  fallbackNote: string;
}) {
  const dimensions: Array<[string, ForkCompareRow[]]> = [
    ["Risk timeline", comparison.dimensions.risk_timeline],
    ["Claims", comparison.dimensions.claims],
    ["Stakeholder pressure", comparison.dimensions.stakeholder_pressure],
  ];
  const { summary } = comparison;
  return (
    <div className="fork-compare">
      <div className="fork-compare-head">
        <div>
          <h4>Side-by-side comparison</h4>
          <p>
            <strong>A</strong> {comparison.a.name} · <strong>B</strong> {comparison.b.name}
          </p>
        </div>
        <div className="fork-summary">
          <span className="status-pill warn">{summary.changed} changed</span>
          <span className="status-pill neutral">{summary.new} new</span>
          <span className="status-pill neutral">{summary.removed} removed</span>
          <span className="status-pill safe">{summary.unchanged} unchanged</span>
        </div>
      </div>
      <p className="evidence-note">Illustrative rerun — decision support, not deterministic forecast.</p>
      {source === "cached" ? (
        <p className="evidence-note">
          Cached showcase comparison (charge £12.50 vs £15.00) — the live fork API is not reachable in this static demo.
          {fallbackNote ? ` (${fallbackNote})` : ""}
        </p>
      ) : null}
      {dimensions.map(([title, rows]) =>
        rows.length ? (
          <div className="compare-dimension" key={title}>
            <h4>{title}</h4>
            {rows.map((row, index) => (
              <ForkCompareRowView row={row} index={index} key={`${title}-${row.key}`} />
            ))}
          </div>
        ) : null,
      )}
    </div>
  );
}

function ForkCompareRowView({ row, index = 0 }: { row: ForkCompareRow; index?: number }) {
  const changed = new Set(row.changed_fields ?? []);
  return (
    <div className={`compare-row ${row.status}`} style={{ animationDelay: `${Math.min(index, 12) * 40}ms` }}>
      <div className="compare-key">
        <code>{row.key}</code>
        <em className={`fork-status ${row.status}`}>{row.status}</em>
      </div>
      <div className="compare-cells">
        <ForkCompareCell label="A" data={row.a} changed={changed} />
        <ForkCompareCell label="B" data={row.b} changed={changed} />
      </div>
    </div>
  );
}

function ForkCompareCell({
  label,
  data,
  changed,
}: {
  label: string;
  data: Record<string, unknown> | null;
  changed: Set<string>;
}) {
  if (!data) {
    return (
      <div className="compare-cell empty">
        <span>{label}</span>
        <p>—</p>
      </div>
    );
  }
  return (
    <div className="compare-cell">
      <span>{label}</span>
      {Object.entries(data).map(([field, value]) => (
        <p className={changed.has(field) ? "field-changed" : ""} key={field}>
          <span className="field-name">{humanizeFieldName(field)}</span> {formatForkValue(value)}
          {ENUM_METER_FIELDS.has(field) ? <EnumMeter value={value} /> : null}
        </p>
      ))}
    </div>
  );
}

function formatForkValue(value: unknown): string {
  if (value === null || value === undefined) return "null";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    return value.map((item) => (typeof item === "string" ? item : JSON.stringify(item))).join(" · ");
  }
  return JSON.stringify(value);
}

function humanizeFieldName(field: string): string {
  const label = field.replace(/_/g, " ");
  return label.charAt(0).toUpperCase() + label.slice(1);
}

function downloadAnchorPackage() {
  const payload = { kaspa_anchor: kaspaAnchor, audit_manifest: auditManifest };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "forkcast-anchor-ulez_2023.json";
  anchor.click();
  URL.revokeObjectURL(url);
}

function AgentReview({
  blocked,
  groupCounts,
  disabledAgents,
  onToggleAgent,
  onApprove,
  onReject,
}: {
  blocked: boolean;
  groupCounts: Record<string, number>;
  disabledAgents: Set<string>;
  onToggleAgent: (id: string) => void;
  onApprove: () => void;
  onReject: () => void;
}) {
  return (
    <Panel>
      <div className="panel-title-row">
        <div>
          <h3>Checkpoint 2: archetype agent review</h3>
          <p>Representative archetypes only. Adjust composition or disable personas before simulation.</p>
        </div>
        <ActionCluster onApprove={onApprove} onReject={onReject} blocked={blocked} />
      </div>
      <div className="composition-grid">
        {Object.entries(groupCounts).map(([id, count]) => (
          <div className="composition-row" key={id}>
            <span>{compactStakeholder(id)}</span>
            <strong>{count}</strong>
            <input type="range" min="0" max="12" defaultValue={count} aria-label={`${id} count`} />
          </div>
        ))}
      </div>
      <h4>Persona controls</h4>
      <div className="persona-list">
        {agents.slice(0, 10).map((agent) => (
          <button
            className={`persona-row ${disabledAgents.has(agent.id) ? "disabled" : ""}`}
            key={agent.id}
            onClick={() => onToggleAgent(agent.id)}
          >
            <span>{agent.archetype}</span>
            <em>{agent.stance} · {agent.adaptation_capacity} adaptation</em>
          </button>
        ))}
      </div>
    </Panel>
  );
}

function SimulationConfig({
  blocked,
  agentCount,
  rounds,
  budget,
  seedLocked,
  liveSample,
  setAgentCount,
  setRounds,
  setBudget,
  setSeedLocked,
  setLiveSample,
  onApprove,
  onReject,
}: {
  blocked: boolean;
  agentCount: number;
  rounds: number;
  budget: number;
  seedLocked: boolean;
  liveSample: boolean;
  setAgentCount: (value: number) => void;
  setRounds: (value: number) => void;
  setBudget: (value: number) => void;
  setSeedLocked: (value: boolean) => void;
  setLiveSample: (value: boolean) => void;
  onApprove: () => void;
  onReject: () => void;
}) {
  return (
    <Panel>
      <div className="panel-title-row">
        <div>
          <h3>Checkpoint 3: simulation config</h3>
          <p>Approve scale, rounds, budget and seed. OASIS live is disabled; mock replay is the MVP path.</p>
        </div>
        <ActionCluster onApprove={onApprove} onReject={onReject} blocked={blocked} approveLabel="Approve run" />
      </div>
      <div className="runsheet">
        <div className="runsheet-params">
          <h4>Parameters</h4>
          <div className="config-grid">
            <NumberControl label="Agent count" value={agentCount} min={10} max={200} onChange={setAgentCount} />
            <NumberControl label="Rounds" value={rounds} min={1} max={5} onChange={setRounds} />
            <NumberControl label="LLM budget cap" value={budget} min={10} max={200} onChange={setBudget} />
            <label className="toggle-row">
              <input type="checkbox" checked={seedLocked} onChange={(event) => setSeedLocked(event.target.checked)} />
              Lock seed
            </label>
          </div>
          <div className="run-actions">
            <button className="primary" onClick={() => setLiveSample(false)}>
              <Play size={16} /> Replay cached run
            </button>
            <button className="secondary" onClick={() => setLiveSample(!liveSample)}>
              <RefreshCcw size={16} /> {liveSample ? "Show full replay" : "Run live sample"}
            </button>
            <button className="secondary" onClick={() => setAgentCount(Math.min(agentCount, 18))}>Downscale</button>
          </div>
        </div>
        <aside className="runsheet-envelope">
          <h4>Run envelope</h4>
          <div className="envelope-grid">
            <Fact label="Mode" value={liveSample ? "Live sample" : "Replay"} />
            <Fact label="LLM budget cap" value={String(budget)} />
            <Fact label="Events cached" value={String(simulation.events.length)} />
            <Fact label="Key signals" value={String(backtest.rules.length)} />
            <Fact label="Agents × rounds" value={`${agentCount} × ${rounds}`} />
            <Fact label="Seed" value={seedLocked ? "Locked" : "Unlocked"} />
          </div>
          <p className="evidence-note">Replay is cached for the demo; live sample stays small.</p>
        </aside>
      </div>
    </Panel>
  );
}

function SimulationReplay({ events, liveSample }: { events: SimulationEvent[]; liveSample: boolean }) {
  return (
    <Panel>
      <div className="panel-title-row">
        <div>
          <h3>Simulation replay</h3>
          <p>{liveSample ? "Small live sample view" : "Cached replay for demo resilience"} · posts, comments and stance shifts.</p>
        </div>
        <StatusPill tone="safe">{simulation.metadata.disclaimer}</StatusPill>
      </div>
      <div className="feed">
        {events.map((event) => (
          <div className={`feed-item ${event.type}`} key={event.event_id}>
            <div>
              <strong>{event.agent_archetype}</strong>
              <span>round {event.round} · {event.type}</span>
            </div>
            <p>{event.content || `${event.from_stance} → ${event.to_stance}: ${event.reason}`}</p>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function ImpactReport({
  claimVisibility,
  setClaimVisibility,
  reviewedClaims,
  onReviewClaim,
}: {
  claimVisibility: Record<string, boolean>;
  setClaimVisibility: (value: Record<string, boolean>) => void;
  reviewedClaims: Set<string>;
  onReviewClaim: (id: string) => void;
}) {
  const claimsAuditRows = buildClaimsAuditRows(impactReport, backtest);
  const provenanceNotice = claimsAuditNotice(claimsAuditRows);
  const visibleClaims = claimsAuditRows.slice(0, 6);
  const reviewedCount = visibleClaims.filter((row) => reviewedClaims.has(row.id)).length;
  return (
    <Panel>
      <div className="panel-title-row">
        <div>
          <h3>Impact report</h3>
          <p>{impactReport.method_note}</p>
          <p className="evidence-note">
            Any dashboard score or monetary framing in this view is illustrative / demo estimate only. Automated R1-R6
            verdicts are keyword-rubric signal coverage; human adjudication is the grading path.
          </p>
        </div>
        <StatusPill tone="neutral">Evidence: {impactReport.backtest_evidence}</StatusPill>
      </div>
      <div className="report-grid">
        <div>
          <h4>Risk timeline</h4>
          <SeverityBars items={impactReport.risk_timeline} />
          {impactReport.risk_timeline.map((risk) => (
            <div className="risk-row" key={risk.stage}>
              <span>{risk.stage}</span>
              <strong>{risk.risk_level}</strong>
              <p>{risk.signal}</p>
            </div>
          ))}
        </div>
        <div>
          <h4 className="review-progress-heading">
            Claim review
            <em className="review-count">
              {reviewedCount} of {visibleClaims.length} reviewed
            </em>
          </h4>
          {visibleClaims.map((row) => (
            <div className={`claim-row ${claimVisibility[row.id] === false ? "muted" : ""}`} key={row.id}>
              <span>{row.id.replace("backtest_", "")}</span>
              <p>{row.claim}</p>
              <ProvenancePill provenance={row.provenance_class} />
              <button
                className="secondary small"
                onClick={() => {
                  setClaimVisibility({ ...claimVisibility, [row.id]: claimVisibility[row.id] === false });
                  onReviewClaim(row.id);
                }}
              >
                {claimVisibility[row.id] === false ? "Restore" : "Delete"}
              </button>
              <button className="secondary small" onClick={() => onReviewClaim(row.id)}>
                Downgrade wording
              </button>
            </div>
          ))}
        </div>
      </div>
      <h4>Mitigation options</h4>
      <div className="mitigation-list">
        {impactReport.mitigation_options.map((item) => (
          <div key={item.option}>
            <strong>{item.option}</strong>
            <p>{item.rationale}</p>
          </div>
        ))}
      </div>
      <h4>Claims audit table</h4>
      <div className="claims-audit-table">
        <div className="claims-audit-head">
          <span>Claim</span>
          <span>Provenance</span>
          <span>Evidence pointer</span>
        </div>
        {provenanceNotice ? <p className="claims-audit-notice">{provenanceNotice}</p> : null}
        {claimsAuditRows.slice(0, 8).map((row) => (
          <div className="claims-audit-row" key={`audit-${row.id}`}>
            <p>{row.claim}</p>
            <ProvenancePill provenance={row.provenance_class} />
            <code>{row.evidence_pointer}</code>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function ProvenancePill({ provenance }: { provenance: ClaimProvenanceRow["provenance_class"] }) {
  return <em className={`provenance-pill ${provenance.toLowerCase()}`}>{PROVENANCE_LABELS[provenance]}</em>;
}

function BlindBacktest() {
  const promptText = `${blindPrediction.prompt.system_prompt}\n${blindPrediction.prompt.user_prompt}`;
  const forbidden = ["51%", "62%", "495", "416", "91.6", "96.2", "88.9", "97.1", "53%", "90,000", "Uxbridge"];
  const found = forbidden.filter((token) => promptText.includes(token));
  return (
    <Panel>
      <div className="panel-title-row">
        <div>
          <h3>Blind prediction rubric coverage</h3>
          <p>ForkCast generates answer-isolated blind predictions; the prediction step does not read outcome data.</p>
          <p className="evidence-note">Automated keyword-rubric verdicts — signal coverage, not semantic verification. See negative controls & human adjudication.</p>
          <p className="evidence-note">Source: runs/ulez_2023_phase2_deepseek/backtest_result.json · rubric: backtest_rubric.md</p>
        </div>
        <StatusPill tone={found.length === 0 ? "safe" : "warn"}>{found.length === 0 ? "No outcome tokens in prompt" : "Prompt scan flagged"}</StatusPill>
      </div>
      <div className="backtest-table">
        <div className="table-head">
          <span>Rule</span>
          <span>Rubric item</span>
          <span>Blind prediction signal</span>
          <span>Real outcome</span>
          <span>Verdict</span>
        </div>
        {backtest.rules.map((rule) => (
          <BacktestRow key={rule.rule_id} rule={rule} />
        ))}
      </div>
      <p className="evidence-note">Display translation — canonical data lives in the anchored run artifacts.</p>
      <div className="prompt-proof">
        <div>
          <h4>Prompt transparency</h4>
          <p>Prediction function does not load truth_set. Stored prompt is inspectable and scanned for outcome tokens.</p>
        </div>
        <pre>{blindPrediction.prompt.system_prompt}</pre>
      </div>
    </Panel>
  );
}

function AuditReview({
  blocked,
  chainDecision,
  setChainDecision,
  onApprove,
  onReject,
}: {
  blocked: boolean;
  chainDecision: "pending" | "payload_approved" | "refused";
  setChainDecision: (value: "pending" | "payload_approved" | "refused") => void;
  onApprove: () => void;
  onReject: () => void;
}) {
  const [spineLit, setSpineLit] = useState(0);
  return (
    <Panel>
      <div className="panel-title-row">
        <div>
          <h3>Checkpoint 4: report and Kaspa review</h3>
          <p>Manifest and chain payload are inspectable. This testnet anchor was broadcast only after checkpoint-4 human approval.</p>
        </div>
        <ActionCluster onApprove={onApprove} onReject={onReject} blocked={blocked} approveLabel="Approve report" />
      </div>
      <ChainSpine lit={spineLit} />
      <div className="audit-layout">
        <div className="audit-list">
          <div className="audit-meta">
            <Fact label="Created" value={formatAuditDate(auditManifest.entries[0]?.timestamp)} />
            <Fact label="Run ID" value="ulez_2023_phase2_deepseek" />
            <Fact label="Data freshness" value="Cached 2026-07-01 replay" />
          </div>
          {auditManifest.entries.map((entry) => (
            <div className="audit-row" key={entry.stage}>
              <span>{entry.stage}</span>
              <code>{entry.hash.slice(0, 18)}…</code>
              <em>{entry.approval}</em>
            </div>
          ))}
        </div>
        <div className="chain-box-wrap">
          <div className="chain-box">
            <ShieldCheck size={24} />
          <h4>Kaspa payload anchoring</h4>
          <p>
            Status: {humanizeStatus(kaspaAnchor.status)}. User approval remains required before any future transaction broadcast.
          </p>
          <div className="kaspa-facts">
            <Fact label="Network" value={kaspaAnchor.network} />
            <Fact label="Payload bytes" value={`${kaspaAnchor.payload_size_bytes}/${kaspaAnchor.payload_practical_limit_bytes}`} />
            <Fact label="Explorer" value={kaspaAnchor.explorer_base_url.replace("https://", "")} />
          </div>
          <div className="hash-stack">
            <span>Manifest hash</span>
            <code>{kaspaAnchor.manifest_hash}</code>
            <span>Payload hash</span>
            <code>{kaspaAnchor.payload_hash}</code>
            {kaspaAnchor.tx_id ? (
              <>
                <span>Kaspa tx id</span>
                <code>{kaspaAnchor.tx_id}</code>
              </>
            ) : null}
          </div>
          {kaspaAnchor.explorer_url ? (
            <a className="explorer-link" href={kaspaAnchor.explorer_url} target="_blank" rel="noreferrer">
              Open Kaspa explorer
            </a>
          ) : (
            <p className="evidence-note">Anchor package can be verified locally until a testnet tx id is configured.</p>
          )}
          <VerifyOnChain onSpineProgress={setSpineLit} />
          <button className="secondary download-anchor" onClick={downloadAnchorPackage}>
            Download anchor package (JSON)
          </button>
          <pre className="payload-preview">{kaspaAnchor.payload_canonical_json}</pre>
            <button className="primary" onClick={() => setChainDecision("payload_approved")}>Approve anchored payload review</button>
            <button className="secondary" onClick={() => setChainDecision("refused")}>Refuse on-chain anchor</button>
            <StatusPill tone={chainDecision === "refused" ? "warn" : "neutral"}>{chainDecision}</StatusPill>
          </div>
        </div>
      </div>
    </Panel>
  );
}

function VerifyOnChain({ onSpineProgress }: { onSpineProgress?: (lit: number) => void }) {
  const [state, setState] = useState<"idle" | "running" | "done">("idle");
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [source, setSource] = useState<"live" | "cached">("live");
  const [fallbackNote, setFallbackNote] = useState("");
  const [revealed, setRevealed] = useState(0);

  const checkEntries = result ? Object.entries(result.checks) : [];
  const totalItems = result ? checkEntries.length + result.links.length + 1 : 0;
  const linksRevealed = result ? Math.max(0, Math.min(revealed - checkEntries.length, result.links.length)) : 0;
  const spineProgress =
    state === "done" && result
      ? revealed >= totalItems
        ? auditManifest.entries.length + 2
        : linksRevealed
      : 0;

  useEffect(() => {
    onSpineProgress?.(spineProgress);
  }, [spineProgress, onSpineProgress]);

  useEffect(() => {
    if (state !== "done" || !result || revealed >= totalItems) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setRevealed(totalItems);
      return;
    }
    const timer = window.setTimeout(() => setRevealed((current) => current + 1), 140);
    return () => window.clearTimeout(timer);
  }, [state, result, revealed, totalItems]);

  async function run() {
    setState("running");
    setRevealed(0);
    setFallbackNote("");
    if (STATIC_SHOWCASE) {
      setResult(CACHED_VERIFY_TRANSCRIPT);
      setSource("cached");
      setState("done");
      return;
    }
    try {
      const live = await verifyAnchor(FORK_PARENT_RUN_ID);
      setResult(live);
      setSource("live");
    } catch (error) {
      setResult(CACHED_VERIFY_TRANSCRIPT);
      setSource("cached");
      setFallbackNote(error instanceof Error ? error.message : "Verify API unreachable.");
    }
    setState("done");
  }

  if (state === "idle") {
    return (
      <button className="secondary verify-cta" onClick={run}>
        <ShieldCheck size={16} /> Verify on chain
      </button>
    );
  }

  if (state === "running" || !result) {
    return <p className="evidence-note verify-running">Recomputing hashes and querying the Kaspa testnet-10 API…</p>;
  }

  return (
    <div className="verify-transcript">
      <div className="verify-meta">
        <span>{humanizeStatus(result.mode)}</span>
        <span>{result.network}</span>
        <code>{result.txid.slice(0, 18)}…</code>
      </div>
      {source === "cached" ? (
        <p className="evidence-note">
          Cached verification transcript, recorded against the live TN-10 API
          {fallbackNote
            ? ` — the live verify call failed (${fallbackNote}).`
            : " — the verify endpoint is not bundled in this static demo."}{" "}
          Reproduce locally: scripts/verify_run.py
        </p>
      ) : null}
      {checkEntries.map(([name, check], index) =>
        index < revealed ? (
          <div className={`verify-row ${check.status.toLowerCase()}`} key={name}>
            <em>{check.status}</em>
            <div>
              <strong>{humanizeStatus(name)}</strong>
              <p>{check.note}</p>
            </div>
          </div>
        ) : null,
      )}
      {result.links.map((link, index) =>
        checkEntries.length + index < revealed ? (
          <div className={`verify-row link ${link.status.toLowerCase()}`} key={link.id}>
            <em>{link.status}</em>
            <div>
              <strong>
                {link.id} · {humanizeStatus(link.stage)}
              </strong>
            </div>
          </div>
        ) : null,
      )}
      {revealed >= totalItems ? (
        <div className={`verify-overall ${result.overall === "PASS" ? "pass" : "fail"}`}>
          Overall: {result.overall}
        </div>
      ) : null}
    </div>
  );
}

function ClosingScreen() {
  return (
    <Panel>
      <div className="closing">
        <h3>Weeks to hours, with the human still in control.</h3>
        <p>Extraction, agent design, run configuration, blind prediction grading and audit manifest stay visible and reversible.</p>
        <div className="closing-metrics">
          <Metric label="Demo run" value="90 sec" tone="safe" />
          <Metric label="Prediction" value="Blind" tone="safe" />
          <Metric label="Autonomy" value="Gated" tone="safe" />
        </div>
        <p className="closing-txs">
          Verified on Kaspa testnet-10 · tx {kaspaAnchor.tx_id?.slice(0, 8)}… (manifest hash) · tx 8a682481… (hash-chain head)
        </p>
      </div>
    </Panel>
  );
}

function CheckpointPanel({ control }: { control: ReturnType<typeof createInitialControlState> }) {
  return (
    <section className="control-panel">
      <div className="side-title">
        <ClipboardCheck size={18} />
        <h3>Human control</h3>
      </div>
      {checkpointSteps.map((key) => {
        const checkpoint = control.checkpoints[key];
        return (
          <div className={`checkpoint-row ${checkpoint.status}`} key={key}>
            <span>{checkpoint.label}</span>
            <strong>{checkpoint.status}</strong>
            <code>{checkpoint.artifactHash}</code>
          </div>
        );
      })}
      <div className="limits">
        <h4>Hard limits</h4>
        {[
          "No automatic chain action",
          "No automatic weight changes",
          "No real-person PII",
          "Archetypes only",
          "Decision support only",
        ].map((item) => (
          <span key={item}><Lock size={12} /> {item}</span>
        ))}
      </div>
      <div className="event-log">
        <h4>Checkpoint history</h4>
        {control.events.slice(-5).map((event) => (
          <div key={event.id}>
            <span>{event.action}</span>
            <p>{event.note}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function AuditSidebar({ control }: { control: ReturnType<typeof createInitialControlState> }) {
  return (
    <section className="audit-sidebar">
      <div className="side-title">
        <ClipboardCheck size={18} />
        <h3>Audit Manifest</h3>
      </div>
      <div className="receipt-wrap">
        <div className="receipt">
          <div className="audit-sidebar-grid">
          <Fact label="Run ID" value="ulez_2023_phase2_deepseek" />
          <Fact label="Created" value={formatAuditDate(auditManifest.entries[0]?.timestamp)} />
          <Fact label="Created by" value="Policy Maker (PM)" />
          <Fact label="Scenario" value="London ULEZ Expansion" />
          <Fact label="Policy Option" value="ULEZ Expansion to Outer London" />
          <Fact label="Data Sources" value="18" />
          <Fact label="Artifacts" value={String(auditManifest.entries.length)} />
          <Fact label="Status" value={kaspaAnchor.status === "anchored" ? "Anchored on TN-10" : "Local verification"} />
        </div>
          <div className="kaspa-mini">
            <span>Kaspa Anchoring</span>
            {kaspaAnchor.explorer_url ? (
              <a href={kaspaAnchor.explorer_url} target="_blank" rel="noreferrer">
                {kaspaAnchor.tx_id?.slice(0, 18)}…
              </a>
            ) : (
              <strong>Local package only</strong>
            )}
          </div>
        </div>
      </div>
      <div className="limits">
        <h4>Hard limits</h4>
        {[
          "No automatic chain action",
          "No automatic weight changes",
          "No real-person PII",
          "Archetypes only",
          "Decision support only",
        ].map((item) => (
          <span key={item}><Lock size={12} /> {item}</span>
        ))}
      </div>
      <div className="event-log">
        <h4>Checkpoint history</h4>
        {control.events.slice(-4).map((event) => (
          <div key={event.id}>
            <span>{event.action}</span>
            <p>{event.note}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function PersonaChat({
  selectedAgentId,
  setSelectedAgentId,
  agent,
  question,
  setQuestion,
}: {
  selectedAgentId: string;
  setSelectedAgentId: (value: string) => void;
  agent: AgentProfile;
  question: string;
  setQuestion: (value: string) => void;
}) {
  const answer = `As an archetype, I am ${agent.stance} because my concerns are ${agent.concerns.slice(0, 3).join(", ")}. I would ${agent.action_tendency}.`;
  return (
    <section className="chat-panel">
      <div className="side-title">
        <MessageSquare size={18} />
        <h3>Persona chat</h3>
      </div>
      <select value={selectedAgentId} onChange={(event) => setSelectedAgentId(event.target.value)}>
        {agents.slice(0, 18).map((item) => (
          <option key={item.id} value={item.id}>{item.archetype}</option>
        ))}
      </select>
      <textarea value={question} onChange={(event) => setQuestion(event.target.value)} />
      <div className="chat-answer">
        <strong>{agent.archetype}</strong>
        <p>{answer}</p>
        <span>Archetype only · no real-person PII</span>
      </div>
    </section>
  );
}

function ActionCluster({
  onApprove,
  onReject,
  blocked,
  approveLabel = "Approve",
}: {
  onApprove: () => void;
  onReject: () => void;
  blocked?: boolean;
  approveLabel?: string;
}) {
  return (
    <div className="action-cluster">
      <button className="primary" onClick={onApprove} disabled={blocked}>
        <Check size={16} /> {approveLabel}
      </button>
      <button className="secondary">
        <SlidersHorizontal size={16} /> Adjust
      </button>
      <button className="danger" onClick={onReject}>
        <X size={16} /> Reject
      </button>
    </div>
  );
}

function BacktestRow({ rule }: { rule: BacktestRule }) {
  return (
    <div className="backtest-row">
      <strong>{rule.rule_id}</strong>
      <p className="rubric-label">{RUBRIC_LABELS[rule.rule_id] ?? rule.rule_id}</p>
      <p>{rule.system_signal}</p>
      <p>{truncate(displayEnglish(rule.real_outcome), 220)}</p>
      <span className={`verdict ${rule.verdict.toLowerCase().replace(" ", "-")}`}>{rule.verdict}</span>
    </div>
  );
}

function NumberControl({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="number-control">
      <span>{label}</span>
      <input type="number" value={value} min={min} max={max} onChange={(event) => onChange(Number(event.target.value))} />
    </label>
  );
}

function Panel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`panel ${className}`}>{children}</section>;
}

function Metric({ label, value, tone }: { label: string; value: string; tone: "safe" | "warn" }) {
  return (
    <div className={`metric ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="fact-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function StatusPill({ children, tone }: { children: React.ReactNode; tone: "safe" | "warn" | "neutral" }) {
  return <span className={`status-pill ${tone}`}>{children}</span>;
}

function CheckpointDot({ status }: { status: string }) {
  return <span className={`checkpoint-dot ${status}`} />;
}

function headlineFor(step: DemoStep) {
  const copy: Record<DemoStep, string> = {
    before: "Make the legacy process legible before replacing it.",
    select_case: "Use a real historical policy case, not a toy example.",
    extraction_review: "The agent proposes. The human approves, edits or rejects.",
    agent_review: "Archetype agents are inspectable and bounded.",
    simulation_config: "Scale, rounds, budget and seed are explicit controls.",
    simulation_replay: "Replay is cached for the demo; live sample stays small.",
    impact_report: "Decision memo, not black-box final answer.",
    blind_backtest: "Prediction is answer-isolated; grading limits stay visible.",
    audit: "Kaspa testnet anchor is live, with the manifest hash still gated by human approval.",
    closing: "Control stays visible from intake to audit.",
    report_chain_review: "Review claims and chain action before any anchor.",
  };
  return copy[step];
}

function countBy<T>(items: T[], key: keyof T) {
  return items.reduce<Record<string, number>>((acc, item) => {
    const value = String(item[key]);
    acc[value] = (acc[value] ?? 0) + 1;
    return acc;
  }, {});
}

function compactStakeholder(id: string) {
  return id.replace("stakeholder_", "").replace(/_/g, " ");
}

function sanitizeName(value: string) {
  return value.replace(/\s*\([^)]*\)/g, "");
}

function stripOutcomeNumbers(value: string) {
  return value.replace(/\d{1,3}(?:\.\d+)?%/g, "directional signal").replace(/\b\d{3,}\b/g, "historical number");
}

function truncate(value: string, limit: number) {
  return value.length <= limit ? value : `${value.slice(0, limit - 1)}…`;
}

function formatAuditDate(value?: string) {
  if (!value) return "2026-07";
  return value.slice(0, 10);
}

function humanizeStatus(value: string) {
  return value.replace(/_/g, " ");
}

async function pollPolicyRun(
  runId: string,
  terminalStatuses: LivePolicyRunStatusName[],
  maxAttempts = 90,
): Promise<LivePolicyRunStatus> {
  let latest = await getPolicyRun(runId);
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    if (terminalStatuses.includes(latest.status)) return latest;
    await delay(1000);
    latest = await getPolicyRun(runId);
  }
  return latest;
}

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function TopbarTile({
  icon,
  label,
  value,
  trailing,
}: {
  icon?: React.ReactNode;
  label: string;
  value: string;
  trailing?: React.ReactNode;
}) {
  return (
    <div className="topbar-tile">
      {icon}
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      {trailing}
    </div>
  );
}

function StatusDock() {
  return (
    <footer className="status-dock">
      <Fact label="Run ID" value="ulez_2023_phase2_deepseek" />
      <Fact label="Scenario" value="London ULEZ Expansion" />
      <Fact label="Policy Option" value="ULEZ Expansion to Outer London" />
      <Fact label="Simulation Rounds" value={String(simulation.metadata.rounds)} />
      <Fact label="Archetype Agents" value={String(agents.length)} />
      <Fact label="Data Freshness" value="Cached 2026-07-01" />
      <Fact label="Anchor Network" value={kaspaAnchor.network} />
      <Fact label="System Status" value="Operational" />
    </footer>
  );
}

export default App;
