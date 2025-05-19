import openai
import os
from dotenv import load_dotenv
load_dotenv()
### Version: 1.77.0
# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_image(prompt, n=1, size="1024x1024"):
    """
    Generate an image using OpenAI's DALL·E.

    Args:
        prompt (str): Text prompt to generate the image.
        n (int): Number of images to generate.
        size (str): Size of the image. Options: "256x256", "512x512", "1024x1024".

    Returns:
        List of URLs to generated images.
    """
    response = openai.Image.create(
        prompt=prompt,
        n=n,
        size=size
    )
    images = [data['url'] for data in response['data']]
    return images

if __name__ == "__main__":
    prompt = "A friendly robot helping people with aphasia, digital art"
    images = generate_image(prompt)

    for idx, url in enumerate(images):
        print(f"Image {idx + 1}: {url}")
