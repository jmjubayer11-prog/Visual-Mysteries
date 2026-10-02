import os
import requests
import random
from google import genai

# ১. সিক্রেট চাবিগুলা নেওয়া
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

# ২. জেমিনি ক্লায়েন্ট সেটআপ
client = genai.Client(api_key=GEMINI_API_KEY)

# ভাইরাল অপটিক্যাল ইলিউশন ক্যাটাগরি
CATEGORIES = [
    "Hidden Animals Optical Illusion (e.g., find the hidden leopard, owl, or tiger in nature)",
    "Mind-bending Geometry & Impossible Shapes Optical Illusion",
    "Color Perception & Hidden Number/Word Illusion Puzzle",
    "Double Meaning Camouflage Optical Illusion Art"
]

def generate_content():
    selected_category = random.choice(CATEGORIES)
    
    prompt = f"""
    You are a viral social media expert specializing in US viral optical illusions and brain teasers.
    Category for this post: {selected_category}

    Generate response in EXACTLY two lines:
    Line 1: A highly detailed, realistic, vivid image generation prompt for creating a stunning, high-contrast optical illusion matching the category. Do NOT include words like "Line 1".
    Line 2: A super engaging short Facebook caption driving comments/shares (e.g., "Only 1% of people can spot it in under 5 seconds! Comment what you see 👇") followed by EXACTLY TWO powerful viral hashtags. Do NOT include words like "Line 2".
    """
    
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )
    
    lines = [line.strip() for line in response.text.strip().split("\n") if line.strip()]
    
    image_prompt = lines[0].replace("Line 1:", "").strip()
    caption = lines[1].replace("Line 2:", "").strip() if len(lines) > 1 else "Can you spot the hidden secret in 5 seconds? Comment below! 🧠 #OpticalIllusion #MindBender"
    
    return image_prompt, caption

def generate_image_url(image_prompt):
    seed = random.randint(1, 999999)
    formatted_prompt = requests.utils.quote(f"masterpiece, high quality, 8k resolution, viral optical illusion, {image_prompt}")
    image_url = f"https://pollinations.ai/p/{formatted_prompt}?width=1080&height=1080&seed={seed}&model=flux&nologo=true"
    return image_url

def post_to_facebook(image_url, caption):
    # মেটা গ্রাফ এপিআই v22.0 এর অফিশিয়াল ফিড মেথড
    url = f"https://graph.facebook.com/v22.0/{FB_PAGE_ID}/feed"
    payload = {
        'link': image_url,
        'message': caption,
        'access_token': FB_PAGE_ACCESS_TOKEN
    }
    res = requests.post(url, data=payload)
    if res.status_code == 200:
        print("Successfully posted viral optical illusion to Facebook!")
    else:
        print("Failed to post:", res.text)

if __name__ == "__main__":
    img_prompt, fb_caption = generate_content()
    img_url = generate_image_url(img_prompt)
    post_to_facebook(img_url, fb_caption)
