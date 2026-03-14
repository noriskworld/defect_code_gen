"""
Test Guardrails: Unit tests for Phase 1 (failure mode validation) and Phase 3 (effect reasoning).
=================================================================================================
Tests the deterministic Python guardrails against known-good and known-bad inputs,
as specified in plan.md Section 4 (TDD Layer).
"""

import json
import os
import sys
import pytest

# Add scripts directory to path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from phase1_validate_fm import validate_draft_failure_modes, PHASE1_SCHEMA, SCHEMA_ANCHORS
from phase3_reasoning import validate_phase3_output, get_node_lineage, build_fmea_prompt


# ==========================================
# PHASE 1 TESTS — Failure Mode Validation
# ==========================================

class TestPhase1StructuralValidation:
    """Stage 1: JSON Schema structural checks."""

    def test_known_good_passes(self):
        """Known Good: valid draft failure modes pass structural and semantic checks."""
        base_function = {"verb": "transfer", "noun": "coolant"}
        draft = [
            {
                "category": "Total Loss of Function",
                "syntactical_description": "Fails to transfer coolant."
            }
        ]
        result = validate_draft_failure_modes(base_function, draft)
        assert result["structural_pass"] is True
        assert result["semantic_results"][0]["is_valid"] is True

    def test_extra_property_rejected(self):
        """If the LLM hallucinated extra fields (e.g., severity), stage 1 should catch it."""
        base_function = {"verb": "transfer", "noun": "coolant"}
        draft = [
            {
                "category": "Total Loss of Function",
                "syntactical_description": "Fails to transfer coolant.",
                "severity": 7  # Not allowed in draft schema
            }
        ]
        result = validate_draft_failure_modes(base_function, draft)
        assert result["structural_pass"] is False
        assert "additional properties" in result["structural_error"].lower() or \
               "Additional properties" in result["structural_error"]

    def test_invalid_category_rejected(self):
        """Category must be one of the 7 allowed enum values."""
        base_function = {"verb": "transfer", "noun": "coolant"}
        draft = [
            {
                "category": "Made Up Category",
                "syntactical_description": "Fails to transfer coolant."
            }
        ]
        result = validate_draft_failure_modes(base_function, draft)
        assert result["structural_pass"] is False

    def test_missing_required_field_rejected(self):
        """Missing syntactical_description should fail structural check."""
        base_function = {"verb": "transfer", "noun": "coolant"}
        draft = [{"category": "Total Loss of Function"}]
        result = validate_draft_failure_modes(base_function, draft)
        assert result["structural_pass"] is False


class TestPhase1SemanticValidation:
    """Stage 2: Regex anchor and context retention checks."""

    def test_total_loss_correct_anchor(self):
        """'Fails to transfer coolant' must pass the Total Loss regex."""
        base_function = {"verb": "transfer", "noun": "coolant"}
        draft = [
            {
                "category": "Total Loss of Function",
                "syntactical_description": "Fails to transfer coolant."
            }
        ]
        result = validate_draft_failure_modes(base_function, draft)
        assert result["semantic_results"][0]["regex_passed"] is True

    def test_total_loss_wrong_anchor(self):
        """'Does not transfer coolant' must FAIL the Total Loss regex (plan.md TDD Step 1)."""
        base_function = {"verb": "transfer", "noun": "coolant"}
        draft = [
            {
                "category": "Total Loss of Function",
                "syntactical_description": "Does not transfer coolant."
            }
        ]
        result = validate_draft_failure_modes(base_function, draft)
        assert result["semantic_results"][0]["regex_passed"] is False

    def test_inability_to_stop_correct_anchor(self):
        """'Fails to cease transferring coolant' must pass Inability to Stop regex."""
        base_function = {"verb": "transfer", "noun": "coolant"}
        draft = [
            {
                "category": "Inability to Stop Function",
                "syntactical_description": "Fails to cease transferring coolant."
            }
        ]
        result = validate_draft_failure_modes(base_function, draft)
        assert result["semantic_results"][0]["regex_passed"] is True

    def test_inability_to_stop_wrong_anchor(self):
        """'Does not stop transferring coolant' must fail (needs 'Fails to cease')."""
        base_function = {"verb": "transfer", "noun": "coolant"}
        draft = [
            {
                "category": "Inability to Stop Function",
                "syntactical_description": "Does not stop transferring coolant."
            }
        ]
        result = validate_draft_failure_modes(base_function, draft)
        assert result["semantic_results"][0]["regex_passed"] is False

    def test_context_loss_missing_noun(self):
        """'Fails to move fluid' missing target noun 'coolant' (plan.md TDD Step 1)."""
        base_function = {"verb": "transfer", "noun": "coolant"}
        draft = [
            {
                "category": "Total Loss of Function",
                "syntactical_description": "Fails to move fluid."
            }
        ]
        result = validate_draft_failure_modes(base_function, draft)
        sem = result["semantic_results"][0]
        assert sem["context_retained"] is False
        assert any("Missing Noun" in e for e in sem["errors"])

    def test_context_loss_missing_verb(self):
        """Missing verb root should flag context loss."""
        base_function = {"verb": "transfer", "noun": "coolant"}
        draft = [
            {
                "category": "Partial / Degraded Function",
                "syntactical_description": "Provides insufficient coolant."
            }
        ]
        result = validate_draft_failure_modes(base_function, draft)
        sem = result["semantic_results"][0]
        assert sem["context_retained"] is False
        assert any("Missing Verb Root" in e for e in sem["errors"])

    def test_all_seven_categories_valid(self):
        """All 7 failure mode categories with correct syntax should pass."""
        base_function = {"verb": "transfer", "noun": "coolant"}
        draft = [
            {"category": "Total Loss of Function",
             "syntactical_description": "Fails to transfer coolant."},
            {"category": "Partial / Degraded Function",
             "syntactical_description": "Transfers insufficient coolant."},
            {"category": "Intermittent Function",
             "syntactical_description": "Intermittently transfers coolant."},
            {"category": "Unintended / Spurious Function",
             "syntactical_description": "Uncommanded transfer of coolant."},
            {"category": "Delayed / Early Function",
             "syntactical_description": "Transfers coolant too late."},
            {"category": "Inability to Stop Function",
             "syntactical_description": "Fails to cease transferring coolant."},
            {"category": "Erratic Function",
             "syntactical_description": "Erratically transfers coolant."},
        ]
        result = validate_draft_failure_modes(base_function, draft)
        assert result["structural_pass"] is True
        for sem in result["semantic_results"]:
            assert sem["regex_passed"] is True, \
                f"{sem['category']} failed regex: {sem['syntactical_description']}"


