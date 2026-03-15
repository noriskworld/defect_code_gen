#!/usr/bin/env python3
"""Batch taxonomy validation: verify all effects against the taxonomy manager."""
import json
import subprocess

EFFECTS_PATH = "/Users/yunweihu/Documents/code/defect_code_gen/inputs/effects.json"
TAXONOMY_SCRIPT = "/Users/yunweihu/.gemini/antigravity/skills/taxonomy_manager/scripts/taxonomy_lookup.py"
TAXONOMY_FILE = "/Users/yunweihu/Documents/code/defect_code_gen/schema/end_effects_library.json"
PYTHON = "/Users/yunweihu/.gemini/antigravity/.venv/bin/python"

with open(EFFECTS_PATH) as f:
    effects = json.load(f)

passed = 0
failed = 0
errors = []

for i, entry in enumerate(effects):
    result = subprocess.run(
        [PYTHON, TAXONOMY_SCRIPT,
         "--effect", entry["end_effect"],
         "--severity", str(entry["severity"]),
         "--taxonomy", TAXONOMY_FILE],
        capture_output=True, text=True
    )

    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        errors.append(f"[{i}] {entry['function_id']}|{entry['category']}: Parse error: {result.stdout[:200]}")
        failed += 1
        continue

    if report.get("matched"):
        passed += 1
    else:
        failed += 1
        errors.append(
            f"[{i}] {entry['function_id']}|{entry['category']}: "
            f"'{entry['end_effect'][:60]}...' -> {report.get('error', 'Unknown')}"
        )

print(f"Taxonomy Validation: {passed}/{len(effects)} matched")
if errors:
    print("FAILURES:")
    for e in errors:
        print(f"  {e}")
else:
    print("ALL EFFECTS VALIDATED AGAINST TAXONOMY")
