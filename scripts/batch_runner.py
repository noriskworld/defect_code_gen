"""
Batch Runner: Process multiple products from a CSV manifest.
=============================================================
Reads a product_manifest.csv and orchestrates the pipeline for each row.
Uses project-local paths for all assets.

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
from typing import List, Dict, Any


def sanitize_dirname(name: str) -> str:
    """Convert a product name into a safe directory name."""
    return re.sub(r'[^\w\-]', '_', name).strip('_').lower()


def load_manifest(path: str) -> List[Dict[str, Any]]:
    """Load and validate the product manifest CSV."""
    products = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Validate headers
        required = {'product_name', 'url'}
        if not required.issubset(set(reader.fieldnames or [])):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(f"Manifest missing required columns: {missing}")

        for i, row in enumerate(reader, start=2):
            name = row.get('product_name', '').strip()
            url = row.get('url', '').strip()

            if not name:
                continue
            if not url:
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


def generate_batch_report(products: List[Dict[str, Any]], output_dir: str) -> Dict[str, Any]:
    """Generate a batch processing report."""
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
    parser = argparse.ArgumentParser(description="Batch runner for the Defect Code pipeline.")
    parser.add_argument('--manifest', required=True, help='Path to CSV manifest')
    parser.add_argument('--output-dir', default='outputs/', help='Root directory for outputs')

    args = parser.parse_args()

    try:
        products = load_manifest(args.manifest)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if not products:
        print("ERROR: No valid products found.")
        sys.exit(1)

    # Use project-relative outputs dir
    report = generate_batch_report(products, args.output_dir)
    
    report_path = os.path.join(args.output_dir, 'batch_report.json')
    os.makedirs(args.output_dir, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"SUCCESS: Batch report saved to {report_path}")


if __name__ == '__main__':
    main()
