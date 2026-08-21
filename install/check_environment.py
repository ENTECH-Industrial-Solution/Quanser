"""
Checks whether the prerequisites listed in README.md's "Prerequisites" section
are in place: Python packages, QLabs, QUARC, and the Quanser Python SDK
(pal/hal/qvl/pit from quanser/Quanser_Academic_Resources).

This only *checks* — it doesn't install MATLAB/QUARC or QLabs (those require
their own installers) and it doesn't clone the Quanser_Academic_Resources repo
for you. Run install.bat first to install the Python packages listed in
requirements.txt, then run this to see what's still missing.
"""

import importlib
import os
import shutil
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

QLABS_DEFAULT_PATH = r"C:\Program Files\Quanser\Quanser Interactive Labs"

REQUIRED_PACKAGES = [
    ("paramiko", "paramiko"),
    ("opencv-python", "cv2"),
    ("numpy", "numpy"),
]
OPTIONAL_PACKAGES = [
    ("ultralytics", "ultralytics"),
]

results = []


def report(ok, label, detail=""):
    tag = "[ OK ]" if ok else "[MISS]"
    line = f"{tag} {label}"
    if detail:
        line += f" - {detail}"
    print(line)
    results.append(ok)


def check_python_version():
    ok = sys.version_info >= (3, 8)
    report(ok, f"Python {sys.version.split()[0]}", "" if ok else "need Python 3.8+")


def check_packages(packages, optional=False):
    for pip_name, import_name in packages:
        try:
            importlib.import_module(import_name)
            report(True, pip_name)
        except ImportError:
            label = f"{pip_name} (optional)" if optional else pip_name
            report(not optional, label, "pip install -r install/requirements.txt")


def check_qlabs():
    ok = os.path.isdir(QLABS_DEFAULT_PATH)
    report(ok, "Quanser Interactive Labs (QLabs)",
           QLABS_DEFAULT_PATH if ok else f"not found at default path: {QLABS_DEFAULT_PATH}")


def check_quarc():
    ok = shutil.which("quarc_run") is not None
    report(ok, "QUARC (quarc_run on PATH)",
           "" if ok else "install MATLAB/Simulink + QUARC and open a QUARC-enabled shell")


def check_quanser_sdk():
    env_path = os.environ.get("QUANSER_ACADEMIC_RESOURCES_PATH")
    candidates = []
    if env_path:
        candidates.append(os.path.join(env_path, "0_libraries", "python"))
    parent = os.path.abspath(os.path.join(REPO_ROOT, ".."))
    candidates.append(os.path.join(parent, "Quanser_Academic_Resources", "0_libraries", "python"))
    candidates.append(os.path.join(parent, "0_libraries", "python"))

    found_path = None
    for candidate in candidates:
        if os.path.isdir(candidate):
            found_path = candidate
            break

    if found_path is None:
        report(False, "Quanser Python SDK (pal/hal/qvl)",
               "no clone of quanser/Quanser_Academic_Resources found - "
               "clone it as a sibling of this repo or set QUANSER_ACADEMIC_RESOURCES_PATH")
        return

    if found_path not in sys.path:
        sys.path.insert(0, found_path)

    missing = []
    for mod in ("pal", "hal", "qvl"):
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(mod)

    ok = not missing
    report(ok, "Quanser Python SDK (pal/hal/qvl)",
           found_path if ok else f"found {found_path} but couldn't import: {', '.join(missing)}")


def main():
    print("--------------------------------")
    print("ENTECH_Quanser environment check")
    print("--------------------------------")
    check_python_version()
    check_packages(REQUIRED_PACKAGES)
    check_packages(OPTIONAL_PACKAGES, optional=True)
    check_qlabs()
    check_quarc()
    check_quanser_sdk()

    print("--------------------------------")
    if all(results):
        print("All checks passed.")
        return 0
    print("Some checks failed - see README.md's Prerequisites section for setup steps.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
