---
name: flowio-fcs-basics
description: Write a small FCS dataset correctly and read its raw event values with FlowIO.
license: BSD-3-Clause
---

# FlowIO: selected FCS read and write operations

Apply Caveman for every task, CocoIndex Code before broad repository navigation,
and Crawl4AI for web-page research. Follow `docs/agent-tools.md` in the
repository root and retain the required execution evidence.

This overlay covers selected examples from the [locked FlowIO skill](provenance/original.SKILL.md)
and its [API reference](provenance/original.api_reference.md). It was tested
with FlowIO 1.4.0 on the recorded Windows and Linux environments. It is not a
complete FCS conformance, biological or clinical validation, or an agent
performance result. The source skill declares BSD-3-Clause; the K-Dense root
notice and the FlowIO package notice are retained separately. Verify applicable
rights for your use.

## Write a new FCS file

Supply a two-dimensional `input_events` array, a nonempty list of
`channel_names`, and either a matching list of `display_names` or `None`.
`output_path` must not already exist. This example accepts finite, nonempty
values representable as float32; it does not preserve higher precision.

```python
import numpy as np
from flowio import create_fcs

values = np.asarray(input_events, dtype=np.float64)
if (
    values.ndim != 2
    or values.shape[0] == 0
    or not channel_names
    or values.shape[1] != len(channel_names)
    or any(not isinstance(name, str) or not name for name in channel_names)
    or (display_names is not None and len(display_names) != len(channel_names))
):
    raise ValueError("Expected nonempty events and matching channel names")
if not np.isfinite(values).all() or np.any(np.abs(values) > np.finfo(np.float32).max):
    raise ValueError("Events must be finite and representable as float32")

with open(output_path, "xb") as file_handle:
    create_fcs(
        file_handle,
        values.astype(np.float32).ravel(order="C").tolist(),
        channel_names,
        opt_channel_names=display_names,
        metadata_dict={"src": "generated example"},
    )
```

FlowIO writes FCS 3.1 float data. A write error can leave a partial new file;
validate the output before use. Do not assume that this example preserves an
existing experiment's metadata, transformations, compensation or semantics.

## Read raw values explicitly

```python
from flowio import FlowData

flow = FlowData(str(input_path))
raw_events = flow.as_array(preprocess=False)
source = flow.text.get("src")
```

In this tested version, TEXT keys are normalized to lowercase without the
leading `$`. `as_array()` defaults to preprocessing; choose raw or preprocessed
values deliberately. In the tested non-unit gain case, preprocessing divides
by the channel gain. Null-channel labels affect channel classification; they
do not remove columns from the event array. Validate channel identity, units,
metadata, calibration and any downstream analysis against the data producer's
requirements.
