# Click prompt output-routing calibration

These records qualify development controls against trusted source variants;
they are not agent trials. Both runs verified the same 142-file Click source
tree. Four additional cases check stdout or stderr routing of the question
text for `prompt` and `confirm`, as well as their returned answers.

| Variant | Original 16 simulated cases | Four routing cases |
| --- | --- | --- |
| Upstream patch | All pass | All pass |
| Readline workaround removed | All pass | All pass |
| Entire prompt passed to input | All pass | Both stderr cases fail |
| `err` ignored | All pass | Both stderr cases fail |

The Windows and Linux observations agree on these cases. Together with the
[terminal calibration](../click-terminal-calibration-v1/), they show why
neither the original simulated tests nor the terminal control alone proves a
complete repair. The entire-input variant is not a recommended fix. No result
establishes an agent advantage or substitutes for a confined grader.

Each `result.json` binds the source snapshot, runtime and control inputs using
portable slash-separated paths. `outputs.json` stores the exact stdout and
stderr bytes in Base64; tests decode them, verify their recorded hashes and
check each expected case outcome. The control executes the same test bytes
with portable traceback filenames, so failure output retains its case, line
and assertion without embedding a local checkout path. CI also retains the
raw output files. The API contract for `err` is documented in the
[Click prompt reference](https://click.palletsprojects.com/en/stable/api/#click.prompt).
The [first calibration](../click-routing-calibration-v1/) remains available
with its original observations and its Windows path-serialization limitation.
