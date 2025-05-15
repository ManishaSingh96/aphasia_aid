from sentence_transformers import SentenceTransformer
from datasets import load_dataset
import faiss
import numpy as np
import requests
from PIL import Image
from io import BytesIO

# 1. Load model and dataset
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
dataset = load_dataset("M-CLIP/ImageCaptions-7M-Translations", split="train[:1000]")  # small sample for demo

# 2. Encode captions
captions = [item["en"] for item in dataset]
caption_embeddings = model.encode(captions, show_progress_bar=True)

# 3. Build FAISS index
dim = caption_embeddings[0].shape[0]
index = faiss.IndexFlatL2(dim)
index.add(np.array(caption_embeddings))

# 4. Define a query function
def retrieve_image(query: str, top_k=1):
    query_embedding = model.encode([query])
    D, I = index.search(np.array(query_embedding), top_k)
    
    results = []
    for idx in I[0]:
        caption = dataset[idx]["en"]
        image_url = dataset[idx]["image"]  # This is a PIL image object if preprocessed by HuggingFace
        results.append((caption, image_url))
    
    return results

# 5. Test with a query
query = "a red football"
results = retrieve_image(query)

# 6. Display result
for caption, image_obj in results:
    print("Caption:", caption)
    if isinstance(image_obj, Image.Image):
        image_obj.show()
    elif isinstance(image_obj, str):
        # If it's a URL or file path
        response = requests.get(image_obj)
        img = Image.open(BytesIO(response.content))
        img.show()
