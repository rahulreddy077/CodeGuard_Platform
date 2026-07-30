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
    def compare_submissions(cls, db: Session, sub1: Submission, sub2: Submission) -> SimilarityPair:
        """
        Compares two submissions: computes embedding cosine similarity, fingerprint Jaccard,
        and saves/updates the SimilarityPair record.
        """
        logger.info(f"Comparing submission {sub1.submission_id} and {sub2.submission_id}")
        
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
            
        # 3. Tree edit distance placeholder (None means it is not yet active)
        tree_edit = None
        
        # 4. Fusion score (combined metric normalized dynamically over active weights)
        total_weight = 0.0
        weighted_sum = 0.0
        
        if emb_sim is not None:
            weighted_sum += emb_sim * SIMILARITY_CONFIG.get("embedding", 0.70)
            total_weight += SIMILARITY_CONFIG.get("embedding", 0.70)
            
        if jaccard_sim is not None:
            weighted_sum += jaccard_sim * SIMILARITY_CONFIG.get("jaccard", 0.20)
            total_weight += SIMILARITY_CONFIG.get("jaccard", 0.20)
            
        if tree_edit is not None:
            weighted_sum += tree_edit * SIMILARITY_CONFIG.get("tree_edit", 0.10)
            total_weight += SIMILARITY_CONFIG.get("tree_edit", 0.10)
            
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
        Computes similarity between the new submission and all other submissions
        for the same assignment, storing the scores in the similarity_pairs table.
        """
        logger.info(f"Running similarity checks for new submission {new_submission.submission_id}")
        
        # Fetch other submissions for the same assignment (excluding itself)
        others = db.query(Submission).filter(
            Submission.assignment_id == new_submission.assignment_id,
            Submission.submission_id != new_submission.submission_id,
            Submission.status != "Failed"  # Skip failed ones
        ).all()
        
        for other in others:
            try:
                cls.compare_submissions(db, new_submission, other)
            except Exception as e:
                logger.error(f"Failed to compare submission {new_submission.submission_id} with {other.submission_id}: {str(e)}")
