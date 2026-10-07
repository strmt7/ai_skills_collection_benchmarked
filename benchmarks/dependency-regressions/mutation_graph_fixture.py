import ast
import hashlib
import importlib.util
import json
import re
import tempfile
from pathlib import Path

from trailmark.query.api import QueryEngine

SOURCE = "def externally_called(value):\n    return value + 1\n\ndef helper(value):\n    return value * 2\n\ndef local_caller(value):\n    return helper(value)\n"


def run(request):
    with tempfile.TemporaryDirectory(prefix="trailmark-graph-") as temporary:
        root = Path(temporary)
        path = root / "library.py"
        path.write_text(SOURCE)
        engine = QueryEngine.from_directory(root, language="python")
        engine.preanalysis()
        graph = json.loads(engine.to_json())
        matching = {
            name: [nid for nid, node in graph["nodes"].items() if node.get("name") == name]
            for name in ("externally_called", "helper", "local_caller")
        }
        assert all(len(ids) == 1 for ids in matching.values()), matching
        callers = {name: engine.callers_of(ids[0]) for name, ids in matching.items()}
        spec = importlib.util.spec_from_file_location("external_library", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.externally_called(41) == 42
        assert module.local_caller(21) == 42
        original = Path(__file__).with_name("original-graph-analysis.md").read_text()
        selected = {
            "find_containing_node",
            "batch_triage",
            "map_removal_to_production_node",
            "infer_production_path",
            "merge_results",
        }
        functions = []
        for code in re.findall(r"```python\n(.*?)```", original, re.S):
            tree = ast.parse(code)
            functions.extend(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in selected)
        assert {node.name for node in functions} == selected and len(functions) == len(selected)
        namespace = {"json": json, "re": re}
        exec(compile(ast.Module(body=functions, type_ignores=[]), "original-graph-analysis", "exec"), namespace)
        line_case = {"file_path": str(path), "line": 2, "mutant_id": "external-return-change"}
        batch = namespace["batch_triage"](
            engine, [line_case, {"file_path": "outside_graph.py", "line": 1, "mutant_id": "unmapped"}]
        )
        map_node = namespace["map_removal_to_production_node"]
        nodes = {
            "a": {"id": "a", "name": "parse", "location": {"file_path": "src/a.py"}},
            "b": {"id": "b", "name": "parse", "location": {"file_path": "src/b.py"}},
        }
        ambiguous = map_node(nodes, "object.parse(data)", "tests/test_unknown.py")
        reversed_choice = map_node(dict(reversed(list(nodes.items()))), "object.parse(data)", "tests/test_unknown.py")
        excluded = map_node(
            {"production": {"id": "production", "name": "validate", "location": {"file_path": "src/contest.py"}}},
            "validate(data)",
            "tests/test_contest.py",
        )
        mutations = {
            "false_positives": [],
            "missing_tests": [{"node_id": "shared", "mutant_id": "one"}, {"node_id": "shared", "mutant_id": "two"}],
            "fuzzing_targets": [],
        }
        removals = {
            "false_positives": [],
            "missing_tests": [{"node_id": "shared", "removal_id": "test-check"}],
            "fuzzing_targets": [],
        }
        merged = namespace["merge_results"](mutations, removals)
        math_cases = []
        for q, width in ((19, 2), (65521, 4)):
            radix = 256**width
            inverse = pow(radix, -1, q)
            internal = [1, 2]
            public = [m * inverse % q for m in internal]
            assert all(x * radix % q == m for x, m in zip(public, internal, strict=True))
            limbs = [[(m >> (8 * k)) & 255 for k in range(width)] for m in internal]
            equal = [a == b for a, b in zip(*limbs, strict=True)]
            assert public[0] != public[1] and not all(equal) and any(equal)
            math_cases.append(
                {
                    "modulus": q,
                    "radix": radix,
                    "canonical_inputs": public,
                    "internal_residues": internal,
                    "limbs": limbs,
                    "limb_AND_equal": all(equal),
                    "limb_OR_equal": any(equal),
                }
            )
        return {
            "source_sha256": hashlib.sha256(SOURCE.encode()).hexdigest(),
            "node_ids": matching,
            "callers": callers,
            "graph": graph,
            "preanalysis_completed": True,
            "attack_surface": engine.attack_surface(),
            "complexity_hotspots": engine.complexity_hotspots(threshold=1),
            "external_invocation_result": module.externally_called(41),
            "library_internal_call_result": module.local_caller(21),
            "original_batch_triage": batch,
            "original_ambiguous_choices": [ambiguous, reversed_choice],
            "original_production_substring_exclusion": excluded,
            "original_many_mutations_one_removal_merge": merged,
            "generic_montgomery_bijection_cases": math_cases,
            "case_study_rust_library_executed": False,
        }
