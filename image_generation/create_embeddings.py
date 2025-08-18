import os
import sys
import time
from typing import List, Optional

import pandas as pd

# Using legacy OpenAI SDK style to match existing project usage
import openai


def load_dataset(path_or_name: str) -> pd.DataFrame:
    """Load dataset from parquet or csv; infer extension if only name provided."""
    candidates = []
    if os.path.exists(path_or_name):
        candidates.append(path_or_name)
    else:
        # Try common filenames in current working directory
        candidates.extend([
            f"{path_or_name}.parquet",
            f"{path_or_name}.csv",
        ])

    for candidate in candidates:
        if os.path.exists(candidate):
            if candidate.endswith(".parquet"):
                return pd.read_parquet(candidate)
            if candidate.endswith(".csv"):
                return pd.read_csv(candidate)

    raise FileNotFoundError(
        f"Could not find dataset for '{path_or_name}'. Tried: {', '.join(candidates)}"
    )


def select_captions(df: pd.DataFrame, limit: int = 200) -> List[str]:
    if "caption" not in df.columns:
        raise KeyError("Expected a 'caption' column in the dataset")
    s = (
        df["caption"].fillna("")
        .astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    s = s[s != ""].head(limit)
    return s.tolist()


def create_embeddings(texts: List[str], model: str = "text-embedding-3-large", batch_size: int = 100,
                      max_retries: int = 3, retry_delay_sec: float = 2.0) -> List[List[float]]:
    """Create embeddings for texts in batches using OpenAI Embeddings API (legacy SDK)."""
    all_embeddings: List[List[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        attempt = 0
        while True:
            try:
                resp = openai.Embedding.create(model=model, input=batch)
                # resp["data"] is list of {embedding: [...], index: i}
                batch_embeddings = [item["embedding"] for item in resp["data"]]
                all_embeddings.extend(batch_embeddings)
                break
            except Exception as e:
                attempt += 1
                if attempt >= max_retries:
                    raise
                time.sleep(retry_delay_sec * attempt)
    return all_embeddings


def embed_captions_df(df: pd.DataFrame, model: str = "text-embedding-3-large", batch_size: int = 100) -> pd.DataFrame:
    """Embed all captions in the provided DataFrame and return a new DataFrame with 'caption', optional 'url', and 'embedding'."""
    if "caption" not in df.columns:
        raise KeyError("Expected a 'caption' column in the DataFrame")
    texts = (
        df["caption"].fillna("")
        .astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    texts = texts.tolist()
    embs = create_embeddings(texts, model=model, batch_size=batch_size)
    out = pd.DataFrame({
        "caption": df["caption"].astype(str).tolist(),
        "embedding": embs,
    })
    if "url" in df.columns:
        out["url"] = df["url"].tolist()
    return out


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Create embeddings for first N captions from a dataset")
    parser.add_argument("dataset", nargs="?", default="towel_image", help="Path or base name of dataset (parquet or csv)")
    parser.add_argument("--limit", type=int, default=200, help="Number of captions to embed")
    parser.add_argument("--model", type=str, default="text-embedding-3-large", help="OpenAI embedding model")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for API calls")
    parser.add_argument("--out", type=str, default=None, help="Output parquet file path")

    args = parser.parse_args(argv)

    # Configure OpenAI
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        print("ERROR: OPENAI_API_KEY is not set in environment", file=sys.stderr)
        return 2

    print(f"Loading dataset '{args.dataset}'...")
    df = load_dataset(args.dataset)

    print(f"Selecting up to {args.limit} captions...")
    captions = select_captions(df, limit=args.limit)
    if not captions:
        print("No captions to embed.")
        return 0

    print(f"Creating embeddings using model '{args.model}' (batch size {args.batch_size})...")
    embeddings = create_embeddings(captions, model=args.model, batch_size=args.batch_size)

    print("Assembling results DataFrame...")
    out_df = pd.DataFrame({
        "caption": captions,
        "embedding": embeddings,
    })

    out_path = args.out or (f"{os.path.splitext(args.dataset)[0]}_embeddings.parquet" if os.path.splitext(args.dataset)[1] else f"{args.dataset}_embeddings.parquet")
    print(f"Saving embeddings to '{out_path}'...")
    out_df.to_parquet(out_path, index=False)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main()) 