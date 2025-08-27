# save as extract_caption_url.py
import os
import sys
import pandas as pd

def extract_caption_url(parquet_path: str, csv_path: str = None) -> str:
    """
    Read a parquet file, select `caption` and `url` columns, and write to CSV.

    Args:
        parquet_path: path to the input .parquet file
        csv_path: optional output csv path; if None -> same name with .csv

    Returns:
        The path to the written CSV.
    """
    if not os.path.isfile(parquet_path):
        raise FileNotFoundError(f"File not found: {parquet_path}")

    # Choose output path
    if csv_path is None:
        base, _ = os.path.splitext(parquet_path)
        csv_path = base + "_caption_url.csv"

    # Read parquet (requires pyarrow or fastparquet)
    try:
        df = pd.read_parquet(parquet_path)  # engine auto-detected
    except Exception as e:
        raise RuntimeError(
            "Failed to read parquet. Ensure the file is a valid parquet and "
            "that `pyarrow` or `fastparquet` is installed.\n"
            f"Original error: {e}"
        )

    # Validate columns (case-sensitive)
    needed = {"caption", "url"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    # Select, drop obvious bad rows, and deduplicate
    out = (
        df.loc[:, ["caption", "url"]]
          .dropna(subset=["url"])
          .drop_duplicates()
    )

    # Optional: keep only http(s) URLs
    out = out[out["url"].astype(str).str.startswith(("http://", "https://"))]

    # Write CSV
    out.to_csv(csv_path, index=False)
    print(f"✅ Wrote {len(out)} rows to {csv_path}")
    return csv_path


if __name__ == "__main__":

    parquet_path = "embeddings/embeddings_Taj Mahal.parquet"
    csv_path = "taj.csv"
    extract_caption_url(parquet_path, csv_path)
