"""Validate and package project-local agent skills into .skill zip archives.

Run from repo root:
    python scripts/package_project_skills.py

Output:
    artifacts/skills/<skill-name>.skill
"""
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"
OUT = ROOT / "artifacts" / "skills"
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")

REQUIRED = [
    "ponytail",
    "ponytail-review",
    "ponytail-audit",
    "ponytail-debt",
    "ponytail-gain",
    "ponytail-help",
    "caveman",
    "frontend-view-creator",
    "frontend-ui-engineering",
    "backend-endpoint-creator",
    "bug-pattern-fixer",
    "code-review-and-quality",
    "web-quality-audit",
    "project-issue-fixer",
    "pre-commit-guard",
    "security-auditor",
]


def frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        raise ValueError("missing opening frontmatter")
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        raise ValueError("missing closing frontmatter")
    return parts[1]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    packed: list[Path] = []

    for name in REQUIRED:
        directory = SKILLS / name
        skill_md = directory / "SKILL.md"
        try:
            if not NAME_RE.match(name):
                raise ValueError(f"bad skill name: {name}")
            if not skill_md.exists():
                raise ValueError("missing SKILL.md")
            text = skill_md.read_text(encoding="utf-8")
            fm = frontmatter(text)
            match = re.search(r"^name:\s*(.+)$", fm, re.M)
            if not match or match.group(1).strip().strip("\"'") != name:
                raise ValueError("frontmatter name mismatch")
            if not re.search(r"^description:\s*(>|.+)$", fm, re.M):
                raise ValueError("missing description")
            body = text.split("---\n", 2)[2]
            if len(body.splitlines()) > 500:
                raise ValueError("body exceeds 500 lines")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{name}: {exc}")
            continue

        package = OUT / f"{name}.skill"
        with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in directory.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(directory.parent))
        packed.append(package)

    for path in packed:
        print(f"packed: {path}")
    if errors:
        print("errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"validation ok: {len(packed)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
