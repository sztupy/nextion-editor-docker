# Browser workbench

An optional image running Nextion Editor **1.68.2** on the existing Wine/AutoHotkey
base. Edit HMI files and use the Editor's Debug simulator through noVNC, or compile
TFT files in isolated containers with a standard-library Python CLI.

This adds a separate image and entry point. The existing `nextion-editor`,
`nextion-scripts`, and Home Assistant add-on remain independent.

## Requirements

- Python 3.9+ on a Linux or macOS client; the CLI uses POSIX file locks.
- Docker with a working Linux amd64 environment. Remote Docker over SSH is supported.
- Docker Compose v2, if using `compose.yaml`.
- Enough Docker storage for the approximately 3.64 GB runtime image and larger
  intermediate layers during builds. The CLI limits containers to 1.5 CPUs and 3 GiB RAM.

Nextion Editor and the other bundled programs keep their own licenses. The build
downloads the official Editor archive and checks its SHA-256. No Editor archive,
HMI project, or generated TFT is checked into this contribution.

## Build and open the Editor

Run from the repository root:

```sh
python3 workbench/nextion.py doctor
python3 workbench/nextion.py build-image
python3 workbench/nextion.py editor /absolute/path/project.hmi
```

Open <http://127.0.0.1:6080> and wait for **Ready to edit**. The browser displays the
actual 1024×768 Editor desktop, scaled to fit the available space. The page uses
English or Korean according to the browser language; `?lang=en` and `?lang=ko`
override that choice.

- Use Save or Ctrl+S in the Editor, then **Download HMI** for the saved project.
- Use File → TFT file output to generate a TFT, then **Download TFT**.
- Use Debug to open the simulator. The HMI needs suitable embedded font resources
  to display non-Latin text on the simulated panel.
- Enter Unicode text in the browser's clipboard field, click **Copy to clipboard**,
  then press Ctrl+V in the Editor. The field is limited to 4,096 characters.

```sh
python3 workbench/nextion.py stop
```

Save in the Editor before stopping. Closing the browser leaves the session running.
The CLI keeps a named volume derived from the Editor version and original HMI hash;
opening the same input again restores the saved workspace. The original input is
copied into the container and is not overwritten. Download a backup before changing
workspaces or upgrading Editor versions.

The web interface has no authentication and is published on **127.0.0.1 only**.
Use an SSH tunnel for remote access. Physical serial/USB flashing is outside the
workbench's scope.

### Compose

After building the image:

```sh
mkdir -p workspace/input
cp /absolute/path/project.hmi workspace/input/project.hmi
docker compose up -d
docker compose logs -f editor
docker compose down
```

Compose uses `./workspace`, rather than the CLI's named volume. Once a saved
workspace exists, it takes precedence over `workspace/input/project.hmi`.
`NEXTION_PORT` changes the localhost port; `NEXTION_IMAGE` selects another image.

### Remote Linux Docker

With an SSH host alias named `docker-host`:

```sh
python3 workbench/nextion.py --host ssh://docker-host build-image
python3 workbench/nextion.py --host ssh://docker-host editor /absolute/path/project.hmi
ssh -N -L 6080:127.0.0.1:6080 docker-host
```

Open <http://127.0.0.1:6080> locally. Input files are copied through Docker, so the
remote machine does not need the client's filesystem paths. Pass the same `--host`
when compiling or stopping the Editor. `--name` and `--port` select a separate
interactive session.

### Apple Silicon

Using `--platform linux/amd64` with an ARM Docker daemon was insufficient to run
this 32-bit Wine prefix in the tested environment. A dedicated x86_64 QEMU Colima
VM passed both browser interaction and unattended compilation:

```sh
brew install colima qemu lima-additional-guestagents
colima start nextion-x86 --arch x86_64 --vm-type qemu --cpu 2 --memory 4 --disk 15 --activate=false --ssh-config=false --mount none
NEXTION_DOCKER_HOST="unix://$HOME/.colima/nextion-x86/docker.sock"

# Import an image built on the Linux host; check both sides of the pipeline.
set -o pipefail
ssh docker-host 'docker save nextion-workbench:1.68.2-slim | gzip -1' | docker --host "$NEXTION_DOCKER_HOST" load

python3 workbench/nextion.py --host "$NEXTION_DOCKER_HOST" doctor
python3 workbench/nextion.py --host "$NEXTION_DOCKER_HOST" editor /absolute/path/project.hmi --port 6082
python3 workbench/nextion.py --host "$NEXTION_DOCKER_HOST" compile /absolute/path/project.hmi --output artifacts/mac --timeout 600
```

