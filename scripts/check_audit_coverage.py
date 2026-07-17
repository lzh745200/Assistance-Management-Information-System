#!/usr/bin/env python3
"""
审计日志覆盖度核查 — 检测写操作端点是否调用 write_work_log / AuditLogger。

军方合规要求：所有写操作必须记录审计日志（write_work_log 或 AuditLogger.log）。
本脚本扫描 app/api/v1/ 下所有 POST/PUT/DELETE 端点，列出未调用审计日志的清单。

退出码：0=通过，1=发现遗漏（--strict 模式）。
"""
import re
import sys
from pathlib import Path

AUDIT_PATTERNS = [
    r"write_work_log",
    r"AuditLogger\.log",
    r"AuditLogger\(",
    r"audit_log",
    r"OperationLog\(",
    r"FundOperationLog\(",
]

WRITE_DECORATORS = [
    r'@router\.post\b',
    r'@router\.put\b',
    r'@router\.patch\b',
    r'@router\.delete\b',
]

# 这些端点类型审计要求较低（只读/模板/导出辅助），可豁免
EXEMPT_PATTERNS = [
    r"/template",       # 模板下载
    r"/options/",       # 选项枚举
    r"/search",         # 搜索（只读语义但用了 POST）
]

BASE_DIR = Path(__file__).parent.parent / "backend" / "app" / "api" / "v1"


def scan_file(filepath: Path) -> list:
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return []

    lines = content.split("\n")
    findings = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if any(re.search(p, line) for p in WRITE_DECORATORS):
            func_start = i
            # 提取路由路径判断是否豁免
            full_decorator = line
            if i + 1 < len(lines) and lines[i + 1].strip().startswith("@router."):
                i += 1
                continue

            func_body = []
            j = i + 1
            while j < len(lines):
                bline = lines[j]
                if j > func_start + 1 and (
                    bline.strip().startswith("@router.") or
                    (bline.strip().startswith("def ") and not bline.startswith(" "))
                ):
                    break
                func_body.append(bline)
                j += 1
                if len(func_body) > 80:
                    break

            func_text = "\n".join(func_body)
            func_name_match = re.search(r"async def (\w+)|def (\w+)", func_text)
            func_name = ""
            if func_name_match:
                func_name = func_name_match.group(1) or func_name_match.group(2)

            # 检查是否豁免（模板/选项/搜索）
            is_exempt = any(re.search(p, full_decorator) for p in EXEMPT_PATTERNS)

            if not is_exempt and func_name:
                has_audit = any(re.search(p, func_text) for p in AUDIT_PATTERNS)
                if not has_audit:
                    findings.append({
                        "file": str(filepath.relative_to(BASE_DIR.parent.parent.parent)),
                        "line": func_start + 1,
                        "function": func_name,
                    })
            i = j
        else:
            i += 1

    return findings


def main():
    strict = "--strict" in sys.argv

    if not BASE_DIR.exists():
        print(f"ERROR: 后端 API 目录不存在: {BASE_DIR}")
        return 2

    all_findings = []
    for f in sorted(BASE_DIR.rglob("*.py")):
        if f.name == "__init__.py":
            continue
        all_findings.extend(scan_file(f))

    if not all_findings:
        print("✅ 审计日志覆盖度通过：所有写端点均包含审计日志调用。")
        return 0

    total = len(all_findings)
    print(f"⚠️  发现 {total} 个写端点未调用审计日志（write_work_log / AuditLogger）：\n")
    print(f"{'文件':<55} {'行号':>6}  {'函数'}")
    print("-" * 90)
    for f in all_findings[:50]:  # 最多显示前50个
        print(f"{f['file']:<55} {f['line']:>6}  {f['function']}")
    if total > 50:
        print(f"\n... 还有 {total - 50} 个未显示")

    print(f"\n建议：为上述端点添加 write_work_log(db, ...) 调用以满足军方审计合规。")
    print(f"      详见 AGENTS.md「安全清单」第 1 项。")

    return 1 if strict else 0


if __name__ == "__main__":
    sys.exit(main())
