"""
CodeGuard - Plagiarism Pair Dataset Builder
=============================================
Reads a folder of original Python solutions (one function/problem per file)
and generates a labeled CSV of plagiarism pairs:

  original_id, original_code, variant_code, technique, label

label = 1 means "variant_code is a disguised copy of original_code"
       (all rows here are label=1 -- you'll separately add label=0 pairs
        by pairing DIFFERENT problems' solutions together, see bottom)

Usage:
    python build_dataset.py --input_dir ./solutions --output pairs.csv
"""

import argparse
import csv
import glob
import os
import random
from obfuscator import generate_obfuscated_variants, generate_combined_obfuscation


def load_solutions(input_dir):
    """Each .py file in input_dir is treated as one original solution."""
    files = sorted(glob.glob(os.path.join(input_dir, "*.py")))
    solutions = {}
    for f in files:
        with open(f, "r") as fh:
            code = fh.read()
        solutions[os.path.basename(f)] = code
    return solutions


def build_positive_pairs(solutions):
    """label=1 pairs: original vs each obfuscated variant, plus one
    'combined' (all techniques stacked) variant per solution."""
    rows = []
    for fname, code in solutions.items():
        try:
            variants = generate_obfuscated_variants(code)
        except ValueError as e:
            print(f"  [skip {fname}] {e}")
            continue

        for technique, variant_code in variants.items():
            rows.append({
                "original_id": fname,
                "original_code": code,
                "variant_code": variant_code,
                "technique": technique,
                "label": 1,
            })

        # Compounded obfuscation variant (hardest case - your novelty experiment)
        try:
            combined = generate_combined_obfuscation(code)
            rows.append({
                "original_id": fname,
                "original_code": code,
                "variant_code": combined,
                "technique": "combined_all",
                "label": 1,
            })
        except Exception as e:
            print(f"  [combined skip {fname}] {e}")
    return rows


def build_negative_pairs(solutions, n_per_solution=2):
    """label=0 pairs: pair each solution with unrelated OTHER solutions,
    so the model also learns what 'genuinely different code' looks like."""
    rows = []
    names = list(solutions.keys())
    if len(names) < 2:
        print("  [warning] Need at least 2 distinct solutions to build negative pairs.")
        return rows

    for fname, code in solutions.items():
        others = [n for n in names if n != fname]
        sample_size = min(n_per_solution, len(others))
        for other in random.sample(others, sample_size):
            rows.append({
                "original_id": fname,
                "original_code": code,
                "variant_code": solutions[other],
                "technique": "unrelated_solution",
                "label": 0,
            })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", required=True,
                         help="Folder containing .py files, one solution per file")
    parser.add_argument("--output", default="pairs.csv")
    args = parser.parse_args()

    solutions = load_solutions(args.input_dir)
    print(f"Loaded {len(solutions)} solution files from {args.input_dir}")

    if not solutions:
        print("No .py files found. Add solution files to the input directory first.")
        return

    pos_rows = build_positive_pairs(solutions)
    neg_rows = build_negative_pairs(solutions)
    all_rows = pos_rows + neg_rows
    random.shuffle(all_rows)

    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "original_id", "original_code", "variant_code", "technique", "label"
        ])
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nDone. Wrote {len(all_rows)} labeled pairs to {args.output}")
    print(f"  Positive (plagiarism) pairs: {len(pos_rows)}")
    print(f"  Negative (unrelated) pairs:  {len(neg_rows)}")


if __name__ == "__main__":
    main()
