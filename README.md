# ics_vgwActor - ICS Actor for the Subaru Gen2 VGW

## Overview

The `ics_vgwActor` is a component of the Instrument Control System (ICS) for the Subaru Prime Focus Spectrograph (PFS).
It bridges the PFS auto-guider to Subaru's Gen2 observation control system: it watches the `ag` and `agcc`
actors for new auto-guider frames, rewrites each frame with celestial WCS and guide-star tables, and hands the result to
Subaru's **datasink** service for transfer to the Gen2 VGW (Vision Guide Window) display.

The actor is passive — it publishes no science keywords and issues no commands to other actors. It is driven entirely by
MHS keyword callbacks.

## Architecture

```
agcc  --[agc_fitsfile]--> Agcc.receiveStatusKeys ─┐
                                                  ├─> Vgw.sendImage(filepath, ...)
ag    --[data]----------> Ag.receiveStatusKeys ───┘        |
                                                           ├─ export()      # rewrite FITS: WCS + object tables
                                                           └─ DataSink      # submit transfer job to Gen2
```

Two paths reach the same sink:

- **`agcc` / `agc_fitsfile`** — every raw AGC exposure, forwarded as-is with a `_` filename prefix and no WCS.
- **`ag` / `data`** — a completed field-acquisition result. Carries field center (RA, Dec, INST-PA) plus paths to three
  `.npy` object tables, so the exported frame gets full WCS and the guide/detected/identified tables.

### Modules

- **`main.py`** — `VgwActor(Actor)` entry point. On first connection it constructs the models and registers the two
  keyword callbacks.
- **`models/ag.py`** — `Ag`; callback for the `ag` actor's `data` key. Loads the `.npy` object tables and pairs them
  with the current `agcc` filepath. Also exposes `guideReady` / `detectionState`.
- **`models/agcc.py`** — `Agcc`; callback for the `agcc` actor's `agc_fitsfile` key. Also exposes `filepath`,
  `frameId`, `dataTime`.
- **`vgw.py`** — `Vgw.sendImage()`; writes the exported FITS into the local `datadir`, then submits a transfer job
  naming the corresponding path under the sink's `datadir`. Submission failures are logged as warnings and do not raise.
- **`export.py`** — rewrites a combined AGC FITS file: sets `RA2000`/`DEC2000`/`RA`/`DEC`/`EQUINOX`/`INST-PA` on the
  primary header, attaches per-camera SIP WCS to the `CAM1`–`CAM6` extensions (rice-compressed), and appends
  `guide_objects`, `detected_objects`, and `identified_objects` binary tables.
- **`pfswcs.py`** — `agcwcs_sip()`; builds the six AGC camera WCS objects (TAN-SIP) from field center and instrument PA,
  using the fitted distortion coefficients.
- **`data_sink.py`** — `DataSink`; thin wrapper over `datasink.client.JobSource`. `connect()` is a context manager that
  connects and always shuts down; `submit()` posts an `scp` transfer job.
- **`Commands/VgwCmd.py`** — MHS command handler.

