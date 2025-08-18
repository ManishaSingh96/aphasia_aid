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

if __name__ == "__main__":
    # Example usage
    keyword = 'towel'
    
    # Step 1: Read parquet file
    print("Step 1: Reading parquet file...")
    df = read_parquet_file(keyword)
    print(f"Found {len(df)} captions containing '{keyword}'")
    
    # Step 2: Convert to LLM message
    print("Step 2: Converting to LLM message format...")
    message = convert_to_llm_message(df.iloc[73:74,:])
    print(f"Converted {len(message.split('caption')) - 1} captions to message format")
    message="the towels in white"
    # Step 3: Call LLM
    print("Step 3: Calling LLM...")
    result = call_llm(keyword, message)

    print("LLM Response:")
    print(clean_json(result))
    
    # Step 4: Parse JSON and find URLs
    print("\nStep 4: Parsing JSON and finding URLs...")
    parsed_json = json.loads(clean_json(result))
    
    # Create new JSON with captions and URLs
    captions_with_urls = {}
    
    for key, caption in parsed_json.items():
        print(f"Searching for caption: {caption}")
        
        # Search for this caption in the filtered DataFrame
        # Clean the caption for comparison
        caption_clean = re.sub(r'\s+', ' ', caption.strip())
        
        # Find matching rows in the DataFrame
        matches = df[df['caption'].str.contains(re.escape(caption_clean), case=False, na=False)]
        
        if not matches.empty:
            # Take the first match
            url = matches.iloc[0]['url']
            captions_with_urls[key] = {
                'caption': caption,
                'url': url
            }
            print(f"Found URL: {url}")
        else:
            captions_with_urls[key] = {
                'caption': caption,
                'url': None
            }
            print("No URL found for this caption")
    
    # Print the final JSON with captions and URLs
    print("\nFinal JSON with captions and URLs:")
    print(json.dumps(captions_with_urls, indent=2))
    
    # Step 5: Calculate similarity scores
    print("\nStep 5: Calculating similarity scores...")
    scorer = SimilarityScorer()
    
    # Define target caption for comparison
    target_caption = f"""A clear image of a whole {keyword} on a plain, uncluttered background. 
The object is centered, well-lit, and sharply visible with natural colors. 
The image should appear simple and easily recognizable, like a textbook or flashcard illustration. 
The {keyword} should have a common everyday appearance familiar in an Indian household. 
The background should be clean and text-free,logo-free and marks-free so the object remains the only focus.



"""
    
    # Process captions with similarity scoring
    results_with_scores = scorer.process_captions_with_urls(
        captions_with_urls,
        target_caption=target_caption,
        similarity_threshold=0
    )
    
    print("\nResults with similarity scores:")
    print(json.dumps(results_with_scores, indent=2))
    
    # Step 6: Get filtered results (only those that passed threshold)
    print("\nStep 6: Filtered results (passed threshold):")
    filtered_results = scorer.get_filtered_results(results_with_scores, similarity_threshold=0.3)
    print(json.dumps(filtered_results, indent=2))
    
    print(f"\nSummary: {len(filtered_results)} out of {len(results_with_scores)} captions passed the similarity threshold.")



