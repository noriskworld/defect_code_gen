# AntiGravity Standardized Defect Codes Generation Pipeline: Implementation Plan
## 1. Executive Summary & Core Objective
The primary objective of this project is to leverage the advanced reasoning capabilities of Large Language Models (LLMs), specifically integrating NotebookLM, to autonomously infer system architecture and physical functions directly from unstructured product manuals and datasheets.
Once the functional baseline is established, the system will algorithmically generate all potential failure modes based on strict syntactical rules. The AI will then infer the system-level end effects of these failures by linking each to a single existing entry in a provided, standardized end_effects.json table. The LLM is permitted to expand this table with novel end effects only if absolutely necessary (enforcing a high threshold for taxonomy expansion).
The final output is a comprehensive, structured list of Standardized Defect Codes. These codes will serve as the foundational data layer used to classify real-world field failures, improve reporting quality, and proactively drive downstream Failure Mode and Effects Analysis (FMEA) for entire product families.
Scope Boundary: In the scope of this project, only the generation of the standardized defect codes, system hierarchy, and their mapping to failure modes and end effects is covered. The execution of a full FMEA process and the visual mapping/visualization of this analysis are strictly out of scope and will be developed as separate modules.
## 2. Architectural Overview
This system utilizes a Hybrid Agentic-Deterministic Architecture. AntiGravity LLM agents handle probabilistic reasoning (reading manuals, defining functions), while global Python skills (Tools) act as impenetrable deterministic guardrails (schema validation, ID generation, regex syntax enforcement).
The Agent Roster
The Orchestrator: Manages the user interface, session state, and routes tasks between sub-agents. Enforces human-in-the-loop (HITL) gates.
The System Architect: Extracts the Bill of Materials (BOM) and system hierarchy from ingested documentation.
The Reliability Engineer: Translates component purposes into strict Verb-Noun pairs, applies 7 algorithmic syntactical derivations for failure modes, and maps consequences to the End Effects taxonomy.
The Integration Analyst: Cross-references components to functions (L-Matrix) and generates final structured datasets.
## 3. The Execution Pipeline
### Phase 1: Ingestion & Grounding
Action: User provides URLs or uploads PDFs to the Orchestrator.
Primary Grounding (Direct URL): To save processing time and tokens, the Orchestrator prioritizes passing provided URLs directly into the NotebookLM_API_Skill to populate the hallucination-free workspace.
Fallback Extraction: If a URL fails to ingest natively into NotebookLM, or if the user uploads a local raw PDF, the Orchestrator calls PDF_Extraction_Skill (using pdfplumber/OCR) to convert documents to clean Markdown, which is then passed to NotebookLM.
Extraction: The System Architect queries NotebookLM to draft the hierarchy JSON.
Gate 1 (HITL): Orchestrator pauses. User visually approves the System Hierarchy.
### Phase 2: Draft Generation (Functional Basis)
Action: The Reliability Engineer iterates through the approved hierarchy.
Reasoning: Queries NotebookLM for component parameters to establish the strict [Verb] + [Noun] function.
Algorithmic Derivation: Applies the 7 syntax rules (e.g., Total Loss, Partial, Intermittent) to generate draft failure modes.
### Phase 3: Deterministic Verification (The Guardrails)
Action: Before Phase 2 is accepted, the Orchestrator passes the draft to JSON_Validator_Skill (Python).
Structural Check: Enforces a flat JSON structure and validates that the category enum perfectly matches one of the 7 allowed variants.
Semantic Check: Runs Regex to ensure exact syntactical anchors (e.g., ^Fails to (?!cease) for Total Loss).
Gate 2 (Auto-Retry): If the Python script detects a violation, it returns a precise string (e.g., "Error: Expected anchor 'Fails to'."). The Orchestrator automatically re-prompts the Reliability Engineer to correct it.
### Phase 4: Taxonomy Enrichment
Action: The Reliability Engineer assigns End Effects and Severities using Chain-of-Thought reasoning.
Tool Execution: Queries Taxonomy_Manager_Skill to link the failure mode to a single, existing semantic match in the provided end_effects.json.
Taxonomy Expansion (High Threshold): The AI is permitted to expand the taxonomy with a novel effect (tagged "origin": "AI_GENERATED") only if a strict high threshold is met—meaning no existing effect accurately describes the customer-facing consequence.
Validation: Python validates that the severity is strictly 1, 4, 7, 9, or 10.
### Phase 5: Assembly & Export
Action: The Integration Analyst maps the component-function L-Matrix.
Tool Execution: MBSE_Assembler_Skill uses Python hashing to generate deterministic, duplicate-free failure_id and defect_code strings.
Export: Pipeline outputs the verified standardized_defect_codes.json in its final structured format and optionally generates a Google Sheet.
## 4. The Test-Driven Development (TDD) Layer
Because LLMs are non-deterministic, TDD focuses strictly on the Python Guardrails (Tools). We treat the LLM as an "untrusted external sensor."
### Step 1: Unit Testing Guardrails (pytest)
Write a test_guardrails.py suite targeting the JSON_Validator_Skill and Taxonomy_Manager_Skill Python scripts.
Known Good: Feed perfect JSONs. Assert is_valid == True.
Known Bad (Regex): Feed "Does not transfer coolant". Assert it fails the Total Loss regex and returns the correct LLM-readable error string.
Known Bad (Context): Feed "Fails to move fluid" (missing the target noun). Assert it fails context retention.
Known Bad (Taxonomy): Feed an effect with severity: 8. Assert it throws a ValidationError.
### Step 2: Skill Integration Testing (Auto-Retry)
Manually feed a "Known Bad" response into the AntiGravity chat to test how the Orchestrator handles the Python error string.
Ensure the Orchestrator reads the error, self-corrects, and successfully passes the gate on the second attempt.
### Step 3: The Golden Dataset (Reasoning Evaluation)
Create a manual baseline of 10 complex functions mapped to End Effects.
Run the live agent pipeline. Use semantic similarity scoring (cosine similarity) to ensure the AI's End Effect mapping matches human engineering judgment .
### Step 4: Dry-Run Production
Run the pipeline on a single subsystem (e.g., EV Cooling Circuit). Import the output into a database or graphing tool and manually verify node linkages.
## 5. Step-by-Step Implementation Instructions
Follow these exact steps in your terminal to build the system within AntiGravity.
### Step 1: Secure the Repository
Initialize Git and establish the critical .gitignore to prevent leaking LLM memory or API keys.
```
cd ~/.gemini
git init
```

