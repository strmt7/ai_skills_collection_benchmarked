# FlowIO FCS compatibility

The locked FlowIO skill and its bundled API reference were read in full. The
checks below cover selected behavior in FlowIO 1.4.0; many other FCS variants,
metadata fields and library paths have not been runtime-tested. This is not a
biological or clinical validation and does not measure agent performance.

The locked writer examples pass a path and a two-dimensional array directly to
`create_fcs`, and some use `metadata=`. In the tested release those examples
fail: the [FlowIO API](https://flowio.readthedocs.io/en/latest/api.html)
requires an open binary file handle, flattened event values and the
`metadata_dict` parameter. The [maintained overlay](../included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/flowio-fcs-basics/SKILL.md)
shows a bounded, validated example.

For the tested file, TEXT keys were lowercase without the leading `$`, and
`null_channel_list` changed classification rather than removing event-array
columns. With a non-unit gain of 2, the tested preprocessed values were half
the raw values; the locked documents instead say to multiply. Do not
extrapolate this one gain control to every FCS transformation. Choose raw or
preprocessed values intentionally and validate the data producer's metadata.

The component controls include independently decoded float32 output bytes and
a pinned [FlowIO tutorial](https://flowio.readthedocs.io/en/stable/notebooks/flowio_tutorial.html)
FCS 2.0 example. Its reported event count, channels and first raw values were
checked against the published tutorial and an independent byte-level read.
The upstream example is fetched by immutable commit and digest for the control;
it is not stored in this repository, and its separate data-use terms were not
independently established. The controls do not prove broad interoperability,
all FCS versions, metadata preservation, compensation or downstream analysis.