The 15 GiB VM is sized for importing and running an image, not building all its
dependencies. A source build inside the VM needs more disk space. This does not
switch the default Docker context. To stop only this dedicated environment:

```sh
python3 workbench/nextion.py --host "$NEXTION_DOCKER_HOST" stop
colima stop --profile nextion-x86
```

Start it again with `colima start nextion-x86 --activate=false --ssh-config=false`.
Local QEMU compilation was substantially slower than remote Linux in the recorded
measurements; see [validation and measurements](VALIDATION.md).

## Isolated TFT builds

```sh
python3 workbench/nextion.py compile /absolute/path/project.hmi --output artifacts/build --timeout 180
```

Each run uses a fresh, network-disabled container. The original HMI is copied and
hashed. Results are stored under `artifacts/build/runs/<run-id>/`:

| File | Purpose |
| --- | --- |
| `result.json` | Status, image ID, Editor version, input/output SHA-256, warnings, duration and header checks |
| `exports/project.tft` and `exports/project.hmi` | Successful build outputs |
| `logs/compiler.txt`, other logs and `logs/screen.png` | Compiler text and diagnostics |
| `resources.json` | Container resource observations |
| `artifacts/build/latest.json` | Pointer to the latest run, including failures |

The command returns nonzero on errors or timeouts. It requires a successful
compiler summary, exactly one new TFT of the reported size, valid TFT header
checksums, and a matching host-side output hash. Old output is never returned as
a new successful build. Concurrent builds targeting the same output directory are
rejected. Compiler warnings are retained in successful result records.

Header checks were tested with the NSPanel F-series model code `0x1ce47603`.
Other TFT formats require separate validation. The tests did not flash a physical
panel. UI automation still depends on the pinned Editor and 1024×768 desktop.

## Resource choices

- The `slim` target removes unused Wine64 libraries, Firefox, Vim resources, and
  installer caches, while retaining the Linux wineserver, 32-bit Wine, .NET,
  Korean fonts, and Gecko needed by the online update view. `--variant full`
  builds the dependency-preserving alternative.
- Large dependency layers are separated from Python, AHK, and HTML files. Code-only
  changes reuse the flattened dependency layer.
- Interactive sessions disable Wine HID/USB device services because browser input
  uses X11. Batch compilation keeps the default drivers. In Compose or a direct
  `docker run`, set `NEXTION_OPTIMIZE_DEVICES=0` to disable this optimization.
- Resource sampling is off for interactive sessions and on for batch builds.
  `NEXTION_METRICS=1` enables it in an interactive container. The last 1,200 raw
  samples are retained, while whole-run means and peaks remain available.

These environment variables must be passed into the container, not just exported
in the CLI client's shell. For example, add `NEXTION_METRICS: "1"` to the Compose
service's `environment` mapping.

## Tests and benchmarks

The unit tests need only Python:

```sh
python3 -m unittest discover -s workbench/tests -v
```

To exercise real compilation, failures, stale outputs, locking, and recovery with
an HMI you can build:

```sh
python3 workbench/verify-integration.py --input /absolute/path/project.hmi --output artifacts/integration
python3 workbench/benchmark.py --image nextion-workbench:1.68.2-slim --input /absolute/path/project.hmi --output artifacts/compile --mode compile --runs 5
python3 workbench/benchmark.py --image nextion-workbench:1.68.2-slim --input /absolute/path/project.hmi --output artifacts/idle --mode idle --seconds 60
```

Add `--host ssh://docker-host` for remote Docker. CPU 100% means one core. Memory
reports both cgroup usage and working set excluding inactive file cache. Measurements
use cgroup v2 and exclude image download time. `--no-web` provides an Editor-only
comparison. Use a dedicated output directory for the integration test, which
creates an intentionally corrupt input and a stale-output fixture.
