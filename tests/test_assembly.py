"""
Test Assembly: Unit tests for Phase 4 (assembly & export).
===========================================================
Validates deterministic ID generation, duplicate detection,
and schema compliance of the assembled output.
"""

import json
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from phase4_assembly import (
    generate_failure_id,
    generate_defect_code,
    check_duplicates,
    assemble,
    validate_output,
    CATEGORY_ABBREV,
)


# ==========================================
# FIXTURES
# ==========================================

@pytest.fixture
def sample_hierarchy():
    return [
        {"node_id": "SYS-001", "parent_id": None, "name": "EV Powertrain",
         "level": "System", "description": "Main powertrain system"},
        {"node_id": "SUB-001", "parent_id": "SYS-001", "name": "Thermal Management",
         "level": "Subsystem", "description": "Cooling subsystem"},
        {"node_id": "COMP-001", "parent_id": "SUB-001", "name": "Coolant Pump",
         "level": "Component", "description": "Circulates coolant"},
    ]


@pytest.fixture
def sample_functions():
    return [
        {
            "function_id": "FUNC-001",
            "verb": "transfer",
            "noun": "coolant",
            "allocations": [
                {"node_id": "COMP-001", "support_level": "Primary"}
            ]
        }
    ]


@pytest.fixture
def sample_effects_map():
    return {
        "FUNC-001|Total Loss of Function": {
            "syntactical_description": "Fails to transfer coolant.",
            "reasoning_trace": "Pump fails -> No coolant flow -> Overheating.",
            "end_effect": "Abrupt and unrecoverable cessation of the primary function during operation.",
            "severity": 7,
            "function_id": "FUNC-001",
            "category": "Total Loss of Function",
        },
        "FUNC-001|Intermittent Function": {
            "syntactical_description": "Intermittently transfers coolant.",
            "reasoning_trace": "Pump intermittently fails -> Unstable temperature.",
            "end_effect": "Product output is erratic, unstable, or of poor quality compared to specifications.",
            "severity": 4,
            "function_id": "FUNC-001",
            "category": "Intermittent Function",
        },
    }


@pytest.fixture
def sample_metadata():
    return {"product_family": "EV Powertrain", "version": "1.0"}


# ==========================================
# ID GENERATION TESTS
# ==========================================

class TestIDGeneration:
    """Tests for deterministic failure_id and defect_code generation."""

    def test_failure_id_format(self):
        """Failure ID should follow FAIL-{FUNC}-{CAT}-{SEQ} format."""
        fid = generate_failure_id("FUNC-001", "Total Loss of Function", 1)
        assert fid == "FAIL-001-TLF-01"

    def test_failure_id_sequences(self):
        """Different sequences produce different IDs."""
        fid1 = generate_failure_id("FUNC-001", "Total Loss of Function", 1)
        fid2 = generate_failure_id("FUNC-001", "Total Loss of Function", 2)
        assert fid1 != fid2

    def test_defect_code_deterministic(self):
        """Same inputs must always produce the same defect code."""
        dc1 = generate_defect_code("FUNC-001", "Total Loss of Function", "Fails to transfer coolant.")
        dc2 = generate_defect_code("FUNC-001", "Total Loss of Function", "Fails to transfer coolant.")
        assert dc1 == dc2

    def test_defect_code_unique(self):
        """Different inputs must produce different defect codes."""
        dc1 = generate_defect_code("FUNC-001", "Total Loss of Function", "Fails to transfer coolant.")
        dc2 = generate_defect_code("FUNC-001", "Intermittent Function", "Intermittently transfers coolant.")
        assert dc1 != dc2

    def test_defect_code_format(self):
        """Defect code should follow DC-{8hex} format."""
        dc = generate_defect_code("FUNC-001", "Total Loss of Function", "Fails to transfer coolant.")
        assert dc.startswith("DC-")
        assert len(dc) == 11  # "DC-" + 8 hex chars

    def test_all_category_abbreviations_exist(self):
        """Every failure mode category must have an abbreviation."""
        expected_categories = [
            "Total Loss of Function",
            "Partial / Degraded Function",
            "Intermittent Function",
            "Unintended / Spurious Function",
            "Delayed / Early Function",
            "Inability to Stop Function",
            "Erratic Function",
        ]
        for cat in expected_categories:
            assert cat in CATEGORY_ABBREV, f"Missing abbreviation for: {cat}"


