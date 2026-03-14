import re
import json
from jsonschema import validate, ValidationError

# ==========================================
# 1. PHASE 1 JSON SCHEMA DEFINITION
# ==========================================
PHASE1_SCHEMA = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "category": {
        "type": "string",
        "enum": [
          "Total Loss of Function",
          "Partial / Degraded Function",
          "Intermittent Function",
          "Unintended / Spurious Function",
          "Delayed / Early Function",
          "Inability to Stop Function",
          "Erratic Function"
        ]
      },
      "syntactical_description": {"type": "string"}
    },
    "required": ["category", "syntactical_description"],
    "additionalProperties": False
  }
}

# ==========================================
# 2. DETERMINISTIC SCHEMA ANCHORS
# ==========================================
SCHEMA_ANCHORS = {
    "Total Loss of Function": r"^Fails to (?!cease)", 
    "Partial / Degraded Function": r"(insufficient|excessive|below threshold|above threshold|degraded)",
    "Intermittent Function": r"^Intermittently",
    "Unintended / Spurious Function": r"^Uncommanded|Spurious",
    "Delayed / Early Function": r"(too late|too early|delayed|early)",
    "Inability to Stop Function": r"^Fails to cease",
    "Erratic Function": r"(^Erratically|corrupted)"
}

def validate_draft_failure_modes(base_function, draft_failure_modes):
    """
    Validates the LLM's raw Phase 1 output.
    """
    report = {
        "structural_pass": False,
        "structural_error": None,
        "semantic_results": []
    }

    # ------------------------------------------
    # STAGE 1: Structural Validation
    # ------------------------------------------
    try:
        validate(instance=draft_failure_modes, schema=PHASE1_SCHEMA)
        report["structural_pass"] = True
    except ValidationError as e:
        report["structural_error"] = f"JSON Schema Error: {e.message}"
        return report # Abort immediately if the structure is broken

    # ------------------------------------------
    # STAGE 2: Semantic Validation (Regex & Context)
    # ------------------------------------------
    target_verb = base_function.get("verb", "").lower()
    target_noun = base_function.get("noun", "").lower()
    verb_root = target_verb.rstrip('s')

    for mode in draft_failure_modes:
        category = mode.get('category')
        text = mode.get('syntactical_description', '')
        
        # Check Regex Anchor
        pattern = SCHEMA_ANCHORS.get(category, "")
        regex_passed = bool(re.search(pattern, text, re.IGNORECASE))
        
        # Check Context Retention
        missing_context = []
        if target_noun and target_noun not in text.lower():
            missing_context.append(f"Missing Noun: '{target_noun}'")
        if verb_root and verb_root not in text.lower():
             missing_context.append(f"Missing Verb Root: '{verb_root}'")

        context_retained = len(missing_context) == 0

        report["semantic_results"].append({
            "category": category,
            "syntactical_description": text,
            "regex_passed": regex_passed,
            "context_retained": context_retained,
            "is_valid": regex_passed and context_retained,
            "errors": missing_context if not context_retained else []
        })

    return report

# ==========================================
# Example Execution / Test Cases
# ==========================================
if __name__ == "__main__":
    mock_function = {"verb": "transfer", "noun": "coolant"}

    # Mock Phase 1 LLM Output (Notice there are no failure_ids or defect_codes yet)
    mock_draft_output = [
        {
            "category": "Total Loss of Function",
            "syntactical_description": "Fails to transfer coolant."
        },
        {
            "category": "Partial / Degraded Function",
            "syntactical_description": "Provides insufficient pressure." # Missing noun 'coolant'
        },
        {
            # If the LLM tried to hallucinate a severity here, Stage 1 would catch it 
            # and reject the entire batch before regex even runs.
            "category": "Inability to Stop Function",
            "syntactical_description": "Does not stop transferring coolant." # Fails regex (needs 'Fails to cease')
        }
    ]

    results = validate_draft_failure_modes(mock_function, mock_draft_output)

    print("--- PHASE 1 VALIDATION REPORT ---")
    if not results["structural_pass"]:
        print(f"[FATAL ERROR] {results['structural_error']}")
        print("Action: Re-prompt LLM to fix JSON structure.")
    else:
        print("[PASSED] JSON Structure Validated. Checking Semantics...\n")
        for res in results["semantic_results"]:
            status = "PASSED" if res['is_valid'] else "FAILED"
            print(f"[{status}] {res['category']}: {res['syntactical_description']}")
            if not res['regex_passed']:
                print(f"   -> Error: Failed Schema Anchor Regex")
            if not res['context_retained']:
                print(f"   -> Error: Context Loss -> {', '.join(res['errors'])}")
            print("-" * 40)