#!/usr/bin/env python3
"""Demonstrate independently specified oracle strengths with current Hypothesis.

These trusted small fixtures are contract controls, not a mutation-tool campaign,
proof for an unbounded domain, or an agent benchmark. No candidate code is loaded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import operator
import re
import sys
from collections import Counter
from pathlib import Path

import hypothesis
from hypothesis import assume, find, given, settings
from hypothesis import strategies as st
from hypothesis.errors import FailedHealthCheck, Unsatisfiable

SEARCH = settings(max_examples=200, derandomize=True, database=None, deadline=None)


def controls():
    results = []

    def observe(name, function):
        try:
            detail = function()
            results.append({"control": name, "passed": True, "detail": detail})
        except Exception as error:
            results.append({"control": name, "passed": False, "error": f"{type(error).__name__}: {error}"})

    def addition_oracle():
        # A direct independently specified arithmetic oracle detects subtraction.
        a, b = find(
            st.tuples(st.integers(-20, 20), st.integers(-20, 20)),
            lambda pair: operator.sub(*pair) != pair[0] + pair[1],
            settings=SEARCH,
        )
        assert operator.add(a, b) == a + b
        assert operator.sub(a, b) != a + b
        return {
            "counterexample": [a, b],
            "expected": a + b,
            "mutated_actual": a - b,
            "correct_reference_actual": operator.add(a, b),
        }

    observe("independent_simple_expression_is_not_a_tautology", addition_oracle)

    def shared_codec_error():
        # Specification: signed 64-bit, big-endian. The zero vector is independent.
        def encode(n):
            return (n + 7).to_bytes(8, "big", signed=True)

        def decode(data):
            return int.from_bytes(data, "big", signed=True) - 7

        for n in range(-200, 201):
            assert decode(encode(n)) == n
        expected = bytes(8)
        assert encode(0) != expected
        return {
            "roundtrip_inputs_checked": 401,
            "roundtrip_passed": True,
            "independent_zero_vector_expected": expected.hex(),
            "actual": encode(0).hex(),
            "format_defect_detected_by_independent_vector": True,
        }

    observe("roundtrip_can_hide_shared_codec_defects", shared_codec_error)

    def normalization():
        # Intended contract: trim surrounding whitespace and preserve the content.
        def constant_normalizer(_):
            return ""

        for text in ["", "a", " b ", "\tunicode Ω\n"]:
            assert constant_normalizer(constant_normalizer(text)) == constant_normalizer(text)
        assert constant_normalizer("content") != "content"
        return {
            "idempotence_passed": True,
            "expected": "content",
            "mutated_actual": "",
            "content_preservation_detects_defect": True,
        }

    observe("idempotence_is_not_a_full_normalization_specification", normalization)

    def duplicates():
        original, mutated = [1, 1, 2], [1, 2, 2]
        assert len(original) == len(mutated) and set(original) == set(mutated)
        assert Counter(original) != Counter(mutated)
        return {
            "input": original,
            "mutated_output": mutated,
            "set_and_length_checks_passed": True,
            "multiset_check_detected_duplicate_loss": True,
        }

    observe("set_plus_length_does_not_preserve_duplicate_multiplicity", duplicates)

    def regex_domain():
        pattern = r"[a-z][a-z0-9]{1,20}"
        text = find(st.from_regex(pattern), lambda s: re.fullmatch(pattern, s) is None, settings=SEARCH)
        assert re.search(pattern, text) and re.fullmatch(pattern, text) is None
        full = find(st.from_regex(pattern, fullmatch=True), lambda s: True, settings=SEARCH)
        assert re.fullmatch(pattern, full)
        return {
            "default_search_counterexample": repr(text),
            "fullmatch_fixture": full,
            "default_strategy_can_generate_outside_fullmatch_domain": True,
        }

    observe("regex_strategy_search_and_fullmatch_domains_differ", regex_domain)

    def collection_type():
        mutable = find(st.sets(st.integers(-3, 3)), lambda _: True, settings=SEARCH)
        frozen = find(st.frozensets(st.integers(-3, 3)), lambda _: True, settings=SEARCH)
        assert isinstance(mutable, set) and isinstance(frozen, frozenset)
        return {"sets_type": type(mutable).__name__, "frozensets_type": type(frozen).__name__}

    observe("set_and_frozenset_strategies_have_distinct_output_types", collection_type)

    def seed_example_budget():
        from hypothesis import given, seed

        calls = []

        @seed(0)
        @settings(max_examples=7, database=None, deadline=None)
        @given(st.integers())
        def probe(n):
            calls.append(n)

        probe()
        assert len(calls) == 7
        return {
            "configured_max_examples": 7,
            "observed_examples": len(calls),
            "seed_does_not_increase_example_budget": True,
        }

    observe("a_seed_does_not_request_more_examples", seed_example_budget)

    def contradictory_assumptions():
        calls = []

        @settings(max_examples=20, derandomize=True, database=None, deadline=None)
        @given(st.integers())
        def impossible(n):
            assume(n > 100)
            assume(n < 50)
            calls.append(n)

        try:
            impossible()
        except (FailedHealthCheck, Unsatisfiable) as error:
            assert not calls
            return {
                "observed_exception": type(error).__name__,
                "successful_examples": 0,
                "test_passed": False,
                "health_checks_suppressed": False,
            }
        raise AssertionError("Contradictory assumptions unexpectedly passed")

    observe("contradictory_assumptions_fail_instead_of_passing_vacuously", contradictory_assumptions)
    return results


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New receipt; never overwritten")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("receipt already exists")
    observations = controls()
    receipt = {
        "schema_version": 1,
        "evidence_class": "independent-property-oracle-contract-controls",
        "passed": all(row["passed"] for row in observations),
        "controls": observations,
        "python_version": sys.version,
        "hypothesis_version": hypothesis.__version__,
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "settings": {"max_examples": 200, "derandomize": True, "database": None, "deadline": None},
        "skill_text_used_to_define_expected_answers": False,
        "mutation_tool_campaign_executed": False,
        "agent_efficacy_scored": False,
        "scope": "Independent fixture specifications expose oracle weaknesses; finite examples do not prove correctness or an efficacy gain",
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))
    return int(not receipt["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
