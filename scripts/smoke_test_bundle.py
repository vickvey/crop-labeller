"""Smoke-test an extracted offline package, as a user would run it.

    python scripts/smoke_test_bundle.py path/to/extracted/crop-labeller [--install-python PY]

For an own-python package, --install-python runs install-with-own-python.{bat,sh}
first, with that interpreter (or `auto` to let the installer find one). Then, using
the package's own Python (bundled python/ or the created .venv), it renders the app
on a sample CSV with Streamlit's AppTest, launches start-crop-labeller.{bat,sh},
and waits for the server's health check.
Runs on Windows (CI) and Linux (local). Stdlib only.
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


def launcher(pkg: Path, name: str) -> list[str]:
    return ["cmd", "/c", str(pkg / f"{name}.bat")] if WINDOWS else [str(pkg / f"{name}.sh")]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("--install-python", help="run the own-python installer with this interpreter "
                        "('auto': let the installer find Python 3.12 itself)")
    args = parser.parse_args()
    pkg = args.package.resolve()
    env = {**os.environ, "CROP_LABELLER_NO_PAUSE": "1"}

    print((pkg / "VERSION.txt").read_text())

    if args.install_python:
        step(f"install-with-own-python using {args.install_python}")
        extra = [] if args.install_python == "auto" else [args.install_python]
        subprocess.run([*launcher(pkg, "install-with-own-python"), *extra], cwd=pkg, env=env, check=True)

    csv_path = pkg / "data" / "zzz_smoke_test.csv"
    csv_path.write_text(SAMPLE_CSV)
    try:
        py = package_python(pkg)
        step(f"AppTest with {py.relative_to(pkg)}")
        subprocess.run([str(py), "-E", "-s", "-c", APPTEST], cwd=pkg, env=env, check=True)

        step("start-crop-labeller launcher + health check")
        server = subprocess.Popen(
            [*launcher(pkg, "start-crop-labeller"), "--server.headless=true", f"--server.port={PORT}"],
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
