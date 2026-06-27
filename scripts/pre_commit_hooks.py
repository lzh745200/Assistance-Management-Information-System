"""Cross-platform pre-commit hooks (replaces bash-only hooks)."""
import subprocess, sys

def run(args, **kwargs):
    result = subprocess.run(args, **kwargs)
    sys.exit(result.returncode)

if __name__ == "__main__":
    hook = sys.argv[1]
    python = sys.executable

    if hook == "check_dockerfile_tail":
        import pathlib, re
        failed = [
            str(f) for f in pathlib.Path(".").glob("docker/Dockerfile*")
            if re.search(r"RUN .* 2>&1$", f.read_text(encoding="utf-8"), re.MULTILINE)
        ]
        if failed:
            for f in failed:
                print(f"ERROR: {f} has RUN commands without | tail")
                print("(under QEMU, truncation is intentional)")
            sys.exit(1)
        sys.exit(0)

    elif hook == "flake8":
        run([python, "-m", "flake8",
             "--max-line-length=120", "--count",
             "backend/app/"])

    elif hook == "bandit":
        run([python, "-m", "bandit", "-r", "backend/app/"])

    elif hook == "vue_tsc":
        run("npx vue-tsc --noEmit", cwd="frontend", shell=True)

    else:
        print(f"Unknown hook: {hook}")
        sys.exit(1)
