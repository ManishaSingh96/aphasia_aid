import os
import sys
from typing import Optional, List

import pandas as pd

from create_sim_score import SimilarityScorer

# Hardcoded settings
TOP_K: int = 10
MODEL_NAME: str = "ViT-B-32"
PRETRAINED: str = "openai"
QUERY_TEMPLATE: str = "A clear well focused of a whole {obj} on a plain, uncluttered background."


def _candidate_filenames(object_name: str) -> List[str]:
    """Generate plausible result CSV filenames for an object name, including messy spacing variants."""
    base_raw = object_name
    trimmed = base_raw.strip()
    compressed = " ".join(trimmed.split())  # collapse multiple spaces
    underscore = compressed.replace(" ", "_")
    nospace = compressed.replace(" ", "")

    variants = [
        base_raw, trimmed, compressed, underscore, nospace,
        compressed.lower(), underscore.lower(), nospace.lower(),
        compressed.title(), underscore.title()
    ]

    candidates: List[str] = []
    for v in variants:
        candidates.append(f"{v}_results.csv")
        candidates.append(f"{v}_result.csv")
        # some datasets have a space before extension
        candidates.append(f"{v}_result .csv")
        candidates.append(f"{v}_results .csv")
    # De-duplicate while preserving order
    seen = set()
    out = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _find_results_file(object_name: str) -> Optional[str]:
    """Resolve the results CSV path by checking common filename variants in CWD and script directory."""
    candidates = _candidate_filenames(object_name)

    # Search in CWD
    for name in candidates:
        if os.path.isfile(name):
            return os.path.abspath(name)

    # Search in script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for name in candidates:
        p = os.path.join(script_dir, name)
        if os.path.isfile(p):
            return p

    return None


def compute_topk_clip_similarity(object_name: str) -> pd.DataFrame:
    """Load results CSV for object, take top-K by score, compute CLIP similarity vs hardcoded query text."""
    resolved = _find_results_file(object_name)
    if not resolved:
        raise FileNotFoundError(
            f"Could not find results CSV for object '{object_name}'. Looked for: {', '.join(_candidate_filenames(object_name))}"
        )

    df = pd.read_csv(resolved)

    if "score" not in df.columns:
        raise KeyError("Results CSV must contain a 'score' column produced by image_generation/model.py")

    if "url" not in df.columns:
        raise KeyError("Results CSV does not contain a 'url' column; cannot compute image similarity without URLs")

    # Select top-K by score (descending)
    df_top = df.sort_values("score", ascending=False).head(TOP_K).copy()

    # Hardcoded query text based on object name
    query_text = QUERY_TEMPLATE.format(obj=object_name)

    scorer = SimilarityScorer(model_name=MODEL_NAME, pretrained=PRETRAINED)

    cos_sims: List[float] = []
    clip_logits: List[float] = []

    for _, row in df_top.iterrows():
        url = row["url"]
        try:
            res = scorer.clip_score(query_text, url)
            cos_sims.append(res.get("cosine_similarity", 0.0))
            clip_logits.append(res.get("clip_logit", 0.0))
        except Exception:
            cos_sims.append(float("nan"))
            clip_logits.append(float("nan"))

    df_top = df_top.assign(cosine_similarity=cos_sims, clip_logit=clip_logits)

    # Reorder columns for readability
    cols: List[str] = []
    for c in ["caption", "url", "score", "cosine_similarity", "clip_logit"]:
        if c in df_top.columns:
            cols.append(c)
    other_cols = [c for c in df_top.columns if c not in cols]
    df_top = df_top[cols + other_cols]

    return df_top


def main() -> int:
    try:
        object_name = input("Enter object name (e.g., 'auto rickshaw'): ").strip()
    except EOFError:
        object_name = ""
    if not object_name:
        object_name = "auto rickshaw"

    print(f"Using object: {object_name}")
    print(f"Query text: {QUERY_TEMPLATE.format(obj=object_name)}")

    try:
        result_df = compute_topk_clip_similarity(object_name=object_name)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Derive output path
    safe_obj = "_".join(object_name.strip().split())
    out_path = f"{safe_obj}_top{TOP_K}_clip_similarity.csv"

    result_df.to_csv(out_path, index=False)

    print(f"Saved similarity results to: {out_path}")
    preview_cols = [c for c in ["caption", "url", "score", "cosine_similarity"] if c in result_df.columns]
    print(result_df[preview_cols].head(TOP_K).to_string(index=False))

    return 0


if __name__ == "__main__":
    sys.exit(main()) 