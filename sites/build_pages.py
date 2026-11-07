from pathlib import Path
import argparse
import shutil

parser = argparse.ArgumentParser(description="Prepare the two standalone dashboards for GitHub Pages")
parser.add_argument("destination", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
sources = {
    "index.html": root / "sites/znr-overview/dashboard.html",
    "experiments/index.html": root / "sites/openspec-experiments/dashboard.html",
}
# Publish only these HTML files; no repository contents are copied implicitly.
for source in sources.values():
    if not source.is_file() or source.is_symlink():
        raise SystemExit(f"Expected a regular dashboard HTML file: {source}")
args.destination.mkdir(parents=True, exist_ok=False)
for relative, source in sources.items():
    destination = args.destination / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    assert destination.read_bytes() == source.read_bytes()
assert sorted(str(p.relative_to(args.destination)) for p in args.destination.rglob("*") if p.is_file()) == sorted(sources)
print("Prepared overview at / and experiment dashboard at /experiments/")
