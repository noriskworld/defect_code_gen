# Work Instruction: Generating Standardized Defect Codes with AntiGravity

## Purpose
This document describes how to use AntiGravity to ingest a product datasheet and generate **Standardized Defect Codes** using project-local assets.

---

## Step 1 — Project Context
Ensure you are in the project directory:
```bash
cd /Users/yunweihu/Documents/code/defect_code_gen
```

All schemas and taxonomies are located in the `./schema/` directory for portability.

---

## Step 2 — Single Product Flow
Trigger the pipeline for a single URL:
```bash
# Example command to trigger the agent
Generate standardized defect codes for: https://example.com/product.pdf
```
AntiGravity will use the local `./schema/` files for validation and assembly.

---

## Step 3 — Batch Processing
1. Update `inputs/product_manifest.csv`.
2. Run the batch runner:
```bash
~/.gemini/antigravity/.venv/bin/python scripts/batch_runner.py \
  --manifest inputs/product_manifest.csv \
  --output-dir outputs/
```
3. Approve the hierarchy for each product when prompted.

---

## Output
Results are stored in `outputs/{product_name}/standardized_defect_codes.json`.
Check `outputs/batch_report.json` for the overall status of a batch run.
