# Objective Benchmark Methods

This registry maps selected external benchmark methods to the skill catalog without claiming benchmark scores. A method is usable here only after it has a concrete adapter definition, objective metrics, integration requirements, and a recorded repository-resolution artifact.

Full-suite execution remains separate from adapter smoke checks. Any future score must include task inputs, environment details, command logs, output artifacts, and evaluator results.

## Methods

| Method | Scope | Metrics | Requirements | Adapter |
|---|---|---|---|---|
| `swe-skills-bench` | Measures skill utility on real software-engineering tasks by comparing paired runs with and without the skill. | with-skill pass rate, without-skill pass rate, pass-rate delta, token overhead | pinned task repository, with-skill run, without-skill run, deterministic acceptance tests | `implemented-smoke-adapter` |
| `skillsbench` | Evaluates agent skill use across diverse verifiable real-world tasks and deterministic verifiers. | task pass rate, skill gain, steps, token usage | task package, skill package, deterministic verifier, agent trajectory | `implemented-smoke-adapter` |
| `skill-bench` | Runs evidence-graded skill eval cases in CI and reports regression-oriented skill scores. | criterion score, evidence coverage, pass/fail, regression delta | eval case YAML, grader criteria, skill path, agent response transcript | `implemented-smoke-adapter` |
| `swe-bench` | Evaluates repository issue resolution by applying patches and running project tests. | resolved instances, patch applies, test pass rate, regression count | Docker-capable host, instance id, prediction patch, test harness output | `implemented-smoke-adapter` |
| `terminal-bench` | Evaluates terminal-native agent tasks with reproducible task containers and verifiers. | task success, command log completeness, execution time, resource use | task definition, container environment, command transcript, verifier result | `implemented-smoke-adapter` |
| `browsergym` | Provides a unified browser-agent environment across MiniWoB, WebArena, VisualWebArena, WorkArena, and related suites. | task success, trace completeness, browser actions, wall time | Playwright browser, environment id, browser trace, task evaluator | `implemented-smoke-adapter` |
| `webarena` | Measures realistic self-hosted web tasks with end-to-end web-agent success criteria. | end-to-end task success, site state correctness, action trace, human-baseline comparison | self-hosted sites, task id, browser trace, state evaluator | `implemented-smoke-adapter` |
| `webarena-verified` | Adds version-controlled verified web tasks and deterministic evaluators on top of WebArena-style environments. | verified task success, network trace evidence, response evaluator result, state evaluator result | verified task set, captured browser/network trace, deterministic evaluator, site snapshot | `implemented-smoke-adapter` |
| `st-webagentbench` | Evaluates safety and trustworthiness for enterprise-oriented web agents. | task success, safety violation rate, trustworthiness score, modality challenge score | web task instance, browser trace, safety policy, evaluator result | `implemented-smoke-adapter` |
| `osworld` | Evaluates multimodal computer-use agents across real desktop applications and operating-system workflows. | task success, execution evaluator result, screen trace, application state correctness | desktop environment, task config, screen/action trace, execution evaluator | `implemented-smoke-adapter` |
| `bfcl` | Evaluates executable tool/function calling, including relevance detection and multi-turn/tool-call scenarios. | AST match, execution accuracy, function relevance, multi-turn correctness | function schema, model/tool-call output, checker output, test split identifier | `implemented-smoke-adapter` |
| `mle-bench` | Evaluates machine-learning engineering agents on Kaggle-style competitions with local grading scripts. | competition score, medal threshold, valid submission rate, runtime budget | Kaggle credentials when needed, competition data, submission artifact, grading script output | `implemented-smoke-adapter` |
| `ml-dev-bench` | Evaluates real-world ML development tasks such as dataset handling, debugging, training, and implementation. | task success, model score, debugging correctness, implementation correctness | task repository, agent patch or outputs, training/evaluation logs, scoring script | `implemented-smoke-adapter` |
| `gittaskbench` | Evaluates code agents on real repository tasks from setup through delivery with cost-aware metrics. | task success, setup success, cost-aware alpha, test result | repository task, environment setup log, agent patch, test/evaluator result | `implemented-smoke-adapter` |

## Adapter Rule

A smoke adapter proves only that the external method can be addressed objectively from this repository. It is not a task pass, not a model score, and not a substitute for running the external suite.
