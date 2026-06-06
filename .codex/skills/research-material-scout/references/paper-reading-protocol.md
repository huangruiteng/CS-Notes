# Paper Reading Protocol for `请你读` / `精读`

Use this reference when the user asks Codex to read a paper, research report, benchmark paper, method repo, arXiv link, OpenReview page, or paper collection. It operationalizes:

- S. Keshav, "How to Read a Paper": three-pass reading, five Cs, virtual reimplementation.
- CMU 11-485/685/785 recitation "How to read research papers?": skim to narrow papers, figures first, purpose-aware reading, skip math on first read and return when needed.
- Academic / PhD / AI research lenses: claim-evidence mapping, novelty and gap, reproducibility, data/model/metric validity, and future-work extraction.

Primary references:

- https://systems.cs.columbia.edu/ds2-class/papers/keshav-paper.pdf
- https://deeplearning.cs.cmu.edu/F25/document/Recitation_0_Series/0.25/Recitation0.25_How_to_read_a_research_paper.pdf

## Borrowed Skill Scan

A one-time local scan/download of external skills informed this protocol. Treat these as design inputs, not authority:

- Academic research skills: Imbad0202/academic-research-skills (`deep-research`, `academic-paper`, `academic-paper-reviewer`, `academic-pipeline`). Borrowed the ideas of multi-perspective review, explicit integrity gates, Devil's Advocate pressure, and claim-verification checkpoints.
- AI research skills: Orchestra/zechenzhangAGI AI-Research-SKILLs (`ara-rigor-reviewer`, `ara-compiler`). Borrowed the epistemic dimensions of evidence relevance, falsifiability, scope calibration, argument coherence, exploration integrity, methodological rigor, and evidence-limited wording.
- Paper reading skills: karpathy/nanochat `read-arxiv-paper` and mizore-style `paper-reading`. Borrowed the arXiv TeX source route, paper-type detection, and 3-8 key figure/table capture rule, while keeping this skill HTML-first rather than PDF-first.
- Research workflow / PhD-adjacent skills: luwill/research-skills (`paper-analyst`, `literature-scout`, `research-proposal`). Borrowed the structured paper card and comparison-table shape; proposal-writing workflows are not part of this reading contract.
- General academic analysis skills: seabbs `analyzing-research-papers`. Borrowed methodology, reproducibility, limitations, and impact assessment prompts.

No reliable dedicated generated skill was found for the exact combination of S. Keshav's "How to Read a Paper" plus CMU 11-785's "How to read a research paper" recitation. Keep the two primary references above as canonical.

## Command Semantics

`请你读:<material>`:

- Read first, then answer. Do not give a generic reading plan.
- Default depth: Keshav pass 1 + targeted pass 2 on sections that determine the user's decision.
- If the material is high-value for the current Agent infra / OpenViking / RL runner / serving line, escalate selected parts to pass 3.
- Return a reader map only after applying the personal-reading value gate below, so the user knows what they personally still need to read and why.
- Because personal-reading recommendations are intentionally conservative, the user-facing digest must be richer when the conclusion is `Codex-summary-enough`: include enough mechanism detail, field/schema detail, key evidence, transfer mapping, and risk boundaries that the user can make progress without opening the original. The digest should compensate for the user not doing a first-pass read; do not stop at the reading recommendation plus a few artifact deltas.
- For tool/standard/framework bundles, start with a **background primer** before claim maps: what problem this family solves, what the user would observe without it, what each component owns in the end-to-end workflow, and why the bundle matters for Agent Harness / OpenViking now. Do not assume the user already knows the observability/eval/runtime ecosystem.
- Keep a **two-focus balance**: first explain the material on its own terms, then map it to the user's current project. The material summary should not collapse into Agent Harness-specific schema too early. For bundles, each component needs a concrete standalone explanation: what it is, what it records/does, what abstractions it introduces, what it does not cover, and one simple example.

`精读:<material>`:

- Use the same output schema as `请你读`, but default to pass 2 plus selective pass 3.
- Reconstruct the method, evidence, assumptions, and failure modes enough that the user can reuse the idea in an artifact, benchmark, interview deep dive, or implementation.
- If source access is incomplete, say exactly which parts were not read and downgrade the confidence.

## Keshav Three-Pass Execution

### Source Route

Use this source order for arXiv and paper-like materials:

1. HTML / official full text first when available.
2. arXiv TeX source for `精读`, method-heavy papers, appendices, algorithms, prompt templates, equations, or citation context.
3. PDF fallback for inaccessible HTML/source or visual-only evidence.
4. Repo/code/configs when implementation, reproducibility, or artifact deltas matter.

Always state which route was actually read. Do not let a PDF-text extraction masquerade as a complete paper read.

Pass 1 - Triage and Positioning:

- Read title, abstract, introduction, section headings, conclusion/discussion, figures/tables captions, related work headings, and references scan.
- Classify paper type early: empirical method, theoretical, survey/review, systems, benchmark/eval, tool/platform, position paper, or product/industry report.
- Answer the five Cs in compact form:
  - Category: method, system, benchmark, theory, survey, product paper, empirical study, position paper.
  - Context: closest prior work, lineage, conference/workshop/repo ecosystem.
  - Correctness: whether assumptions look plausible enough to continue.
  - Contributions: one to three concrete claims, not marketing language.
  - Clarity: whether the paper is readable and reproducible enough.
