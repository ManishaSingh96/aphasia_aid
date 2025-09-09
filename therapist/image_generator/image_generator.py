import os
import json
import pandas as pd

from therapist.image_generator.store_embeddings import store_embeddings
from therapist.image_generator.caption_scorer import caption_scorer
from therapist.image_generator.caption_generator import CaptionGenerator
from therapist.image_generator.create_sim_score import SimilarityScorer
from therapist.image_generator.helper_functions import *


class generate_image:
    def __init__(self, model, batch_size, metadata_file="object_metadata.json"):
        self.embedding_model = model
        self.batch_size = batch_size
        self.scorer = caption_scorer()
        self.caption_generator = CaptionGenerator()
        self.store_emebddings = store_embeddings(model=self.embedding_model, batch_size=self.batch_size,
                                                 max_rows=2000)
        self.create_sim_score = SimilarityScorer()

        # metadata file to store object → {caption, url, sim_score}
        self.metadata_file = metadata_file
        self.metadata = self._load_metadata()

    def _load_metadata(self):
        """Load JSON metadata file if exists, else return empty dict"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        return {}

    def _save_metadata(self):
        """Save current metadata to file"""
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=4)

    def generate_image(self, object_name, df):
        emb_df = self.store_emebddings.generate_embeddings(object_name, df)
        captions = self.caption_generator.generate_positive_and_negative_captions(object_name)
        print("captions ", captions)

        scored_df = self.scorer.score_embeddings_df_with_pos_neg(
            emb_df, captions=captions, model=self.embedding_model
        )
        scored_df["score"] = scored_df["pos_sims"] - scored_df["neg_sims"]

        top_caption = scored_df.sort_values("pos_sims", ascending=False).head(10)
        target_caption = (
            f"A clear, well-focused and real-life image of {object_name} "
            "centered on a plain, uncluttered background"
        )

        sim_score_df = self.create_sim_score.score_dataframe_with_image(top_caption, target_caption)
        best_row = sim_score_df.sort_values("sim_score_image", ascending=False).iloc[0]
        top_img_caption = best_row["caption"]
        top_img_url = best_row["url"]
        top_img_sim_score = float(best_row["sim_score_image"])
        # Check metadata and update if necessary
        if object_name not in self.metadata:
            self.metadata[object_name] = {
                "caption": top_img_caption,
                "url": top_img_url,
                "sim_score": top_img_sim_score,
            }
            
        else:
            existing_score = self.metadata[object_name]["sim_score"]
            if top_img_sim_score > existing_score:
                self.metadata[object_name] = {
                    "caption": top_img_caption,
                    "url": top_img_url,
                    "sim_score": top_img_sim_score,
                }
                
            else:
                print(f"⏩ Kept existing entry for '{object_name}' (score {existing_score:.4f} >= {top_img_sim_score:.4f})")

        # Save changes to JSON
        self._save_metadata()

        return self.metadata[object_name] ['url'] # return best entry


if __name__ == "__main__":
    img = generate_image(model="text-embedding-3-large", batch_size=100)
    result = img.generate_image(object_name="window", df=pd.DataFrame())
    print(result)
