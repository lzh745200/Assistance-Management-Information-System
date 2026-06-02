#!/usr/bin/env python3
"""
TypeScript 类型自动生成脚本

从 FastAPI OpenAPI 规范生成前端 TypeScript 类型定义，
确保前后端接口类型一致性（方案 #16）。

Usage:
    python scripts/generate_api_types.py

Prerequisites:
    - 后端服务必须正在运行（默认 http://localhost:8000）
    - npx openapi-typescript 必须可用
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_URL = os.environ.get("API_URL", "http://localhost:8000")
OPENAPI_PATH = BACKEND_URL + "/openapi.json"
OUTPUT_FILE = PROJECT_ROOT / "frontend" / "src" / "types" / "api-generated.ts"


def fetch_openapi_spec() -> dict:
    """从后端获取 OpenAPI 规范 JSON"""
    print(f"Fetching OpenAPI spec from {OPENAPI_PATH}...")
    try:
        with urlopen(OPENAPI_PATH) as resp:
            spec = json.loads(resp.read())
        print(f"  OK — {len(spec.get('paths', {}))} paths, {len(spec.get('components', {}).get('schemas', {}))} schemas")
        return spec
    except Exception as e:
        print(f"  ERROR: Cannot reach backend at {BACKEND_URL} — {e}")
        print("  Make sure the backend server is running (python backend/start.py)")
        sys.exit(1)


def write_spec_file(spec: dict) -> Path:
    """将 OpenAPI 规范写入临时 JSON 文件"""
    tmp_file = PROJECT_ROOT / "backend" / "openapi_generated.json"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    print(f"  Wrote spec to {tmp_file}")
    return tmp_file


def generate_types(spec_file: Path) -> None:
    """使用 openapi-typescript 生成 TypeScript 类型"""
    cmd = [
        "npx", "openapi-typescript",
        str(spec_file),
        "--output", str(OUTPUT_FILE),
        "--alphabetize",
        "--export-type",
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))

    if result.returncode == 0:
        print(f"  OK — Types written to {OUTPUT_FILE}")
    else:
        print(f"  STDERR: {result.stderr}")
        # openapi-typescript might not be installed; fall back gracefully
        print("  WARNING: openapi-typescript may not be installed.")
        print("  Install it via: npm install -D openapi-typescript")
        sys.exit(1)


def main():
    print("=" * 60)
    print("  TypeScript API 类型自动生成")
    print("=" * 60)
    spec = fetch_openapi_spec()
    spec_file = write_spec_file(spec)
    generate_types(spec_file)
    # Cleanup
    spec_file.unlink(missing_ok=True)
    print("Done.")


if __name__ == "__main__":
    main()
