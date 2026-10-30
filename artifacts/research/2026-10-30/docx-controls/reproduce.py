"""Reproduce scoped docx-js page layout and module-resolution observations."""

import json
import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

VERSION = "9.15.0"
LAYOUT = r"""
const fs = require("node:fs");
const {Document, Packer, Paragraph, PageOrientation} = require("docx");
(async () => {
  const pages = {
    default: {},
    letter: {size: {width: 12240, height: 15840}},
    landscape: {size: {width: 12240, height: 15840, orientation: PageOrientation.LANDSCAPE}},
  };
  for (const [name, page] of Object.entries(pages)) {
    const doc = new Document({sections: [{properties: {page}, children: [new Paragraph("Example")]}]});
    fs.writeFileSync(name + ".docx", await Packer.toBuffer(doc));
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
"""
GLOBAL_CONTROL = r"""
const path = require("node:path");
const globalModules = process.platform === "win32" ? "../prefix/node_modules/docx" : "../prefix/lib/node_modules/docx";
const direct = require(path.resolve(__dirname, globalModules));
let result;
try { require("docx"); result = "loaded"; }
catch (error) { result = error.code; }
console.log(JSON.stringify({explicit_loaded: typeof direct.Document === "function", package_result: result}));
"""
LOCAL_CONTROL = r"""
const {Document} = require("docx");
console.log(JSON.stringify({local_loaded: typeof Document === "function"}));
"""
MISSING_FS_CONTROL = r"""
const {Document, Packer} = require("docx");
const doc = new Document({sections: [{children: []}]});
Packer.toBuffer(doc).then((buffer) => fs.writeFileSync("doc.docx", buffer));
"""


def run(command, cwd, env):
    return subprocess.run(
        command, cwd=cwd, env=env, check=True, capture_output=True, text=True, timeout=120
    ).stdout.strip()


def main():
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    node = shutil.which("node")
    if not npm or not node:
        raise RuntimeError("Node.js and npm are required")
    with tempfile.TemporaryDirectory(prefix="docx-research-") as directory:
        root = Path(directory)
        consumer = root / "consumer"
        prefix = root / "prefix"
        consumer.mkdir()
        env = os.environ.copy()
        env.pop("NODE_PATH", None)
        env["npm_config_cache"] = str(root / "npm-cache")
        flags = ["--ignore-scripts", "--no-audit", "--no-fund"]
        run([npm, "install", "--global", "--prefix", str(prefix), *flags, "docx@" + VERSION], root, env)
        (consumer / "global.cjs").write_text(GLOBAL_CONTROL, encoding="utf-8")
        global_result = json.loads(run([node, "global.cjs"], consumer, env))
        if global_result != {"explicit_loaded": True, "package_result": "MODULE_NOT_FOUND"}:
            raise RuntimeError(f"unexpected global resolution: {global_result}")
        run([npm, "install", "--no-save", "--no-package-lock", *flags, "docx@" + VERSION], consumer, env)
        (consumer / "local.cjs").write_text(LOCAL_CONTROL, encoding="utf-8")
        local_result = json.loads(run([node, "local.cjs"], consumer, env))
        if local_result != {"local_loaded": True}:
            raise RuntimeError(f"unexpected local resolution: {local_result}")
        (consumer / "missing-fs.cjs").write_text(MISSING_FS_CONTROL, encoding="utf-8")
        missing_fs = subprocess.run(
            [node, "missing-fs.cjs"], cwd=consumer, env=env, capture_output=True, text=True, timeout=120
        )
        if missing_fs.returncode == 0 or "ReferenceError: fs is not defined" not in missing_fs.stderr:
            raise RuntimeError("missing fs import control did not fail as expected")
        (consumer / "layout.cjs").write_text(LAYOUT, encoding="utf-8")
        run([node, "layout.cjs"], consumer, env)
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        layouts = {}
        for name in ("default", "letter", "landscape"):
            with zipfile.ZipFile(consumer / (name + ".docx")) as archive:
                element = ET.fromstring(archive.read("word/document.xml")).find(".//" + ns + "pgSz")
            if element is None:
                raise ValueError(f"missing page size: {name}")
            layouts[name] = {key.removeprefix(ns): value for key, value in element.attrib.items()}
        expected = {
            "default": {"w": "11906", "h": "16838", "orient": "portrait"},
            "letter": {"w": "12240", "h": "15840", "orient": "portrait"},
            "landscape": {"w": "15840", "h": "12240", "orient": "landscape"},
        }
        if layouts != expected:
            raise RuntimeError(f"unexpected page sizes: {layouts}")
        package = json.loads((consumer / "node_modules/docx/package.json").read_text(encoding="utf-8"))
        if package["version"] != VERSION:
            raise RuntimeError("installed docx version does not match requested version")
        print(
            json.dumps(
                {
                    "node": run([node, "--version"], root, env),
                    "npm": run([npm, "--version"], root, env),
                    "docx": package["version"],
                    "global_resolution": global_result,
                    "local_resolution": local_result,
                    "missing_fs_reference_error": True,
                    "page_sizes": layouts,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
