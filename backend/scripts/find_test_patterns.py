#!/usr/bin/env python
"""Find all response.json() access patterns in test_assessment_api.py that need updating."""
import re

filepath = "tests/unit/test_assessment_api.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# Patterns that need updating:
# data["items"] -> data["data"]["items"]
# data["total"] -> data["data"]["total"]
# data["year"] -> data["data"]["year"]
# data["weights"] -> data["data"]["weights"]
# resp.json()["items"] -> resp.json()["data"]["items"]
# resp.json()["total"] -> resp.json()["data"]["total"]

patterns = [
    (r'data\["items"\]', 'data["data"]["items"]'),
    (r'data\["total"\]', 'data["data"]["total"]'),
    (r'data\["year"\]', 'data["data"]["year"]'),
    (r'data\["weights"\]', 'data["data"]["weights"]'),
    (r'resp\.json\(\)\["items"\]', 'resp.json()["data"]["items"]'),
    (r'resp\.json\(\)\["total"\]', 'resp.json()["data"]["total"]'),
    (r'json\(\)\["items"\]', 'json()["data"]["items"]'),
    (r'json\(\)\["total"\]', 'json()["data"]["total"]'),
]

for i, line in enumerate(lines, 1):
    for pat, _ in patterns:
        if re.search(pat, line):
            print(f"  L{i}: {line.strip()[:100]}")
            break
