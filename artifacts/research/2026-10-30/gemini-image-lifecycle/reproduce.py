"""Compare two image skills with captured Google and OpenRouter model information."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path

MODEL = "gemini-3.1-flash-image-preview"
ROUTER_ID = "google/" + MODEL
FILES = {
    "google_skill": (
        "included/skills/by-category/devops-cloud-operations/creative-reference/gemini-image-generation/SKILL.md",
        "144acf2589583ce21f2fbbd995e449969493aa7ef04ef9b67e5b0608c83ee933",
    ),
    "router_skill": (
        "included/skills/by-category/science-research-data-analysis/latest-release-community/generate-image/SKILL.md",
        "2ab48426472f215696898828346e9b9572bf3055c3cb1304b0136556695ac45f",
    ),
    "router_script": (
        "included/skills/by-category/science-research-data-analysis/latest-release-community/generate-image/scripts/generate_image.py",
        "c449361bfedba91b81164b9bfb6d0216c7d449175980c57c6b9db6d28a834461",
    ),
}
CAPTURES = {
    "google": "2868e0b1715a54e2d8937777a274bf2deef835995dea62e8ae10149c7f9287b4",
    "openrouter": "e41ae4995b9dcd75f5ad66f3876986f9cacd5af79ae406c3152428f28e07ec74",
}


def read(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Unexpected source bytes: {path.name}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--google-native", type=Path, required=True)
    parser.add_argument("--openrouter-api", type=Path, required=True)
    parser.add_argument("--current-script", type=Path, required=True)
    args = parser.parse_args()
    files = {name: read(args.root / path, digest).decode("utf-8") for name, (path, digest) in FILES.items()}
    google = json.loads(read(args.google_native, CAPTURES["google"]))
    router = json.loads(read(args.openrouter_api, CAPTURES["openrouter"]))
    if (
        google["url"] != "https://ai.google.dev/gemini-api/docs/deprecations"
        or google["status_code"] != 200
        or google["success"] is not True
    ):
        raise ValueError("Unexpected Google source scope or status")
    legend = "Already-shutdown models are indicated with gray backgrounds."
    if legend not in google["markdown"]["raw_markdown"]:
        raise ValueError("Google lifecycle legend missing")
    pattern = r'<tr class="row-gray">\s*<td><code>gemini-3\.1-flash-image-preview</code></td>(.*?)</tr>'
    rows = re.findall(pattern, google["cleaned_html"], re.DOTALL)
    if len(rows) != 1 or "June 25, 2026" not in rows[0]:
        raise ValueError("Expected Google model lifecycle row missing")
    matches = [item for item in router["data"] if item.get("id") == ROUTER_ID]
    if len(matches) != 1:
        raise ValueError("Expected one OpenRouter catalog entry")
    current = read(args.current_script, "977b40ddc398a6e62f13e61482237363251b5d4b17b9997e947e2ef87fb12a6a")
    current_tree = ast.parse(current.decode("utf-8"))
    assignments = [
        ast.literal_eval(node.value)
        for node in current_tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "DEFAULT_MODEL" for target in node.targets)
    ]
    if assignments != ["google/gemini-3.1-flash-image"]:
        raise ValueError("Unexpected current upstream model default")
    current_matches = [item for item in router["data"] if item.get("id") == assignments[0]]
    if len(current_matches) != 1:
        raise ValueError("Expected one current-model catalog entry")
    tree = ast.parse(files["router_script"])
    functions = [
        n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "generate_image"
    ]
    if len(functions) != 1:
        raise ValueError("Image generation function not found")
    fn = functions[0]
    defaults = dict(zip([arg.arg for arg in fn.args.args][-len(fn.args.defaults) :], fn.args.defaults, strict=True))
    function_default = ast.literal_eval(defaults["model"])
    cli_defaults = [
        ast.literal_eval(k.value)
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "add_argument"
        and any(isinstance(a, ast.Constant) and a.value == "--model" for a in n.args)
        for k in n.keywords
        if k.arg == "default"
    ]
    if (
        f'"GEMINI_MODEL_ID": "{MODEL}"' not in files["google_skill"]
        or ROUTER_ID not in files["router_skill"]
        or function_default != ROUTER_ID
        or cli_defaults != [ROUTER_ID]
    ):
        raise ValueError("Expected source model configuration changed")
    out = {
        "google_skill_example": MODEL,
        "google_marks_already_shutdown": True,
        "google_table_date": "June 25, 2026",
        "openrouter_skill_default": function_default,
        "openrouter_cli_default": cli_defaults[0],
        "openrouter_catalog_matches": len(matches),
        "openrouter_listed_name": matches[0].get("name"),
        "current_upstream_default": assignments[0],
        "current_default_catalog_matches": len(current_matches),
        "api_generation_attempted": False,
        "catalog_listing_proves_runtime_availability": False,
        "agent_scored": False,
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
