import os
import requests
import random
import time
from google import genai

# ১. সিক্রেট চাবিগুলা নেওয়া
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

# ভাইরাল অপটিক্যাল ইলিউশন ব্যাকআপ ডাটাবেজ
FALLBACK_TEMPLATES = [
    {
        "prompt": "A ultra-realistic hidden camouflage leopard perfectly blended into rocky autumn trees and dry brown leaves optical illusion, high contrast, highly detailed",
        "caption": "Only 1% of people can spot the hidden leopard in under 5 seconds! Comment what you see 👇 🧠 #OpticalIllusion #MindBender"
    },
    {
        "prompt": "A mind-bending impossible triangle optical illusion geometry structure made of glowing neon glass blocks in a surreal dark ambient environment",
        "caption": "Your brain will freeze trying to figure this out! Can you trace the shape? 🌀 #OpticalIllusion #BrainTeaser"
    },
    {
        "prompt": "An owl hidden seamlessly in the wooden bark of an old ancient tree trunk optical illusion artwork, ultra vivid, detailed texture",
        "caption": "Find the hidden owl in this tree bark! 95% fail on the first try! 🦉 #OpticalIllusion #MindBender"
    },
    {
        "prompt": "A optical illusion image of a hidden lion face woven into a mountain landscape with waterfalls and pine trees",
        "caption": "Is it a mountain or a majestic lion? Look closely! 🦁 #OpticalIllusion #BrainTeaser"
    }
]

def generate_content():
    # জেমিনি এআই দিয়ে ট্রাই করা
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        selected_category = random.choice([
            "Hidden Animals Optical Illusion",
            "Mind-bending Geometry & Impossible Shapes",
            "Color Perception & Hidden Word Illusion Puzzle",
            "Double Meaning Camouflage Optical Illusion Art"
        ])
        
        prompt = f"""
        You are a viral social media expert specializing in US viral optical illusions.
        Category: {selected_category}

        Generate response in EXACTLY two lines:
        Line 1: A highly detailed, realistic image generation prompt for an optical illusion.
        Line 2: A super engaging short Facebook caption with EXACTLY TWO viral hashtags.
        """
        
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )
        
        if response and response.text:
            lines = [line.strip() for line in response.text.strip().split("\n") if line.strip()]
            image_prompt = lines[0].replace("Line 1:", "").strip()
            caption = lines[1].replace("Line 2:", "").strip() if len(lines) > 1 else "Can you spot the hidden secret? Comment below! 🧠 #OpticalIllusion #MindBender"
            print("Successfully generated content via Gemini API!")
            return image_prompt, caption
            
    except Exception as e:
        print(f"Gemini API currently busy or down ({e}). Using viral fallback template!")
        
    # গুগল এআই ডাউন থাকলে ব্যাকআপ টেমপ্লেট থেকে অটোম্যাটিক পিক করবে
    fallback = random.choice(FALLBACK_TEMPLATES)
    return fallback["prompt"], fallback["caption"]

def generate_image_url(image_prompt):
    seed = random.randint(1, 999999)
    formatted_prompt = requests.utils.quote(f"masterpiece, high quality, 8k resolution, viral optical illusion, {image_prompt}")
    image_url = f"https://pollinations.ai/p/{formatted_prompt}?width=1080&height=1080&seed={seed}&model=flux&nologo=true"
    return image_url

def post_to_facebook(image_url, caption):
    url = f"https://graph.facebook.com/v22.0/{FB_PAGE_ID}/photos"
    payload = {
        'url': image_url,
        'caption': caption,
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
