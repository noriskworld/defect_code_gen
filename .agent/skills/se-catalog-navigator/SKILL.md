---
name: SE Catalog Navigator
description: A workspace-specific skill to navigate the Schneider Electric catalog and extract Technical Characteristics for FMEA analysis via the flipbook intelligence workflow.
---

# SE Catalog Navigator Skill

## Purpose
Activate this skill when the user asks for technical specs, standards, or "SE data" for any component (e.g., "Easy TeSys"). This skill provides authoritative data (System, Functions, Standards) from the Schneider flipbook to support FMEA risk assessments.

## Tools
- **Node.js Flipbook Script:** Uses `npm run flipbook:check` (located at `tools/flipbook-check.js`).

## Execution Steps

### 1. Extract Data
Depending on the user's input (product name or specific page numbers), run the appropriate command. 

**If you have a product name:**
```bash
npm run flipbook:check -- --product "<product_name>"
```
*Example: `npm run flipbook:check -- --product "easy tesys"`*

**If you only have page numbers:**
```bash
npm run flipbook:check -- --pages "<page_list>"
```

### 2. Format for FMEA
The script extracts the product section, function/use-case wording, standards references (IEC, NF, EN, ISO), and the system/subsystem hierarchy.

From the output, perform the following FMEA-specific mapping:
- **System:** The product name and its inferred hierarchy / section.
- **Sub-functions:** The function or use-case wording detected from the snippets.
- **Standards:** The extracted standards (e.g., IEC/EN).
- **Potential Failure Modes:** Suggest 3 potential failure modes based on the extracted functions (e.g., if a function is "overload protection", a failure mode is "fails to trip on overload").

### 3. Save Artifacts
Save this final structured analysis in `docs/research/fmea_input.md` or a similarly appropriate research document, and notify the user.

## Configuration & Notes
- Use `--no-ocr` to disable OCR if the snippets are sufficient.
- Add `--json` for structured JSON output if you require it for automated script chaining.
- Evaluate the confidence guidelines: High confidence means standards/functions appear clearly in search snippets; Low confidence requires more manual review of the OCR text.
