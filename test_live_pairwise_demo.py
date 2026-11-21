"""
CodeGuard - Live Pairwise Demo Verification (4-File Benchmark)
================================================================
Simulates 4 student uploads for Assignment 1:
 1. Original Bubble Sort
 2. Obfuscated Bubble Sort
 3. Unrelated Binary Search
 4. Complex Class-Based File Parser (Distinct domain & structure)

Checks database similarity_pairs table to verify pairwise comparison engine.
"""

import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.connection import SessionLocal
from backend.database import crud
from backend.database.models import SimilarityPair
from backend.services.analysis import AnalysisService
from datasets.obfuscated_pairs.obfuscator import generate_obfuscated_variants

def assign_risk_label(score: float) -> str:
    if score >= 0.86:
        return "[HIGH RISK - FLAGGED]"
    elif score >= 0.60:
        return "[MODERATE OVERLAP]"
    else:
        return "[LOW RISK - ORIGINAL]"

def run_pairwise_verification():
    db = SessionLocal()
    
    print("=== 1. Preparing Test Code Snippets ===")
    with open("datasets/obfuscated_pairs/solutions/bubble_sort.py", "r") as f:
        bubble_orig = f.read()
        
    variants = generate_obfuscated_variants(bubble_orig)
    bubble_obf = list(variants.values())[0] # Obfuscated variant
    
    with open("datasets/obfuscated_pairs/solutions/binary_search.py", "r") as f:
        binary_code = f.read()
        
    class_parser_code = r"""
import os
import json
import logging

class ConfigurationParser:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.settings = {}

    def load_config(self) -> dict:
        if not os.path.exists(self.config_path):
            self.logger.error(f"Config file not found: {self.config_path}")
            raise FileNotFoundError(f"Configuration file missing: {self.config_path}")
            
        with open(self.config_path, "r", encoding="utf-8") as fh:
            self.settings = json.load(fh)
        return self.settings

    def get_setting(self, key: str, default=None):
        return self.settings.get(key, default)

    def validate_schema(self, required_keys: list) -> bool:
        missing = [k for k in required_keys if k not in self.settings]
        if missing:
            self.logger.warning(f"Missing required config keys: {missing}")
            return False
        return True
"""
        
    print("Code snippets ready.")
    
    print("\n=== 2. Creating / Fetching Test Student Accounts ===")
    students = []
    for i in range(1, 5):
        uname = f"demo_student_{i}"
        user = crud.get_user_by_username(db, uname)
        if not user:
            user = crud.create_user(db, username=uname, email=f"{uname}@test.com", password_raw="password123", role="Student")
        students.append(user)
        
    print(f"Test students: {[s.username for s in students]}")
    
    print("\n=== 3. Uploading & Analyzing 4 Submissions for Assignment 1 ===")
    code_samples = [
        ("bubble_orig.py", bubble_orig),
        ("bubble_obf.py", bubble_obf),
        ("binary_search.py", binary_code),
        ("class_parser.py", class_parser_code)
    ]
    
    submissions = []
    for idx, (fname, code) in enumerate(code_samples):
        student = students[idx]
        sub = crud.create_submission(
            db=db,
            student_id=student.id,
            assignment_id=1,
            section_id=1,
            file_name=fname,
            language="python",
            raw_code=code
        )
        print(f"Created Submission {sub.submission_id} for {student.username} ({fname})")
        
        # Run analysis pipeline
        AnalysisService.analyze_submission(db, sub)
        print(f"  Analysis complete. Status: {sub.status}")
        submissions.append(sub)

    print("\n=== 4. Inspecting SQLite `similarity_pairs` Database Table ===")
    pairs = db.query(SimilarityPair).all()
    print(f"Total Similarity Pairs in DB: {len(pairs)}\n")
    
    print(f"{'Sub 1':<6} | {'Sub 2':<6} | {'Embedding Sim':<15} | {'Jaccard Sim':<12} | {'Fused Score':<12} | {'Risk Label':<30}")
    print("-" * 95)
    
    for p in pairs:
        label = assign_risk_label(p.fusion)
        print(f"{p.submission1:<6} | {p.submission2:<6} | {str(p.embedding):<15} | {str(p.jaccard):<12} | {str(p.fusion):<12} | {label:<30}")
        
    db.close()
    return pairs

if __name__ == "__main__":
    run_pairwise_verification()
