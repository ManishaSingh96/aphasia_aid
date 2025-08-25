import os
import sys
import pandas as pd

from therapist.image_generator.store_embeddings import store_embeddings
from therapist.image_generator.caption_scorer import caption_scorer
from therapist.image_generator.caption_generator import CaptionGenerator
# from therapist.image_generator.create_sim_score import SimilarityScorer
from therapist.image_generator.helper_functions import *



class generate_image:
    def __init__(self,model,batch_size):
        self.embedding_model=model
        self.batch_size=batch_size
        self.scorer = caption_scorer()
        self.caption_generator=CaptionGenerator()
        self.store_emebddings=store_embeddings(model=self.embedding_model, batch_size=self.batch_size,
                 source_parquet="cc12m_7m_subset_translated.parquet",
                 max_rows=200)
        # self.create_sim_score=SimilarityScorer()

    def generate_image(self,object_name):
        emb_df = self.store_emebddings.generate_embeddings(object_name)
        captions=self.caption_generator.generate_positive_and_negative_captions(object_name)
        print("captions ",captions)
        scored_df = self.scorer.score_embeddings_df_with_pos_neg(emb_df, captions=captions, model=self.embedding_model)
        scored_df["score"] = scored_df["pos_sims"] - scored_df["neg_sims"]
        top_caption=scored_df.sort_values('score',ascending=False).head(1)
        # target_caption=f"""A clear, well-focused and  well -lit picture of {object_name} on a plain, uncluttered background"""
        # sim_score_df=self.create_sim_score.score_dataframe_with_image(top_caption,target_caption)

        # return sim_score_df.sort_values('score',ascending=False).head(1)['url']
        # print("url")
        # print(top_caption['url'])
        # print("aa")
        
        img_url=top_caption['url'].iloc[0]

        return img_url
    
if __name__ == "__main__":
    img=generate_image(model='text-embedding-3-large',batch_size=100)
    top_caption=img.generate_image(object_name='window')
        


