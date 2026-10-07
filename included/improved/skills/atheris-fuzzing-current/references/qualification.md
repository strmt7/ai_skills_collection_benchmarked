# Qualified scope

Eight actual source/engine controls use unchanged Atheris 3.1.0 on Linux/Python
3.14.8, with current urllib3 2.8.0. They cover version/preload-path verification,
lossy decoding, body-only HTTP behavior, hidden unexpected exceptions, empty
provider defaults, 64 bounded instrumented callbacks and known-seed replay.

The complete official wheel is installed unchanged in an offline image. The
execution backend checks its exact immutable image ID and original constraints.
The engine's raw sanitizer-helper warnings are retained. No native target,
sanitizer initialization, compiler compatibility, leak campaign, macOS/ARM,
coverage.py export or coding-agent efficacy is qualified by these controls.

Sources: [Atheris 3.1.0](https://pypi.org/project/atheris/3.1.0/),
[pinned README](https://github.com/google/atheris/tree/e36da74cf42b5834c4e31d7cabb58d796695d29f),
[native guide](https://github.com/google/atheris/blob/e36da74cf42b5834c4e31d7cabb58d796695d29f/native_extension_fuzzing.md).
