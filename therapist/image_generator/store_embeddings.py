# store_embeddings.py

import os
import pandas as pd
from pathlib import Path
from create_embeddings import embed_captions_df
from helper_functions import *


def chunk_df(df, size):
    return [df.iloc[i:i + size] for i in range(0, len(df), size)]


class store_embeddings:
    def __init__(self, model, batch_size,
                 source_parquet="cc12m_7m_subset_translated.parquet",
                 max_rows=1000,
                 emb_dir="embeddings"):
        self.embedding_model = model
        self.batch_size = batch_size
        self.source_parquet = str(Path(__file__).parent / source_parquet)
        self.max_rows = max_rows
        self.emb_dir = emb_dir

        os.makedirs(self.emb_dir, exist_ok=True)

    def generate_embeddings(self, object_name):
        emb_path = os.path.join(self.emb_dir, f"embeddings_{object_name}.parquet")

        if os.path.exists(emb_path):
            print(f"Found existing embeddings: {emb_path}")
            return pd.read_parquet(emb_path)

        if not os.path.exists(self.source_parquet):
            raise FileNotFoundError(f"Source parquet not found: {self.source_parquet}")

        df = pd.read_parquet(self.source_parquet)
        filtered_df = filter_df_with_object(df, object_name)
        print(f"Filtered rows for '{object_name}': {len(filtered_df)}")

        if filtered_df.empty:
            print("No rows after filtering. Exiting.")
            return pd.DataFrame()

        filtered_df = filtered_df.iloc[: self.max_rows, :]
        # chunks = chunk_df(filtered_df, self.batch_size)

        # results = []
        # for chunk in chunks:
        try:
            result = embed_captions_df(filtered_df, model=self.embedding_model, batch_size=500)
                
        except Exception as e:
            print(f"Embedding failed for a batch: {e}")

        if result is None:
            raise RuntimeError("All embedding batches failed.")

        # emb_df = pd.concat(result).reset_index(drop=True)
        emb_df=result
        if "embedding" not in emb_df.columns:
            raise ValueError("embed_captions_df must return a column named 'embedding'.")

        emb_df.to_parquet(emb_path, index=False)
        print(f"Saved embeddings to {emb_path}")

        return emb_df
