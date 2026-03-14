"""
Phase 4: Assembly & Export
==========================
Assembles validated pipeline outputs into the final standardized_defect_codes JSON.

Inputs:
  --hierarchy   : Path to the validated system hierarchy JSON (array of nodes)
  --functions   : Path to the validated functions JSON (array of verb-noun pairs with allocations)
  --effects     : Path to the reasoned effects JSON (mapping of failure descriptions to end effects)
  --metadata    : Product family name (string), e.g. "Industrial Contactor"
  --schema      : Path to the output schema for validation (defaults to global location)
  --output      : Path to write the final assembled JSON

Outputs:
  - Deterministic failure_id and defect_code strings (structured, human-readable)
  - Final standardized_defect_codes.json validated against the v1 schema
"""

import argparse
import hashlib
import json
import os
import sys

from jsonschema import validate, ValidationError


# ==========================================
# 1. DETERMINISTIC ID GENERATION
# ==========================================

# Category abbreviations for human-readable codes
CATEGORY_ABBREV = {
    "Total Loss of Function": "TLF",
    "Partial / Degraded Function": "PDF",
    "Intermittent Function": "ITF",
    "Unintended / Spurious Function": "USF",
    "Delayed / Early Function": "DEF",
    "Inability to Stop Function": "ISF",
    "Erratic Function": "ERF",
}


def generate_failure_id(function_id: str, category: str, sequence: int) -> str:
    """
    Generates a structured, human-readable failure_id.
    Format: FAIL-{FUNC_SUFFIX}-{CAT_ABBREV}-{SEQ:02d}
    Example: FAIL-001-TLF-01
    """
    func_suffix = function_id.replace("FUNC-", "")
    cat_abbrev = CATEGORY_ABBREV.get(category, "UNK")
    return f"FAIL-{func_suffix}-{cat_abbrev}-{sequence:02d}"


def generate_defect_code(function_id: str, category: str, syntactical_description: str) -> str:
    """
    Generates a deterministic defect_code using SHA-256 hash of the composite key.
    Format: DC-{8-char hex}
    The same inputs always produce the same code (deterministic, duplicate-free).
    """
    composite_key = f"{function_id}|{category}|{syntactical_description}"
    hash_hex = hashlib.sha256(composite_key.encode("utf-8")).hexdigest()[:8]
    return f"DC-{hash_hex}"


# ==========================================
# 2. DUPLICATE DETECTION
# ==========================================

def check_duplicates(failure_modes: list) -> list:
    """
    Checks for duplicate defect_codes in the assembled output.
    Returns a list of error strings (empty if no duplicates).
    """
    seen_codes = {}
    errors = []
    for fm in failure_modes:
        code = fm.get("defect_code")
        if code in seen_codes:
            errors.append(
                f"Duplicate defect_code '{code}' found: "
                f"indices {seen_codes[code]} and {failure_modes.index(fm)}"
            )
        else:
            seen_codes[code] = failure_modes.index(fm)
    return errors


# ==========================================
# 3. ASSEMBLY ENGINE
# ==========================================

def assemble(hierarchy: list, functions: list, effects_map: dict, metadata: dict) -> dict:
    """
    Assembles the final standardized_defect_codes JSON.

    Args:
        hierarchy: Validated hierarchy nodes (list of dicts with node_id, parent_id, name, level)
        functions: Validated functions (list of dicts with function_id, verb, noun, allocations)
        effects_map: Mapping of (function_id, category) tuples to reasoned effects
                     Each value has: reasoning_trace, end_effect, severity
        metadata: Product metadata dict (product_family, domain_standards, version)

    Returns:
        Complete standardized_defect_codes dict matching the v1 schema.
    """
    assembled_failure_modes = []

    # Track sequence counters per function_id for readable IDs
    seq_counter = {}

    for func in functions:
        function_id = func["function_id"]
        verb = func["verb"]
        noun = func["noun"]

        # Iterate through all 7 failure categories for this function
        for category in CATEGORY_ABBREV.keys():
            # Build the lookup key for this function-category pair
            lookup_key = f"{function_id}|{category}"

            # Check if we have a reasoned effect for this combination
            if lookup_key not in effects_map:
                continue  # Skip categories that weren't generated for this function

            effect_data = effects_map[lookup_key]

            # Generate deterministic IDs
            seq_counter.setdefault(function_id, 0)
            seq_counter[function_id] += 1

            failure_id = generate_failure_id(
                function_id, category, seq_counter[function_id]
            )
            defect_code = generate_defect_code(
                function_id, category, effect_data.get("syntactical_description", "")
            )

            assembled_failure_modes.append({
                "failure_id": failure_id,
                "function_id": function_id,
                "category": category,
                "syntactical_description": effect_data.get("syntactical_description", ""),
                "defect_code": defect_code,
                "end_effect": effect_data.get("end_effect", ""),
                "severity": effect_data.get("severity"),
            })

    return {
        "metadata": metadata,
        "hierarchy": hierarchy,
        "functions": functions,
        "failure_modes": assembled_failure_modes,
    }


