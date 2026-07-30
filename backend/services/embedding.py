import logging
from typing import List

logger = logging.getLogger(__name__)

# Global variables for lazy loading
_tokenizer = None
_model = None

class EmbeddingService:
    @staticmethod
    def _lazy_init():
        global _tokenizer, _model
        if _tokenizer is None or _model is None:
            logger.info("Initializing GraphCodeBERT tokenizer and model (microsoft/graphcodebert-base)...")
            try:
                from transformers import AutoTokenizer, AutoModel
                
                model_name = "microsoft/graphcodebert-base"
                _tokenizer = AutoTokenizer.from_pretrained(model_name)
                _model = AutoModel.from_pretrained(model_name)
                logger.info("GraphCodeBERT initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize GraphCodeBERT: {str(e)}")
                raise RuntimeError(f"Embedding initialization error: {str(e)}") from e

    @classmethod
    def get_embedding(cls, code: str) -> List[float]:
        """
        Generates a 768-dimensional embedding vector for source code using GraphCodeBERT.
        """
        cls._lazy_init()
        
        try:
            import torch
            
            # Tokenize code text (GraphCodeBERT supports standard input text)
            inputs = _tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs = _model(**inputs)
                
            # Extract CLS token representation (first token hidden state)
            cls_embedding = outputs.last_hidden_state[0, 0].cpu().numpy().tolist()
            return cls_embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise RuntimeError(f"Failed to compute embedding: {str(e)}") from e
