import os
import openai
import pandas as pd
import re
import json
from typing import List, Dict, Any, Optional


class Image_Caption_Filter:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def clean_json(self, text: str) -> str:
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            json_text = match.group(1).strip()
            print("match found")
        else:
            json_text = text.strip()
            print("No match found.")
        return json_text

    def generate_pos_neg_captions(self, object_name: str) -> dict:
        """
        Generate short, descriptive, flashcard-style captions for the given object.
        Returns a dict like {"positive_captions": [...], "negative_captions": [...]}.
        """
        system_prompt = """
        You are a caption generator that generates suitable captions for flashcard style images 
        used in naming from description exercise for speech therapy.

        """
                

        user_prompt = f"""
        INPUT:
TARGET_OBJECT: {object_name}

TASK:
1. Generate 10 **positive captions** that describe the TARGET_OBJECT in a descriptive, textbook/flashcard style.
   - Captions should be short.
   - Only the object itself should be described (no people, no extra objects).
   - Assume a plain or neutral background.
   - Use the most common and simple variants of the object.

2. Generate 10 **negative captions** that are unsuitable for textbook/flashcard style.
   - These may include people, other objects, or uncommon/novel variants.
   - Examples: object being used by people, in busy scenes, branded versions, or as part of a recipe.

OUTPUT:
Return **strict JSON only**, with the following structure and no extra text, no markdown, no trailing commas:

{{
  "positive_captions": [
    "caption text 1",
    "caption text 2",
    ...
    "caption text 10"
  ],
  "negative_captions": [
    "caption text 1",
    "caption text 2",
    ...
    "caption text 10"
  ]
}}

FEW-SHOT EXAMPLES:

TARGET_OBJECT: Apple
{{
  "positive_captions": [
    "A red apple with green leaves",
    "A red apple with green stem",
    "A whole green apple",
    "A single apple on plain background",
    "A shiny red apple",
    "A plain yellow apple",
    "A ripe apple on white background",
    "A fresh apple with smooth skin",
    "A single apple centered in frame",
    "A clean red apple with stem"
  ],
  "negative_captions": [
    "Apple pie on a plate",
    "Apple wine in a glass",
    "Girl plucking apple from tree",
    "A hand holding an Apple phone",
    "A basket filled with apples",
    "An apple orchard with many trees",
    "Cut apple slices on a plate",
    "Caramel apple on a stick",
    "Apple with chocolate topping",
    "Apple logo on a laptop"
  ]
}}

TARGET_OBJECT: Towel
{{
  "positive_captions": [
    "A plain white towel",
    "A folded towel",
    "A towel hanging on a hook",
    "A rolled towel",
    "A clean bath towel",
    "A hand towel on plain background",
    "A grey towel folded neatly",
    "A stack of white towels",
    "A striped towel on plain background",
    "A single towel centered in frame"
  ],
  "negative_captions": [
    "A girl wearing a towel on the beach",
    "A man drying with a towel",
    "A towel with cartoon characters",
    "Towel on hotel bed with flowers",
    "A dog wrapped in a towel",
    "A towel rack in a bathroom",
    "A towel with brand logo",
    "Two people sharing a towel",
    "A branded towel displayed in a store",
    "A towel used in a beach party"
  ]
}}

        """

        messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=messages,
            )
        raw = response.choices[0].message.content.strip()
        cleaned = self.clean_json(raw)
        data = json.loads(cleaned)
        return data  

    # --- New utilities for embedding and similarity scoring ---
    def embed_texts(self, texts: List[str], model: str = "text-embedding-3-large", batch_size: int = 100) -> List[List[float]]:
        embeddings: List[List[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start+batch_size]
            resp = openai.Embedding.create(model=model, input=batch)
            embeddings.extend([d["embedding"] for d in resp["data"]])
        return embeddings

    @staticmethod
    def _cosine_sim(a: List[float], b: List[float]) -> float:
        # Manual cosine similarity to avoid extra deps
        import math
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(y*y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def score_embeddings_with_pos_neg(self,
                                      embeddings_path: str,
                                      object_name: str,
                                      model: str = "text-embedding-3-large",
                                      out_path: str = None,
                                      dataset_csv_path: Optional[str] = "towel_image.csv") -> pd.DataFrame:
        """
        Load dataset embeddings parquet (with columns 'caption', 'embedding'),
        generate positive and negative captions for object_name, embed them,
        and compute per-row MAX similarity against all positive and MAX against all negative captions.

        Optionally merges URL by matching caption from dataset_csv_path if present.

        Returns a DataFrame with columns:
          - dataset_caption
          - url (if merged)
          - pos_sims: float (max positive similarity)
          - neg_sims: float (max negative similarity)
        """
        print(f"Loading embeddings from '{embeddings_path}'...")
        df = pd.read_parquet(embeddings_path)
        if "embedding" not in df.columns or "caption" not in df.columns:
            raise KeyError("Embeddings file must have 'caption' and 'embedding' columns")

        print(f"Generating positive/negative captions for '{object_name}'...")
        caps = self.generate_pos_neg_captions(object_name)
        pos_caps: List[str] = list(dict.fromkeys([c.strip() for c in caps.get("positive_captions", []) if c and c.strip()]))
        neg_caps: List[str] = list(dict.fromkeys([c.strip() for c in caps.get("negative_captions", []) if c and c.strip()]))

        print("Embedding positive captions...")
        pos_embs = self.embed_texts(pos_caps, model=model)
        print("Embedding negative captions...")
        neg_embs = self.embed_texts(neg_caps, model=model)

        print("Scoring dataset embeddings against positive/negative caption embeddings (max scores)...")
        out_rows: List[Dict[str, Any]] = []
        for i, row in df.iterrows():
            vec = row["embedding"]
            # Ensure list[float]
            if isinstance(vec, str):
                vec = json.loads(vec)
            pos_sims_list = [self._cosine_sim(vec, pe) for pe in pos_embs] if pos_embs else [0.0]
            neg_sims_list = [self._cosine_sim(vec, ne) for ne in neg_embs] if neg_embs else [0.0]
            pos_max = max(pos_sims_list) if pos_sims_list else 0.0
            neg_max = max(neg_sims_list) if neg_sims_list else 0.0
            out_rows.append({
                "dataset_caption": row["caption"],
                "pos_sims": float(pos_max),
                "neg_sims": float(neg_max),
            })

        out_df = pd.DataFrame(out_rows)

        # Optional URL merge from dataset CSV
        if dataset_csv_path and os.path.exists(dataset_csv_path):
            try:
                src_df = pd.read_csv(dataset_csv_path, usecols=["caption", "url"])
                out_df = out_df.merge(src_df, left_on="dataset_caption", right_on="caption", how="left")
                out_df = out_df.drop(columns=["caption"])  # drop duplicate key
            except Exception as e:
                print(f"Warning: could not merge URLs from {dataset_csv_path}: {e}")
        else:
            print(f"Note: dataset CSV '{dataset_csv_path}' not found; skipping URL merge.")

        if out_path:
            print(f"Saving scores to '{out_path}'...")
            # Directly save floats to CSV or parquet
            if out_path.endswith(".csv"):
                out_df.to_csv(out_path, index=False)
            else:
                out_df.to_parquet(out_path, index=False)
        return out_df

    def score_embeddings_df_with_pos_neg(self,
                                         emb_df: pd.DataFrame,
                                         object_name: str,
                                         model: str = "text-embedding-3-large") -> pd.DataFrame:
        """
        Take a DataFrame with columns ['caption','embedding', optional 'url'] and compute
        per-row MAX similarities against generated positive and negative captions for the object.
        Returns a new DataFrame with columns: caption, pos_sims, neg_sims, (url if present).
        """
        if "embedding" not in emb_df.columns or "caption" not in emb_df.columns:
            raise KeyError("Expected columns 'caption' and 'embedding' in emb_df")

        caps = self.generate_pos_neg_captions(object_name)
        pos_caps: List[str] = list(dict.fromkeys([c.strip() for c in caps.get("positive_captions", []) if c and c.strip()]))
        neg_caps: List[str] = list(dict.fromkeys([c.strip() for c in caps.get("negative_captions", []) if c and c.strip()]))

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


if __name__ == "__main__":
    gen = Image_Caption_Filter()
    # Example run for towel
    embeddings_file = "towel_image_embeddings.parquet"
    results = gen.score_embeddings_with_pos_neg(
        embeddings_path=embeddings_file,
        object_name="towel",
        model="text-embedding-3-large",
        out_path="towel_image_posneg_sims.csv",
        dataset_csv_path="towel_image.csv"
    )
    print(results.head())
