import os
import requests
import random
import time
from google import genai

# ১. গিটহাব সিক্রেটস থেকে কি ও আইডিগুলো নেওয়া
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

# ২. গুগল জেমেনি ক্লায়েন্ট
client = genai.Client(api_key=GEMINI_API_KEY)

# ব্যাকআপ ভাইরাল অপটিক্যাল ইলিউশন ডাটাবেজ
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
    try:
        selected_category = random.choice([
            "Hidden Animals Optical Illusion (e.g., find the hidden leopard, owl, or tiger in nature)",
            "Mind-bending Geometry & Impossible Shapes Optical Illusion",
            "Color Perception & Hidden Number/Word Illusion Puzzle",
            "Double Meaning Camouflage Optical Illusion Art"
        ])
        
        prompt = f"""
        You are a viral social media expert specializing in US viral optical illusions and brain teasers.
        Category for this post: {selected_category}

        Generate response in EXACTLY two lines:
        Line 1: A highly detailed, realistic, vivid image generation prompt for creating a stunning, high-contrast optical illusion matching the category. Do NOT include words like "Line 1".
        Line 2: A super engaging short Facebook caption driving comments/shares (e.g., "Only 1% of people can spot it in under 5 seconds! Comment what you see 👇") followed by EXACTLY TWO powerful viral hashtags. Do NOT include words like "Line 2".
        """
        
        response = None
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt
                )
                if response and response.text:
                    print(f"Successfully generated content using gemini-3.8-flash on attempt {attempt + 1}!")
                    break
            except Exception as e:
                print(f"Gemini attempt {attempt + 1} failed: {e}")
                time.sleep(2)
        
        if response and response.text:
            lines = [line.strip() for line in response.text.strip().split("\n") if line.strip()]
            image_prompt = lines[0].replace("Line 1:", "").strip()
            caption = lines[1].replace("Line 2:", "").strip() if len(lines) > 1 else "Can you spot the hidden secret in 5 seconds? Comment below! 🧠 #OpticalIllusion #MindBender"
            return image_prompt, caption
            
    except Exception as e:
        print(f"Gemini API unavailable ({e}). Switching to viral fallback template!")
        
    fallback = random.choice(FALLBACK_TEMPLATES)
    return fallback["prompt"], fallback["caption"]

def generate_image_and_save(image_prompt):
    seed = random.randint(1, 999999)
    formatted_prompt = requests.utils.quote(f"masterpiece, high quality, 8k resolution, viral optical illusion, {image_prompt}")
    image_url = f"https://pollinations.ai/p/{formatted_prompt}?width=1080&height=1080&seed={seed}&model=flux&nologo=true"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    res = requests.get(image_url, headers=headers)
    if res.status_code == 200:
        with open("illusion.jpg", "wb") as f:
            f.write(res.content)
        print("Image downloaded and saved successfully as illusion.jpg!")
        return "illusion.jpg"
    else:
        raise Exception(f"Failed to download image. Status code: {res.status_code}")

def post_to_facebook(image_path, caption):
    url = f"https://graph.facebook.com/v22.0/{FB_PAGE_ID}/photos"
    payload = {
        'caption': caption,
        'access_token': FB_PAGE_ACCESS_TOKEN
    }
    
    with open(image_path, 'rb') as img_file:
        files = {
            'source': ('illusion.jpg', img_file, 'image/jpeg')
        }
        res = requests.post(url, data=payload, files=files)
        
    if res.status_code == 200:
        print("Successfully posted viral optical illusion to Facebook!")
    else:
        print("Failed to post:", res.text)

if __name__ == "__main__":
    img_prompt, fb_caption = generate_content()
    local_img_path = generate_image_and_save(img_prompt)
    post_to_facebook(local_img_path, fb_caption)