- Decide: `must-read`, `Codex-summary-enough`, `background-only`, or `skip`.

### Personal-Reading Value Gate

Before marking any section as something the user should personally read, ask whether the user can create meaningful incremental value after reading Codex's summary. Default to `Codex-summary-enough` unless at least one condition holds:

- The section contains a dense schema, table, algorithm, prompt, code path, or case study that the user may directly implement, quote, defend in an interview, or transfer into Agent Harness/OpenViking.
- The original wording matters for judgment, such as a subtle limitation, leakage risk, eval setup, benchmark definition, or claim boundary that could be distorted by summary.
- The material is central to a current artifact the user is actively editing, and seeing the original structure will help the user make a design decision that Codex cannot safely make alone.
- The section is short enough and high-leverage enough that reading it saves future coordination cost.

Do not ask the user to personally read a section merely because it is important, interesting, or canonical. If Codex has already extracted the mechanism, evidence, artifact delta, and risks, say `no personal read needed` and optionally list the section as `Codex-read / user-skippable`.

When recommending personal reading, include an explicit reason in the form: `read this because it enables <specific decision/artifact/interview defense>; skip otherwise`.

When deciding `Codex-summary-enough`, compensate with a **substitute-quality digest**:

- Treat this as a replacement for the user's first-pass read, not a teaser. If the user later says the summary felt incomplete, the default correction is to expand mechanism, evidence, schema, failure boundaries, and transfer notes immediately.
- Extract the original's core design in enough detail to replace a first-pass user read: modules, data flow, action space, labels/rewards, prompt/tool/API shape, schemas, and lifecycle.
- For a bundle of multiple tools/standards, give each item its own mini-card before synthesis: problem, core abstraction, important fields/APIs, normal usage, limitations, and relation to the other items.
- Include concrete identifiers from the source: section names, figure/table numbers, metric names, field names, repo paths, config names, or API names when available.
- State the main evidence with numbers or table-level comparisons when the source has them; if not, say the evidence is qualitative or conceptual.
- Separate author claims from Codex interpretation and from the user's artifact delta.
- Preserve the important caveats that a careful reader would notice: leakage, confounders, cost, version status, scope limits, missing ablations, or deployment constraints.
- End with a reader map that may say `no personal read needed`, but still names the inspected sections and why they are skippable.

Pass 2 - Content and Evidence:

- Read main method/system sections, key figures/tables, experiments, ablations, limitations, and appendix sections needed for the claim.
- For key figures/tables, capture the source identifier, caption, axes/columns, raw values or qualitative content, and the exact claim it supports before interpretation.
- Prefer 3-8 key figures/tables for high-value papers: architecture/framework, core algorithm flow, main results, ablations, failure analysis, qualitative examples, or cost/latency tables.
- If making a filtered or merged view, label it as a derived subset rather than treating it as the original figure/table.
- For each main claim, attach evidence:
  - figure/table/section/code path,
  - benchmark/data split,
  - baseline,
  - metric,
  - ablation or counterexample,
  - remaining risk.
- Skip proofs/equations on first pass unless they define the method, loss, metric, or impossibility claim.

Pass 3 - Virtual Reimplementation:

- Reconstruct the method as data -> model/workflow -> objective -> eval -> failure handling.
- Challenge every load-bearing assumption.
- Identify missing citations, weak baselines, leakage risk, metric validity, and deployment constraints.
- For high-value `精读`, run a small internal review pass from three perspectives: methodologist, domain/practitioner, and Devil's Advocate.
- Convert the paper into a reusable artifact delta: schema fields, feedback signal, eval variant, TODO, benchmark row, or interview argument.

## AI Research Reading Lens

For AI / ML / Agent papers, always extract these if present:

- Problem formulation: task, input/output, constraints, and what changes relative to prior work.
- Data: source, construction, labels, splits, scale, contamination/leakage risk, human vs synthetic signal.
- Model or system design: modules, control flow, training/inference separation, prompts/tools/retrievers/memory components.
- Objective: loss, reward, ranking target, supervision source, optimization trick, or policy update.
- Evaluation: benchmarks, baselines, metrics, ablations, sensitivity, cost/latency, statistical significance if claimed.
- Reproducibility: code, checkpoints, data, configs, hidden API dependencies, hardware assumptions.
- Failure modes: where it should not work, negative results, OOD transfer, confounders.

For Agent infra specifically, map the paper to:

- `source_trajectory`, `memory_candidate`, `retrieval_query`, `exposure`, `feedback`, `outcome`, `ranker_training_row`, `tool_call`, `trace_span`, `policy_reason`, or `lifecycle_event`.
- Whether it changes OpenViking / Agent Harness schema, eval protocol, runner design, memory lifecycle, or serving constraints.

## Academic / PhD Research Lens

Do not only summarize the paper. Identify its research move:

