from io import BytesIO
from urllib.parse import urlparse
from pathlib import Path

import requests
from PIL import Image

import pandas as pd
import torch
import open_clip
import json


class SimilarityScorer:
    def __init__(self, model_name: str = "ViT-B-32", pretrained: str = "openai"):
        """
        Initialize the SimilarityScorer class
        
        Args:
            model_name (str): CLIP model name
            pretrained (str): Pretrained model version
        """
        self.model_name = model_name
        self.pretrained = pretrained
        self.model, self.preprocess, self.tokenizer, self.device = self._load_model()
    
    def _load_model(self):
        """Load the CLIP model and return model components"""
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model, _, preprocess = open_clip.create_model_and_transforms(self.model_name, self.pretrained)
        model = model.to(device).eval()
        tokenizer = open_clip.get_tokenizer(self.model_name)
        return model, preprocess, tokenizer, device

    def _load_pil_image(self, src: str) -> Image.Image:
        """Load image from URL or local path"""
        parsed = urlparse(src)
        if parsed.scheme in ("http", "https"):
            r = requests.get(src, timeout=20)
            r.raise_for_status()
            return Image.open(BytesIO(r.content)).convert("RGB")
        return Image.open(Path(src)).convert("RGB")

    @torch.no_grad()
    def clip_score(self, caption: str, image_src: str) -> dict:
        """
        Return similarity between caption and image.
        
        Args:
            caption (str): text query
            image_src (str): HTTPS URL or local path
            
        Returns:
            dict: {'cosine_similarity': float in [-1,1], 'clip_logit': float}
        """
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
    
    def process_dataframe(self, df: pd.DataFrame, target_caption: str, similarity_threshold: float = 0.3) -> pd.DataFrame:
        """
        Process DataFrame with URLs and calculate similarity scores against target caption
        
        Args:
            df (pandas.DataFrame): DataFrame with 'caption' and 'url' columns
            target_caption (str): Target caption to compare against
            similarity_threshold (float): Minimum similarity score threshold
            
        Returns:
            pandas.DataFrame: DataFrame with captions, URLs, and similarity scores > threshold
        """
        results = []
        
        print(f"Processing {len(df)} images...")
        
        for idx, row in df.iterrows():
            caption = row['caption']
            url = row['url']
            
            if pd.isna(url) or url is None:
                continue
                
            try:
                # Calculate similarity score
                similarity_result = self.clip_score(target_caption, url)
                cosine_sim = similarity_result.get('cosine_similarity', 0)
                clip_logit = similarity_result.get('clip_logit', 0)
                
                # Only add to results if similarity score is above threshold
                if cosine_sim > similarity_threshold:
                    results.append({
                        'caption': caption,
                        'url': url,
                        'cosine_similarity': cosine_sim,
                        'clip_logit': clip_logit,
                        'original_index': idx
                    })
                
                # Progress indicator
                if idx % 50 == 0:
                    print(f"Processed {idx} images, current similarity: {cosine_sim:.4f}")
                    
            except Exception as e:
                print(f"Error processing image {idx}: {str(e)}")
                continue
        
        # Convert results to DataFrame
        if results:
            result_df = pd.DataFrame(results)
            # Sort by similarity score (highest first)
            result_df = result_df.sort_values('cosine_similarity', ascending=False)
            print(f"Found {len(result_df)} images with similarity score > {similarity_threshold}")
            return result_df
        else:
            print(f"No images found with similarity score > {similarity_threshold}")
            return pd.DataFrame(columns=['caption', 'url', 'cosine_similarity', 'clip_logit', 'original_index'])
    
    def process_captions_with_urls(self, captions_json: dict, target_caption: str = None, similarity_threshold: float = 0.3) -> dict:
        """
        Process captions with URLs and calculate similarity scores
        
        Args:
            captions_json (dict): JSON with captions and URLs
            target_caption (str): Target caption to compare against (optional)
            similarity_threshold (float): Minimum similarity score threshold
            
        Returns:
            dict: JSON with captions, URLs, and similarity scores
        """
        results = {}
        
        for key, data in captions_json.items():
            caption = data.get('caption')
            url = data.get('url')
            
            if not url:
                results[key] = {
                    'caption': caption,
                    'url': url,
                    'cosine_similarity': None,
                    'clip_logit': None,
                    'passed_threshold': False
                }
                continue
            
            try:
                # Use target_caption if provided, otherwise use the caption itself
                comparison_caption = target_caption if target_caption else caption
                
                # Calculate similarity score
                similarity_result = self.clip_score(comparison_caption, url)
                
                cosine_sim = similarity_result.get('cosine_similarity', 0)
                clip_logit = similarity_result.get('clip_logit', 0)
                
                results[key] = {
                    'caption': caption,
                    'url': url,
                    'cosine_similarity': cosine_sim,
                    'clip_logit': clip_logit,
                    'passed_threshold': cosine_sim > similarity_threshold
                }
                
                print(f"Processed {key}: similarity = {cosine_sim:.4f}, passed threshold = {cosine_sim > similarity_threshold}")
                
            except Exception as e:
                print(f"Error processing {key}: {str(e)}")
                results[key] = {
                    'caption': caption,
                    'url': url,
                    'cosine_similarity': None,
                    'clip_logit': None,
                    'passed_threshold': False,
                    'error': str(e)
                }
        
        return results
    
    def get_filtered_results(self, results: dict, similarity_threshold: float = 0.3) -> dict:
        """
        Filter results to only include items that passed the similarity threshold
        
        Args:
            results (dict): Results from process_captions_with_urls
            similarity_threshold (float): Minimum similarity score threshold
            
        Returns:
            dict: Filtered results with only passed items
        """
        filtered = {}
        for key, data in results.items():
            if data.get('passed_threshold', False):
                filtered[key] = data
        
        return filtered


# Example usage (commented out for import)
# if __name__ == "__main__":
#     scorer = SimilarityScorer()
#     
#     # Example DataFrame
#     df = pd.DataFrame({
#         'caption': ['A towel on white background', 'A red towel'],
#         'url': ['https://example.com/image1.jpg', 'https://example.com/image2.jpg']
#     })
#     
#     target_caption = "A clear image of a whole towel on a plain, uncluttered background."
#     
#     # Process DataFrame
#     results_df = scorer.process_dataframe(df, target_caption, similarity_threshold=0.3)
#     print(results_df)
