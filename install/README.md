# install/

One-time environment setup for this repo, separate from the per-demo
`setup_environment/` folders under `QCar2/**` (those configure the QLabs
*scene* - walls, spawn points, etc. - not your machine).

## Usage

```
install\install.bat
```

This installs the Python packages this repo's scripts depend on
(`requirements.txt`), then runs `check_environment.py` to report what's
still missing.

`check_environment.py` can also be run on its own at any time to re-check
your setup:

```
python install\check_environment.py
```

It checks for:

- Python 3.8+
- Required packages: `paramiko`, `opencv-python`, `numpy`
- Optional package: `ultralytics` (only needed for the 360-vision YOLOv8
  detection overlay)
- Quanser Interactive Labs (QLabs), at its default install path
- QUARC (`quarc_run` on `PATH`)
- The official Quanser Python SDK (`pal`/`hal`/`qvl`) from
  [quanser/Quanser_Academic_Resources](https://github.com/quanser/Quanser_Academic_Resources)

## What this does NOT do

- Install MATLAB/Simulink, QUARC, or QLabs themselves - those need their own
  official installers.
- Clone `quanser/Quanser_Academic_Resources` for you. Clone it yourself as a
  sibling of this repo, or point `QUANSER_ACADEMIC_RESOURCES_PATH` at your
  existing clone. See the root [README.md](../README.md#prerequisites) for
  the exact layout expected.

See the root [README.md](../README.md) for full prerequisite details.