# ==========================================
# 4. SCHEMA VALIDATION
# ==========================================

DEFAULT_SCHEMA_PATH = os.path.expanduser(
    "~/.gemini/antigravity/schemas/standardized_defect_codes_v1.json"
)


def validate_output(assembled_data: dict, schema_path: str) -> dict:
    """
    Validates the assembled output against the standardized_defect_codes_v1 schema.
    Returns a report dict.
    """
    report = {"is_valid": False, "errors": []}

    # Load schema
    try:
        with open(schema_path, "r") as f:
            schema = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        report["errors"].append(f"Schema load error: {e}")
        return report

    # Validate structure
    try:
        validate(instance=assembled_data, schema=schema)
    except ValidationError as e:
        report["errors"].append(f"Schema validation error: {e.message}")
        return report

    # Check for duplicate defect codes
    dup_errors = check_duplicates(assembled_data.get("failure_modes", []))
    if dup_errors:
        report["errors"].extend(dup_errors)
        return report

    report["is_valid"] = True
    return report


# ==========================================
# 5. CLI INTERFACE
# ==========================================

def main():
    parser = argparse.ArgumentParser(
        description="Phase 4: Assemble validated pipeline outputs into standardized defect codes JSON."
    )
    parser.add_argument("--hierarchy", required=True, help="Path to validated hierarchy JSON")
    parser.add_argument("--functions", required=True, help="Path to validated functions JSON")
    parser.add_argument("--effects", required=True, help="Path to reasoned effects JSON")
    parser.add_argument("--metadata", required=True, help="Product family name")
    parser.add_argument(
        "--schema", default=DEFAULT_SCHEMA_PATH,
        help="Path to output schema (default: global AntiGravity schema)"
    )
    parser.add_argument("--output", required=True, help="Path to write assembled output JSON")

    args = parser.parse_args()

    # --- Load inputs ---
    try:
        with open(args.hierarchy, "r") as f:
            hierarchy = json.load(f)
        with open(args.functions, "r") as f:
            functions = json.load(f)
        with open(args.effects, "r") as f:
            effects_raw = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading inputs: {e}")
        sys.exit(1)

    # --- Build effects map (keyed by "function_id|category") ---
    effects_map = {}
    if isinstance(effects_raw, list):
        for entry in effects_raw:
            key = f"{entry['function_id']}|{entry['category']}"
            effects_map[key] = entry
    elif isinstance(effects_raw, dict):
        effects_map = effects_raw

    # --- Build metadata ---
    metadata = {"product_family": args.metadata, "version": "1.0"}

    # --- Assemble ---
    assembled = assemble(hierarchy, functions, effects_map, metadata)

    # --- Validate ---
    report = validate_output(assembled, args.schema)

    if not report["is_valid"]:
        print("VALIDATION FAILED:")
        for err in report["errors"]:
            print(f"  - {err}")
        sys.exit(1)

    # --- Write output ---
    with open(args.output, "w") as f:
        json.dump(assembled, f, indent=2)

    fm_count = len(assembled["failure_modes"])
    print(f"SUCCESS: Assembled {fm_count} failure modes -> {args.output}")


if __name__ == "__main__":
    main()
