# Benchmark Results

This page reports measured results only. Offline static checks were run against the mirrored files in this repository. Runtime benchmark counts include only committed independent benchmark artifacts that pass `tools/check_benchmark_artifact.py`. Source-proof artifacts are provenance checks, not runtime benchmark passes.

## Summary

- Skills checked: `673`
- Static checks passed: `8076` / `8076`
- Average static score: `100.0`
- Runtime scenario artifacts recorded: `10`
- Runtime scenario artifacts passed: `0`
- Runtime scenario artifacts failed: `10`
- Source-proof provenance artifacts recorded: `10`

## Benchmark Tracks

| Track | Assigned scenarios | Runtime artifacts |
|---|---:|---:|
| `source-skill-repository` | 673 | 0 |
| `swe-bench-lite` | 57 | 1 |
| `nyc-tlc-trip-records` | 32 | 0 |
| `sec-edgar-companyfacts` | 251 | 0 |
| `common-crawl-warc` | 24 | 0 |
| `beir-retrieval` | 24 | 0 |
| `ms-marco` | 75 | 0 |
| `enron-email` | 71 | 0 |
| `stackoverflow-survey` | 14 | 0 |
| `ome-ngff-samples` | 194 | 0 |
| `cellxgene-census` | 148 | 0 |
| `chembl` | 148 | 0 |
| `owasp-benchmark` | 76 | 0 |
| `owasp-juice-shop` | 85 | 0 |
| `kubernetes-examples` | 305 | 9 |
| `opentelemetry-demo` | 294 | 0 |
| `coco-captions` | 58 | 0 |
| `local-omero-compose-workflows` | 105 | 0 |
| `air-defense-android-benchmarks` | 58 | 0 |

## Skill Scores

