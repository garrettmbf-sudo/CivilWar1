# Local serialization round-trip sample

The user supplied `test_roundtrip.sav` (19,284 bytes; SHA-256 `64d660f0f509585a750e3f3e20a00180a2e8d2df3163824a1015e48f60ac5f2a`) together with four PowerShell map utilities.

**Status:** Experimental save-data artifact, not proof of a playable Shenandoah map. It is intended for inspection and controlled read/write tests. Do not load BinaryFormatter content from untrusted sources.

Keep the original input unchanged. Verify that the file can be loaded and saved in the exact installed Hex of Steel version before claiming a working game round trip.

If the binary sample is not included alongside this README in the branch, the local user-supplied file must be uploaded unchanged; do not replace it with synthetic bytes.
