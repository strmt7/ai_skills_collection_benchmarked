# Objective Benchmark Methods

This registry records declared metrics, integration requirements and historical repository-resolution checks. The declared smoke-adapter stage does not establish that a native task package, harness or verifier has been executed.

Full-suite execution remains separate from adapter smoke checks. Any future score must include task inputs, environment details, command logs, output artifacts, and evaluator results.

## Methods

| Method | Scope | Metrics | Requirements | Adapter |
|---|---|---|---|---|
| `swe-skills-bench` | Measures skill utility on real software-engineering tasks by comparing paired runs with and without the skill. | with-skill pass rate, without-skill pass rate, pass-rate delta, token overhead | pinned task repository, with-skill run, without-skill run, deterministic acceptance tests | `declared-source-probe` |
| `skillsbench` | Evaluates agent skill use across diverse verifiable real-world tasks and deterministic verifiers. | task pass rate, skill gain, steps, token usage | task package, skill package, deterministic verifier, agent trajectory | `declared-source-probe` |
| `skill-bench` | Runs evidence-graded skill eval cases in CI and reports regression-oriented skill scores. | criterion score, evidence coverage, pass/fail, regression delta | eval case YAML, grader criteria, skill path, agent response transcript | `declared-source-probe` |
| `swe-bench` | Evaluates repository issue resolution by applying patches and running project tests. | resolved instances, patch applies, test pass rate, regression count | Docker-capable host, instance id, prediction patch, test harness output | `declared-source-probe` |
| `terminal-bench` | Evaluates terminal-native agent tasks with reproducible task containers and verifiers. | task success, command log completeness, execution time, resource use | task definition, container environment, command transcript, verifier result | `declared-source-probe` |
| `browsergym` | Provides a unified browser-agent environment across MiniWoB, WebArena, VisualWebArena, WorkArena, and related suites. | task success, trace completeness, browser actions, wall time | Playwright browser, environment id, browser trace, task evaluator | `declared-source-probe` |
| `webarena` | Measures realistic self-hosted web tasks with end-to-end web-agent success criteria. | end-to-end task success, site state correctness, action trace, human-baseline comparison | self-hosted sites, task id, browser trace, state evaluator | `declared-source-probe` |
| `webarena-verified` | Adds version-controlled verified web tasks and deterministic evaluators on top of WebArena-style environments. | verified task success, network trace evidence, response evaluator result, state evaluator result | verified task set, captured browser/network trace, deterministic evaluator, site snapshot | `declared-source-probe` |
| `st-webagentbench` | Evaluates safety and trustworthiness for enterprise-oriented web agents. | task success, safety violation rate, trustworthiness score, modality challenge score | web task instance, browser trace, safety policy, evaluator result | `declared-source-probe` |
| `osworld` | Evaluates multimodal computer-use agents across real desktop applications and operating-system workflows. | task success, execution evaluator result, screen trace, application state correctness | desktop environment, task config, screen/action trace, execution evaluator | `declared-source-probe` |
| `bfcl` | Evaluates executable tool/function calling, including relevance detection and multi-turn/tool-call scenarios. | AST match, execution accuracy, function relevance, multi-turn correctness | function schema, model/tool-call output, checker output, test split identifier | `declared-source-probe` |
| `mle-bench` | Evaluates machine-learning engineering agents on Kaggle-style competitions with local grading scripts. | competition score, medal threshold, valid submission rate, runtime budget | Kaggle credentials when needed, competition data, submission artifact, grading script output | `declared-source-probe` |
| `ml-dev-bench` | Evaluates real-world ML development tasks such as dataset handling, debugging, training, and implementation. | task success, model score, debugging correctness, implementation correctness | task repository, agent patch or outputs, training/evaluation logs, scoring script | `declared-source-probe` |
| `gittaskbench` | Evaluates code agents on real repository tasks from setup through delivery with cost-aware metrics. | task success, setup success, cost-aware alpha, test result | repository task, environment setup log, agent patch, test/evaluator result | `declared-source-probe` |
| `swe-bench-pro-v2` | Tests long-horizon repository changes with clean-image patch regrading and regression checks. | resolved tasks, fail-to-pass outcomes, pass-to-pass regressions, attempt cost | pinned V2 split and images, reference and empty-patch controls, clean-image regrading, all attempt outcomes | `declared-source-probe` |
| `deepswe` | Tests original long-horizon engineering tasks with committed-patch verification in a fresh environment. | task pass rate, named test outcomes, agent steps, token usage | pinned task and verifier versions, fresh verification image, committed patch, complete CTRF test inventory | `declared-source-probe` |
| `workarena` | Tests atomic and composed enterprise knowledge-work journeys on ServiceNow through BrowserGym. | task success, application state correctness, action count, attempt cost | approved disposable ServiceNow instance, pinned BrowserGym environment, task level and seeds, native state evaluator | `declared-source-probe` |
| `scienceagentbench` | Tests data-driven scientific programming across multiple disciplines using executable output checks. | task success, program execution, scientific output correctness, attempt cost | pinned dataset and dependency environment, discipline-specific output oracle, submission program, data and model provenance | `declared-source-probe` |

## Adapter Rule

A smoke adapter proves only that the external method can be addressed objectively from this repository. It is not a task pass, not a model score, and not a substitute for running the external suite.

Current source research and immutable release pins for SkillsBench are recorded in [the SkillsBench review](research-skillsbench.md). Historical probes remain unchanged; no agent-efficacy result is inferred from them.

The [expanded benchmark review](benchmark-expansion.md) separates skill-effect studies, repository engineering, terminal workflows, enterprise browser tasks and scientific programming. `declared-source-probe` means a source-resolution definition; it does not mean a native evaluation adapter is implemented. The new selected source probes are retained separately from the historical 14-method run.
