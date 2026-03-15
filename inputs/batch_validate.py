#!/usr/bin/env python3
"""Batch validator: extracts each function's failure modes and validates them."""
import json
import subprocess
import sys

DRAFT_PATH = "/Users/yunweihu/Documents/code/defect_code_gen/inputs/draft_fm_all.json"
FUNCTIONS_PATH = "/Users/yunweihu/Documents/code/defect_code_gen/inputs/functions.json"
VALIDATOR = "/Users/yunweihu/.gemini/antigravity/skills/json_validator/scripts/validator.py"
PYTHON = "/Users/yunweihu/.gemini/antigravity/.venv/bin/python"

with open(DRAFT_PATH) as f:
    drafts = json.load(f)

with open(FUNCTIONS_PATH) as f:
    functions = json.load(f)

func_map = {fn["function_id"]: fn for fn in functions}
all_passed = True
results = {}

for func_id, modes in drafts.items():
    fn = func_map.get(func_id)
    if not fn:
        print(f"SKIP: {func_id} not in functions.json")
        continue

    # Write temp file for this batch
    tmp = f"/tmp/draft_{func_id}.json"
    with open(tmp, "w") as f:
        json.dump(modes, f)

    result = subprocess.run(
        [PYTHON, VALIDATOR, "--input", tmp, "--function-verb", fn["verb"], "--function-noun", fn["noun"]],
        capture_output=True, text=True
    )

    report = json.loads(result.stdout)
    passed = report.get("all_valid", False)
    results[func_id] = {"passed": passed, "verb": fn["verb"], "noun": fn["noun"]}

    if not passed:
        all_passed = False
        print(f"FAIL: {func_id} ({fn['verb']} {fn['noun']})")
        for sr in report.get("semantic_results", []):
            if not sr.get("is_valid"):
                print(f"  - {sr['category']}: {sr.get('errors', [])}")
    else:
        print(f"PASS: {func_id} ({fn['verb']} {fn['noun']})")

print(f"\n{'ALL PASSED' if all_passed else 'SOME FAILED'}: {sum(1 for v in results.values() if v['passed'])}/{len(results)} functions validated.")