- What gap does it claim?
- What exactly is new: problem, data, model, training objective, benchmark, analysis, system integration, or framing?
- What would make the claim false?
- What is the strongest alternative explanation for the results?
- Which one experiment would most improve trust?
- Which follow-up idea is worth the user's time, and which is academic noise?

For literature context:

- Name closest related work only when it changes interpretation.
- If reading a paper collection or radar, triage many papers with pass 1, then deep-read only the highest-leverage subset.
- If the user asks for `请你读` a single paper, do not turn it into a broad survey unless the paper cannot be understood without one or the user asks.

## Claim-Evidence Review

For `精读`, S-ranked materials, benchmark papers, and anything likely to affect OpenViking / Agent Harness / memory-runtime design, explicitly review:

- Evidence relevance: whether the cited section, table, figure, or code actually supports the claim in substance.
- Falsifiability quality: what concrete observation would make the claim false, and whether an independent reader could test it.
- Scope calibration: whether the claim says exactly what the evidence supports, no stronger and no weaker.
- Argument coherence: whether problem -> gap -> insight -> design -> evidence forms a logical chain.
- Exploration integrity: whether failures, ablations, rejected alternatives, or dead ends are visible rather than hidden.
- Methodological rigor: whether baselines, ablations, metrics, splits, variance, costs, and reproducibility details are adequate for the claim type.

Type-aware checks:

- Causal claim -> needs isolating ablation or intervention-style evidence.
- Generalization claim -> needs heterogeneous datasets, tasks, models, users, or environments.
- Improvement claim -> needs recent, relevant baselines and comparable metrics.
- Systems claim -> needs cost, latency, throughput, reliability, scaling, and operational constraints.
- Benchmark claim -> needs task validity, data construction, contamination/leakage analysis, metric validity, and annotator/evaluator quality.
- Agent-memory/runtime claim -> needs trajectory source, retrieval/exposure path, feedback/outcome definition, lifecycle, and failure recovery details.

## Output Contract

For `请你读` / `精读`, produce this shape unless the user asks for a different one:

1. Bottom line: one sentence on whether the user should personally read it.
2. Background primer: explain the local problem space in plain terms before introducing source-specific jargon. For bundles, include a component responsibility map.
3. What I actually read: source path, HTML/TeX source/PDF/repo route, read completeness, unread parts.
4. Source-content mini-cards: for every material in a bundle, explain what it is, key concepts/fields/APIs, common usage, and limitations before project-specific interpretation.
5. Claim map: 2-5 main claims with evidence, confidence, and scope.
6. Mechanism-first summary: problem -> core design -> why it works -> where it breaks.
7. AI research checklist: paper type, data, model/system, objective, eval, baselines, limitations.
8. Artifact delta for the user: concrete schema / benchmark / TODO / note / interview point.
9. Reader map: exact sections, figures, tables, appendix, source files, repo paths marked `user-must-read`, `Codex-summary-enough`, `optional`, or `skippable`, with a one-line incremental-value reason for every `user-must-read`.
10. Sharp verification questions: 3-6 questions to ask while reading or implementing.

If the answer is short, keep all ten ideas but compress them. Never omit the reader map for high-value material, but it is valid for the reader map to say `no personal read needed` when Codex's summary already captures the actionable value.

Depth tradeoff rule:

- If recommending `user-must-read`, keep the digest concise and point the user to the exact original source.
- If recommending `no personal read needed` or `Codex-summary-enough`, make the digest more complete: core design, key details, evidence, artifact mapping, and caveats should be explicit enough that the user does not lose meaningful value by skipping the original.

Survey / taxonomy paper branch:

- For survey, taxonomy, ecosystem-map, or awesome-list style materials, do not treat the work as a method paper with a hidden algorithm.
- Explain the source itself first: taxonomy dimensions, inclusion criteria, source corpus, representative examples, and what the framework helps distinguish.
- Separate "field map value" from "empirical proof": project catalogs and taxonomy tables can justify vocabulary and landscape coverage, but they usually do not prove causal performance gains.
- Give the user a compact reader map that prioritizes the framework definition, synthesis/open-problem sections, and any tables/figures that change design language; mark long per-project catalogs as reference-only unless a concrete implementation decision depends on them.
- In artifact mapping, prefer one or two concrete organizing deltas such as a module-to-taxonomy map, evaluation checklist, or interview vocabulary map. Avoid overfitting every layer of the survey into the user's current project.

## Quality Rules

- Prefer primary source over secondary commentary.
- Do not claim a paper was read if only abstract/social post was read.
- Do not bury the judgment after a long summary.
- Do not summarize section-by-section unless the paper structure itself is the insight.
- Do not let "interesting paper" become "user must read"; reading priority is `project relevance * actionability / reading cost`.
- Do not let "Codex found this useful" become "the user should read it". Personal reading must create value beyond the summary: a design decision, artifact edit, implementation check, or interview-defense advantage.
- Do not use downloaded external skills as factual authority. They only contribute workflow ideas; technical facts still need primary sources.
- For S/A candidates, end with a concrete next action and whether Codex or the user should do it.
