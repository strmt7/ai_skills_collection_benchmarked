---
name: zarr-python-basics
description: Create, resize, and inspect a small Zarr v3 array using the tested Python API.
license: MIT
---

# Zarr Python: selected array operations

Apply Caveman for every task, CocoIndex Code before broad repository navigation,
and Crawl4AI for web-page research. Follow `docs/agent-tools.md` in the repository
root and retain the required execution evidence.

This overlay addresses selected examples from the [locked upstream skill](provenance/original.SKILL.md).
It was checked with Zarr Python 3.4.2 and NumPy 2.5.4 on the recorded Windows and
Linux environments. The Zarr Python package version and the array format version
are distinct: this example explicitly requests format 3. Python 3.12 or later is
required by the tested Zarr package version; check the selected release's own
requirements when using another version.

## Create, resize, and inspect

```python
import numpy as np
import zarr
from zarr.codecs import BloscCodec
from zarr.storage import MemoryStore

array = zarr.create_array(
    store=MemoryStore(),
    shape=(2, 2),
    chunks=(2, 2),
    dtype="int32",
    zarr_format=3,
    compressors=[BloscCodec(cname="zstd", clevel=5, shuffle="shuffle")],
)
array[:] = np.array([[1, 2], [3, 4]], dtype="int32")
array.resize((3, 2))
values = array[:]
stored_bytes = array.nbytes_stored()
```

`MemoryStore` is ephemeral. Choose a persistent store and its lifecycle according
to the application. Resize takes a shape tuple; call `nbytes_stored()` to obtain
the stored size. `compressors` specifies compression, while serialization is a
separate setting. Check the version's API before configuring either. In the
tested version, `chunks=None` can still produce multiple chunks; inspect the
resulting chunk shape. The locked reference's `array.copy()` and
`array.info_items()` examples are unavailable in this version.

For separate processes, the Zarr documentation requires writes to different
chunks and a storage backend supporting atomic writes for concurrent operation;
coordinate writers that can affect the same chunk. Validate the actual storage
and write pattern, including sharded layouts, before relying on concurrency.
The old `ThreadSynchronizer` and `ProcessSynchronizer` examples are not supported
by the tested Zarr Python 3 API. Cloud stores, sharding, concurrency, other codecs,
and agent performance were not tested by this overlay's component control.
