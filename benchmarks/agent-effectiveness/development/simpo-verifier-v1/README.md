# SimPO verifier development controls

The [task brief](TASK.md) and its original 17 controls are public development
material. They are not a holdout, a qualified grading sandbox, or an agent
benchmark result.

Four additional controls cover the task's explicitly required
`numpy.allclose(reference, output, rtol=1e-5, atol=1e-6)` argument order for
both the initial and regenerated arrays. They use finite boundary values for
which reversing the arguments changes the result. NumPy documents that
[`allclose` is not symmetric](https://numpy.org/doc/stable/reference/generated/numpy.allclose.html)
and scales relative tolerance against its second argument. These controls
enforce this task's stated contract; that ordering is not a general
recommendation for other comparisons.

Three deliberately incorrect references reverse the initial, regenerated, or
both comparisons. Each passes the original 17 controls but fails the relevant
additional cases. The two differently expressed correct references pass all
four. [Windows and Linux calibration records](../../../../artifacts/research/2026-11-02/simpo-tolerance-direction-v1/qualification.json)
bind the observations to the inputs and preserve the original evidence.

Install the locked platform requirements as described in [the task brief](TASK.md),
then run this with Python 3.13.18 in that environment and a new output directory:

```sh
python benchmarks/agent-effectiveness/development/simpo-verifier-v1/controls/calibrate_tolerance_direction.py --output /path/to/new/output
```

The process executes only checked-in reference code and synthetic mutations on
the host. It must not grade agent submissions. No model is invoked or scored.