Create `~/.gemini/.gitignore` and include rules to block `/tmp/`, `cache/`, `*.log`, `state.json`, `antigravity/.venv/`, and `.env`.

### Step 2: Create the Master Virtual Environment
Establish the single, global Python environment that all AntiGravity skills will share.
uv venv ~/.gemini/antigravity/.venv
uv pip install --python ~/.gemini/antigravity/.venv/bin/python pdfplumber pymupdf pytesseract pdf2image jsonschema pytest pandas

### Step 3: Data Foundation
Place the master taxonomy in `schema/end_effects_library.json`.
Place the output schema in `schema/standardized_defect_codes_v1.json`.

### Step 4: Build the Deterministic Python Scripts (Tools)

Find or Create directories for your skills.

```
mkdir -p ~/.gemini/antigravity/skills/pdf_extraction/scripts
mkdir -p ~/.gemini/antigravity/skills/json_validator/scripts
mkdir -p ~/.gemini/antigravity/skills/taxonomy_manager/scripts
```

Write `extract.py` (incorporating argparse for --output).
Write `validator.py` (incorporating Regex syntax checks and jsonschema).

### Step 5: Execute the TDD Suite
Create a `tests/ directory` at the root.
Write `test_guardrails.py`.
Run `~/.gemini/antigravity/.venv/bin/python -m pytest tests/` and ensure all "Known Bad" tests successfully catch errors.

### Step 6: Bind Scripts to AntiGravity (SKILL.md)
For each skill directory, create a SKILL.md file.
Define the exact terminal command the agent must use (pointing to the global .venv).
Instruct the agent on how to read the output and what to do if the script returns an error string.

### Step 7: Configure the Agents  
Define the Orchestrator, System Architect, Reliability Engineer, and Integration Analyst prompts within your AntiGravity configuration (e.g., GEMINI.md or session templates).
Enforce Rule 1: Absolute Traceability.
Enforce Rule 2: Strict Linguistic Compliance.

### Step 8: The Dry Run
Start an AntiGravity session. Provide a URL for a simple component (e.g., a standard industrial pump). Monitor the terminal and agent thought process to verify it hits Gate 1, applies NotebookLM grounding, passes the Regex Python validators, and outputs a compliant JSON.