# ==========================================
# PHASE 3 TESTS — Effect Reasoning
# ==========================================

class TestPhase3Validation:
    """Tests for Phase 3 reasoning guardrails."""

    MASTER_TAXONOMY = [
        "Loss of Vehicle Propulsion",
        "Thermal Runaway",
        "Degraded Cabin Comfort",
        "No Noticeable Effect",
    ]

    def test_known_good_passes(self):
        """Valid JSON with an in-taxonomy effect should pass."""
        good_json = json.dumps({
            "reasoning_trace": "Pump fails -> System overheats -> Propulsion lost.",
            "end_effect": "Loss of Vehicle Propulsion",
            "severity": 7
        })
        result = validate_phase3_output(good_json, self.MASTER_TAXONOMY)
        assert result["is_valid"] is True

    def test_hallucinated_effect_rejected(self):
        """An effect not in the taxonomy must be rejected (plan.md TDD Step 1)."""
        bad_json = json.dumps({
            "reasoning_trace": "Pump fails, car gets hot.",
            "end_effect": "Car Overheats",  # Not in taxonomy
            "severity": 7
        })
        result = validate_phase3_output(bad_json, self.MASTER_TAXONOMY)
        assert result["is_valid"] is False
        assert any("Taxonomy Violation" in e for e in result["errors"])

    def test_severity_8_rejected(self):
        """Severity 8 must be rejected — only {1, 4, 7, 9, 10} allowed (plan.md TDD Step 1)."""
        bad_json = json.dumps({
            "reasoning_trace": "Pump fails -> System overheats.",
            "end_effect": "Thermal Runaway",
            "severity": 8  # Not in [1, 4, 7, 9, 10]
        })
        result = validate_phase3_output(bad_json, self.MASTER_TAXONOMY)
        assert result["is_valid"] is False
        assert any("Schema Error" in e for e in result["errors"])

    def test_severity_valid_values(self):
        """All allowed severity values should pass."""
        for sev in [1, 4, 7, 9, 10]:
            good_json = json.dumps({
                "reasoning_trace": "Test trace.",
                "end_effect": "No Noticeable Effect",
                "severity": sev
            })
            result = validate_phase3_output(good_json, self.MASTER_TAXONOMY)
            assert result["is_valid"] is True, f"Severity {sev} should pass"

    def test_invalid_json_rejected(self):
        """Non-JSON string should be caught."""
        result = validate_phase3_output("this is not json", self.MASTER_TAXONOMY)
        assert result["is_valid"] is False
        assert any("valid JSON" in e for e in result["errors"])


class TestPhase3HierarchyTraversal:
    """Tests for the hierarchy traversal utility."""

    MOCK_HIERARCHY = [
        {"node_id": "SYS-001", "parent_id": None, "name": "EV Powertrain", "level": "System"},
        {"node_id": "SUB-001", "parent_id": "SYS-001", "name": "Thermal Management", "level": "Subsystem"},
        {"node_id": "COMP-001", "parent_id": "SUB-001", "name": "Coolant Pump", "level": "Component"},
    ]

    def test_full_lineage(self):
        """Should produce a full path from root to target."""
        lineage = get_node_lineage(self.MOCK_HIERARCHY, "COMP-001")
        assert "EV Powertrain" in lineage
        assert "Thermal Management" in lineage
        assert "Coolant Pump" in lineage

    def test_root_node_lineage(self):
        """Root node should produce a single-item lineage."""
        lineage = get_node_lineage(self.MOCK_HIERARCHY, "SYS-001")
        assert "EV Powertrain" in lineage
        assert "->" not in lineage  # Only one node

    def test_nonexistent_node(self):
        """Nonexistent node should return empty."""
        lineage = get_node_lineage(self.MOCK_HIERARCHY, "FAKE-999")
        assert lineage == ""
