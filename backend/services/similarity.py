import json
import math
import logging
from sqlalchemy.orm import Session
from backend.database.models import Submission, SimilarityPair
from backend.config import SIMILARITY_CONFIG

logger = logging.getLogger(__name__)

class SimilarityService:
    @staticmethod
    def calculate_cosine_similarity(vec1: list, vec2: list) -> float:
        """
        Calculates cosine similarity between two float vectors.
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = math.sqrt(sum(a * a for a in vec1))
        norm_b = math.sqrt(sum(b * b for b in vec2))
        
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
            
        return round(dot_product / (norm_a * norm_b), 4)

    @staticmethod
    def calculate_jaccard_similarity(str1: str, str2: str) -> float:
        """
        Calculates Jaccard similarity of word sets between two fingerprint strings.
        """
        if not str1 or not str2:
            return 0.0
            
        set1 = set(str1.split())
        set2 = set(str2.split())
        
        if not set1 or not set2:
            return 0.0
            
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        return round(len(intersection) / len(union), 4)

    @classmethod
    def compute_structural_similarity(cls, code1: str, code2: str) -> float:
        """
        Reference implementation of structural similarity:
        parses Python code to AST, normalizes the AST via normalize_ast() (docstrings removed,
        variables normalized), extracts structural fingerprint with exclude_context=True,
        and computes Jaccard similarity.
        """
        if not code1 or not code2 or not code1.strip() or not code2.strip():
            return 0.0
        try:
            from modules.ast import parse_code, normalize_ast, generate_fingerprint
            tree1 = normalize_ast(parse_code(code1, language="python"))
            tree2 = normalize_ast(parse_code(code2, language="python"))
            fp1 = generate_fingerprint(tree1, exclude_context=True, language="python")
            fp2 = generate_fingerprint(tree2, exclude_context=True, language="python")
            return cls.calculate_jaccard_similarity(fp1, fp2)
        except Exception as e:
            logger.warning(f"Structural similarity calculation error: {e}")
            return 0.0

    @classmethod
    def compare_submissions(cls, db: Session, sub1: Submission, sub2: Submission) -> SimilarityPair:
        """
        Compares two submissions: computes embedding cosine similarity, fingerprint Jaccard,
        and saves/updates the SimilarityPair record. Submissions MUST belong to the same assignment.
        """
        if sub1.student_id == sub2.student_id:
            logger.error(
                f"Self-comparison similarity rejected: "
                f"Sub #{sub1.submission_id} vs Sub #{sub2.submission_id} (both student #{sub1.student_id})"
            )
            raise ValueError(
                f"Self-comparison similarity rejected: "
                f"Sub #{sub1.submission_id} vs Sub #{sub2.submission_id} belong to the same student #{sub1.student_id}"
            )

        if sub1.assignment_id != sub2.assignment_id:
            logger.error(
                f"Cross-assignment similarity comparison rejected: "
                f"Sub #{sub1.submission_id} (Assignment {sub1.assignment_id}) vs "
                f"Sub #{sub2.submission_id} (Assignment {sub2.assignment_id})"
            )
            raise ValueError(
                f"Cross-assignment similarity comparison rejected: "
                f"Sub #{sub1.submission_id} (Assignment {sub1.assignment_id}) vs "
                f"Sub #{sub2.submission_id} (Assignment {sub2.assignment_id})"
            )

        logger.info(f"Comparing submission {sub1.submission_id} and {sub2.submission_id} (Assignment #{sub1.assignment_id})")
        
        # 1. Cosine similarity of GraphCodeBERT embeddings
        emb_sim = 0.0
        vec1_str = sub1.embedding.embedding_vector if sub1.embedding else None
        vec2_str = sub2.embedding.embedding_vector if sub2.embedding else None
        if vec1_str and vec2_str:
            try:
                vec1 = json.loads(vec1_str)
                vec2 = json.loads(vec2_str)
                emb_sim = cls.calculate_cosine_similarity(vec1, vec2)
            except Exception as e:
                logger.error(f"Error parsing embeddings for similarity: {str(e)}")
        
        # 2. Fingerprint Jaccard similarity
        jaccard_sim = 0.0
        fp1 = sub1.ast.structural_fingerprint if sub1.ast else None
        fp2 = sub2.ast.structural_fingerprint if sub2.ast else None
        if fp1 and fp2:
            jaccard_sim = cls.calculate_jaccard_similarity(fp1, fp2)
            
        # 3. Tree edit distance (NULL / inactive in production)
        tree_edit = None
        
        # 4. Fusion score (0.60 semantic + 0.40 structural, from SIMILARITY_CONFIG)
        sem_w = SIMILARITY_CONFIG.get("semantic_weight", 0.60)
        struct_w = SIMILARITY_CONFIG.get("structural_weight", 0.40)
        
        weighted_sum = (emb_sim or 0.0) * sem_w + (jaccard_sim or 0.0) * struct_w
        total_weight = sem_w + struct_w
        fusion = round(weighted_sum / total_weight, 4) if total_weight > 0.0 else 0.0
        
        # Determine submission IDs order to avoid duplicates (sub1 < sub2)
        id1, id2 = min(sub1.submission_id, sub2.submission_id), max(sub1.submission_id, sub2.submission_id)
        
        # Find existing pair
        pair = db.query(SimilarityPair).filter(
            SimilarityPair.submission1 == id1,
            SimilarityPair.submission2 == id2
        ).first()
        
        if not pair:
            pair = SimilarityPair(submission1=id1, submission2=id2)
            db.add(pair)
            
        pair.embedding = emb_sim
        pair.jaccard = jaccard_sim
        pair.tree_edit = tree_edit
        pair.fusion = fusion
        pair.version = "fusion_v1"
        
        db.commit()
        db.refresh(pair)
        return pair

    @classmethod
    def run_similarity_checks(cls, db: Session, new_submission: Submission) -> None:
        """
        Computes similarity between the new submission and the latest submissions
        of other students for the SAME assignment, storing scores in similarity_pairs.
        Excludes older drafts and self-comparisons.
        """
        from backend.database import crud
        logger.info(f"Running similarity checks for new submission {new_submission.submission_id} (Student #{new_submission.student_id}, Assignment #{new_submission.assignment_id})")
        
        latest_subs = crud.get_latest_submissions(db, new_submission.assignment_id)
        latest_sub_ids = {s.submission_id for s in latest_subs}
        
        if new_submission.submission_id not in latest_sub_ids:
            logger.info(f"Submission #{new_submission.submission_id} is an older draft for student #{new_submission.student_id}. Skipping similarity checks.")
            return

        for other in latest_subs:
            if other.student_id == new_submission.student_id or other.submission_id == new_submission.submission_id:
                continue
            if other.assignment_id != new_submission.assignment_id:
                continue
            try:
                cls.compare_submissions(db, new_submission, other)
            except ValueError as ve:
                logger.warning(f"Skipped invalid comparison attempt: {str(ve)}")
            except Exception as e:
                logger.error(f"Failed to compare submission {new_submission.submission_id} with {other.submission_id}: {str(e)}")
