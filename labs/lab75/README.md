# Lab 75: citation integrity, semantic examples and evaluation design

This extends the handover's corrected five-test citation checker. Its distinction
between citation existence and semantic support is preserved. All passages and
claims are synthetic; ExampleNOS is fictional. No LLM, embedding model, retrieval
service, live API or network is run.

```
python rag_grounding.py
python citation_cases.py
python -m unittest discover -v
```

Thirteen tests cover structural validation, the compatibility entry point,
negation, wrong targets/devices/quantities/releases, omitted qualifications,
conflicts, derivations and input-type boundaries. Twelve annotated cases appear
in `citation_cases.py`. The expected support label and explanation were manually
reviewed as text relationships independently of the checker. They are **fixture
data**, not machine judgements, independently collected operational evidence or
external expert review. Tests confirm the checker does not promote those cases
to semantic success; they do not measure a model's entailment accuracy.

Valid citation IDs and exact quotations return `needs_semantic_review`. Unknown
IDs and fabricated quotations receive structural error statuses. `grounded` is
retained for compatibility but always returns False; its name is not a verdict.
An exact quotation can still be stale, false or inapplicable. A supported statement
about what a source says is different from verified current network state.

The cases include:
- Negating the source's TCP-AO statement.
- Changing AS64500 to AS64501 or lab-r1 to lab-r2.
- Changing a maintenance interval or an explicitly excluded release.
- Turning parser acceptance into a forwarding-test claim.
- Turning an unconfirmed hypothesis into a confirmed cause.
- Calculating 100 minus 80 Gbit/s from cited inputs.
- Combining sources that disagree about the maintenance day.

Output includes a fixture version and SHA256 for each passage. Hashes bind the
report to text; they do not authenticate a source, enforce tenant access or
establish truth. The checker implements none of those surrounding controls.

`evaluation-plan.md` is Lab 75.2: a protocol to complete before a real evaluation.
It includes deterministic and retrieval-only baselines, evidence/abstention
criteria, access tests, severity, repeated runs and operating cost. It is not a
claim that an assistant was evaluated.
