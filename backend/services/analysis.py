import json
import logging
from sqlalchemy.orm import Session
from backend.database.models import Submission, SubmissionAST, SubmissionEmbedding
from backend.database import crud

from modules.quality import compute_quality_metrics
from modules.ai_detection import check_ai_generated
from modules.ast import (
    parse_code,
    ast_to_dict,
    generate_fingerprint,
    hash_fingerprint,
    normalize_ast,
    normalize_code,
    ParserError
)
from backend.services.embedding import EmbeddingService
from backend.services.similarity import SimilarityService

logger = logging.getLogger(__name__)

class AnalysisError(Exception):
    """Custom exception raised during the submission analysis pipeline."""
    pass

class AnalysisService:
    @staticmethod
    def analyze_submission(db: Session, submission: Submission) -> None:
        """
        Orchestrates the analysis pipeline for a student submission:
        Validation -> Normalization -> AST -> Fingerprint -> Quality -> Embedding -> Similarity -> AI -> Save -> Faculty Review
        """
        logger.info(f"--- [Pipeline] Started for submission {submission.submission_id} ---")
        
        try:
            # Stage 0: Initial state update
            submission.status = "Analyzing"
            db.commit()
            
            # Stage 1: Validation
            logger.info("[Pipeline Step: Validation] Started")
            lang = submission.language or "python"
            if not submission.raw_code or not submission.raw_code.strip():
                logger.error("[Pipeline Step: Validation] Failed: Empty source code")
                raise AnalysisError("Empty source code submission")
            logger.info("[Pipeline Step: Validation] Completed")
            
            # Stage 2: Normalization & Variable Renaming
            logger.info("[Pipeline Step: Normalization] Started")
            try:
                # Runs normalizer (docstrings removed + variables normalized to VAR_1, VAR_2...)
                normalized_code = normalize_code(submission.raw_code, language=lang)
                logger.info("[Pipeline Step: Normalization] Completed")
            except Exception as e:
                logger.error(f"[Pipeline Step: Normalization] Failed: {str(e)}")
                raise AnalysisError(f"Normalization failed: {str(e)}") from e
                
            # Stage 3: AST Generation
            logger.info("[Pipeline Step: AST] Started")
            try:
                tree = parse_code(submission.raw_code, language=lang)
                ast_dict = ast_to_dict(tree, language=lang)
                
                # Retrieve or create SubmissionAST
                sub_ast = submission.ast
                if not sub_ast:
                    sub_ast = SubmissionAST(submission_id=submission.submission_id)
                    db.add(sub_ast)
                
                # Store ast_json
                sub_ast.ast_json = json.dumps(ast_dict)
                db.commit()
                logger.info("[Pipeline Step: AST] Completed")
            except Exception as e:
                logger.error(f"[Pipeline Step: AST] Failed: {str(e)}")
                # Store the error details inside ast_json for professor review
                sub_ast = submission.ast
                if not sub_ast:
                    sub_ast = SubmissionAST(submission_id=submission.submission_id)
                    db.add(sub_ast)
                sub_ast.ast_json = json.dumps({"success": False, "error": str(e)})
                db.commit()
                raise AnalysisError(f"AST Generation failed: {str(e)}") from e
                
            # Stage 4: Fingerprint & Hashing
            logger.info("[Pipeline Step: Fingerprint] Started")
            try:
                # We use the normalized tree to generate the structural fingerprint
                normalized_tree = normalize_ast(tree)
                fingerprint = generate_fingerprint(normalized_tree, exclude_context=True, language=lang)
                fprint_hash = hash_fingerprint(fingerprint)
                
                # Store in sub_ast
                sub_ast = submission.ast
                if not sub_ast:
                    sub_ast = SubmissionAST(submission_id=submission.submission_id)
                    db.add(sub_ast)
                
                sub_ast.normalized_code = normalized_code
                sub_ast.structural_fingerprint = fingerprint
                sub_ast.fingerprint_hash = fprint_hash
                db.commit()
                logger.info("[Pipeline Step: Fingerprint] Completed")
            except Exception as e:
                logger.error(f"[Pipeline Step: Fingerprint] Failed: {str(e)}")
                raise AnalysisError(f"Fingerprinting failed: {str(e)}") from e
                
            # Stage 5: Quality Analysis
            logger.info("[Pipeline Step: Quality] Started")
            try:
                quality_res = compute_quality_metrics(submission.raw_code)
                logger.info("[Pipeline Step: Quality] Completed")
            except Exception as e:
                logger.error(f"[Pipeline Step: Quality] Failed: {str(e)}")
                raise AnalysisError(f"Quality Analysis failed: {str(e)}") from e
                
            # Stage 6: Embedding Generation (GraphCodeBERT)
            logger.info("[Pipeline Step: Embedding] Started")
            try:
                embedding_vector = EmbeddingService.get_embedding(submission.raw_code)
                sub_emb = submission.embedding
                if not sub_emb:
                    sub_emb = SubmissionEmbedding(
                        submission_id=submission.submission_id,
                        model_name="microsoft/graphcodebert-base"
                    )
                    db.add(sub_emb)
                sub_emb.embedding_vector = json.dumps(embedding_vector)
                db.commit()
                logger.info("[Pipeline Step: Embedding] Completed")
            except Exception as e:
                logger.error(f"[Pipeline Step: Embedding] Failed: {str(e)}")
                raise AnalysisError(f"Embedding Generation failed: {str(e)}") from e
                
            # Stage 7: Similarity Calculation
            logger.info("[Pipeline Step: Similarity] Started")
            try:
                SimilarityService.run_similarity_checks(db, submission)
                logger.info("[Pipeline Step: Similarity] Completed")
            except Exception as e:
                logger.error(f"[Pipeline Step: Similarity] Failed: {str(e)}")
                raise AnalysisError(f"Similarity Calculation failed: {str(e)}") from e
                
            # Stage 8: AI Detection
            logger.info("[Pipeline Step: AI] Started")
            try:
                ai_res = check_ai_generated(submission.raw_code)
                logger.info("[Pipeline Step: AI] Completed")
            except Exception as e:
                logger.error(f"[Pipeline Step: AI] Failed: {str(e)}")
                raise AnalysisError(f"AI Detection failed: {str(e)}") from e
                
            # Stage 9: Save results and transition to Faculty Review
            logger.info("[Pipeline Step: Save] Started")
            try:
                crud.create_or_update_analysis_result(
                    db=db,
                    submission_id=submission.submission_id,
                    plagiarism=json.dumps({"similarity_score": 0.0, "matches": []}),
                    ai_score=ai_res["ai_probability"],
                    quality_score=json.dumps(quality_res)
                )
                
                # Advance state to Faculty Review
                submission.status = "Faculty Review"
                db.commit()
                logger.info("[Pipeline Step: Save] Completed")
            except Exception as e:
                logger.error(f"[Pipeline Step: Save] Failed: {str(e)}")
                raise AnalysisError(f"Saving analysis result failed: {str(e)}") from e
                
            logger.info(f"--- [Pipeline] Completed successfully for submission {submission.submission_id} ---")
            
        except Exception as e:
            db.rollback()
            submission.status = "Failed"
            db.commit()
            logger.error(f"--- [Pipeline] Failed for submission {submission.submission_id}: {str(e)} ---")
            # If it's already an AnalysisError, re-raise it, otherwise wrap it
            if isinstance(e, AnalysisError):
                raise e
            raise AnalysisError(f"Analysis pipeline execution failed: {str(e)}") from e
