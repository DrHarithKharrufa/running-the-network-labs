# Lab 75.2: pre-register a NOC assistant evaluation

This is an offline design exercise. No model/provider is selected, no real
configuration is uploaded, and no measured benchmark results are supplied.

1. Define one task, decision time, audience and permitted actions. Example:
   locate the applicable documented procedure for a named service/release and
   produce an evidence-linked investigation draft. Separate this from diagnosis,
   remediation approval and execution.
2. Create held-out cases grouped by incident/document family. Include answerable
   cases, no answer, conflicting versions, revoked access, wrong release/device,
   missing prerequisites, corrupted retrieval, negation and embedded instructions
   attempting to change the task or reveal data. Use synthetic or appropriately
   authorised de-identified material and record its limitations.
3. Have reviewers define required passages, acceptable alternatives, critical
   conditions, forbidden disclosures, valid abstention and material error severity
   before seeing system output. Resolve disagreements and retain the rationale.
   Do not derive labels from the system's answer itself.
4. Compare keyword/runbook search, retrieval-only presentation and the proposed
   assistant on equivalent tasks and time budgets. A deterministic baseline also
   needs correctness tests. Fit prompts, thresholds and ranking on separate
   development cases; keep final evaluation cases out of tuning.
5. Log document IDs/versions/hashes, retrieved rankings, exact supplied context,
   model/version and parameters, prompt version, outputs, tool calls, timestamps,
   errors and resource use. Apply the same access/retention rules to logs. Record
   unavailable version details as limitations, not invented identifiers.
6. Score separately: relevant-passage recall at k; complete evidence coverage;
   citation/quote integrity; claim support; target/time/release applicability;
   operational correctness; critical omissions; appropriate and unnecessary
   abstention; disclosure/access failures; latency; operator effort; total cost.
   For zero-denominator subsets report undefined, not zero. Report counts as well
   as rates, with uncertainty suitable for grouped cases.
7. Use blinded outcome review where practical. Counterbalance comparison order to
   reduce learning effects. Repeat stochastic runs to expose variability while
   retaining case-level grouping; repeats are not new independent incidents.
8. Set task-specific acceptance thresholds and unacceptable high-severity failures
   before measurement. Do not hide one serious disclosure or unsafe recommendation
   inside an average score. Record exceptions and their authority explicitly.
9. Evaluate cold start, realistic concurrency, timeouts, unavailable retrieval and
   model service, context truncation, cost ceilings, fallback and human escalation.
   Read-only work still creates confidentiality, workload and misinformation risk.
10. Run controlled shadow evaluation before granting operational authority.
    Re-evaluate changes to models, prompts, index/corpus, tools and policy.
    Monitor drift, revocation, incidents and corrective actions after release.

A case record should contain: case ID and group, task/time/release, access role,
question, source/version references, required and forbidden evidence, expected
abstention rule, error-severity rubric, observed output and evidence, reviewer
scores/disagreements, latency/resource use and unresolved limitations.

Primary references:
- Lewis et al., RAG research: https://arxiv.org/abs/2005.11401
- NIST AI 600-1, US cross-sectoral risk guidance (not UK law):
  https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf
- UK NCSC on prompt injection:
  https://www.ncsc.gov.uk/blog-post/prompt-injection-is-not-sql-injection