# ==========================================
# DUPLICATE DETECTION TESTS
# ==========================================

class TestDuplicateDetection:
    """Tests for the duplicate defect_code checker."""

    def test_no_duplicates(self):
        """A list with unique codes should pass."""
        modes = [
            {"defect_code": "DC-aaaa0001"},
            {"defect_code": "DC-bbbb0002"},
        ]
        assert check_duplicates(modes) == []

    def test_duplicates_detected(self):
        """Duplicate defect codes should be flagged."""
        modes = [
            {"defect_code": "DC-aaaa0001"},
            {"defect_code": "DC-aaaa0001"},
        ]
        errors = check_duplicates(modes)
        assert len(errors) > 0
        assert "Duplicate" in errors[0]


# ==========================================
# ASSEMBLY INTEGRATION TESTS
# ==========================================

class TestAssembly:
    """Integration tests for the full assembly pipeline."""

    def test_assembly_produces_correct_structure(self, sample_hierarchy, sample_functions,
                                                  sample_effects_map, sample_metadata):
        """Assembled output must contain all required top-level keys."""
        result = assemble(sample_hierarchy, sample_functions, sample_effects_map, sample_metadata)
        assert "metadata" in result
        assert "hierarchy" in result
        assert "functions" in result
        assert "failure_modes" in result

    def test_assembly_failure_mode_count(self, sample_hierarchy, sample_functions,
                                         sample_effects_map, sample_metadata):
        """Should produce one failure mode per effects_map entry."""
        result = assemble(sample_hierarchy, sample_functions, sample_effects_map, sample_metadata)
        assert len(result["failure_modes"]) == 2  # Two entries in effects_map

    def test_assembly_no_duplicate_codes(self, sample_hierarchy, sample_functions,
                                          sample_effects_map, sample_metadata):
        """Assembled output should have zero duplicate defect codes."""
        result = assemble(sample_hierarchy, sample_functions, sample_effects_map, sample_metadata)
        codes = [fm["defect_code"] for fm in result["failure_modes"]]
        assert len(codes) == len(set(codes)), "Duplicate defect codes found!"

    def test_assembly_failure_modes_have_required_fields(self, sample_hierarchy, sample_functions,
                                                          sample_effects_map, sample_metadata):
        """Each failure mode must have all schema-required fields."""
        result = assemble(sample_hierarchy, sample_functions, sample_effects_map, sample_metadata)
        required = ["failure_id", "function_id", "category", "syntactical_description", "defect_code"]
        for fm in result["failure_modes"]:
            for field in required:
                assert field in fm, f"Missing required field: {field}"

    def test_schema_validation_passes(self, sample_hierarchy, sample_functions,
                                       sample_effects_map, sample_metadata):
        """Assembled output should pass validation against the v1 schema."""
        result = assemble(sample_hierarchy, sample_functions, sample_effects_map, sample_metadata)
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "schema", "standardized_defect_codes_v1.json"
        )
        if os.path.exists(schema_path):
            report = validate_output(result, schema_path)
            assert report["is_valid"] is True, f"Schema errors: {report['errors']}"
        else:
            pytest.skip("Schema file not found at global path")

    def test_empty_effects_map(self, sample_hierarchy, sample_functions, sample_metadata):
        """Empty effects map should produce zero failure modes (not crash)."""
        result = assemble(sample_hierarchy, sample_functions, {}, sample_metadata)
        assert len(result["failure_modes"]) == 0
