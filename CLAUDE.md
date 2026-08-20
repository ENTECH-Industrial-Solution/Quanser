# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is a development folder for software built on top of Quanser's **currently-sold**
commercial robotics products (QCar2, Qube-Servo2). It is not a research prototype or a
fork of Quanser's own SDK — it's ENTECH's own scripts/models layered on top of official
Quanser hardware and software (QUARC, QLabs, the Quanser Python SDK), aimed at real
customer-facing demos/labs. Treat compatibility with the official Quanser tooling and the
physical robots as a hard constraint, not an implementation detail to refactor away.

QCar2 (and Qube-Servo2) project files for Quanser's ground-vehicle robotics platform:
Simulink models plus Python launch/control scripts for both **physical** QCar2 hardware
(Jetson-based robot, SSH'd into from a host PC) and **virtual** QCar2 in Quanser
Interactive Labs (QLabs). There is no application build/package — this is a collection of
launcher scripts, `.slx` models, and config JSON files driven by `.bat` (Windows) files.

This repo is **not self-contained**. It depends on MATLAB/Simulink + QUARC, on QLabs, and
on the official Quanser Python SDK (`pal`, `hal`, `qvl`, `pit`), none of which are vendored
here. Read `README.md`'s Prerequisites section before assuming any script can run as-is.

## Repo layout

```
QCar2/
  Linux/{Physical, Virtual, Virtual + Physical}/
  Windows/{Physical, Virtual, Virtual + Physical}/
Qube_servo2/        # currently empty
isaac_sim/          # Isaac Sim + ROS2/Nav2 packages for QCar2 and QBot Platform (untracked in git)
```

Each `<OS>/<mode>` folder is a largely self-contained set of scripts for that
platform/mode combination — Windows and Linux copies of the same demo are **not shared
code**, they are parallel, independently-maintained copies (e.g.
`QCar2/Windows/Virtual + Physical/run_physical_lidar_avoidance.py` and
`QCar2/Linux/Physical/run_physical_lidar_avoidance.py` are separate files). When fixing a
bug or changing behavior that conceptually applies to "both OSes" or "both Windows
variants", check whether the same script exists under the sibling folder and whether the
user wants the fix mirrored there — don't assume one edit covers both.

`QCar2/Windows/Virtual + Physical/` is the most actively developed folder and the one with
the most tooling (see below). `QCar2/Windows/Virtual/` and `QCar2/Windows/Physical/` are
narrower, single-purpose script sets (spawn, camera, lidar, controller, environment setup)
each with a matching `.bat` launcher.

## Running things

There's no build/lint/test suite in the conventional sense. What exists:

- **`<mode>/start_qcar2_demo*.bat`** — the standard entry points. Each one stops any
  running QUARC models/clients, opens the matching `.slx` model from the sibling
  `Simulink/` folder, starts peripheral clients, then launches the physical/virtual car
  models via `quarc_run`. `stop_all.bat` tears everything down.
- **Python scripts** are run directly (`python script.py`), often invoked *from* a `.bat`
  file rather than standalone. There's no test runner; the closest thing to a correctness
  check is `python -m py_compile <file>` (syntax-only) since there's no CI here.
- MATLAB-side: `Simulink/connect.m` is used with QUARC to connect to models — this repo
  does not script MATLAB itself.

## Path portability

Scripts resolve paths relative to their own location
(`os.path.dirname(os.path.abspath(__file__))`) rather than assuming a fixed clone path —
this was a deliberate fix (see commit "Make repo portable") so the repo works when cloned
anywhere. Preserve this pattern in new scripts; don't reintroduce absolute paths.

## Quanser SDK resolution

Scripts that need `pal`/`hal`/`qvl`/`pit` (the official Quanser Python SDK, not vendored)
resolve it via:
1. `QUANSER_ACADEMIC_RESOURCES_PATH` env var if set, else
2. a sibling-repo fallback: `../../../../` from the script up to a directory assumed to be
   a clone of `quanser/Quanser_Academic_Resources`, then `0_libraries/python`.

This pattern is duplicated per-script (not factored into a shared module) — follow the
existing inline style when touching these scripts rather than introducing a shared import,
since the codebase intentionally has no shared internal package.

## Physical-QCar2 SSH pattern

Scripts that talk to the physical robot (`ssh_qcar2.py`, `run_physical_lidar_avoidance.py`,
`view_physical_360_vision.py`, etc.) SSH into the Jetson on the car (default credentials
`nvidia`/`nvidia`), `sftp.put` the relevant local script(s) — and, where applicable,
`network_config.json` — to `/home/nvidia/Documents/`, then execute them remotely and stream
stdout/stderr back. A companion script (`view_physical_360_vision.py` pairs with a
`_probe.py` counterpart on the robot side, etc.) is the receiving end that opens an
`ObserverAgent`/`Probe` stream to display camera/LiDAR data sent back from the Jetson.

## Network config (`QCar2/Windows/Virtual + Physical/` only)

`network_config.json` in this folder is the single source of truth for the QCar2's IP
(`qcar_ip`), the traffic-light device IP (`traffic_light_ip`), and the host PC fallback IP
(`host_pc_ip_fallback`). Python scripts in this folder load it directly via `json.load`;
`.bat` scripts pull values into env vars with a `python -c "import json;print(json.load(...))"`
+ `for /f` one-liner near the top of the file, before any `cd`. `qcar2_physical_lidar_avoidance.py`
(which runs on the Jetson after being sftp'd there) reads the same file if it was synced
alongside it, falling back to a hardcoded default otherwise.

This centralization is **scoped to `Windows/Virtual + Physical/` only** — the other mode
folders (`Windows/Virtual`, `Windows/Physical`, and everything under `Linux/`) still
hardcode IPs per-script. Don't assume changing `network_config.json` affects those.

Note: this pattern was reverted once and then reinstated at the user's explicit request —
treat it as the settled approach, not something to second-guess or simplify away.

Other JSON config files in the repo follow the same "plain JSON tunable, loaded by both
Python and a `.bat`-driven tool" pattern, e.g. `hsv_config.json` (lane-detection HSV
thresholds, edited via `tune_hsv.bat` → `hsv_tuner_virtual_camera.py`) and
`wall_config.json` (QLabs environment wall placement, under `Windows/Virtual/setup_environment/`).

## `isaac_sim/`

A separate area for running QCar2 / QBot Platform in NVIDIA Isaac Sim with ROS2 Nav2.
`qcar2_isaac_nav2/` and `qbot_platform_isaac_nav2/` are ROS2 (colcon) packages, not
integrated with the QCar2/ Simulink+QUARC workflow above — treat it as a distinct subsystem
with its own README-documented setup (Ubuntu 24.04, Isaac Sim 5.1.0, ROS Kilted, Nav2).
