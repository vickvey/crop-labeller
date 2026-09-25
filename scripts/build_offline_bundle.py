"""Build the offline zips attached to each GitHub release.

Two variants, both fully offline on the target machine:
  bundled     the app plus a private Python with every dependency preinstalled.
              Unzip, double-click start-crop-labeller.bat. Recommended.
  own-python  the app plus a wheelhouse/ of exact-pinned wheels, for installing
              into the user's OWN Python (install-with-own-python.bat or plain pip).

    uv run python scripts/build_offline_bundle.py                    # both Windows zips
    uv run python scripts/build_offline_bundle.py --platform linux   # same layouts, for smoke tests
    uv run python scripts/build_offline_bundle.py --allow-dirty ...  # local testing only

Release builds refuse uncommitted changes, so the commit in VERSION.txt is exactly
what's inside, and app files are taken from `git archive HEAD`. Needs internet and
`uv` on the build machine. Output (zips + SHA256SUMS.txt) goes to dist/.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import shutil
import subprocess
import sys
import tarfile
import tomllib
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / "build"
DIST_DIR = ROOT / "dist"
TOP = "crop-labeller"  # folder name inside the zip

# python-build-standalone (the same Python builds uv uses). Bump deliberately:
# the wheel set must match PYTHON_VERSION's minor version.
PYTHON_VERSION = "3.12"
PBS_RELEASE = "20260924"
PBS_BASE = f"https://github.com/astral-sh/python-build-standalone/releases/download/{PBS_RELEASE}"
PLATFORMS = {
    "windows": {
        "archive": f"cpython-3.12.14+{PBS_RELEASE}-x86_64-pc-windows-msvc-install_only_stripped.tar.gz",
        "sha256": "c5bf8edfe858c1df9891be498b5bbc8761d383df5b9790658b088fea4870433a",
        "uv_platform": "x86_64-pc-windows-msvc",
        "pip_platforms": ["win_amd64"],
        "site_packages": "python/Lib/site-packages",
        "launchers": {
            "bundled": ["packaging/windows/start-crop-labeller.bat"],
            "own-python": ["packaging/windows/start-crop-labeller.bat",
                           "packaging/windows/install-with-own-python.bat"],
        },
    },
    "linux": {
        "archive": f"cpython-3.12.14+{PBS_RELEASE}-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz",
        "sha256": "269b2c99e4db15b242bf01832f4fea1e8f1a664f273cff519393f296e9820b41",
        "uv_platform": "x86_64-manylinux_2_28",
        "pip_platforms": ["manylinux_2_28_x86_64", "manylinux_2_17_x86_64", "manylinux2014_x86_64"],
        "site_packages": f"python/lib/python{PYTHON_VERSION}/site-packages",
        "launchers": {
            "bundled": ["packaging/linux/start-crop-labeller.sh"],
            "own-python": ["packaging/linux/start-crop-labeller.sh",
                           "packaging/linux/install-with-own-python.sh"],
        },
    },
}
VARIANTS = ["bundled", "own-python"]
ZIP_SUFFIX = {"bundled": "offline", "own-python": "offline-own-python"}

# Project files shipped in every zip (taken from the commit being built).
APP_PATHS = [
    "src",
    "reference",
    "run.py",
    "pyproject.toml",
    "requirements.txt",
    "README.md",
    "USAGE-GUIDELINES.md",
    "USAGE-GUIDELINES.pdf",
    "output/.gitkeep",
]

# Windows Explorer's "Extract All" fails past MAX_PATH (260 chars). Keep paths
# inside the zip short enough to survive being unzipped a few folders deep.
MAX_ZIP_PATH = 140

# Not needed at runtime; dropped from the bundled Python to save space and shorten paths.
PRUNE_DIR_NAMES = {"__pycache__", "tests"}
PRUNE_REL_DIRS = ["pyarrow/include", "pyarrow/src", "streamlit/.agents", "bin"]

DATA_README = """\
Put the CSV file(s) you want to review directly in this folder (not in a
subfolder), then start the app. See USAGE-GUIDELINES.pdf, section 2.
"""

EXPORT_CMD = ["uv", "export", "--no-dev", "--no-hashes", "--no-emit-project",
              "--format", "requirements-txt", "--frozen"]


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, check=True, cwd=ROOT, **kwargs)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def check_sources(allow_dirty: bool) -> str:
    """Refuse to build a release from anything but a clean, consistent commit."""

    def pins(text: str) -> list[str]:
        return [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]

    exported = subprocess.run(EXPORT_CMD, cwd=ROOT, check=True, capture_output=True, text=True).stdout
    if pins(exported) != pins((ROOT / "requirements.txt").read_text()):
        sys.exit(
            "requirements.txt is out of date with uv.lock. Regenerate it with:\n"
            "  uv export --no-dev --no-hashes --no-emit-project --format requirements-txt -o requirements.txt"
        )

    commit = git("rev-parse", "--short", "HEAD").strip()
    if git("status", "--porcelain", "--untracked-files=normal").strip():
        if not allow_dirty:
            sys.exit(
                "Uncommitted changes in the working tree. Commit (or stash) them first, so the\n"
                "zip is exactly the commit recorded in VERSION.txt. (--allow-dirty for local tests.)"
            )
        return f"{commit}+uncommitted-changes (TEST BUILD, not for release)"
    return commit


def download_python(spec: dict) -> Path:
    cache = BUILD_DIR / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / spec["archive"]
    if not archive.exists():
        url = f"{PBS_BASE}/{spec['archive'].replace('+', '%2B')}"
        print(f"Downloading {url}")
        partial = archive.with_name(archive.name + ".part")
        with urllib.request.urlopen(url) as resp, open(partial, "wb") as f:
            shutil.copyfileobj(resp, f)
        partial.rename(archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != spec["sha256"]:
        archive.unlink()
        sys.exit(f"Checksum mismatch for {archive.name}: got {digest}")
    return archive


def resolve_for_target(spec: dict, work: Path) -> Path:
    # Resolve for the *target* platform: markers like `sys_platform == 'win32'`
    # (e.g. tzdata) would otherwise be evaluated against the build machine.
    target_reqs = work / "requirements-target.txt"
    run(
        ["uv", "pip", "compile", "requirements.txt",
         "--python-platform", spec["uv_platform"], "--python-version", PYTHON_VERSION,
         "--only-binary", ":all:", "--no-header", "--no-annotate", "-q", "-o", str(target_reqs)]
    )
    return target_reqs


def stage_bundled_python(spec: dict, stage: Path, target_reqs: Path) -> None:
    with tarfile.open(download_python(spec)) as tar:
        tar.extractall(stage, filter="tar")  # archive's top-level dir is python/
    site_packages = stage / spec["site_packages"]
    run(
        ["uv", "pip", "install", "--target", str(site_packages),
         "--python-platform", spec["uv_platform"], "--python-version", PYTHON_VERSION,
         "--only-binary", ":all:", "--no-deps", "--no-compile", "-q", "-r", str(target_reqs)]
    )
    for rel in PRUNE_REL_DIRS:
        shutil.rmtree(site_packages / rel, ignore_errors=True)
    for path in sorted(site_packages.rglob("*"), reverse=True):
        if path.is_dir() and path.name in PRUNE_DIR_NAMES:
            shutil.rmtree(path, ignore_errors=True)


def stage_wheelhouse(spec: dict, stage: Path, target_reqs: Path) -> None:
    platform_flags = [flag for p in spec["pip_platforms"] for flag in ("--platform", p)]
    run(
        ["uv", "run", "--no-project", "--with", "pip", "python", "-m", "pip", "download",
         "--no-deps", "--only-binary=:all:", "--python-version", PYTHON_VERSION,
         "--implementation", "cp", *platform_flags, "--disable-pip-version-check", "-q",
         "-r", str(target_reqs), "-d", str(stage / "wheelhouse")]
    )
    wanted = {line.split("==")[0].lower().replace("_", "-") for line in target_reqs.read_text().splitlines()
              if "==" in line}
    got = {w.name.split("-")[0].lower().replace("_", "-") for w in (stage / "wheelhouse").glob("*.whl")}
    if missing := wanted - got:
        sys.exit(f"wheelhouse is missing: {sorted(missing)}")


def stage_app_files(stage: Path, from_working_tree: bool) -> None:
    if from_working_tree:
        rels = [r for r in git("ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", *APP_PATHS)
                .split("\0") if r]
        for rel in rels:
            src = ROOT / rel
            if src.is_file():
                (stage / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, stage / rel)
    else:
        archive = subprocess.run(["git", "archive", "--format=tar", "HEAD", "--", *APP_PATHS],
                                 cwd=ROOT, check=True, capture_output=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(stage, filter="data")
    (stage / "data").mkdir(exist_ok=True)
    (stage / "data" / "put-your-csv-files-here.txt").write_text(DATA_README)


def write_zip(stage: Path, zip_path: Path) -> None:
    entries = sorted(stage.rglob("*"))
    names = [f"{TOP}/{p.relative_to(stage).as_posix()}" for p in entries]
    if too_long := [n for n in names if len(n) > MAX_ZIP_PATH]:
        sys.exit(
            f"{len(too_long)} path(s) exceed {MAX_ZIP_PATH} chars (Windows MAX_PATH risk), e.g.\n  "
            + "\n  ".join(sorted(too_long, key=len, reverse=True)[:5])
        )
    if spaced := [n for n in names if " " in n.split("/site-packages/")[0].split("/wheelhouse/")[0]]:
        sys.exit(f"Filenames with spaces in the bundle: {spaced[:5]}")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    zip_path.unlink(missing_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p, name in zip(entries, names):
            zf.write(p, name)
    size_mb = zip_path.stat().st_size / 1e6
    print(f"Wrote {zip_path.relative_to(ROOT)} ({size_mb:.0f} MB, {len(entries)} entries, "
          f"longest path {max(map(len, names))} chars)\n")


def write_checksums(zips: list[Path]) -> None:
    lines = [f"{hashlib.sha256(z.read_bytes()).hexdigest()}  {z.name}\n" for z in sorted(zips)]
    (DIST_DIR / "SHA256SUMS.txt").write_text("".join(lines))
    print("".join(lines), end="")


def build(platform: str, variant: str, version: str, commit: str, from_working_tree: bool) -> Path:
    spec = PLATFORMS[platform]
    work = BUILD_DIR / f"{platform}-{variant}"
    stage = work / TOP
    shutil.rmtree(work, ignore_errors=True)
    stage.mkdir(parents=True)

    target_reqs = resolve_for_target(spec, work)
    if variant == "bundled":
        stage_bundled_python(spec, stage, target_reqs)
        python_note = f"bundled Python {spec['archive'].split('+')[0].removeprefix('cpython-')}"
    else:
        stage_wheelhouse(spec, stage, target_reqs)
        python_note = f"wheels for your own 64-bit Python {PYTHON_VERSION}"
    stage_app_files(stage, from_working_tree)
    for launcher in spec["launchers"][variant]:
        shutil.copy2(ROOT / launcher, stage / Path(launcher).name)

    built = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    (stage / "VERSION.txt").write_text(
        f"Crop Labeller {version} (commit {commit})\n"
        f"Package: {platform}, {variant} ({python_note})\n"
        f"Built {built}\n"
    )
    zip_path = DIST_DIR / f"crop-labeller-{version}-{platform}-{ZIP_SUFFIX[variant]}.zip"
    write_zip(stage, zip_path)
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--platform", choices=sorted(PLATFORMS), default="windows")
    parser.add_argument("--variant", choices=[*VARIANTS, "all"], default="all")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="build from the working tree even with uncommitted changes (never release these)")
    args = parser.parse_args()

    commit = check_sources(args.allow_dirty)
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    from_working_tree = "uncommitted" in commit
    variants = VARIANTS if args.variant == "all" else [args.variant]

    for old in DIST_DIR.glob(f"crop-labeller-*-{args.platform}-*.zip"):
        old.unlink()
    zips = [build(args.platform, v, version, commit, from_working_tree) for v in variants]
    write_checksums(zips)


if __name__ == "__main__":
    main()