| Skill | Category | Static checks | Static score | Runtime artifacts | Fix points | Failed static checks |
|---|---|---:|---:|---:|---:|---|
| `strmt7-simple-ai-bitcoin-trading-binance-agents-skills-context-budget-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 1 | 4 | none |
| `strmt7-project-air-defense-agents-skills-android-visual-qa-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-project-air-defense-agents-skills-browser-fallback-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 2 | none |
| `strmt7-project-air-defense-agents-skills-caveman-help-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-project-air-defense-agents-skills-caveman-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-project-air-defense-agents-skills-compliance-and-rate-limit-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 2 | none |
| `strmt7-project-air-defense-agents-skills-context-budget-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-project-air-defense-agents-skills-level-asset-curation-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-project-air-defense-agents-skills-site-extract-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 2 | none |
| `strmt7-project-air-defense-agents-skills-source-audit-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 2 | none |
| `strmt7-project-air-defense-agents-skills-ue5-city-pipeline-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-project-air-defense-agents-skills-ue5-commonui-menu-systems-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-project-air-defense-agents-skills-ue5-mobile-gameplay-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-project-air-defense-agents-skills-ue5-mobile-rendering-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-project-air-defense-agents-skills-ue5-mobile-ui-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-project-air-defense-agents-skills-ue5-photoreal-city-scene-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-project-air-defense-agents-skills-verification-loop-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-project-air-defense-agents-skills-web-discovery-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 2 | none |
| `strmt7-project-air-defense-skills-android-3d-air-defense-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-ai-regression-testing-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-browser-fallback-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-caveman-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-compliance-and-rate-limit-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-context-budget-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-deployment-patterns-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-django-patterns-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-django-security-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-django-verification-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-docker-patterns-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-docs-knowledge-maintainer-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-documentation-lookup-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-env-contract-reviewer-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-frontend-preview-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-omero-runtime-verifier-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-plugin-regression-triager-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-postgres-patterns-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-python-patterns-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-python-testing-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-search-first-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-security-finding-triager-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-security-review-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-site-extract-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-source-audit-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-tdd-workflow-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-verification-loop-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-agents-skills-web-discovery-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 2 | none |
| `zmb-uzh-omero-docker-extended-third-party-caveman-v1-6-0-skills-caveman-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 3 | none |
| `zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-ai-regression-testing-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 3 | none |
| `zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-context-budget-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 3 | none |
| `zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-deployment-patterns-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 3 | none |
| `zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-django-patterns-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 4 | none |
| `zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-django-security-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 4 | none |
| `zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-django-verification-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 3 | none |
| `zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-docker-patterns-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 3 | none |
| `zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-documentation-lookup-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 3 | none |
| `zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-postgres-patterns-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 3 | none |
| `zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-python-patterns-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 4 | none |
| `zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-python-testing-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 4 | none |
| `zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-search-first-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 3 | none |
| `zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-security-review-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 3 | none |
| `zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-tdd-workflow-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 3 | none |
| `zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-verification-loop-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-ome-zarr-c-agents-skills-ai-regression-testing-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `strmt7-ome-zarr-c-agents-skills-benchmark-first-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `strmt7-ome-zarr-c-agents-skills-browser-fallback-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-ome-zarr-c-agents-skills-compliance-and-rate-limit-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-ome-zarr-c-agents-skills-context-budget-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `strmt7-ome-zarr-c-agents-skills-cpp-parity-porting-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `strmt7-ome-zarr-c-agents-skills-cpp-performance-optimization-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `strmt7-ome-zarr-c-agents-skills-immutable-parity-proof-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `strmt7-ome-zarr-c-agents-skills-pybind11-runtime-parity-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `strmt7-ome-zarr-c-agents-skills-python-testing-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `strmt7-ome-zarr-c-agents-skills-search-first-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `strmt7-ome-zarr-c-agents-skills-site-extract-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-ome-zarr-c-agents-skills-source-audit-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-ome-zarr-c-agents-skills-tdd-workflow-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `strmt7-ome-zarr-c-agents-skills-verification-loop-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `strmt7-ome-zarr-c-agents-skills-web-discovery-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `strmt7-ome-zarr-c-agents-skills-workflow-supply-chain-maintenance-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `strmt7-simple-ai-bitcoin-trading-binance-agents-skills-verification-loop-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 1 | 4 | none |
| `varnan-tech-opendirectory-packages-cli-skills-show-hn-writer-skill-md` | Agent infrastructure & skill creation | 12/12 | 100.0 | 0 | 3 | none |
| `affaan-m-everything-claude-code-agents-skills-claude-api-skill-md` | Agent infrastructure & skill creation | 12/12 | 100.0 | 0 | 2 | none |
| `affaan-m-everything-claude-code-agents-skills-dmux-workflows-skill-md` | Agent infrastructure & skill creation | 12/12 | 100.0 | 0 | 2 | none |
| `affaan-m-everything-claude-code-agents-skills-mcp-server-patterns-skill-md` | Agent infrastructure & skill creation | 12/12 | 100.0 | 0 | 3 | none |
| `affaan-m-everything-claude-code-agents-skills-strategic-compact-skill-md` | Agent infrastructure & skill creation | 12/12 | 100.0 | 0 | 2 | none |
| `anthropics-skills-skills-mcp-builder-skill-md` | Agent infrastructure & skill creation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-building-secure-contracts-skills-token-integration-analyzer-skill-md` | Agent infrastructure & skill creation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-skill-improver-skills-skill-improver-skill-md` | Agent infrastructure & skill creation | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-azure-pipelines-generator-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-azure-pipelines-validator-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-loki-config-generator-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 4 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-ai-agents-persistent-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-ai-document-intelligence-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-ai-openai-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-ai-projects-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-ai-voicelive-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-eventgrid-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-eventhub-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-identity-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-mgmt-apicenter-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-mgmt-apimanagement-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 1 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-mgmt-applicationinsights-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-mgmt-arizeaiobservabilityeval-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-mgmt-botservice-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-mgmt-fabric-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-mgmt-mongodbatlas-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-mgmt-weightsandbiases-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-resource-manager-cosmosdb-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-resource-manager-durabletask-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-resource-manager-mysql-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-resource-manager-playwright-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-resource-manager-redis-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-resource-manager-sql-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-search-documents-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-security-keyvault-keys-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-servicebus-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-m365-agents-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-microsoft-azure-webjobs-extensions-authentication-events-dotnet-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-ai-agents-persistent-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-ai-anomalydetector-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-ai-contentsafety-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-ai-formrecognizer-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-ai-projects-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-ai-vision-imageanalysis-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-ai-voicelive-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-appconfiguration-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-communication-callautomation-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-communication-callingserver-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-communication-chat-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-communication-common-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-communication-sms-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-compute-batch-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-cosmos-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-data-tables-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-eventgrid-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-eventhub-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-identity-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-messaging-webpubsub-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-monitor-ingestion-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 1 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-monitor-opentelemetry-exporter-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-monitor-query-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-security-keyvault-keys-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-security-keyvault-secrets-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-storage-blob-java-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-agent-framework-azure-ai-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-agents-v2-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-ai-contentsafety-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-ai-contentunderstanding-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-ai-language-conversations-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-ai-ml-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-ai-projects-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-ai-textanalytics-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-ai-transcription-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-ai-translation-document-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-ai-translation-text-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-ai-vision-imageanalysis-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-ai-voicelive-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-appconfiguration-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-containerregistry-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-cosmos-db-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-cosmos-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-data-tables-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-eventgrid-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-eventhub-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-identity-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 4 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-keyvault-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-messaging-webpubsubservice-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-mgmt-apicenter-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-mgmt-apimanagement-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-mgmt-botservice-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-mgmt-fabric-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-monitor-ingestion-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-monitor-opentelemetry-exporter-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-monitor-opentelemetry-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-monitor-query-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-search-documents-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 4 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-servicebus-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-speech-to-text-rest-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-storage-blob-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-storage-file-datalake-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-storage-file-share-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-azure-storage-queue-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-fastapi-router-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-hosted-agents-v2-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-m365-agents-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 1 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-python-skills-pydantic-models-py-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-rust-skills-azure-cosmos-rust-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-rust-skills-azure-eventhub-rust-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-rust-skills-azure-identity-rust-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-rust-skills-azure-keyvault-certificates-rust-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-rust-skills-azure-keyvault-keys-rust-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-rust-skills-azure-keyvault-secrets-rust-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-rust-skills-azure-storage-blob-rust-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-ai-contentsafety-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-ai-document-intelligence-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-ai-projects-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-ai-translation-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-ai-voicelive-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-appconfiguration-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-cosmos-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-eventhub-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-identity-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-keyvault-keys-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-keyvault-secrets-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-microsoft-playwright-testing-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-monitor-opentelemetry-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-search-documents-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-servicebus-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-storage-blob-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-storage-file-share-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-storage-queue-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 4 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-web-pubsub-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-frontend-ui-dark-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 4 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-m365-agents-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-react-flow-node-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-zustand-store-ts-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-appinsights-instrumentation-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-ai-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-aigateway-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-cloud-migrate-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-compliance-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-compute-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-cost-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-deploy-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-diagnostics-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-enterprise-infra-planner-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-hosted-copilot-sdk-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-kubernetes-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-kusto-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-messaging-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-prepare-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-quotas-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-rbac-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-resource-lookup-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-resource-visualizer-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-storage-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-upgrade-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-azure-validate-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-entra-app-registration-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-microsoft-foundry-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 1 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-microsoft-foundry-models-deploy-model-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 1 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-microsoft-foundry-models-deploy-model-capacity-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 1 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-microsoft-foundry-models-deploy-model-customize-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 1 | 3 | none |
| `microsoft-skills-github-plugins-azure-skills-skills-microsoft-foundry-models-deploy-model-preset-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 1 | 3 | none |
| `microsoft-skills-github-plugins-deep-wiki-skills-wiki-ado-convert-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-deep-wiki-skills-wiki-agents-md-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-deep-wiki-skills-wiki-architect-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-deep-wiki-skills-wiki-changelog-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-deep-wiki-skills-wiki-llms-txt-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-deep-wiki-skills-wiki-onboarding-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-deep-wiki-skills-wiki-page-writer-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-deep-wiki-skills-wiki-qa-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-deep-wiki-skills-wiki-researcher-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-deep-wiki-skills-wiki-vitepress-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-skills-cloud-solution-architect-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-skills-continual-learning-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-skills-copilot-sdk-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 4 | none |
| `microsoft-skills-github-skills-entra-agent-id-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-skills-frontend-design-review-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-skills-github-issue-creator-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-skills-kql-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-skills-mcp-builder-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-skills-microsoft-docs-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-skills-podcast-generation-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-skills-skill-creator-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-building-secure-contracts-skills-cosmos-vulnerability-scanner-skill-md` | Cloud, Azure & Microsoft SDKs | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-claude-md-generator-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-explain-this-pr-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-meta-ads-skill-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-position-me-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-stargazer-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-yc-intent-radar-skill-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `affaan-m-everything-claude-code-agents-skills-api-design-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `affaan-m-everything-claude-code-agents-skills-backend-patterns-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `affaan-m-everything-claude-code-agents-skills-eval-harness-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 2 | none |
| `affaan-m-everything-claude-code-agents-skills-everything-claude-code-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 2 | none |
| `affaan-m-everything-claude-code-agents-skills-investor-materials-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 2 | none |
| `affaan-m-everything-claude-code-agents-skills-nextjs-turbopack-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 2 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-makefile-generator-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 4 | none |
| `anthropics-skills-skills-claude-api-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-codex-skills-gh-cli-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-ask-questions-if-underspecified-skills-ask-questions-if-underspecified-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-building-secure-contracts-skills-code-maturity-assessor-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-building-secure-contracts-skills-guidelines-advisor-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-dimensional-analysis-skills-dimensional-analysis-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-dwarf-expert-skills-dwarf-expert-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-git-cleanup-skills-git-cleanup-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-let-fate-decide-skills-let-fate-decide-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-testing-handbook-skills-skills-address-sanitizer-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-testing-handbook-skills-skills-aflpp-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-testing-handbook-skills-skills-constant-time-testing-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-testing-handbook-skills-skills-fuzzing-dictionary-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-testing-handbook-skills-skills-fuzzing-obstacles-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-testing-handbook-skills-skills-libafl-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-trailmark-skills-trailmark-structural-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-trailmark-skills-trailmark-summary-skill-md` | Coding, refactoring & repository automation | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-kill-the-standup-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-linkedin-post-generator-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-meeting-brief-generator-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-newsletter-digest-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-noise2blog-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-outreach-sequence-builder-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-pr-description-writer-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-reddit-post-engine-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-tweet-thread-from-blog-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-twitter-gtm-find-skill-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `affaan-m-everything-claude-code-agents-skills-content-engine-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 2 | none |
| `affaan-m-everything-claude-code-agents-skills-crosspost-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 2 | none |
| `affaan-m-everything-claude-code-agents-skills-investor-outreach-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 2 | none |
| `anthropics-skills-skills-internal-comms-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-amazon-reviews-api-skill-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-browser-act-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-business-contact-social-links-skill-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-industry-key-contact-radar-api-skill-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-web-search-scraper-api-skill-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-angry-customer-playbook-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-auto-tag-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-bug-report-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-call-summary-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-chatbot-review-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-contact-sync-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-csat-followup-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-customer-360-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-draft-reply-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-email-verify-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-escalate-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-feedback-digest-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-freshdesk-triage-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-handoff-notes-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-inbox-zero-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-intercom-resolve-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-knowledge-search-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-lead-enrich-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-macro-builder-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-merge-tickets-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-nps-collect-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-outreach-campaign-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-proposal-draft-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-response-templates-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-root-cause-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-sentiment-check-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-support-metrics-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-ticket-summarize-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-ticket-triage-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-tone-rewriter-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-translate-ticket-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-vip-alert-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-weekly-digest-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-whatsapp-support-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-zendesk-triage-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-zoho-desk-triage-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `hardikpandya-stop-slop-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-devcontainer-setup-skills-devcontainer-setup-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-modern-python-skills-modern-python-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-trailmark-skills-crypto-protocol-diagram-skill-md` | Communication, productivity & support | 12/12 | 100.0 | 0 | 3 | none |
| `bria-ai-bria-skill-skills-bria-ai-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `bria-ai-bria-skill-skills-image-utils-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `bria-ai-bria-skill-skills-remove-background-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `bria-ai-bria-skill-skills-vgl-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `evolinkai-music-generation-skill-for-openclaw-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `evolinkai-video-generation-skill-for-openclaw-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `raven7979-ai-video-editing-skill-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-blog-cover-image-cli-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `affaan-m-everything-claude-code-agents-skills-article-writing-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 2 | none |
| `affaan-m-everything-claude-code-agents-skills-brand-voice-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `affaan-m-everything-claude-code-agents-skills-fal-ai-media-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 2 | none |
| `anthropics-skills-skills-algorithmic-art-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `anthropics-skills-skills-brand-guidelines-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `anthropics-skills-skills-slack-gif-creator-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-amazon-product-api-skill-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-google-image-api-skill-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-social-media-finder-skill-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-youtube-batch-transcript-extractor-api-skill-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-youtube-comments-api-skill-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-youtube-transcript-analysis-api-skill-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-youtube-transcript-extractor-api-skill-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-youtube-video-api-skill-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `designrique-ai-graphic-design-skill-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `fruteroclub-marketing-designer-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `guinacio-claude-image-gen-skills-image-generation-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-banner-design-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-design-system-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-ui-styling-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `supermemoryai-skills-svg-animations-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `yuvalsuede-agent-media-skill-skill-md` | Creative, media & design | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-cook-the-blog-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 4 | none |
| `varnan-tech-opendirectory-packages-cli-skills-hackernews-intel-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-reddit-icp-monitor-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 4 | none |
| `varnan-tech-opendirectory-packages-cli-skills-schema-markup-generator-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 4 | none |
| `affaan-m-everything-claude-code-agents-skills-video-editing-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `ahmedasmar-devops-claude-skills-aws-cost-optimization-skills-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 4 | none |
| `ahmedasmar-devops-claude-skills-gitops-workflows-skills-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `ahmedasmar-devops-claude-skills-iac-terraform-skills-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `ahmedasmar-devops-claude-skills-k8s-troubleshooter-skills-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `ahmedasmar-devops-claude-skills-monitoring-observability-skills-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-ansible-generator-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 4 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-bash-script-generator-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-dockerfile-generator-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 4 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-fluentbit-generator-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-github-actions-generator-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-gitlab-ci-generator-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 5 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-helm-generator-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-jenkinsfile-generator-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-k8s-debug-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-logql-generator-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-promql-generator-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 5 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-terraform-generator-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 4 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-terragrunt-generator-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 5 | none |
| `anthropics-skills-skills-doc-coauthoring-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 4 | none |
| `browser-act-skills-amazon-best-selling-products-finder-api-skill-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-amazon-buy-box-monitor-api-skill-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-amazon-product-search-api-skill-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-google-maps-reviews-api-skill-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-google-news-api-skill-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-reddit-competitor-analysis-api-skill-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-wechat-article-search-api-skill-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-youtube-api-skill-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-youtube-search-api-skill-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-zhihu-search-api-skill-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-refund-processor-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-culture-index-skills-interpreting-culture-index-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-workflow-skill-design-skills-designing-workflow-skills-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 4 | none |
| `twwch-comfyui-workflow-skill-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 4 | none |
| `ztj7728-gemini-image-generation-skill-md` | DevOps, cloud & operations | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-docs-from-code-skill-md` | Documents, spreadsheets & presentations | 12/12 | 100.0 | 0 | 3 | none |
| `affaan-m-everything-claude-code-agents-skills-frontend-slides-skill-md` | Documents, spreadsheets & presentations | 12/12 | 100.0 | 0 | 2 | none |
| `aizzaku-create-infographics-skill-md` | Documents, spreadsheets & presentations | 12/12 | 100.0 | 0 | 4 | none |
| `anthropics-skills-skills-canvas-design-skill-md` | Documents, spreadsheets & presentations | 12/12 | 100.0 | 0 | 3 | none |
| `anthropics-skills-skills-docx-skill-md` | Documents, spreadsheets & presentations | 12/12 | 100.0 | 0 | 4 | none |
| `anthropics-skills-skills-pdf-skill-md` | Documents, spreadsheets & presentations | 12/12 | 100.0 | 0 | 3 | none |
| `anthropics-skills-skills-pptx-skill-md` | Documents, spreadsheets & presentations | 12/12 | 100.0 | 0 | 3 | none |
| `anthropics-skills-skills-theme-factory-skill-md` | Documents, spreadsheets & presentations | 12/12 | 100.0 | 0 | 3 | none |
| `anthropics-skills-skills-xlsx-skill-md` | Documents, spreadsheets & presentations | 12/12 | 100.0 | 0 | 3 | none |
| `hugohe3-ppt-master-skills-ppt-master-skill-md` | Documents, spreadsheets & presentations | 12/12 | 100.0 | 0 | 3 | none |
| `nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-design-skill-md` | Documents, spreadsheets & presentations | 12/12 | 100.0 | 0 | 3 | none |
| `nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-slides-skill-md` | Documents, spreadsheets & presentations | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-producthunt-launch-kit-skill-md` | Finance, commerce & forecasting | 12/12 | 100.0 | 0 | 3 | none |
| `affaan-m-everything-claude-code-agents-skills-market-research-skill-md` | Finance, commerce & forecasting | 12/12 | 100.0 | 0 | 2 | none |
| `affaan-m-everything-claude-code-agents-skills-coding-standards-skill-md` | Frontend, UI & browser automation | 12/12 | 100.0 | 0 | 3 | none |
| `affaan-m-everything-claude-code-agents-skills-frontend-patterns-skill-md` | Frontend, UI & browser automation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-claude-in-chrome-troubleshooting-skills-claude-in-chrome-troubleshooting-skill-md` | Frontend, UI & browser automation | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-optimize-for-gpu-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pufferlib-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-google-maps-api-skill-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-google-maps-search-api-skill-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-maps-search-dotnet-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-ui-ux-pro-max-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-firebase-apk-scanner-skills-firebase-apk-scanner-skill-md` | Game, mobile & visual QA | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-omero-integration-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-resource-manager-postgresql-dotnet-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 3 | none |
| `microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-postgres-ts-skill-md` | OMERO, Django, Docker & lab infrastructure | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-adaptyv-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-aeon-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-anndata-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-arboreto-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-astropy-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-benchling-integration-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-bgpt-paper-search-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-biopython-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-bioservices-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-cellxgene-census-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 5 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-cirq-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-citation-management-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-clinical-decision-support-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-clinical-reports-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-cobrapy-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-consciousness-council-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-dask-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-database-lookup-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-datamol-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 5 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-deepchem-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-deeptools-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-depmap-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-dhdna-profiler-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-diffdock-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-dnanexus-integration-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-docx-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-esm-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-etetoolkit-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-exploratory-data-analysis-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-flowio-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 5 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-fluidsim-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-generate-image-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-geniml-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-geomaster-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-geopandas-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-get-available-resources-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-gget-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-ginkgo-cloud-lab-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-glycoengineering-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-gtars-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-histolab-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 5 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-hypogenic-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 5 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-hypothesis-generation-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-imaging-data-commons-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 5 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-infographics-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-iso-13485-certification-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-labarchive-integration-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-lamindb-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-latchbio-integration-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-latex-posters-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-literature-review-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-markdown-mermaid-writing-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-market-research-reports-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-markitdown-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-matchms-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-matlab-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-matplotlib-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-medchem-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-modal-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-molecular-dynamics-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-molfeat-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 5 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-networkx-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-neurokit2-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-neuropixels-analysis-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-open-notebook-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-opentrons-integration-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-paper-lookup-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-paperzilla-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-parallel-web-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pathml-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pdf-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-peer-review-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pennylane-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-phylogenetics-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-polars-bio-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-polars-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pptx-posters-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pptx-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-primekg-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-protocolsio-integration-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pydeseq2-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pydicom-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pyhealth-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pylabrobot-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pymatgen-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pymc-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pymoo-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pyopenms-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pysam-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pytdc-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pytorch-lightning-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-pyzotero-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-qiskit-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-qutip-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-rdkit-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-research-grants-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-research-lookup-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-rowan-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 5 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-scanpy-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-scholar-evaluation-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-scientific-brainstorming-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-scientific-critical-thinking-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-scientific-schematics-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-scientific-slides-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-scientific-visualization-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-scientific-writing-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-scikit-bio-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-scikit-learn-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-scikit-survival-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-scvelo-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-scvi-tools-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-seaborn-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 5 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-shap-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 5 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-simpy-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-stable-baselines3-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-statistical-analysis-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-statsmodels-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 5 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-sympy-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-tiledbvcf-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-timesfm-forecasting-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-torch-geometric-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-torchdrug-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-transformers-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-treatment-plans-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-umap-learn-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-usfiscaldata-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-vaex-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-venue-templates-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-what-if-oracle-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 4 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-xlsx-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 3 | none |
| `k-dense-ai-scientific-agent-skills-scientific-skills-zarr-python-skill-md` | Science, research & data analysis | 12/12 | 100.0 | 0 | 5 | none |
| `varnan-tech-opendirectory-packages-cli-skills-google-trends-api-skills-skill-md` | Search, retrieval & web automation | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-luma-attendees-scraper-skill-md` | Search, retrieval & web automation | 12/12 | 100.0 | 0 | 3 | none |
| `affaan-m-everything-claude-code-agents-skills-deep-research-skill-md` | Search, retrieval & web automation | 12/12 | 100.0 | 0 | 2 | none |
| `affaan-m-everything-claude-code-agents-skills-documentation-lookup-skill-md` | Search, retrieval & web automation | 12/12 | 100.0 | 0 | 2 | none |
| `affaan-m-everything-claude-code-agents-skills-exa-search-skill-md` | Search, retrieval & web automation | 12/12 | 100.0 | 0 | 2 | none |
| `anthropics-skills-skills-frontend-design-skill-md` | Search, retrieval & web automation | 12/12 | 100.0 | 0 | 3 | none |
| `anthropics-skills-skills-web-artifacts-builder-skill-md` | Search, retrieval & web automation | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-amazon-asin-lookup-api-skill-skill-md` | Search, retrieval & web automation | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-amazon-competitor-analyzer-skill-md` | Search, retrieval & web automation | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-amazon-listing-competitor-analysis-skill-skill-md` | Search, retrieval & web automation | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-github-project-contributor-finder-api-skill-skill-md` | Search, retrieval & web automation | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-web-research-assistant-skill-md` | Search, retrieval & web automation | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-youtube-channel-api-skill-skill-md` | Search, retrieval & web automation | 12/12 | 100.0 | 0 | 3 | none |
| `browser-act-skills-youtube-influencer-finder-api-skill-skill-md` | Search, retrieval & web automation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-second-opinion-skills-second-opinion-skill-md` | Search, retrieval & web automation | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-trailmark-skills-diagramming-code-skill-md` | Search, retrieval & web automation | 12/12 | 100.0 | 0 | 3 | none |
| `varnan-tech-opendirectory-packages-cli-skills-dependency-update-bot-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `varnan-tech-opendirectory-packages-cli-skills-llms-txt-generator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `affaan-m-everything-claude-code-agents-skills-security-review-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 3 | none |
| `affaan-m-everything-claude-code-agents-skills-x-api-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 3 | none |
| `ahmedasmar-devops-claude-skills-ci-cd-skills-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-ansible-validator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-bash-script-validator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-dockerfile-validator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-fluentbit-validator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-github-actions-validator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-gitlab-ci-validator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-helm-validator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-jenkinsfile-validator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-k8s-yaml-generator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-k8s-yaml-validator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-makefile-validator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-promql-validator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 3 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-terraform-validator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-terragrunt-validator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `composio-community-support-skills-customer-winback-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `composio-community-support-skills-sla-monitor-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-brand-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-agentic-actions-auditor-skills-agentic-actions-auditor-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-audit-context-building-skills-audit-context-building-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-building-secure-contracts-skills-algorand-vulnerability-scanner-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-building-secure-contracts-skills-audit-prep-assistant-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-building-secure-contracts-skills-cairo-vulnerability-scanner-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-building-secure-contracts-skills-secure-workflow-guide-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-building-secure-contracts-skills-solana-vulnerability-scanner-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-building-secure-contracts-skills-substrate-vulnerability-scanner-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-building-secure-contracts-skills-ton-vulnerability-scanner-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-burpsuite-project-parser-skills-burpsuite-project-parser-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-constant-time-analysis-skills-constant-time-analysis-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-differential-review-skills-differential-review-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-entry-point-analyzer-skills-entry-point-analyzer-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-fp-check-skills-fp-check-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-insecure-defaults-skills-insecure-defaults-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-seatbelt-sandboxer-skills-seatbelt-sandboxer-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-semgrep-rule-creator-skills-semgrep-rule-creator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-semgrep-rule-variant-creator-skills-semgrep-rule-variant-creator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-sharp-edges-skills-sharp-edges-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-spec-to-code-compliance-skills-spec-to-code-compliance-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-static-analysis-skills-codeql-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-static-analysis-skills-sarif-parsing-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-static-analysis-skills-semgrep-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-supply-chain-risk-auditor-skills-supply-chain-risk-auditor-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-testing-handbook-skills-skills-cargo-fuzz-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-testing-handbook-skills-skills-harness-writing-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 5 | none |
| `trailofbits-skills-plugins-testing-handbook-skills-skills-ossfuzz-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-testing-handbook-skills-skills-testing-handbook-generator-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-trailmark-skills-audit-augmentation-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-trailmark-skills-graph-evolution-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-trailmark-skills-mermaid-to-proverif-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-trailmark-skills-trailmark-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-variant-analysis-skills-variant-analysis-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-yara-authoring-skills-yara-rule-authoring-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-zeroize-audit-skills-zeroize-audit-skill-md` | Security, compliance & risk | 12/12 | 100.0 | 0 | 4 | none |
| `affaan-m-everything-claude-code-agents-skills-bun-runtime-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 3 | none |
| `affaan-m-everything-claude-code-agents-skills-e2e-testing-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 3 | none |
| `affaan-m-everything-claude-code-agents-skills-tdd-workflow-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 3 | none |
| `affaan-m-everything-claude-code-agents-skills-verification-loop-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 3 | none |
| `anthropics-skills-skills-skill-creator-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 3 | none |
| `anthropics-skills-skills-webapp-testing-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 3 | none |
| `composio-community-support-skills-qa-response-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 4 | none |
| `lackeyjb-playwright-skill-skills-playwright-skill-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-debug-buttercup-skills-debug-buttercup-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 3 | none |
| `trailofbits-skills-plugins-mutation-testing-skills-mutation-testing-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-property-based-testing-skills-property-based-testing-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-testing-handbook-skills-skills-atheris-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 5 | none |
| `trailofbits-skills-plugins-testing-handbook-skills-skills-coverage-analysis-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 5 | none |
| `trailofbits-skills-plugins-testing-handbook-skills-skills-libfuzzer-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 5 | none |
| `trailofbits-skills-plugins-testing-handbook-skills-skills-ruzzy-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-testing-handbook-skills-skills-wycheproof-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 5 | none |
| `trailofbits-skills-plugins-trailmark-skills-genotoxic-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 4 | none |
| `trailofbits-skills-plugins-trailmark-skills-vector-forge-skill-md` | Testing, QA & benchmarking | 12/12 | 100.0 | 0 | 4 | none |

## Runtime Artifacts

| Artifact | Skill | Scenario | Verdict | Score | Runner |
|---|---|---|---|---:|---|
| `artifacts/benchmark-runs/2026-04-17-independent-runtime-readiness-batch-01/microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-mgmt-apimanagement-dotnet-skill-md/cloud-azure-and-microsoft-sdks-kubernetes-examples/artifact.json` | `microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-mgmt-apimanagement-dotnet-skill-md` | `cloud-azure-and-microsoft-sdks-kubernetes-examples` | `failed` | 90.0 | tools/create_independent_runtime_batch.py |
| `artifacts/benchmark-runs/2026-04-17-independent-runtime-readiness-batch-01/microsoft-skills-github-plugins-azure-sdk-java-skills-azure-monitor-ingestion-java-skill-md/cloud-azure-and-microsoft-sdks-kubernetes-examples/artifact.json` | `microsoft-skills-github-plugins-azure-sdk-java-skills-azure-monitor-ingestion-java-skill-md` | `cloud-azure-and-microsoft-sdks-kubernetes-examples` | `failed` | 90.0 | tools/create_independent_runtime_batch.py |
| `artifacts/benchmark-runs/2026-04-17-independent-runtime-readiness-batch-01/microsoft-skills-github-plugins-azure-sdk-python-skills-m365-agents-py-skill-md/cloud-azure-and-microsoft-sdks-kubernetes-examples/artifact.json` | `microsoft-skills-github-plugins-azure-sdk-python-skills-m365-agents-py-skill-md` | `cloud-azure-and-microsoft-sdks-kubernetes-examples` | `failed` | 90.0 | tools/create_independent_runtime_batch.py |
| `artifacts/benchmark-runs/2026-04-17-independent-runtime-readiness-batch-01/microsoft-skills-github-plugins-azure-skills-skills-microsoft-foundry-models-deploy-model-capacity-skill-md/cloud-azure-and-microsoft-sdks-kubernetes-examples/artifact.json` | `microsoft-skills-github-plugins-azure-skills-skills-microsoft-foundry-models-deploy-model-capacity-skill-md` | `cloud-azure-and-microsoft-sdks-kubernetes-examples` | `failed` | 90.0 | tools/create_independent_runtime_batch.py |
| `artifacts/benchmark-runs/2026-04-17-independent-runtime-readiness-batch-01/microsoft-skills-github-plugins-azure-skills-skills-microsoft-foundry-models-deploy-model-customize-skill-md/cloud-azure-and-microsoft-sdks-kubernetes-examples/artifact.json` | `microsoft-skills-github-plugins-azure-skills-skills-microsoft-foundry-models-deploy-model-customize-skill-md` | `cloud-azure-and-microsoft-sdks-kubernetes-examples` | `failed` | 90.0 | tools/create_independent_runtime_batch.py |
| `artifacts/benchmark-runs/2026-04-17-independent-runtime-readiness-batch-01/microsoft-skills-github-plugins-azure-skills-skills-microsoft-foundry-models-deploy-model-preset-skill-md/cloud-azure-and-microsoft-sdks-kubernetes-examples/artifact.json` | `microsoft-skills-github-plugins-azure-skills-skills-microsoft-foundry-models-deploy-model-preset-skill-md` | `cloud-azure-and-microsoft-sdks-kubernetes-examples` | `failed` | 90.0 | tools/create_independent_runtime_batch.py |
| `artifacts/benchmark-runs/2026-04-17-independent-runtime-readiness-batch-01/microsoft-skills-github-plugins-azure-skills-skills-microsoft-foundry-models-deploy-model-skill-md/cloud-azure-and-microsoft-sdks-kubernetes-examples/artifact.json` | `microsoft-skills-github-plugins-azure-skills-skills-microsoft-foundry-models-deploy-model-skill-md` | `cloud-azure-and-microsoft-sdks-kubernetes-examples` | `failed` | 90.0 | tools/create_independent_runtime_batch.py |
| `artifacts/benchmark-runs/2026-04-17-independent-runtime-readiness-batch-01/microsoft-skills-github-plugins-azure-skills-skills-microsoft-foundry-skill-md/cloud-azure-and-microsoft-sdks-kubernetes-examples/artifact.json` | `microsoft-skills-github-plugins-azure-skills-skills-microsoft-foundry-skill-md` | `cloud-azure-and-microsoft-sdks-kubernetes-examples` | `failed` | 90.0 | tools/create_independent_runtime_batch.py |
| `artifacts/benchmark-runs/2026-04-17-independent-runtime-readiness-batch-01/strmt7-simple-ai-bitcoin-trading-binance-agents-skills-context-budget-skill-md/devops-cloud-and-operations-kubernetes-examples/artifact.json` | `strmt7-simple-ai-bitcoin-trading-binance-agents-skills-context-budget-skill-md` | `devops-cloud-and-operations-kubernetes-examples` | `failed` | 90.0 | tools/create_independent_runtime_batch.py |
| `artifacts/benchmark-runs/2026-04-17-independent-runtime-readiness-batch-01/strmt7-simple-ai-bitcoin-trading-binance-agents-skills-verification-loop-skill-md/testing-qa-and-benchmarking-swe-bench-lite/artifact.json` | `strmt7-simple-ai-bitcoin-trading-binance-agents-skills-verification-loop-skill-md` | `testing-qa-and-benchmarking-swe-bench-lite` | `failed` | 90.0 | tools/create_independent_runtime_batch.py |

## Source-Proof Provenance Artifacts

| Artifact | Skill | Scenario | Runner |
|---|---|---|---|
| `artifacts/benchmark-runs/2026-04-17-first-source-proofs/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-azure-pipelines-generator-skill-md/skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-azure-pipelines-generator-skill-md/artifact.json` | `akin-ozer-cc-devops-skills-devops-skills-plugin-skills-azure-pipelines-generator-skill-md` | `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-azure-pipelines-generator-skill-md` | tools/create_source_proof_batch.py |
| `artifacts/benchmark-runs/2026-04-17-first-source-proofs/bria-ai-bria-skill-skills-bria-ai-skill-md/skill-proof-bria-ai-bria-skill-skills-bria-ai-skill-md/artifact.json` | `bria-ai-bria-skill-skills-bria-ai-skill-md` | `skill-proof-bria-ai-bria-skill-skills-bria-ai-skill-md` | tools/create_source_proof_batch.py |
| `artifacts/benchmark-runs/2026-04-17-first-source-proofs/strmt7-ome-zarr-c-agents-skills-ai-regression-testing-skill-md/skill-proof-strmt7-ome-zarr-c-agents-skills-ai-regression-testing-skill-md/artifact.json` | `strmt7-ome-zarr-c-agents-skills-ai-regression-testing-skill-md` | `skill-proof-strmt7-ome-zarr-c-agents-skills-ai-regression-testing-skill-md` | tools/create_source_proof_batch.py |
| `artifacts/benchmark-runs/2026-04-17-first-source-proofs/strmt7-project-air-defense-agents-skills-android-visual-qa-skill-md/skill-proof-strmt7-project-air-defense-agents-skills-android-visual-qa-skill-md/artifact.json` | `strmt7-project-air-defense-agents-skills-android-visual-qa-skill-md` | `skill-proof-strmt7-project-air-defense-agents-skills-android-visual-qa-skill-md` | tools/create_source_proof_batch.py |
| `artifacts/benchmark-runs/2026-04-17-first-source-proofs/strmt7-simple-ai-bitcoin-trading-binance-agents-skills-context-budget-skill-md/skill-proof-strmt7-simple-ai-bitcoin-trading-binance-agents-skills-context-budget-skill-md/artifact.json` | `strmt7-simple-ai-bitcoin-trading-binance-agents-skills-context-budget-skill-md` | `skill-proof-strmt7-simple-ai-bitcoin-trading-binance-agents-skills-context-budget-skill-md` | tools/create_source_proof_batch.py |
| `artifacts/benchmark-runs/2026-04-17-first-source-proofs/strmt7-simple-ai-bitcoin-trading-binance-agents-skills-verification-loop-skill-md/skill-proof-strmt7-simple-ai-bitcoin-trading-binance-agents-skills-verification-loop-skill-md/artifact.json` | `strmt7-simple-ai-bitcoin-trading-binance-agents-skills-verification-loop-skill-md` | `skill-proof-strmt7-simple-ai-bitcoin-trading-binance-agents-skills-verification-loop-skill-md` | tools/create_source_proof_batch.py |
| `artifacts/benchmark-runs/2026-04-17-first-source-proofs/varnan-tech-opendirectory-packages-cli-skills-claude-md-generator-skill-md/skill-proof-varnan-tech-opendirectory-packages-cli-skills-claude-md-generator-skill-md/artifact.json` | `varnan-tech-opendirectory-packages-cli-skills-claude-md-generator-skill-md` | `skill-proof-varnan-tech-opendirectory-packages-cli-skills-claude-md-generator-skill-md` | tools/create_source_proof_batch.py |
| `artifacts/benchmark-runs/2026-04-17-first-source-proofs/varnan-tech-opendirectory-packages-cli-skills-kill-the-standup-skill-md/skill-proof-varnan-tech-opendirectory-packages-cli-skills-kill-the-standup-skill-md/artifact.json` | `varnan-tech-opendirectory-packages-cli-skills-kill-the-standup-skill-md` | `skill-proof-varnan-tech-opendirectory-packages-cli-skills-kill-the-standup-skill-md` | tools/create_source_proof_batch.py |
| `artifacts/benchmark-runs/2026-04-17-first-source-proofs/varnan-tech-opendirectory-packages-cli-skills-show-hn-writer-skill-md/skill-proof-varnan-tech-opendirectory-packages-cli-skills-show-hn-writer-skill-md/artifact.json` | `varnan-tech-opendirectory-packages-cli-skills-show-hn-writer-skill-md` | `skill-proof-varnan-tech-opendirectory-packages-cli-skills-show-hn-writer-skill-md` | tools/create_source_proof_batch.py |
| `artifacts/benchmark-runs/2026-04-17-first-source-proofs/zmb-uzh-omero-docker-extended-agents-skills-ai-regression-testing-skill-md/skill-proof-zmb-uzh-omero-docker-extended-agents-skills-ai-regression-testing-skill-md/artifact.json` | `zmb-uzh-omero-docker-extended-agents-skills-ai-regression-testing-skill-md` | `skill-proof-zmb-uzh-omero-docker-extended-agents-skills-ai-regression-testing-skill-md` | tools/create_source_proof_batch.py |
