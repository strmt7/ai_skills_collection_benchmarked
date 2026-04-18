# Benchmark Suite

Scenario definitions live in `data/benchmark_scenarios.json`; per-skill assignments live in `data/benchmark_assignments.json`.

The current suite contains `673` source-grounded skill-proof scenarios and `45` category workflow templates. A scenario is only a template until a runner records artifacts under the rules in [Benchmark runner requirements](benchmark-runner-requirements.md). Current measured outputs are summarized in [Benchmark results](benchmark-results.md), with independent runtime-readiness batches in [Runtime benchmark batch 01](runtime-benchmark-batch-01.md), [Runtime benchmark batch 02](runtime-benchmark-batch-02.md), and [Runtime benchmark batch 03](runtime-benchmark-batch-03.md). Exact unresolved local Markdown targets are grouped in [Local Markdown link failures](local-markdown-link-failures.md).

## Scoring Rules

A benchmark run must record the skill ID, scenario ID, source commit, dataset or website snapshot, environment, commands or transcript, output artifact, objective metrics, and evaluator result. Synthetic fixtures may supplement coverage, but they do not replace a real source repository, real dataset, real website, or recorded runtime workflow when the scenario calls for one.

## Source skill repository proof

- ID: `source-skill-repository`
- URL: https://github.com/strmt7/ai_skills_collection_benchmarked
- Workflow: Use the skill source repository itself as the proof fixture: inspect SKILL.md, companion resources, and source path to verify trigger, constraints, and expected artifacts.
- Metrics: frontmatter valid, trigger derivable, proof artifact schema valid

## SWE-bench Lite

- ID: `swe-bench-lite`
- URL: https://github.com/SWE-bench/SWE-bench
- Workflow: Patch real GitHub issue tasks and verify with repository tests.
- Metrics: patch applies, test pass rate, regression count

## NYC TLC trip records

- ID: `nyc-tlc-trip-records`
- URL: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- Workflow: Clean, aggregate, and explain large real trip data.
- Metrics: schema correctness, aggregation accuracy, runtime budget

## SEC EDGAR company facts

- ID: `sec-edgar-companyfacts`
- URL: https://www.sec.gov/edgar/sec-api-documentation
- Workflow: Extract and reconcile financial facts from filings.
- Metrics: citation coverage, numeric reconciliation, filing provenance

## Common Crawl WARC

- ID: `common-crawl-warc`
- URL: https://commoncrawl.org/
- Workflow: Retrieve, parse, and cite web-scale documents.
- Metrics: source precision, deduplication, citation traceability

## BEIR retrieval benchmark

- ID: `beir-retrieval`
- URL: https://github.com/beir-cellar/beir
- Workflow: Evaluate retrieval workflows across datasets.
- Metrics: nDCG@10, recall@100, query latency

## MS MARCO

- ID: `ms-marco`
- URL: https://microsoft.github.io/msmarco/
- Workflow: Rank passages and support answer extraction.
- Metrics: MRR, recall, answer support

## CMU Enron email dataset

- ID: `enron-email`
- URL: https://www.cs.cmu.edu/~enron/
- Workflow: Classify, summarize, and route real email threads.
- Metrics: routing accuracy, PII handling, summary faithfulness

## Stack Overflow Developer Survey

- ID: `stackoverflow-survey`
- URL: https://survey.stackoverflow.co/
- Workflow: Analyze survey data and produce reproducible charts.
- Metrics: cleaning correctness, chart reproducibility, method clarity

## OME-NGFF sample data

- ID: `ome-ngff-samples`
- URL: https://idr.github.io/ome-ngff-samples/
- Workflow: Read and validate multiscale microscopy data.
- Metrics: metadata validity, chunk correctness, shape parity

## CZ CELLxGENE Census

- ID: `cellxgene-census`
- URL: https://chanzuckerberg.github.io/cellxgene-census/
- Workflow: Query and analyze single-cell expression data.
- Metrics: query correctness, metadata filters, reproducibility

## ChEMBL

- ID: `chembl`
- URL: https://www.ebi.ac.uk/chembl/
- Workflow: Retrieve molecular bioactivity records.
- Metrics: identifier accuracy, filter correctness, citation provenance

## OWASP Benchmark

- ID: `owasp-benchmark`
- URL: https://owasp.org/www-project-benchmark/
- Workflow: Find and classify vulnerability test cases.
- Metrics: true positives, false positives, CWE mapping

## OWASP Juice Shop

- ID: `owasp-juice-shop`
- URL: https://owasp.org/www-project-juice-shop/
- Workflow: Run safe local security workflows against a known vulnerable app.
- Metrics: finding reproducibility, risk classification, remediation quality

## Kubernetes examples

- ID: `kubernetes-examples`
- URL: https://github.com/kubernetes/examples
- Workflow: Validate manifests and operational runbooks.
- Metrics: schema validity, least privilege, rollout success

## OpenTelemetry demo

- ID: `opentelemetry-demo`
- URL: https://github.com/open-telemetry/opentelemetry-demo
- Workflow: Debug telemetry across microservices.
- Metrics: trace completeness, metric coverage, diagnostic accuracy

## COCO captions

- ID: `coco-captions`
- URL: https://cocodataset.org/#download
- Workflow: Evaluate image understanding and visual QA tasks.
- Metrics: caption faithfulness, object coverage, layout accuracy

## ZMB-UZH OMERO workflows

- ID: `local-omero-compose-workflows`
- URL: https://github.com/ZMB-UZH/omero-docker-extended
- Workflow: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.
- Metrics: compose health, plugin workflow, regression count

## Project Air Defense Android benchmarks

- ID: `air-defense-android-benchmarks`
- URL: https://github.com/strmt7/project_air_defense/tree/main/benchmarks
- Workflow: Run startup, gameplay, and visual QA benchmark scenarios.
- Metrics: startup time, frame stability, visual regressions
