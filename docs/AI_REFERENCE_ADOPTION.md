# RecruitOS AI Reference Adoption Plan

## Decision

External resume-screening repositories are research references, not direct dependencies. RecruitOS independently implements useful concepts inside its secure, configurable, tenant-aware architecture.

## Adopted design principles

### Deterministic foundation

Mandatory requirements, experience rules, configured weights and recommendations remain visible and reproducible.

### AI augmentation

Future AI modules will add:

- schema-validated resume and JD extraction;
- evidence mapping to source sections/pages;
- semantic embeddings and hybrid retrieval;
- alternative-role recommendations;
- candidate comparison and recruiter Q&A;
- candidate-specific interview questions;
- confidence, model version and prompt version metadata.

### Human review

AI may prioritize, explain and identify uncertainty. It must not silently auto-reject a candidate or overwrite configured mandatory rules.

### Tenant isolation

AI providers, prompts, models, vector indexes and retrieval results must be tenant-scoped. Configuration version `0.7.4` provides the governance anchor for future model, prompt, embedding and taxonomy snapshots.

## Reference concepts selected

- hybrid keyword + semantic retrieval and fusion;
- small-to-big retrieval that searches chunks but evaluates full authorized evidence;
- section-by-section LLM extraction into strict schemas;
- role-specific evaluation packs and evidence-based explanations;
- hierarchical skill/qualification taxonomies and equivalence groups;
- provider abstraction for local and approved hosted models;
- top-K alternative-role classification;
- multilingual and internationalization readiness;
- prompt-injection, invisible-text and repeated-run variance testing.

## Rejected patterns

- hardcoded role/skill dictionaries;
- shared global job requirements;
- direct loading of unverified pickle/joblib models;
- credentials embedded in source;
- candidate documents stored in Git or application tables as ungoverned blobs;
- unexplained single-score or single-label decisions;
- AI decisions without evidence, confidence and human review.

## Future AI metadata

Every AI-assisted screening will eventually record:

- provider and model;
- model version and artifact hash;
- prompt/template version;
- embedding and retrieval version;
- tenant configuration version and SHA-256;
- evidence references;
- confidence and uncertainty;
- latency and cost;
- human reviewer decision and override reason.
