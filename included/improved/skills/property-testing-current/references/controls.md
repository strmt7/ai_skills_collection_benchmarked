# Qualified controls

`benchmarks/dependency-regressions/property_oracle_controls.py` contains trusted
independent fixtures under Python 3.14.8 / Hypothesis 6.168.3. The current
`property-oracle-runtime-controls-v2.json` receipt records eight actual controls:

- An independent addition expression rejects a subtraction mutant.
- A shifted encoder and inverse decoder pass 401 roundtrips but violate an
  independently specified signed 64-bit big-endian zero vector.
- A constant normalizer passes idempotence and violates content preservation.
- Set equality and length accept changed duplicate counts; a multiset rejects it.
- Default regex generation can violate a full-match domain; `fullmatch=True`
  generates a full-match fixture.
- `sets` and `frozensets` produce different collection types.
- A fixed seed retains the configured seven-example budget.
- Contradictory assumptions fail with `FailedHealthCheck`, with zero successful
  examples and no health-check suppression.

These fixtures expose oracle and strategy contracts. They are not a Mewt
campaign, skill runtime benchmark score, proof for an unbounded domain, or an
independent coding-agent comparison. Earlier seven-control evidence is retained.

Official current documentation:
[Hypothesis strategies](https://hypothesis.readthedocs.io/en/latest/reference/strategies.html),
[settings and replay](https://hypothesis.readthedocs.io/en/latest/settings.html),
[stateful model testing](https://hypothesis.readthedocs.io/en/latest/stateful.html),
and [flaky failures](https://hypothesis.readthedocs.io/en/latest/tutorial/flaky.html).