`export.py`, `pfswcs.py`, and `data_sink.py` each have an `if __name__ == "__main__"` block for standalone use;
see [Standalone tools](#standalone-tools).

## Prerequisites

| Dependency       | Notes                                                        |
|------------------|--------------------------------------------------------------|
| Python 3.12+     | As declared by `requires-python` in `pyproject.toml`         |
| `tron_actorcore` | MHS actor framework (`actorcore`, `opscore`)                 |
| `ics_actorkeys`  | EUPS package — MHS key definitions                           |
| `pfs_instdata`   | EUPS package — supplies `config/actors/vgw.yaml`             |
| `pfs_utils`      | EUPS package — PFS utilities                                 |
| `ics_agActor`    | Provides `agActor` (used by the `export.py` standalone tool) |
| `datasink`       | Git submodule, `python/datasink` — NAOJ transfer client      |
| `g2cam`          | Git submodule, `python/g2cam` — NAOJ Gen2 camera interface   |

The two NAOJ submodules are vendored, not pip-installed. Clone with them:

```bash
git clone --recurse-submodules https://github.com/Subaru-PFS/ics_vgwActor.git
# or, in an existing checkout:
git submodule update --init --recursive
```

`ups/ics_vgwActor.table` puts `python/`, `python/datasink`, and `python/g2cam` on `PYTHONPATH`, so under EUPS the
submodules are importable without installation. Outside EUPS you must add them yourself.

### Environment variables

| Variable            | Used for                                              |
|---------------------|-------------------------------------------------------|
| `ICS_MHS_DATA_ROOT` | Root of the local and remote `vgw` data directories   |
| `ICS_MHS_LOGS_ROOT` | Actor log directory                                   |
| `ICS_VGWACTOR_DIR`  | Set by EUPS; used to resolve the datasink config path |

## Configuration

Runtime configuration is read from `pfs_instdata/config/actors/vgw.yaml` via `actor.actorConfig`. The keys
`vgw.py` requires are:

```yaml
datadir: $ICS_MHS_DATA_ROOT/vgw     # where the exported FITS is written locally
data_sink:
  confpath: $ICS_VGWACTOR_DIR/etc/pfsag_sum.yml   # datasink realm/credentials file
  hostname: ...                                   # transfer destination host
  username: ...                                   # transfer account
  topic: pfs_ag                                   # datasink topic
  datadir: $ICS_MHS_DATA_ROOT/vgw                 # path as seen by the sink
```

Environment variables in `datadir` and `confpath` are expanded with `os.path.expandvars`.

`etc/` holds the datasink realm configs consumed via `confpath` — `pfsag_sum.yml` (summit) and `pfsag.yml`
(simulator) — plus `etc/vgw.cfg`, the legacy pre-`actorConfig` tron/logging config.

> **Note:** the files under `etc/` contain plaintext datasink credentials and are committed to the repository.
> Treat the checkout accordingly, and consider rotating those secrets and moving them out of version control.

## MHS Interface

### Keys consumed

| Actor  | Key            | Description                                                                              |
|--------|----------------|------------------------------------------------------------------------------------------|
| `agcc` | `agc_fitsfile` | A new AGC exposure was written; carries the FITS filename and timestamp                  |
| `ag`   | `data`         | Field acquisition completed; carries RA, Dec, PA and paths to three `.npy` object tables |

Callbacks act only when the key is both `isCurrent` and `isGenuine`.

### Commands accepted

| Command  | Description                                              |
|----------|----------------------------------------------------------|
| `ping`   | Returns the product name; used as a liveness check       |
| `status` | Reports version and status keywords                      |
| `show`   | Dumps all key-value pairs from the subscribed MHS models |

## Standalone tools

Each can be run directly for debugging, outside the actor, from the `python/vgwActor` directory:

```bash
cd python/vgwActor

# Re-export a frame from OpDB + design, exactly as the actor would
PYTHONPATH=.:../ python export.py --frame-id 143362 --input-file in.fits --output-file out.fits \
    [--design-id ID] [--dsn DSN]

# Print the six AGC camera WCS headers for a field center
python pfswcs.py <ra_hr> <dec_deg> [--inst-pa DEG]

# Submit a file to the datasink, optionally on a repeating cadence
python data_sink.py --data-path FILE [--conf-path pfsag.yml] [--cadence SEC]
```

## Development

```bash
# Lint
ruff check python/

# Format
ruff format python/

# Tests (no test suite yet — see below)
pytest
```

There is currently **no `tests/` directory**. `pyproject.toml` already carries the pytest and coverage configuration for
one (`testpaths = ["tests"]`, `--cov=vgwActor`), so tests can be added without further setup; until then `pytest`
collects nothing.

### Code style

- **camelCase is intentional** — ruff rules `N802/N803/N806/N815/N816` are suppressed. Names like `sendImage`,
  `receiveStatusKeys`, and `frameId` follow Subaru / PFS conventions.
- Line length: **110**. Ruff rule sets: `E`, `W`, `F`, `I`, `N`, `D`, `UP`, `B`, `C4`, `SIM`, `RUF`.
- Docstrings follow the numpy convention.
- The vendored `python/datasink` and `python/g2cam` submodules are excluded from ruff and pytest.

### Versioning

The version is managed by [`lsst-versions`](https://pypi.org/project/lsst-versions/) and written to
`python/vgwActor/version.py` at build time, configured under `[tool.lsst_versions]` in `pyproject.toml`.

## License

This project is part of the Subaru Prime Focus Spectrograph (PFS) project and is subject to the licensing terms of the
PFS collaboration.

## See Also

- [`ics_agActor`](https://github.com/Subaru-PFS/ics_agActor) — auto-guider actor; source of the `data` key
- [`ics_agccActor`](https://github.com/Subaru-PFS/ics_agccActor) — AG camera control; source of `agc_fitsfile`
- Subaru PFS project: https://pfs.ipmu.jp/
