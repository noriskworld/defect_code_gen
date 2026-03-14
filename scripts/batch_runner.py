"""
Batch Runner: Process multiple products from a CSV manifest.
=============================================================
Reads a product_manifest.csv and orchestrates the pipeline for each row.

Usage:
  ~/.gemini/antigravity/.venv/bin/python scripts/batch_runner.py \
    --manifest inputs/product_manifest.csv \
    --output-dir outputs/

CSV Format:
  product_name,url,domain_standards
  "Schneider EasyTeSys","https://example.com/spec.pdf","IEC 60947, UL 508"

Each row produces:
  outputs/{sanitized_product_name}/standardized_defect_codes.json
"""

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone


def sanitize_dirname(name: str) -> str:
    """Convert a product name into a safe directory name."""
    return re.sub(r'[^\w\-]', '_', name).strip('_').lower()


def load_manifest(path: str) -> list[dict]:
    """Load and validate the product manifest CSV."""
    products = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Validate headers
        required = {'product_name', 'url'}
        if not required.issubset(set(reader.fieldnames or [])):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(f"Manifest missing required columns: {missing}")

        for i, row in enumerate(reader, start=2):  # start=2 because row 1 is header
            name = row.get('product_name', '').strip()
            url = row.get('url', '').strip()

            if not name:
                print(f"WARNING: Row {i} has empty product_name, skipping.")
                continue
            if not url:
                print(f"WARNING: Row {i} '{name}' has empty URL, skipping.")
                continue

            products.append({
                'product_name': name,
                'url': url,
                'domain_standards': [
                    s.strip() for s in row.get('domain_standards', '').split(',') if s.strip()
                ],
                'row_number': i,
            })

    return products


def generate_batch_report(products: list[dict], output_dir: str) -> dict:
    """
    Generate a batch processing report.
    This is the manifest that the agent reads to know what to process.
    """
    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total_products': len(products),
        'output_directory': os.path.abspath(output_dir),
        'products': []
    }

    for product in products:
        dirname = sanitize_dirname(product['product_name'])
        product_output_dir = os.path.join(output_dir, dirname)
        os.makedirs(product_output_dir, exist_ok=True)

        report['products'].append({
            'product_name': product['product_name'],
            'url': product['url'],
            'domain_standards': product['domain_standards'],
            'output_dir': product_output_dir,
            'output_file': os.path.join(product_output_dir, 'standardized_defect_codes.json'),
            'status': 'pending',
        })

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Prepare batch processing from a product manifest CSV."
    )
    parser.add_argument(
        '--manifest', required=True,
        help='Path to product_manifest.csv'
    )
    parser.add_argument(
        '--output-dir', default='outputs/',
        help='Root directory for all outputs (default: outputs/)'
    )

    args = parser.parse_args()

    # Load manifest
    try:
        products = load_manifest(args.manifest)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if not products:
        print("ERROR: No valid products found in manifest.")
        sys.exit(1)

    print(f"Loaded {len(products)} product(s) from manifest.")

    # Generate batch report
    report = generate_batch_report(products, args.output_dir)

    # Save the report for the agent to read
    report_path = os.path.join(args.output_dir, 'batch_report.json')
    os.makedirs(args.output_dir, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"SUCCESS: Batch report saved to {report_path}")
    print(f"\n--- BATCH MANIFEST ---")
    for p in report['products']:
        print(f"  [{p['status'].upper()}] {p['product_name']}")
        print(f"           URL: {p['url']}")
        print(f"        Output: {p['output_file']}")
        print()


if __name__ == '__main__':
    main()
