from io import BytesIO
from urllib.parse import urlparse
from pathlib import Path

import requests
from PIL import Image

import pandas as pd
import torch
import open_clip
import numpy as np

class SimilarityScorer:
    def __init__(self, model_name: str = "ViT-B-32", pretrained: str = "openai"):
        self.model_name = model_name
        self.pretrained = pretrained
        self.model, self.preprocess, self.tokenizer, self.device = self._load_model()
    
    def _load_model(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model, _, preprocess = open_clip.create_model_and_transforms(self.model_name, self.pretrained)
        model = model.to(device).eval()
        tokenizer = open_clip.get_tokenizer(self.model_name)
        return model, preprocess, tokenizer, device

    def _load_pil_image(self, src: str) -> Image.Image:
        parsed = urlparse(src)
        if parsed.scheme in ("http", "https"):
            r = requests.get(src, timeout=20)
            r.raise_for_status()
            return Image.open(BytesIO(r.content)).convert("RGB")
        return Image.open(Path(src)).convert("RGB")

    @torch.no_grad()
    def clip_score(self, caption: str, image_src: str) -> dict:
        img = self._load_pil_image(image_src)
        image = self.preprocess(img).unsqueeze(0).to(self.device)
        text = self.tokenizer([caption]).to(self.device)

        use_amp = (self.device == "cuda")
        with torch.cuda.amp.autocast(enabled=use_amp):
            image_features = self.model.encode_image(image)
            text_features = self.model.encode_text(text)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            cos = (text_features @ image_features.T).squeeze().item()
            logit = (self.model.logit_scale.exp() * (text_features @ image_features.T)).squeeze().item()

        return {"cosine_similarity": float(cos), "clip_logit": float(logit)}

    def score_dataframe_with_image(self, df: pd.DataFrame, target_caption: str) -> pd.DataFrame:
        """
        For each row in df, compute CLIP similarity between `target_caption` and the image at `url`.
        Return a copy of df with an added column `sim_score_image` (and `clip_logit_image`).
        Rows with missing/invalid URLs receive NaN scores.

        Required columns in df: 'url'
        Other columns (e.g., caption, pos_sim, neg_sim, etc.) are preserved untouched.
        """
        if "url" not in df.columns:
            raise ValueError("Input DataFrame must contain a 'url' column.")

        sim_scores = []
        logit_scores = []

        total = len(df)
        print(f"Scoring {total} rows against target caption...")
        for i, url in enumerate(df["url"].tolist()):
            if not isinstance(url, str) or url.strip() == "":
                sim_scores.append(np.nan)
                logit_scores.append(np.nan)
                continue

            try:
                out = self.clip_score(target_caption, str(url))
                sim_scores.append(out.get("cosine_similarity", np.nan))
                logit_scores.append(out.get("clip_logit", np.nan))
            except Exception as e:
                # Any fetch/decoding/scoring issue → set NaN
                sim_scores.append(np.nan)
                logit_scores.append(np.nan)
                # Optional: print a lightweight error (kept short to avoid noisy logs)
                print(f"[{i}] URL failed: {e}")

            if (i + 1) % 50 == 0:
                print(f"Processed {i + 1}/{total}")

        out_df = df.copy()
        out_df["sim_score_image"] = sim_scores
        out_df["clip_logit_image"] = logit_scores
        return out_df
