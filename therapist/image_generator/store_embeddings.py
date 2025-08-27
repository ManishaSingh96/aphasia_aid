import os
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from therapist.image_generator.create_embeddings import embed_captions_df
from therapist.image_generator.helper_functions import *

def chunk_df(df, size):
    return [df.iloc[i:i + size] for i in range(0, len(df), size)]

class store_embeddings:
    def __init__(
        self,
        model,
        batch_size,
        # source_parquet="cc12m_7m_subset_translated.parquet",
        max_rows=200,
        emb_dir="embeddings"
    ):
        self.embedding_model = model
        self.batch_size = batch_size
        # self.source_parquet = str(Path(__file__).parent / source_parquet)
        self.max_rows = max_rows
        self.emb_dir = emb_dir
        os.makedirs(self.emb_dir, exist_ok=True)

    def _process_chunk(self, chunk):
        """Helper to process one chunk safely."""
        try:
            return embed_captions_df(chunk, model=self.embedding_model, batch_size=len(chunk))
        except Exception as e:
            print(f"Embedding failed for chunk: {e}")
            return None

    def generate_embeddings(self, object_name,df):
        emb_path = os.path.join(self.emb_dir, f"embeddings_{object_name}.parquet")

        # If already processed, load cached embeddings
        if os.path.exists(emb_path):
            print(f"Found existing embeddings: {emb_path}")
            return pd.read_parquet(emb_path)

        # Ensure source parquet exists
        # if not os.path.exists(self.source_parquet):
        #     raise FileNotFoundError(f"Source parquet not found: {self.source_parquet}")

        # Load and filter
        # df = pd.read_parquet(self.source_parquet)
        filtered_df = filter_df_with_object(df, object_name)
        print(f"Filtered rows for '{object_name}': {len(filtered_df)}")

        # Drop large df to free memory
        del df  

        # Handle empty case
        if filtered_df.empty:
            print("No rows after filtering. Exiting.")
            return pd.DataFrame()

        # Limit rows for safety
        filtered_df = filtered_df.iloc[: self.max_rows, :]
        chunks = chunk_df(filtered_df, self.batch_size)

        # Free filtered_df from memory as well
        del filtered_df  

        results = []

        # If batch size < 20 → parallel processing
        if self.batch_size < 20:
            max_workers = min(8, len(chunks))  # cap threads for safety
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(self._process_chunk, chunk): chunk for chunk in chunks}
                for future in as_completed(futures):
                    result = future.result()
                    if result is not None:
                        results.append(result)
        else:
            # Sequential processing for large batches
            for chunk in chunks:
                result = self._process_chunk(chunk)
                if result is not None:
                    results.append(result)

        # If no embeddings were successfully generated
        if not results:
            raise RuntimeError("All embedding batches failed.")

        # Combine results
        emb_df = pd.concat(results).reset_index(drop=True)

        # Ensure embedding column exists
        if "embedding" not in emb_df.columns:
            raise ValueError("embed_captions_df must return a column named 'embedding'.")

        # Save results
        emb_df.to_parquet(emb_path, index=False)
        print(f"Saved embeddings to {emb_path}")

        return emb_df
