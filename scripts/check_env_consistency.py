"""
环境一致性检查脚本

检查 requirements.txt 与实际安装包的版本一致性。
用法: python scripts/check_env_consistency.py
"""

import importlib.metadata
import re
import sys
from pathlib import Path


_REQ_PATTERN = re.compile(r"^([a-zA-Z0-9_-]+)([><=!~]+)([\d.]+)")


def parse_requirements(path: str) -> dict:
    """解析 requirements.txt，返回 {包名: 指定版本}"""
    pkgs = {}

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # 处理环境标记: pkg==1.0; sys_platform == 'win32'
            if ";" in line:
                pkg_part = line.split(";")[0].strip()
            else:
                pkg_part = line

            match = _REQ_PATTERN.match(pkg_part)
            if match:
                name = match.group(1).lower().replace("_", "-")
                pkgs[name] = match.group(3)
    return pkgs


def main():
    backend_dir = Path(__file__).resolve().parent.parent / "backend"
    req_path = backend_dir / "requirements.txt"

    if not req_path.exists():
        print(f"[ERROR] requirements.txt not found at {req_path}")
        sys.exit(1)

    print("=" * 70)
    print("ENVIRONMENT CONSISTENCY CHECK")
    print("=" * 70)

    required = parse_requirements(str(req_path))
    installed = {}
    for dist in importlib.metadata.distributions():
        name = dist.metadata["Name"].lower()
        installed[name] = dist.version

    mismatches = []
    missing = []

    for pkg, req_ver in required.items():
        if pkg in installed:
            if installed[pkg] != req_ver:
                mismatches.append((pkg, req_ver, installed[pkg]))
        else:
            missing.append(pkg)

    if mismatches:
        print(f"\nFAIL VERSION MISMATCHES ({len(mismatches)}):")
        print(f"   {'Package':<35} {'Required':<15} {'Installed':<15}")
        print(f"   {'-'*35} {'-'*15} {'-'*15}")
        for pkg, req, inst in mismatches:
            print(f"   {pkg:<35} {req:<15} {inst:<15}")
    else:
        print("\nPASS All package versions match requirements.txt")

    if missing:
        print(f"\nWARN️  PACKAGES IN requirements.txt BUT NOT INSTALLED ({len(missing)}):")
        for pkg in missing:
            print(f"   - {pkg}")
    else:
        print("PASS All required packages are installed")

    print(f"\n--- Summary ---")
    print(f"Required packages: {len(required)}")
    print(f"Installed packages: {len(installed)}")
    print(f"Mismatches: {len(mismatches)}")
    print(f"Missing: {len(missing)}")

    # Check multiple requirements files for consistency
    req_files = ["requirements.txt", "requirements-prod.txt",
                 "requirements-minimal.txt", "requirements-docker.txt"]
    all_pkgs = {}
    for rf in req_files:
        rp = backend_dir / rf
        if rp.exists():
            all_pkgs[rf] = set(parse_requirements(str(rp)).keys())

    if all_pkgs:
        print(f"\n--- Cross-file consistency ---")
        # Compare against requirements.txt (canonical)
        canonical = all_pkgs.get("requirements.txt", set())
        for rf, pkgs in all_pkgs.items():
            if rf == "requirements.txt":
                continue
            missing_in = canonical - pkgs
            extra_in = pkgs - canonical
            if missing_in or extra_in:
                print(f"   WARN️  {rf} differs from requirements.txt:")
                if missing_in:
                    print(f"      Missing: {', '.join(sorted(missing_in)[:10])}")
                if extra_in:
                    print(f"      Extra: {', '.join(sorted(extra_in)[:10])}")
            else:
                print(f"   PASS {rf} consistent with requirements.txt")

    if mismatches or missing:
        print(f"\n[FIX] To fix: pip install -r {req_path}")
        sys.exit(1)
    else:
        print("\n[OK] Environment is fully consistent!")


if __name__ == "__main__":
    main()
