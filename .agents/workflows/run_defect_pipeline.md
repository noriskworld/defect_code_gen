---
description: Run the full Standardized Defect Codes generation pipeline with HITL gates
---

# Defect Code Generation Pipeline

Run this workflow to process a product manual through all 5 phases and produce a `standardized_defect_codes.json`.

## Prerequisites
- Input PDF in `inputs/` or a public URL for direct NotebookLM ingestion
- NotebookLM MCP server authenticated (`mcp_notebooklm_get_health`)
- Global venv: `~/.gemini/antigravity/.venv/bin/python`

---

## Phase 1: Ingestion & Grounding

1. **Primary path (URL):** If a public URL is available, use `mcp_notebooklm_ask_question` to ingest directly.
2. **Fallback (PDF extraction):**
   ```bash
   # // turbo
   ~/.gemini/antigravity/.venv/bin/python ~/.gemini/antigravity/skills/pdf_extraction/scripts/extract.py \
     "<absolute_path_to_pdf>" --output /tmp/extracted_product.md
   ```
3. Read the extracted Markdown and upload to NotebookLM if using fallback.
4. **System Architect role:** Query NotebookLM to draft the system hierarchy JSON:
   - Prompt: *"Extract the complete product hierarchy as JSON with fields: node_id, parent_id, name, level (System/Subsystem/Component), description."*
5. Save hierarchy to `/tmp/hierarchy.json`.

### 🚦 Gate 1 (HITL)
**Stop and present the hierarchy to the user for visual approval.** Do not proceed until confirmed.

---
## Phase 2: Functional Analysis (INCOSE)

6. **Initial Extraction**: For the product query NotebookLM:
   - Prompt: *"Extract the primary functional requirements for [product] from the documentation. Provide the raw text as found."*
7. **Function Analyst role (INCOSE Refinement)**:
   - Analyze each requirement against **INCOSE Guidelines**:
     - **Singularity**: Does it express only ONE capability? (Avoid "and/or").
     - **Verifiability**: Is it measurable/testable? (Remove "as far as possible", "high quality").
     - **Unambiguity**: Is it clear and interpretation-free? (Replace "immediately" with "within X ms").
   - **Rewrite**: Create a high-quality version of each failing requirement.
   - **Format**: Present a table with columns: `Req. ID`, `Original Requirement`, `Revised Requirement`, `Analysis Notes`.
8. Save refined functions to `/tmp/functions.json`.

### 🚦 Gate 2 (HITL)
**Present the Functional Requirements Table to the user for approval.**

---

## Phase 3: Draft Failure Mode Generation

9. **Reliability Engineer role**: For each *approved* functional requirement:
   - Derive a strict **[Verb] + [Noun]** pair (e.g., "Conduct Current").
   - Apply the 7 syntactical derivation rules to generate draft failure modes:
     1. **Total Loss of Function**: "Fails to [Verb] [Noun]"
     2. **Partial Loss of Function**: "Provides degraded [Verb] [Noun]"
     3. **Over-Function**: "Provides excessive [Verb] [Noun]"
     4. **Intermittent Function**: "Intermittently [Verb] [Noun]"
     5. **Degraded Function**: "[Verb] [Noun] outside specified limits"
     6. **Unintended/Spurious Function**: "[Verb] [Noun] without command"
     7. **Delayed/Early Function**: "[Verb] [Noun] too late/early"
   - Save drafts to `/tmp/draft_fm.json`.

---

## Phase 4: Deterministic Verification

10. **Run the JSON Validator skill:**
   ```bash
   ~/.gemini/antigravity/.venv/bin/python ~/.gemini/antigravity/skills/json_validator/scripts/validator.py \
     --input /tmp/draft_fm.json \
     --function-verb "<verb>" \
     --function-noun "<noun>"
   ```

### 🚦 Gate 3 (Auto-Retry, max 3 attempts)
- If exit code 1: read the error JSON, fix the specific failure mode, regenerate, and re-validate.
- If 3 failures: escalate to user (HITL).

---

## Phase 5: Taxonomy Enrichment

10. **Reliability Engineer role:** For each validated failure mode, use Chain-of-Thought reasoning to determine the system-level end effect.
11. **Run the Taxonomy Manager skill:**
   ```bash
   ~/.gemini/antigravity/.venv/bin/python ~/.gemini/antigravity/skills/taxonomy_manager/scripts/taxonomy_lookup.py \
     --effect "<proposed_end_effect>" \
     --severity <N>
   ```
10. If no match: re-prompt with the nearest candidates. If truly novel, use `--expand`.
11. Save enriched effects to `/tmp/effects.json`.

---

## Phase 6: Assembly & Export

12. **Run the Assembly script:**
    ```bash
    ~/.gemini/antigravity/.venv/bin/python scripts/phase4_assembly.py \
      --hierarchy /tmp/hierarchy.json \
      --functions /tmp/functions.json \
      --effects /tmp/effects.json \
      --metadata "<Product Family Name>" \
      --output outputs/standardized_defect_codes.json
    ```
13. If exit code 0: present the final JSON to the user.
14. If exit code 1: read the schema validation errors and fix inputs.

---

## Post-Pipeline

15. Clean up temp files: `rm /tmp/draft_fm.json /tmp/hierarchy.json /tmp/effects.json /tmp/functions.json`
16. Optionally export to Google Sheets using the Google Workspace skill.