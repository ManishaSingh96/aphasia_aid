from pathlib import Path
import os
import pandas as pd
from pathlib import Path
from helper_functions import *
from caption_generator import CaptionGenerator
import re

class caption_gen:
    def __init__(self, source_parquet="cc12m_7m_subset_translated.parquet"):
        self.source_parquet = str(Path(__file__).parent / source_parquet)
        self.cc=CaptionGenerator()
    def get_caption(self, object_name):
        df = pd.read_parquet(self.source_parquet)

        # Step 1: Filter with object name
        filtered_df = filter_df_with_object(df, object_name)
        print(f"Filtered rows for '{object_name}': {len(filtered_df)}")

        if filtered_df.empty:
            print("No rows after filtering. Exiting.")
            return pd.DataFrame()

        # Step 2: Filter captions with less than 20 tokens
        filtered_df["token_length"] = filtered_df["caption"].str.split().apply(len)
        filtered_df = filtered_df[filtered_df["token_length"] <= 20]
        print(f"Remaining after token length filter: {len(filtered_df)}")

        # Step 3: Generate negative patterns using your regex agent
        NEGATIVE_PATTERNS = self.cc.generate_positive_and_negative_captions(object_name)['NEGATIVE_PATTERNS']
        # print ("aaa")
        # print(NEGATIVE_PATTERNS)  # <- your LLM agent call
        
        # NEGATIVE_PATTERNS=[
        # # ".*\\btowels?\\b.*\\b(soap|shampoo|conditioner|sponge|sink|rack|mirror|hook|shower|bucket|toothbrush)\\b.*",
        # # ".*\\b(cat|dog|elephant|animal|pet|bear|duck|mouse|toy)\\b.*\\btowels?\\b.*",
        # # ".*\\btowels?\\b.*\\b(bed|couch|chair|carpet|table|sofa|floor|furniture|curtain)\\b.*",
        # # ".*\\btowels?\\b.*\\b(hotel|bathroom|room|spa|gym|changing room|locker)\\b.*",
        # # ".*\\btowels?\\b.*\\b(bar|brass|steel|rod|rack|double|standard|aged)\\b.*",
        # # ".*\\btowels?\\b.*\\b(elephant|origami|sculpture|folded like|shaped like|designed like)\\b.*",
        # # ".*\\btowels?\\b.*\\b(shoulders|wrapped around|covering|wearing)\\b.*",
        # # ".*\\btowels?\\b.*\\b(next to|with|on top of|near|underneath|beside|between|along with|together with)\\b.*\\b(soap|mirror|shampoo|cat|bed|bucket|clothes|hook|wall|floor)\\b.*"
        #                  ]

        def has_negative_pattern(caption):
            for pattern in NEGATIVE_PATTERNS:
                # print(pattern)
                if re.search(pattern, caption.lower()):
                    return True
            return False

        # Step 4: Remove captions with negative patterns
        filtered_df = filtered_df[~filtered_df["caption"].apply(has_negative_pattern)]
        print(f"Remaining after regex pattern filtering: {len(filtered_df)}")

        # Step 5: Save results
        result_path = Path(__file__).parent / f"{object_name}_final_captions.csv"
        filtered_df[["caption", "url"]].to_csv(result_path, index=False)
        print(f"Final captions saved to: {result_path}")

        return filtered_df

if __name__ == "__main__":
    img=caption_gen()
    top_caption=img.get_caption(object_name='eggs')
        

