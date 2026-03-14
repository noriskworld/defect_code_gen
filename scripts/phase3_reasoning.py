import json
from jsonschema import validate, ValidationError

# ==========================================
# 1. PHASE 3 JSON SCHEMA DEFINITION
# ==========================================
PHASE3_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "reasoning_trace": {"type": "string"},
        "end_effect": {"type": "string"},
        "severity": {"type": "integer", "enum": [1, 4, 7, 9, 10]}
    },
    "required": ["reasoning_trace", "end_effect", "severity"],
    "additionalProperties": False
}

# ==========================================
# 2. HIERARCHY TRAVERSAL LOGIC
# ==========================================
def get_node_lineage(hierarchy_data, target_node_id):
    """
    Traverses the hierarchy from the target component up to the top-level system.
    Returns a list of node names to give the LLM structural context.
    """
    lineage = []
    current_id = target_node_id
    
    # Create a quick lookup dictionary for faster traversal
    nodes_by_id = {node['node_id']: node for node in hierarchy_data}
    
    while current_id:
        node = nodes_by_id.get(current_id)
        if not node:
            break
        
        # Insert at the beginning so the final list reads Top-Down or Bottom-Up logically
        lineage.insert(0, f"{node['name']} ({node['level']})")
        current_id = node.get('parent_id') # Move up to the parent
        
    return " -> ".join(lineage)

# ==========================================
# 3. PROMPT GENERATION
# ==========================================
def build_fmea_prompt(failure_description, lineage_string, allowed_effects):
    """
    Constructs the exact prompt to send to the LLM for Phase 3.
    """
    effects_list = "\n".join([f"- {effect}" for effect in allowed_effects])
    
    prompt = f"""You are an expert Reliability Engineer performing an FMEA.
    
TASK:
1. Write a step-by-step causal chain explaining how the component failure propagates up the hierarchy to affect the end-user.
2. Select the single most appropriate system-level end effect from the ALLOWED EFFECTS taxonomy.
3. Assign a severity score (1-10).

CONTEXT:
- Failure Mode: "{failure_description}"
- System Hierarchy Path: {lineage_string}

ALLOWED EFFECTS (You MUST choose exactly one from this list):
{effects_list}

Respond ONLY with a valid JSON object matching the provided schema. Do not include markdown formatting like ```json.
"""
    return prompt

# ==========================================
# 4. PHASE 3 VALIDATION GUARDRAILS
# ==========================================
def validate_phase3_output(llm_response_json, allowed_effects):
    """
    Ensures the LLM output is structurally sound and adheres to the Master Taxonomy.
    """
    report = {
        "is_valid": False,
        "errors": [],
        "parsed_data": None
    }
    
    # 1. Parse JSON
    try:
        data = json.loads(llm_response_json)
        report["parsed_data"] = data
    except json.JSONDecodeError:
        report["errors"].append("LLM did not return valid JSON.")
        return report

    # 2. Structural Validation (jsonschema bounds checking for Severity 1-10)
    try:
        validate(instance=data, schema=PHASE3_SCHEMA)
    except ValidationError as e:
        report["errors"].append(f"Schema Error: {e.message}")
        return report

    # 3. Master Taxonomy Enforcement (Did the LLM hallucinate an effect?)
    selected_effect = data.get("end_effect")
    if selected_effect not in allowed_effects:
        report["errors"].append(f"Taxonomy Violation: '{selected_effect}' is not in the Master List.")
        return report

    report["is_valid"] = True
    return report

# ==========================================
# 5. EXAMPLE EXECUTION / TEST PIPELINE
# ==========================================
if __name__ == "__main__":
    # Mock Master Taxonomy of End Effects
    MASTER_TAXONOMY = [
        "Loss of Vehicle Propulsion",
        "Thermal Runaway",
        "Degraded Cabin Comfort",
        "No Noticeable Effect"
    ]

    # Mock Hierarchy from your schema
    mock_hierarchy = [
        {"node_id": "SYS-001", "parent_id": None, "name": "EV Powertrain", "level": "System"},
        {"node_id": "SUB-001", "parent_id": "SYS-001", "name": "Thermal Management", "level": "Subsystem"},
        {"node_id": "COMP-001", "parent_id": "SUB-001", "name": "Coolant Pump", "level": "Component"}
    ]

    # Mock Validated Failure Mode (coming from Phase 2)
    validated_failure = {
        "syntactical_description": "Fails to transfer coolant.",
        "node_id": "COMP-001" # Extracted from the function's allocations
    }

    # Step A: Build Context
    lineage = get_node_lineage(mock_hierarchy, validated_failure["node_id"])
    print(f"--- CONTEXT BUILT ---\nPath: {lineage}\n")

    # Step B: Generate Prompt
    prompt = build_fmea_prompt(validated_failure["syntactical_description"], lineage, MASTER_TAXONOMY)
    print(f"--- PROMPT FOR LLM ---\n{prompt}\n")

    # Step C: Mock LLM Responses
    # Good Response
    mock_llm_good = '{"reasoning_trace": "Coolant pump fails -> Thermal Management cannot cool inverter -> Inverter overheats and shuts down -> Powertrain loses power.", "end_effect": "Loss of Vehicle Propulsion", "severity": 8}'
    
    # Bad Response (Hallucinated Effect)
    mock_llm_bad = '{"reasoning_trace": "Pump fails, car gets hot.", "end_effect": "Car Overheats", "severity": 8}'

    # Step D: Validate
    print("--- VALIDATION RESULTS ---")
    
    good_result = validate_phase3_output(mock_llm_good, MASTER_TAXONOMY)
    print(f"Good Mock Validated? {good_result['is_valid']}")
    
    bad_result = validate_phase3_output(mock_llm_bad, MASTER_TAXONOMY)
    print(f"Bad Mock Validated? {bad_result['is_valid']}")
    print(f"Bad Mock Errors: {bad_result['errors']}")