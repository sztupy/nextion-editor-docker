# Validation and measurements

Measured during development on 2026-10-15. These are observations from one Linux
host and one Apple Silicon Mac, not performance guarantees. The baseline below is
an earlier **workbench prototype with the same features and Editor version**, not
the repository's existing published image.

## Functional checks

- Eight Python unit tests passed: compiler errors/warnings, incomplete logs,
  stale/ambiguous output selection, corrupt/truncated TFT rejection, and bounded
  resource history. The history test feeds 10,000 samples and verifies that the
  initial peak survives after old raw samples are discarded.
- Ten integration checks passed: an output lock, a corrupt HMI, a forced deadline,
  no stale export on either failure, diagnostic capture, a subsequent successful
  build, unchanged input, and build-container cleanup.
- A current portrait NSPanel HMI compiled successfully in five Linux runs. A legacy
  NSPanel Blueprint v21.6 project also compiled. Each produced the same TFT hash as
  its pre-optimization reference. Both retained zero errors and 32 warnings.
- Browser mouse/keyboard interaction, Unicode clipboard input, Korean save/reopen,
  simulator text rendering, and HMI/TFT downloads were exercised. Saved HMI content
  survived a container restart and the optimized-image transition.
- Unattended compilation completed in a dedicated x86_64 QEMU Colima VM on Apple
  Silicon. Its TFT was byte-identical to the Linux output. Browser connection and
  page selection also worked. Native ARM Docker was not a working Wine alternative
  in this environment.

No physical panel was flashed. HMI/TFT fixtures, personal workspaces, raw session
logs and screenshots are not included; the supplied integration and benchmark
commands accept an HMI supplied by the reviewer.

After preparing the contribution's English/Korean browser page, the image was
rebuilt using the cached runtime layers. A further Linux build completed in
33.579 seconds with the same TFT hash, and both browser languages, the noVNC
connection and Unicode clipboard contents were checked again. This additional
build is a functional check, separate from the five-run timing comparison below.

## Measurements

| Measurement | Earlier prototype | Optimized runtime |
| --- | ---: | ---: |
| Linux image, Docker uncompressed size | 4,842,492,421 bytes | 3,635,532,461 bytes (24.9% smaller) |
| Linux idle CPU, 100% = one core | 13.455% | 11.153% (17.1% lower) |
| Linux mean idle working set | 419.3 MiB | 382.2 MiB (37.1 MiB lower) |
| Linux compile, median of five runs each | 34.727 s | 34.006 s |
| Mac QEMU compile, one run each | 255.948 s | 256.177 s |
| Resource sample history | Grows with runtime | Last 1,200 raw samples, whole-run summary |

The five optimized Linux compile durations were 34.006, 34.961, 34.110, 33.643 and
33.417 seconds. Small timing differences on a shared host are not treated as a
compiler speedup. The Mac result is a single observation and its practical latency
was unchanged. Linux CPU reductions are not extrapolated to the whole Mac VM.

Conditions:

- Linux: x86_64 Docker host, 4 CPUs, approximately 15.4 GiB RAM; each test container
  limited to 1.5 CPUs and 3 GiB, with 128 MiB shared memory.
- Idle: same portrait HMI, noVNC server enabled, no browser client; five seconds of
  settling after readiness, then 60 seconds of cgroup v2 observations per variant.
- Mac: dedicated x86_64 QEMU VM on Apple Silicon, 2 CPUs and 4 GiB RAM. The VM used
  the imported Linux core with small replacement layers; runtime file hashes were
  checked against the source, while image IDs and final sizes differed.
- Compile times include Editor startup, opening/saving the HMI, UI automation,
  compilation and validation; image download/import time is excluded.
- Image size above describes the measured optimized runtime before the small
  English/Korean web-page update prepared for this contribution.

The comparison HMI SHA-256 was
`f33a71fe6dfb55b8966b6c40bfa236708fac9ee17e3160270e58ae61f6770085`.
Its generated 13,521,100-byte TFT SHA-256 was
`08739f5ec75ae014ad843f9477973d3ebf0e85ec7a971ef6e82666d88b6de096`.

## Decisions retained after experiments

Removing Gecko prevented the Editor's online update view from initializing, so
the slim image retains it. A native-control-only batch automation experiment
timed out under Mac QEMU; the existing UI Automation batch path and default Wine
device drivers were retained. Native control lookup is used only for dismissing
the interactive startup warning. .NET precompilation did not show a useful gain
and is not part of this change.

Reproduce the relevant checks with the commands in [README.md](README.md). For a
before/after comparison, keep the same HMI, host, resource limits and browser
connection state, and record each image ID with the measurements.
