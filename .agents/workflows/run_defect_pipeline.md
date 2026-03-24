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

## Phase 1: Ingestion & Multi-Source Collection

1. **Information Collection:** Gather technical data from three primary layers:
    - **Local PDF:** Ingest via `scripts/extract.py`.
    - **Web Search:** Search `se.com` for specific technical characteristics (Utilization categories, lifecycle).
    - **Flipbook Intelligence:** Use the `se-catalog-navigator` skill to extract hierarchy and functions from official flipbooks.
2. **Synthesize Technical Bundle:** Create a Markdown artifact (e.g., `technical_collection.md`) containing the synthesized raw data from all sources.
3. **NotebookLM Grounding:** If a public catalog URL is available, prefer adding it as a **"Website/URL"** source so NotebookLM can access the original document directly. Otherwise, use the `browser_subagent` (or MCP if `add_source` is available) to upload the synthesized Technical Bundle as a "Copied text" source.
4. **Hierarchy Extraction:** Query NotebookLM to draft the product hierarchy:
   - Prompt: *"Extract the complete product hierarchy with node_id, parent_id, name, level, and description."*
5. Save hierarchy to `/tmp/hierarchy.json` and [fmea_input_ready.md](file:///Users/yunweihu/Documents/code/defect_code_gen/docs/research/fmea_input_ready.md).

### 🚦 Gate 1 (HITL)
**Stop and present the hierarchy to the user for visual approval.** Do not proceed until confirmed.

---
## Phase 2: High-Fidelity Functional Analysis (INCOSE)

6. **Functional Elicitation**: Query NotebookLM using the grounded source:
   - Prompt: *"Review the technical collection and: 1. Identify primary functions. 2. Prepare 5 reliability elicitation questions to clarify system behavior."*
7. **INCOSE Refinement**:
   - Rewrite each function into the pattern: **[Condition][Subject][Action][Object][Constraint]**.
   - Ensure singular, verifiable, and unambiguous language (e.g., replace "effective" with specific timing/current limits).
8. **Output Generation**: Produce the `fmea_input_ready.md` with:
   - **Requirements Table**: Columns for `ID`, `Original Function`, `Short Desc`, and `Functional Requirement (INCOSE)`.
   - **Traceability Matrix**: Subsystem vs. Function mapping (Primary/Secondary).
9. Save refined functions to `/tmp/functions.json` and the final FMEA input report.

### 🚦 Gate 2 (HITL)
**Present the refined Requirements Table and Traceability Matrix to the user for approval.**

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