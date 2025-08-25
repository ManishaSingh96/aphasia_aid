import os
import openai
import pandas as pd
import re
import json
from typing import List, Dict, Any, Optional
import math
    

class caption_scorer:
    def __init__(self):
        pass 

    def embed_texts(self, texts: List[str], model: str = "text-embedding-3-large", batch_size: int = 100) -> List[List[float]]:
        embeddings: List[List[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start+batch_size]
            resp = openai.Embedding.create(model=model, input=batch)
            embeddings.extend([d["embedding"] for d in resp["data"]])
        return embeddings

    @staticmethod
    def _cosine_sim(a: List[float], b: List[float]) -> float:
        
        
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(y*y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)          

    def score_embeddings_df_with_pos_neg(self,
                                         emb_df: pd.DataFrame,
                                         captions: str,
                                         model: str = "text-embedding-3-large") -> pd.DataFrame:
        """
        Take a DataFrame with columns ['caption','embedding', optional 'url'] and compute
        per-row MAX similarities against generated positive and negative captions for the object.
        Returns a new DataFrame with columns: caption, pos_sims, neg_sims, (url if present).
        """

        if "embedding" not in emb_df.columns or "caption" not in emb_df.columns:
            raise KeyError("Expected columns 'caption' and 'embedding' in emb_df")

        # caps = self.generate_pos_neg_captions(object_name)
        pos_caps: List[str] = list(dict.fromkeys([c.strip() for c in captions.get("positive_captions", []) if c and c.strip()]))
        neg_caps: List[str] = list(dict.fromkeys([c.strip() for c in captions.get("negative_captions", []) if c and c.strip()]))

        pos_embs = self.embed_texts(pos_caps, model=model)
        neg_embs = self.embed_texts(neg_caps, model=model)

        out_rows: List[Dict[str, Any]] = []
        for _, row in emb_df.iterrows():
            vec = row["embedding"]
            if isinstance(vec, str):
                vec = json.loads(vec)
            pos_sims_list = [self._cosine_sim(vec, pe) for pe in pos_embs] if pos_embs else [0.0]
            neg_sims_list = [self._cosine_sim(vec, ne) for ne in neg_embs] if neg_embs else [0.0]
            pos_max = max(pos_sims_list) if pos_sims_list else 0.0
            neg_max = max(neg_sims_list) if neg_sims_list else 0.0
            row_out = {
                "caption": row["caption"],
                "pos_sims": float(pos_max),
                "neg_sims": float(neg_max),
            }
            if "url" in emb_df.columns:
                row_out["url"] = row["url"]
            out_rows.append(row_out)

        return pd.DataFrame(out_rows)

