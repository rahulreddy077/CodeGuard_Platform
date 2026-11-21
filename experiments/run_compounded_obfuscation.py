"""
CodeGuard - Task B: Compounded Obfuscation Experiment
======================================================
Tests detection robustness under stacked obfuscations:
 1. Reads baseline AI-generated solution files from datasets/obfuscated_pairs/ai_generated/
 2. Applies generate_combined_obfuscation() (stacked variable renaming, loop modification, comment stripping)
 3. Measures detection scores before and after compounded obfuscation.
 4. Outputs results & performance degradation delta to results/compounded_obfuscation.csv.
"""

import os
import glob
import sys
import pandas as pd
import numpy as np

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datasets.obfuscated_pairs.obfuscator import generate_combined_obfuscation
from modules.ast.parser import parse_code
from modules.ast.fingerprint import generate_fingerprint
from backend.services.similarity import SimilarityService

def get_structural_similarity(code1: str, code2: str) -> float:
    try:
        ast1 = parse_code(code1)
        ast2 = parse_code(code2)
        fp1 = generate_fingerprint(ast1)
        fp2 = generate_fingerprint(ast2)
        return SimilarityService.calculate_jaccard_similarity(fp1, fp2)
    except Exception:
        return 0.0

def run_compounded_obfuscation():
    ai_dir = os.path.join("datasets", "obfuscated_pairs", "ai_generated")
    sol_dir = os.path.join("datasets", "obfuscated_pairs", "solutions")
    
    ai_files = sorted(glob.glob(os.path.join(ai_dir, "*.py")))
    print(f"Loaded {len(ai_files)} AI-generated files from {ai_dir}...")

    records = []
    
    for ai_path in ai_files:
        base_name = os.path.basename(ai_path)
        sol_path = os.path.join(sol_dir, base_name)
        
        if not os.path.exists(sol_path):
            continue
            
        with open(sol_path, "r", encoding="utf-8") as f:
            orig_code = f.read()
            
        with open(ai_path, "r", encoding="utf-8") as f:
            ai_code = f.read()
            
        # Baseline AST similarity
        base_sim = get_structural_similarity(orig_code, ai_code)
        
        # Apply compounded obfuscation
        try:
            compounded_code = generate_combined_obfuscation(ai_code)
            compounded_sim = get_structural_similarity(orig_code, compounded_code)
            status = "Success"
        except Exception as e:
            compounded_sim = 0.0
            status = f"Failed: {str(e)}"
            
        records.append({
            "File": base_name,
            "Baseline AST Sim": round(base_sim, 4),
            "Compounded AST Sim": round(compounded_sim, 4),
            "Delta": round(compounded_sim - base_sim, 4),
            "Status": status
        })

    df = pd.DataFrame(records)
    
    print("\n=======================================================")
    print("      COMPOUNDED OBFUSCATION EXPERIMENT RESULTS        ")
    print("=======================================================")
    print(df.to_string(index=False))
    
    avg_base = df["Baseline AST Sim"].mean()
    avg_comp = df["Compounded AST Sim"].mean()
    avg_delta = df["Delta"].mean()
    
    print(f"\nAverage Baseline Structural Similarity:   {avg_base:.4f}")
    print(f"Average Compounded Structural Similarity: {avg_comp:.4f}")
    print(f"Average Performance Delta:                {avg_delta:.4f}")

    os.makedirs("results", exist_ok=True)
    out_csv = os.path.join("results", "compounded_obfuscation.csv")
    df.to_csv(out_csv, index=False)
    print(f"\nResults saved to {out_csv}")
    return df

if __name__ == "__main__":
    run_compounded_obfuscation()
