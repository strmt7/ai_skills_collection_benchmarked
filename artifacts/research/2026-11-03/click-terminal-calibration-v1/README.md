# Click terminal calibration

These are local controls for the public Click development task, not agent
trials. Both runs verified the same 142-file source tree and used a real POSIX
pseudo-terminal. They typed three characters, deleted them with backspace, and
checked the visible prompt and returned value for `prompt` and `confirm`.

| Local runtime | Upstream patch | Workaround removed | Entire prompt passed to input |
| --- | --- | --- | --- |
| CPython 3.12.3, GNU readline | Both terminal cases pass | Both fail | Both pass |
| CPython 3.14.10, libedit | Both terminal cases fail | Both fail | Both pass |

Each variant also passed all 16 existing simulated cases. The upstream patch
therefore is not a universal terminal reference. The entire-input variant is a
positive control only for these terminal cases; output routing, colors, hidden
input and other Click contracts need separate tests before treating it as a
repair. The results do not cover every terminal, operating system or readline
build and do not show how any model performs.

Each directory retains the runtime identity, input hashes, simulated-test
output and machine-readable observations. Terminal files use a lossless
Base64 transport (`.terminal.b64`); each decoded byte stream is checked
against the recorded native trace hash. CI retains the original terminal files
in its workflow artifact. Source inputs and
commands are documented in the [task guide](../../../../benchmarks/agent-effectiveness/development/click-prompt-suffix-v1/README.md).
The upstream issue describes the [suffix regression](https://github.com/pallets/click/issues/3019)
and its underlying [readline backspace behavior](https://github.com/pallets/click/issues/665).
