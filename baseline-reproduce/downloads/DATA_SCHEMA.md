# Text delivery schema 1.0

This is a separate handoff schema, not a replacement for the existing website's
gold/silver EV2R schema. Its measurements must not be copied into EV2R fields.

## Files

- `metrics.json`: `schema_version`, `created_utc`, `scope`, `model`, `date_policy`,
  `gold_label_counts`, `majority_label_accuracy`, `budget`, `evaluation`, `systems`.
- `claims.json`: `schema_version` and `claims`, an ordered list of 100 objects.
- `results.csv`: the four system summaries, with probabilities on a 0–1 scale.
- `manifest.json`: SHA256 for each payload/document and each frozen source output,
  plus the evaluation's scorer/gold hashes. It does not hash itself.
- `VALIDATION.json`: independently checked counts, metrics, privacy scan and hashes.
- `REPORT.md`: interpretation and limitations.
- `WEBSITE_HANDOFF.md`: integration instructions; publication is not authorized.

## Claim object

Each claim has `key` (`averitec/dev/<original_index>`), `dataset`, `split`,
`original_index` (0–99, never renumber), `claim`, `claim_date` (dataset string),
`gold_label`, and `results` keyed by the four system IDs. There is exactly one
result for every system/claim pair, including failures.

Each result has:

- `status`: native final status, `ok`, `no_evidence` or `retrieval_failed` here.
- `predicted_label`: model label for verdict-bearing outcomes, otherwise null.
- `label_correct`: full-denominator match; failures are false.
- `qa_pairs`: ordered `{question, answer, url, source_status, placeholder}`.
  A missing URL is null, not an implied link to another source. `placeholder`
  means the literal `No Evidence.` used by SANCTUARY, not a supporting fact.
- `justification`: native generated reasoning when present; may be null. Do not
  fabricate reasoning for a system that did not produce it.
- `admitted_sources`: candidate pages admitted by date policy, each with `url`,
  `date`, `date_class`, `date_policy`. These are not all final cited evidence.
- `legacy_scores`: `question_hu_meteor` and `qa_hu_meteor`, 0–1 values. These are
  lexical reference similarities, not confidence, truth probabilities or EV2R.
- `error_category`: native non-ok status or null. No raw exceptions are exported.
- `source_output_sha256`: identity of the frozen original system output.
- `qa_source_note`: SANCTUARY's compact QA can concatenate evidence from multiple
  pages while retaining only the first URL. This note must be visible.

## Metric object

Per system: fixed `n_planned=100`, `n_terminal=100`, `n_valid_verdict`, `n_correct`,
`status_counts`, full-sample and valid-only accuracy, four-class `macro_f1`,
`class_f1`, `confusion_matrix` (gold rows, prediction columns, explicit
`SYSTEM_FAILED` column), question and QA legacy means, and
`legacy_joint_by_threshold`. Joint scores use **strict greater than** threshold,
not greater-than-or-equal. Show all recorded thresholds when offering selection.

Counts also include `non_ok_ids`, `qa_count`, `qa_missing_source_url`,
`claims_with_missing_qa_url`, `verdict_fallback_count`. Missing URL counts include
explicit unanswerable/absence-of-evidence statements. They are not automatically
fabricated citations. Conversely a nonempty URL has not been entailment-verified.

Generation completion is 400/400 terminal records, with 391 ok, 5 no_evidence
and 4 retrieval_failed. It does not mean 400 successful predictions or completion
of the deferred six-system scope. `budget.all_history_conservative_usd` includes
all historical experiments, including deferred multimodal smoke and uncertain
billing. It is not the provider invoice or the net cost of the formal text set.

## Privacy and provenance

Claim text, model answers, public source URLs and selected evidence text embedded
in answers are included for review. Raw page bodies, full model request messages,
keys, billing journals, machine aliases and absolute local/remote paths are not.
No private audit files are needed to render this package. Publication still
requires the user's approval and the website's own release/privacy check.

The full report and JSON retain all outcomes without filtering on correctness.
Generated answers should be displayed as untrusted text, never injected as HTML.

