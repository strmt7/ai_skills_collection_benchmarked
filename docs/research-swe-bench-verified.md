# SWE-bench Verified dataset compatibility

SWE-bench Verified is a public set of 500 issue-resolution tasks; its [dataset card](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified) describes human review of the instances. The repository's [existing SWE-bench adapter](external-benchmark-adapter-smoke.md) is a source-resolution smoke check, not a suite run or an agent score.

On 1 November 2026, an isolated Windows control passed all 500 rows from each of two dataset-server snapshots to the installed SWE-bench 5.0.2 `make_test_spec` function. The rows had matching instance IDs, source repositories and base commits. All 500 rows from `princeton-nlp/SWE-bench_Verified` raised `KeyError: 'image'`; all 500 rows from `SWE-bench/SWE-bench_Verified` produced a test specification. The [recorded results](../artifacts/external-benchmark-integrations/swe-verified-schema-v1/result.json) include hashes for every API page and the [source observations](../artifacts/external-benchmark-integrations/swe-verified-schema-v1/source-observations.json) identify the tested wheel and observed dataset revisions. The dataset-server responses were not cryptographically bound to those separately observed revisions.

In a 2026 [OpenAI audit of SWE-bench Verified](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/),
59.4% of 138 selected tasks that models often failed had material test or problem-description
issues. That selected subset is not an estimate for all 500 tasks. The audit also describes
contamination concerns.

In July 2026, [OpenAI withdrew its earlier recommendation of SWE-bench Pro](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)
after finding substantial issues in that version. The benchmark maintainers subsequently
[announced Pro V2](https://labs.scale.com/leaderboard/swe_bench_pro_public_v2), including task
removals and corrections. This repository has not independently qualified the revised suite.
These findings do not establish an agent result for this collection.

This check did not execute the evaluation scripts, pull images, run gold patches, score agents, or establish that an image or test suite works. A test specification being constructed is a necessary input check, not an evaluation result. The dataset is public and cannot be treated as a private holdout. Before a benchmark run, verify the selected harness and dataset versions, pin the actual inputs, run the [official harness controls](https://www.swebench.com/SWE-bench/guides/quickstart/), and retain results for each planned condition and failure.

## Reproduce the input check

From the repository root on Windows with Python 3.13, the following creates a fresh temporary directory, downloads the ten dataset-server response pages, and installs the tested harness into a separate virtual environment. It does not install SWE-bench into this collection or run an evaluation. Network contents and dependencies can change; compare the printed page hashes with the recorded result when reproducing the exact observation.

```powershell
$pages = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $pages | Out-Null
foreach ($label in 'legacy', 'current') {
    $dataset = if ($label -eq 'legacy') {
        'princeton-nlp%2FSWE-bench_Verified'
    } else {
        'SWE-bench%2FSWE-bench_Verified'
    }
    foreach ($offset in 0, 100, 200, 300, 400) {
        $url = "https://datasets-server.huggingface.co/rows?dataset=$dataset&config=default&split=test&offset=$offset&length=100"
        Invoke-WebRequest -Uri $url -OutFile (Join-Path $pages "$label-$offset.json")
    }
}
py -3.13 -m venv (Join-Path $pages 'venv')
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed' }
$python = Join-Path $pages 'venv/Scripts/python.exe'
& $python -m pip install 'swebench==5.0.2'
if ($LASTEXITCODE -ne 0) { throw 'Harness installation failed' }
& $python artifacts/external-benchmark-integrations/swe-verified-schema-v1/reproduce.py --pages $pages
if ($LASTEXITCODE -ne 0) { throw 'The captured inputs or observed behavior differ' }
```

The control checks page completeness, ordering, truncation, unique IDs and matched source identities. It invokes the test-spec builder with network access disabled for the imported Hugging Face client and disables implicit `.env` loading. Retain the temporary inputs and installed dependency list when investigating a different result.
