# Preserve prompt suffixes

At the source revision in `source.json`, `click.prompt` and `click.confirm`
append an unwanted space when `prompt_suffix` is empty. Other suffixes can
also be changed: a suffix ending without a space gains one, while multiple
trailing spaces collapse to one. Correct both functions so the displayed
prompt preserves the supplied suffix exactly. Preserve normal input handling,
defaults, retries, and the requested stdout or stderr prompt routing. The
existing workaround for readline behavior must keep working; simply reverting
that workaround is not sufficient.

Work from the complete pinned Click source tree. Add appropriate regression
tests and run the relevant checks. The issue and task are public development
material. The acceptance controls and reference patch must not be provided to
an agent under evaluation. They were visible during development and are not an
untouched holdout. This task has not been used in an agent trial.

The task comes from the [public issue](https://github.com/pallets/click/issues/3019)
and Click's documented prompt APIs, independently of any skill instructions.
Calibration controls execute trusted examples directly on the host; they must
not be used to grade an agent's submission. See the repository's
[trial protocol](../../../../docs/agent-trial-protocol.md) for that requirement.
