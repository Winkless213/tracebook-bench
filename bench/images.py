"""Build one Docker image per repository snapshot: agent base + source tree at the knowledge commit + installed deps."""
import io
import json
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path

DOCKERFILE = """FROM tb-agent-base
COPY src/ /workspace/
WORKDIR /workspace
RUN {install}
"""


def image_name(repo):
    return f"tb-repo-{repo.lower()}"


def export_tree(clone, commit, dest):
    data = subprocess.run(["git", "-C", str(clone), "-c", "core.autocrlf=false", "archive", "--format=tar", commit],
                          capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        tar.extractall(dest, filter="data")


def build(repo, spec, clones_dir, log):
    # TB_WORK puts the build context on a disk with room for the source tree; unset means the system temp dir
    with tempfile.TemporaryDirectory(prefix=f"tb-img-{repo}-", dir=os.environ.get("TB_WORK")) as ctx:
        ctx = Path(ctx)
        export_tree(Path(clones_dir) / repo, spec["commit"], ctx / "src")
        (ctx / "Dockerfile").write_text(DOCKERFILE.format(install=spec["install"]), encoding="utf-8", newline="\n")
        with open(log, "w", encoding="utf-8") as fh:
            p = subprocess.run(["docker", "build", "-t", image_name(repo), str(ctx)], stdout=fh,
                               stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    return p.returncode


if __name__ == "__main__":
    import sys
    config_path, clones_dir, *repos = sys.argv[1:]
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    for repo in repos or config:
        log = Path(clones_dir).parent / "logs" / f"build-{repo}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        print(repo, "->", image_name(repo), "exit", build(repo, config[repo], clones_dir, log), "log", log)
