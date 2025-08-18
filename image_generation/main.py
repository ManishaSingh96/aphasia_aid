import pandas as pd
from image_caption_gen import Image_Caption_Filter
import re
import json
from create_sim_score import SimilarityScorer



def clean_json(text):
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        json_text = match.group(1).strip()
        
    else:
        json_text=text
       
    return json_text

def read_parquet_file(keyword, file_path="cc12m_7m_subset_translated.parquet"):
    """
    Read parquet file and filter by keyword
    
    Args:
        keyword (str): Keyword to search for
        file_path (str): Path to parquet file
        
    Returns:
        pandas.DataFrame: Filtered dataframe
    """
    df = pd.read_parquet(file_path, columns=["caption", "url"])
    mask = df["caption"].str.contains(keyword, case=False, na=False)
    filtered_df = df.loc[mask].copy()
    return filtered_df

def convert_to_llm_message(df):
    """
    Convert dataframe captions to LLM input message format
    
    Args:
        df (pandas.DataFrame): DataFrame with captions
        
    Returns:
        str: Formatted message for LLM
    """
    s = (df['caption'].fillna("")
            .astype(str)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip())
    
    parts = [f"caption{i+1}: {text}\n" for i, text in enumerate(s) if text]
    return " ".join(parts)

def call_llm(keyword, captions_message):
    """
    Call LLM to get top captions
    
    Args:
        keyword (str): Target keyword
        captions_message (str): Formatted captions message
        
    Returns:
        str: LLM response
    """
    cc = Image_Caption_Filter()
    response = cc.generate_caption(object_name=keyword, captions=captions_message)
    return response

def _get_spacy_model():
    try:
        import spacy
        try:
            return spacy.load("en_core_web_sm")
        except Exception:
            print("spaCy model 'en_core_web_sm' not available; skipping noun removal.")
            return None
    except ImportError:
        print("spaCy not installed; skipping noun removal.")
        return None


def remove_excess_nouns(text, max_nouns: int = 5) -> str:
    if text is None:
        return ""
    doc_model = _get_spacy_model()
    if doc_model is None:
        return str(text)
    doc = doc_model(str(text))
    noun_tokens = [t for t in doc if t.pos_ in ("NOUN", "PROPN")]
    if len(noun_tokens) <= max_nouns:
        print(text)
        return str(text)
    kept_tokens = [t.text for t in doc if t.pos_ not in ("NOUN", "PROPN")]
    cleaned = " ".join(kept_tokens)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


if __name__ == "__main__":
    # Example usage
    keyword = 'towel'
    
    # Step 1: Read parquet file
    print("Step 1: Reading parquet file...")
    df = read_parquet_file(keyword)
    print(f"Found {len(df)} captions containing '{keyword}'")
    
    # Step 2: Filter captions by token length (< 20 words)
    print("Step 2: Filtering captions with token length < 20...")
    df_long = df.copy()
    df_long['token_len'] = (df_long['caption']
                            .fillna("")
                            .astype(str)
                            .str.split()
                            .str.len())
    df_long = df_long[df_long['token_len'] <10].drop(columns=['token_len'])
    print(f"Remaining after filter: {len(df_long)} rows")
    
    # Step 2b: Remove nouns if caption has more than 5 nouns
    print("Step 2b: Removing nouns from captions that have > 5 nouns...")
    df_long['caption'] = df_long['caption'].apply(lambda x: remove_excess_nouns(x, max_nouns=5))
    # Drop empty captions after noun removal
    df_long = df_long[df_long['caption'].astype(str).str.strip().ne("")]
    print(f"Remaining after noun removal: {len(df_long)} rows")
    
    df_long.to_csv('filtered.csv')
    
 #     # Step 3: Calculate similarity scores for filtered DataFrame
 #     print("Step 3: Calculating similarity scores for filtered URLs...")
 #     scorer = SimilarityScorer()
    
 #     # Define target caption for comparison
 #     target_caption = f"""A clear image of a whole {keyword} on a plain, uncluttered background. 
 # The object is centered, well-lit, and sharply visible with natural colors. 
 # The image should appear simple and easily recognizable, like a textbook or flashcard illustration. 
 # The {keyword} should have a common everyday appearance familiar in an Indian household. 
 # The background should be clean and text-free,logo-free and marks-free so the object remains the only focus.
 # """
    
 #     # Process captions with similarity scoring
 #     results_with_scores = scorer.process_dataframe(
 #         df=df_long.iloc[:50, :],
 #         target_caption=target_caption,
 #         similarity_threshold=0
 #     )
    
 #     print("\nResults with similarity scores:")
 #     print(json.dumps(results_with_scores, indent=2))
    
 #     # Step 6: Get filtered results (only those that passed threshold)
 #     print("\nStep 6: Filtered results (passed threshold):")
 #     filtered_results = scorer.get_filtered_results(results_with_scores, similarity_threshold=0.3)
 #     print(json.dumps(filtered_results, indent=2))
    
 #     print(f"\nSummary: {len(filtered_results)} out of {len(results_with_scores)} captions passed the similarity threshold.")



