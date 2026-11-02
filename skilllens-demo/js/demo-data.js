/* Paper numbers for the demo, coding domain only. Source: SkillLens (ACL submission #8998, PDF of 2026-10-13).
 * Table 1 counts are pass counts out of 57; the 7 models also present in the saved per-task file reproduce
 * these counts exactly (checked 2026-11-01/02). Category benchmarks and verifiers come from the sbench
 * handover document, not from the paper. */
window.PAPER = {
  cite: "SkillLens: Diagnosing Agent Skills in Language-Agent Benchmarks (ACL submission #8998, under review; PDF of 2026-10-13)",
  N_TASKS: 57,
  // Table 1, Code column: Base (= N), Matched (= M), Routed (= R); [pass rate %, pass count]
  MODELS: [
    { id: "haiku", data: "haiku", name: "Claude Haiku 4.5", B: [73.7, 42], M: [86.0, 49], R: [84.2, 48] },
    { id: "sonnet", data: "sonnet", name: "Claude Sonnet 4.6", B: [94.7, 54], M: [96.5, 55], R: [98.2, 56] },
    { id: "gemma", data: "gemma", name: "Gemma-4-26B", B: [59.6, 34], M: [70.2, 40], R: [71.9, 41] },
    { id: "glm", data: "glm", name: "GLM-5.1", B: [91.2, 52], M: [89.5, 51], R: [89.5, 51] },
    { id: "mini", data: "gpt54", name: "GPT-5.4-Mini", B: [57.9, 33], M: [57.9, 33], R: [57.9, 33] },
    { id: "sol", data: null, name: "GPT-5.6-Sol", B: [84.2, 48], M: [80.7, 46], R: [82.5, 47] },
    { id: "kimi", data: "kimi", name: "Kimi-K2.6", B: [89.5, 51], M: [86.0, 49], R: [89.5, 51] },
    { id: "qwen", data: "qwen8b", name: "Qwen3-8B", B: [35.1, 20], M: [29.8, 17], R: [33.3, 19] }
  ],
  // Table 2, Code: N / M / X / B for the three models that ran all four conditions; [rate %, count]
  CTRL: [
    { name: "Claude Haiku 4.5", N: [73.7, 42], M: [86.0, 49], X: [80.7, 46], B: [77.2, 44] },
    { name: "Gemma-4-26B", N: [59.6, 34], M: [70.2, 40], X: [52.6, 30], B: [64.9, 37] },
    { name: "Qwen3-8B", N: [35.1, 20], M: [29.8, 17], X: [31.6, 18], B: [31.6, 18] }
  ],
  // Table 3, Code: model uptake = (repairs − regressions) / 57
  UPTAKE: [
    { name: "Claude Haiku 4.5", r: 10, g: 3, u: 12.3 },
    { name: "Gemma-4-26B", r: 8, g: 2, u: 10.5 },
    { name: "Qwen3-8B", r: 2, g: 5, u: -5.3 }
  ],
  // Table 6 (category utility over Haiku, Gemma, Qwen: (R − G) / (n × 3)); Figure 2(b) task counts
  CATS: [
    { skill: "python-traceback-reading", name: "Python traceback reading", n: 9, u: 11.1, r: 4, g: 1, bench: "SWE-bench Lite", verifier: "SWE-bench pytest (FAIL_TO_PASS / PASS_TO_PASS)" },
    { skill: "django-orm", name: "Django ORM", n: 8, u: 12.5, r: 6, g: 3, bench: "SWE-bench Lite", verifier: "SWE-bench pytest" },
    { skill: "dynamic-programming-patterns", name: "Dynamic programming", n: 5, u: 13.3, r: 2, g: 0, bench: "LiveCodeBench / AtCoder", verifier: "stdin/stdout exact match" },
    { skill: "data-cleaning-eda-workflow", name: "Data cleaning and EDA", n: 5, u: -6.7, r: 1, g: 2, bench: "InfiAgent-DABench", verifier: "answer key–value match" },
    { skill: "kaggle-ml-pipeline-optimization", name: "Kaggle ML pipelines", n: 5, u: 13.3, r: 3, g: 1, bench: "MLE-bench (Kaggle)", verifier: "competition metric threshold" },
    { skill: "sql-join-window-functions", name: "SQL joins and windows", n: 5, u: 0.0, r: 0, g: 0, bench: "BIRD-Critic 1.0", verifier: "SQL execution check" },
    { skill: "react-state-form-testing", name: "React state and form testing", n: 5, u: -6.7, r: 0, g: 1, bench: "WebApp1K-React", verifier: "vitest unit tests" },
    { skill: "cross-file-dependency-tracing", name: "Cross-file dependency tracing", n: 5, u: -6.7, r: 1, g: 2, bench: "RepoExec (Scrapy)", verifier: "benchmark test harness" },
    { skill: "edge-case-regression-test-generation", name: "Edge-case regression testing", n: 5, u: 20.0, r: 3, g: 0, bench: "BugsInPy", verifier: "fail-before / pass-after" },
    { skill: "sql-injection-prevention", name: "SQL injection prevention", n: 5, u: 0.0, r: 0, g: 0, bench: "SVEN (CWE-089)", verifier: "CodeQL analysis" }
  ],
  // Table 5, Code (descriptive variance check, "not a strong causal model", §3.5)
  VAR: [["Model", 3.6], ["Category", 5.0], ["Additive", 8.6], ["+Inter.", 8.6], ["Residual", 82.9]]
};
