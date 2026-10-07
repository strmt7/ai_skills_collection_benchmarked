"""Offline controls for a pinned SkillsBench development task; no model score.

Acquire task commit 55bfe693f2a19f6b2f29aca3f54fe98b9d994668 separately.
Requires the repository's test environment, Docker, and the qualified image.
The original skill text and oracle solution are not loaded.
"""

import argparse
import copy
import dataclasses
import hashlib
import importlib.util
import json
import sys
import tempfile
import textwrap
import types
from pathlib import Path


def qualify(root, task):
    workspace = task / "environment/workspace"
    files = {
        workspace / "sequential.py": "c4db418799f1b90804df928acfadc0f5ef479c11cfee9aa1ae778691cc30b697",
        workspace / "document_generator.py": "ae5347801de8f6d60b5337de46b8f2269784613a0fa92c7f6ec8c1445a8c59ee",
        task / "verifier/test_outputs.py": "3de14cb18c18d2c4afdf ee4cf70809acb866aa67c13d8d6f4bc67d7f44e26c20".replace(
            " ", ""
        ),
    }
    for path, expected in files.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("pinned task source changed")
    sys.path.insert(0, str(root / "tools"))
    from compare_tfidf_outputs import compare
    from isolated_python import run_isolated

    sys.path.insert(0, str(workspace))
    from document_generator import Document
    from sequential import batch_search_sequential, build_tfidf_index_sequential

    def encode(value):
        if dataclasses.is_dataclass(value):
            return encode(dataclasses.asdict(value))
        if isinstance(value, dict):
            return {str(key): encode(item) for key, item in value.items()}
        if isinstance(value, (tuple, list)):
            return [encode(item) for item in value]
        if isinstance(value, set):
            return sorted(value)
        return value

    def oracle(request):
        documents = [Document(**item) for item in request["documents"]]
        index = build_tfidf_index_sequential(documents).index
        results = batch_search_sequential(request["queries"], index, request["top_k"], documents)
        return {"index": encode(index), "search_results": encode(results)}

    documents = [
        {"doc_id": 7, "title": "Alpha", "content": "alpha alpha beta", "topic": "fixture", "word_count": 3},
        {"doc_id": 42, "title": "Beta", "content": "beta gamma gamma", "topic": "fixture", "word_count": 3},
        {"doc_id": 91, "title": "the and", "content": "a I 1 23", "topic": "fixture", "word_count": 4},
    ]
    cases = [
        {
            "name": "noncontiguous-empty-unknown-stopword-queries",
            "documents": documents,
            "queries": ["alpha", "gamma beta", "", "the and", "unknownterm"],
            "top_k": 10,
        },
        {"name": "zero-top-k", "documents": documents, "queries": ["alpha", "gamma beta"], "top_k": 0},
        {"name": "empty-corpus", "documents": [], "queries": ["alpha", ""], "top_k": 10},
        {"name": "empty-query-batch", "documents": documents, "queries": [], "top_k": 10},
    ]
    expected_outputs = [oracle(case) for case in cases]

    # Execute the original verifier method unchanged with a deliberately wrong,
    # fully controlled parallel fixture. This is not submitted agent code.
    spec = importlib.util.spec_from_file_location("reviewed_upstream_test_outputs", task / "verifier/test_outputs.py")
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    shim = types.ModuleType("parallel_solution")
    shim.build_tfidf_index_parallel = lambda docs, **kwargs: build_tfidf_index_sequential(docs)
    shim.batch_search_parallel = lambda *args, **kwargs: ([], 0.0)
    previous = sys.modules.get("parallel_solution")
    sys.modules["parallel_solution"] = shim
    try:
        fixture_docs = [Document(**item) for item in documents]
        original.TestCorrectnessSmall().test_search_results_match(
            fixture_docs, build_tfidf_index_sequential(fixture_docs)
        )
        empty_output_accepted = True
    finally:
        if previous is None:
            del sys.modules["parallel_solution"]
        else:
            sys.modules["parallel_solution"] = previous

    bad = copy.deepcopy(expected_outputs[0])
    bad["search_results"] = []
    bad_errors = compare(expected_outputs[0], bad)
    wrapper = """
    import dataclasses
    from document_generator import Document
    from sequential import batch_search_sequential, build_tfidf_index_sequential
    def encode(value):
        if dataclasses.is_dataclass(value):
            return encode(dataclasses.asdict(value))
        if isinstance(value, dict):
            return {str(key): encode(item) for key, item in value.items()}
        if isinstance(value, (tuple, list)):
            return [encode(item) for item in value]
        if isinstance(value, set):
            return sorted(value)
        return value
    def run(request):
        outputs = []
        for case in request:
            docs = [Document(**item) for item in case['documents']]
            index = build_tfidf_index_sequential(docs).index
            results = batch_search_sequential(case['queries'], index, case['top_k'], docs)
            outputs.append({'index': encode(index), 'search_results': encode(results)})
        return outputs
    """
    with tempfile.TemporaryDirectory(prefix="tfidf-controls-") as temporary:
        staging = Path(temporary)
        for name in ["sequential.py", "document_generator.py"]:
            (staging / name).write_bytes((workspace / name).read_bytes())
        (staging / "candidate.py").write_text(textwrap.dedent(wrapper), encoding="utf-8")
        execution = run_isolated(
            staging,
            ["candidate.py", "sequential.py", "document_generator.py"],
            cases,
            timeout=10,
            output_limit=262144,
            profile="skillsbench-tfidf",
        )
    actual_outputs = execution.get("candidate_response", {}).get("result")
    if not isinstance(actual_outputs, list) or len(actual_outputs) != len(cases):
        differences = ["missing or incomplete reference-control output"]
    else:
        differences = [
            f"{cases[index]['name']}: {error}"
            for index in range(len(cases))
            for error in compare(expected_outputs[index], actual_outputs[index])
        ]
    report = {
        "schema_version": 1,
        "evidence_class": "pinned-external-verifier-and-new-comparator-controls",
        "task_commit": "55bfe693f2a19f6b2f29aca3f54fe98b9d994668",
        "source_sha256": {path.relative_to(task).as_posix(): expected for path, expected in files.items()},
        "original_unchanged_verifier_accepted_empty_results": empty_output_accepted,
        "new_comparator_rejected_empty_results": bool(bad_errors),
        "empty_output_differences": bad_errors,
        "reference_control_cases": [case["name"] for case in cases],
        "reference_control_differences": differences,
        "execution": execution,
        "comparator_sha256": hashlib.sha256((root / "tools/compare_tfidf_outputs.py").read_bytes()).hexdigest(),
        "scope": "Known-good sequential reference and known-bad empty-output controls, not an agent result or performance score. Expectations computed outside candidate container; original task skill text and oracle solution remain unread.",
    }
    passed = (
        empty_output_accepted
        and bool(bad_errors)
        and not differences
        and execution["status"] == "completed"
        and execution["cleanup_verified"]
    )
    print(
        json.dumps(
            {
                "passed": passed,
                "original_empty_acceptance_reproduced": empty_output_accepted,
                "new_empty_rejection": bool(bad_errors),
                "reference_cases": len(cases),
                "reference_differences": differences,
                "execution_status": execution["status"],
            }
        )
    )
    report["all_controls_passed"] = bool(passed)
    report["reproducer_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return report


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("receipt already exists; select a new output path")
    root = Path(__file__).resolve().parents[3]
    report = qualify(root, args.task.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    return 0 if report["all_controls_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
