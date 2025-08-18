import os
import sys
import pandas as pd

from create_embeddings import embed_captions_df
from positive_and_neg_caption_gen import Image_Caption_Filter


def filter_parquet_by_object(parquet_path: str, object_name: str) -> pd.DataFrame:
    df = pd.read_parquet(parquet_path, columns=["caption", "url"])  # keeps url for later
    # filter by keyword in caption
    mask = df["caption"].astype(str).str.contains(object_name, case=False, na=False)
    df = df.loc[mask].copy()
    # token length < 20
    token_len = (df["caption"].fillna("").astype(str).str.split().str.len())
    df = df[token_len < 20]
    # clean whitespace
    df["caption"] = (df["caption"].fillna("")
                      .astype(str)
                      .str.replace(r"\s+", " ", regex=True)
                      .str.strip())
    # drop empties
    df = df[df["caption"] != ""]
    return df.reset_index(drop=True)


def main():
    # Hardcoded settings
    PARQUET_PATH = "cc12m_7m_subset_translated.parquet"
    EMBED_MODEL = "text-embedding-3-large"
    BATCH_SIZE = 100

    # Ask for object only
    try:
        object_name = input("Enter object name (e.g., 'towel'): ").strip()
    except EOFError:
        object_name = ""
    if not object_name:
        object_name = "egg"

    print(f"Filtering '{PARQUET_PATH}' for object='{object_name}' and token_len<20 ...")
    df_filtered = filter_parquet_by_object(PARQUET_PATH, object_name)
    print(f"Filtered rows: {len(df_filtered)}")

    if df_filtered.empty:
        print("No rows after filtering. Exiting.")
        return 0

    print("Creating embeddings for filtered captions...")
    emb_df = embed_captions_df(df_filtered.iloc[:200,:], model=EMBED_MODEL, batch_size=BATCH_SIZE)

    print("Scoring with positive and negative captions...")
    scorer = Image_Caption_Filter()
    scored_df = scorer.score_embeddings_df_with_pos_neg(emb_df, object_name=object_name, model=EMBED_MODEL)

    print("Computing final score = pos_sims - neg_sims ...")
    scored_df["score"] = scored_df["pos_sims"] - scored_df["neg_sims"]

    out_path = f"{object_name}_results.csv"
    print(f"Saving final results to '{out_path}'...")
    # Ensure columns order
    cols = ["caption", "pos_sims", "neg_sims", "score"]
    if "url" in scored_df.columns:
        cols.insert(1, "url")
    scored_df[cols].to_csv(out_path, index=False)

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main()) 