# Work Instruction: Generating Standardized Defect Codes with AntiGravity

## Purpose
This document describes how to use AntiGravity to ingest a product datasheet (via URL or PDF) and generate a complete set of **Standardized Defect Codes** — including system hierarchy, functional basis, failure modes, and end effects.

---

## Prerequisites

| Requirement | How to verify |
|---|---|
| AntiGravity with global `.venv` | `~/.gemini/antigravity/.venv/bin/python --version` |
| NotebookLM MCP authenticated | Ask AntiGravity: *"Check NotebookLM health"* |
| Project cloned | `cd ~/Documents/code/defect_code_gen` |

---

## Step 1 — Provide the Source

Give AntiGravity the product documentation. Two options:

### Option A: Public URL (Preferred — fastest, no extraction needed)
```
I need to generate defect codes for this product:
https://cdn.automationdirect.com/static/specs/schneiderelectriceasytesys.pdf
```
AntiGravity will ingest the URL directly into NotebookLM as a grounded knowledge source.

### Option B: Local PDF (fallback)
```
I need to generate defect codes from this PDF:
/absolute/path/to/product_manual.pdf
```
AntiGravity will extract the PDF to Markdown, then ingest into NotebookLM.

---

## Step 2 — Review System Hierarchy (Gate 1)

AntiGravity will query NotebookLM to extract the product's structural breakdown:

```
System → Subsystem → Component
```

**You will be shown the hierarchy JSON for approval.** Check that:
- [ ] All major subsystems are captured
- [ ] Component names match the datasheet
- [ ] Parent-child relationships are correct
- [ ] Levels (System/Subsystem/Component) are assigned correctly

**Say "Approved" to proceed**, or provide corrections.

---

## Step 3 — Automatic Generation (Phases 2–4)

After hierarchy approval, AntiGravity runs the remaining pipeline automatically:

1. **Functional Basis** — extracts `[Verb] + [Noun]` pairs per component (e.g., *"transfer coolant"*)
2. **Failure Mode Derivation** — applies 7 syntactical rules per function:
   - Total Loss · Partial/Degraded · Intermittent · Unintended/Spurious · Delayed/Early · Inability to Stop · Erratic
3. **Regex Validation** — the `json_validator` skill checks every failure mode against strict syntax anchors
4. **End Effect Mapping** — each failure mode is traced to a system-level consequence from the master taxonomy
5. **Assembly** — deterministic IDs and defect codes are generated

> **Auto-retry:** If the validator catches a syntax error, AntiGravity automatically re-prompts and corrects (up to 3 attempts). You are only asked to intervene if it can't self-correct.

---

## Step 4 — Review the Output

The final output is a JSON file: `outputs/standardized_defect_codes.json`

It contains 4 sections:

| Section | Content |
|---|---|
| `metadata` | Product family name, standards, version |
| `hierarchy` | Approved system tree from Step 2 |
| `functions` | Verb-noun pairs with component allocations |
| `failure_modes` | Every generated failure with `failure_id`, `defect_code`, `end_effect`, and `severity` |

### Severity Scale
| Value | Meaning | Example |
|---|---|---|
| 10 | Safety — injury or death | Fire, high-energy release |
| 9 | Compliance — loss of certification | Emissions violation |
| 7 | Reliability — loss of main function | Complete shutdown |
| 4 | Performance — degraded function | Reduced capacity |
| 1 | Cosmetic — no performance impact | Discoloration |

---

## Quick-Start Command

You can trigger the full pipeline with the slash command:

```
/run_defect_pipeline
```

Or simply tell AntiGravity:

```
Generate standardized defect codes for this product: <URL or PDF path>
```

---

## Batch Mode — Processing Multiple Products

For processing multiple products at once, fill in the manifest table and let AntiGravity loop through them.

### 1. Edit the Manifest

Open `inputs/product_manifest.csv` and add one row per product:

```csv
product_name,url,domain_standards
Schneider EasyTeSys Contactors,https://cdn.automationdirect.com/static/specs/schneiderelectriceasytesys.pdf,"IEC 60947-4-1, UL 60947-4-1"
ABB Motor Starters,https://example.com/abb_starters.pdf,"IEC 60947-4-1"
Siemens SIRIUS Relays,https://example.com/sirius_relays.pdf,"IEC 60947-5-1, UL 508"
```

| Column | Required | Description |
|---|---|---|
| `product_name` | ✅ | Human-readable product name |
| `url` | ✅ | Public URL to the product datasheet (PDF or web page) |
| `domain_standards` | Optional | Comma-separated applicable standards |

### 2. Run the Batch Runner

```
Process all products in the manifest: inputs/product_manifest.csv
```

Or via terminal:
```bash
~/.gemini/antigravity/.venv/bin/python scripts/batch_runner.py \
  --manifest inputs/product_manifest.csv \
  --output-dir outputs/
```

### 3. Output Structure

Each product gets its own directory:

```
outputs/
├── batch_report.json                           ← master status tracker
├── schneider_easytesys_contactors/
│   └── standardized_defect_codes.json
├── abb_motor_starters/
│   └── standardized_defect_codes.json
└── siemens_sirius_relays/
    └── standardized_defect_codes.json
```

### 4. Gate 1 still applies per product
AntiGravity will pause for hierarchy approval on **each** product before proceeding. You review and approve each one individually.

---

## Troubleshooting

| Issue | Solution |
|---|---|
| NotebookLM not responding | Run: *"Check NotebookLM health"* → *"Re-authenticate NotebookLM"* |
| PDF extraction fails | Verify `tesseract-ocr` and `poppler-utils` are installed |
| Validator keeps failing | After 3 auto-retries, manually review the draft JSON in `/tmp/draft_fm.json` |
| Severity validation error | Only `{1, 4, 7, 9, 10}` are allowed — check end effects mapping |
| Batch manifest error | Check CSV has `product_name` and `url` columns, no empty rows |

---

## Example Sessions

### Single Product
```
You:    Generate defect codes for:
        https://cdn.automationdirect.com/static/specs/schneiderelectriceasytesys.pdf

Agent:  [Ingests into NotebookLM]
        [Extracts hierarchy — shows you the tree]
        "Here is the system hierarchy. Please review."

You:    Approved.

Agent:  [Generates failure modes → validates → maps effects → assembles]
        "Done. 42 failure modes generated across 6 components.
         Output saved to outputs/schneider_easytesys_contactors/standardized_defect_codes.json"
```

### Batch (Multiple Products)
```
You:    Process all products in the manifest: inputs/product_manifest.csv

Agent:  [Reads manifest — 3 products found]
        "Starting batch. Product 1/3: Schneider EasyTeSys Contactors"
        [Ingests → extracts hierarchy]
        "Here is the hierarchy for EasyTeSys Contactors. Please review."

You:    Approved.

Agent:  [Completes EasyTeSys → moves to Product 2/3]
        "Product 2/3: ABB Motor Starters"
        [Ingests → extracts hierarchy]
        "Here is the hierarchy for ABB Motor Starters. Please review."

You:    Approved.

Agent:  [Continues through all products...]
        "Batch complete. 3/3 products processed. See outputs/ for results."
```

