# ENTECH_Quanser

QCar2 project files (Simulink models, Python launch/control scripts) for physical and
virtual QCar2 setups. This repo is **not fully self-contained** — it depends on the
official Quanser Python SDK and on MATLAB/Simulink tooling that must be installed
separately. See Prerequisites below before cloning and running anything.

## Structure

```
QCar2/
  Linux/
    Physical/            # Physical QCar2 launch scripts + Simulink models (Linux host)
    Virtual/              # Virtual QCar2 (QLabs) scripts, split by task
    Virtual + Physical/
  Windows/
    Physical/
    Virtual/
    Virtual + Physical/   # Combined virtual + physical demo scripts + Simulink models
Qube_servo2/               # (currently empty)
```

## Prerequisites

1. **MATLAB/Simulink** with **QUARC** (Quanser's real-time target support package) —
   required to build/run the `.slx` models and the `quarc_run` / `qc_connect_model` calls
   used by the `.bat` scripts and `connect.m`.
2. **Quanser Interactive Labs (QLabs)** — installed at its default location
   (`C:\Program Files\Quanser\Quanser Interactive Labs\`), required for anything that
   imports `qvl.*` or is launched via `start_QLabs.bat`.
3. **The official Quanser Academic Resources repo**
   ([quanser/Quanser_Academic_Resources](https://github.com/quanser/Quanser_Academic_Resources)),
   for the Quanser Python SDK under `0_libraries/python/` (`pal`, `hal`, `qvl`, `pit`).
   These packages are not on PyPI and are not vendored in this repo. Two ways to make
   them importable:
   - Clone that repo as a **sibling** of this one, e.g.:
     ```
     Quanser/
       Quanser_Academic_Resources/   <- official repo clone
       ENTECH_Quanser/               <- this repo
     ```
     A few scripts (`ssh_qcar2.py`'s companions, `run_physical_lidar_avoidance.py`,
     `view_physical_360_vision.py`) fall back to this sibling layout automatically.
   - Or set an environment variable pointing at your clone and add it to `PYTHONPATH`:
     ```
     set QUANSER_ACADEMIC_RESOURCES_PATH=D:\path\to\Quanser_Academic_Resources
     set PYTHONPATH=%QUANSER_ACADEMIC_RESOURCES_PATH%\0_libraries\python;%PYTHONPATH%
     ```
4. **Python 3.x** with: `paramiko`, `opencv-python`, `numpy`, `ultralytics` (YOLOv8,
   optional — only needed for the 360-vision detection overlay).

## Running a demo

Each `<mode>/start_qcar2_demo*.bat` script:
1. Stops any running models/clients.
2. Opens the matching Simulink model in `Simulink/` (same folder, resolved relative to
   the script's own location — safe to run after cloning to any path).
3. Starts peripheral clients and the physical/virtual car models.

The physical-QCar2 scripts (`ssh_qcar2.py`, `run_physical_lidar_avoidance.py`,
`view_physical_360_vision.py`) SSH into the Jetson on the QCar2 (default credentials
`nvidia`/`nvidia`) and sync local scripts/libraries to it — check the hardcoded IP
addresses near the top of each file (`qcar_ip`, `QCAR_IP`) match your robot's actual
network address before running.

## Known limitations

- `Qube_servo2/` is currently empty.
- IP addresses for QCar2 units and the host PC are hardcoded per-script rather than
  centrally configured.
