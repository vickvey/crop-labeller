"""Smoke-test an installed copy of the app, the way a user would run it.

    python scripts/smoke_test_install.py DIR [--install-python PY]

DIR is either an extracted offline package or a source checkout with a .venv
(pip/uv install of requirements.txt). For an own-python package, --install-python
runs install-with-own-python.{bat,sh} first, with that interpreter (or `auto` to
let the installer find one). Then, using DIR's Python (bundled python/ or .venv),
it renders the app on a sample CSV with Streamlit's AppTest, starts the app the
way that setup is meant to be started (start-crop-labeller.{bat,sh} in a package,
`python run.py` in a checkout), and waits for the server's health check.
Runs on Windows, macOS and Linux. Stdlib only.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

WINDOWS = os.name == "nt"
PORT = 8765

SAMPLE_CSV = """\
sample_id,label,class_name,region,year,NDVI_1,NDVI_2,NDVI_3,label_confidence_score,flag
1,1,wheat,Punjab,2021,0.21,0.55,0.81,0.93,ok
2,0,non_wheat,Punjab,2021,0.18,0.22,0.25,0.12,labeled_nonwheat_wheatlike_profile
"""

APPTEST = """
import sys
sys.path.insert(0, "src")
from streamlit.testing.v1 import AppTest
at = AppTest.from_file("src/crop_labeller/app.py", default_timeout=120).run()
assert not at.exception, list(at.exception)
assert [r for r in at.radio if r.label == "Label"], "label radio missing"
assert at.get("plotly_chart"), "NDVI plot missing"
print("AppTest OK:", sys.version.split()[0], sys.executable)
"""


def step(msg: str) -> None:
    print(f"\n=== {msg}", flush=True)


def package_python(pkg: Path) -> Path:
    for rel in (["python/python.exe", ".venv/Scripts/python.exe"] if WINDOWS
                else ["python/bin/python3", ".venv/bin/python"]):
        if (pkg / rel).exists():
            return pkg / rel
    sys.exit("No python/ or .venv/ in the package")


def launcher(pkg: Path, name: str) -> list[str] | None:
    path = pkg / (f"{name}.bat" if WINDOWS else f"{name}.sh")
    if not path.exists():
        return None
    return ["cmd", "/c", str(path)] if WINDOWS else [str(path)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("--install-python", help="run the own-python installer with this interpreter "
                        "('auto': let the installer find Python 3.12 itself)")
    args = parser.parse_args()
    pkg = args.package.resolve()
    env = {**os.environ, "CROP_LABELLER_NO_PAUSE": "1"}

    if (pkg / "VERSION.txt").exists():
        print((pkg / "VERSION.txt").read_text())

    if args.install_python:
        step(f"install-with-own-python using {args.install_python}")
        extra = [] if args.install_python == "auto" else [args.install_python]
        installer = launcher(pkg, "install-with-own-python")
        if installer is None:
            sys.exit("no install-with-own-python script in this directory")
        subprocess.run([*installer, *extra], cwd=pkg, env=env, check=True)

    csv_path = pkg / "data" / "zzz_smoke_test.csv"
    csv_path.write_text(SAMPLE_CSV)
    try:
        py = package_python(pkg)
        step(f"AppTest with {py.relative_to(pkg)}")
        subprocess.run([str(py), "-E", "-s", "-c", APPTEST], cwd=pkg, env=env, check=True)

        start = launcher(pkg, "start-crop-labeller") or [str(py), "run.py"]
        step(f"start the app ({' '.join(Path(a).name for a in start)}) + health check")
        server = subprocess.Popen(
            [*start, "--server.headless=true", f"--server.port={PORT}"],
            cwd=pkg, env=env, stdin=subprocess.DEVNULL,
        )
        try:
            for _ in range(90):
                if server.poll() is not None:
                    sys.exit(f"launcher exited early with code {server.returncode}")
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/_stcore/health", timeout=2) as r:
                        if r.read().strip() == b"ok":
                            print("health check OK")
                            break
                except OSError:
                    time.sleep(1)
            else:
                sys.exit("server never became healthy")
        finally:
            if WINDOWS:
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(server.pid)], capture_output=True)
            else:
                server.terminate()
            server.wait(timeout=30)
    finally:
        csv_path.unlink(missing_ok=True)
    step("smoke test passed")


if __name__ == "__main__":
    main()
