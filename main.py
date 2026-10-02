import os
import requests
import random
import time
from google import genai

# ১. পরিবেশের সিক্রেট কি (Environment Variables) রিড করা
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

# ভাইরাল অপটিক্যাল ইলিউশন ব্যাকআপ ডাটাবেজ (জেমিনি লিমিট শেষ হলে ব্যবহারের জন্য)
FALLBACK_TEMPLATES = [
    {
        "prompt": "A ultra realistic hidden camouflage leopard perfectly blended into rocky autumn trees and dry brown leaves optical illusion, high contrast, 8k",
        "caption": "Only 1% of people can spot the hidden leopard in under 5 seconds! Comment what you see 👇 🧠 #OpticalIllusion #MindBender"
    },
    {
        "prompt": "A mind-bending impossible triangle optical illusion geometry structure made of glowing neon glass blocks in a dark ambient environment, 8k",
        "caption": "Your brain will freeze trying to figure this out! Can you trace the shape? 🌀 #OpticalIllusion #BrainTeaser"
    },
    {
        "prompt": "An owl hidden seamlessly in the wooden bark of an old ancient tree trunk optical illusion artwork, ultra vivid, detailed texture",
        "caption": "Find the hidden owl in this tree bark! 95% fail on the first try! 🦉 #OpticalIllusion #MindBender"
    },
    {
        "prompt": "A high contrast optical illusion image of a hidden lion face woven into a mountain landscape with waterfalls and pine trees",
        "caption": "Is it a mountain or a majestic lion? Look closely! 🦁 #OpticalIllusion #BrainTeaser"
    }
]

def generate_content():
    """জেমিনি এপিআই থেকে প্রম্পট ও ক্যাপশন জেনারেট করা, ব্যর্থ হলে ব্যাকআপ ব্যবহার করা"""
    image_prompt = None
    caption = None

    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = """
            You are a viral social media expert specializing in optical illusions.
            Generate response in EXACTLY two lines:
            Line 1: A highly detailed image generation prompt for a stunning optical illusion (e.g., hidden animals, camouflage, or impossible geometry). Do NOT include "Line 1:".
            Line 2: An engaging short Facebook caption asking users what they see with 2 viral hashtags. Do NOT include "Line 2:".
            """
            
            # অফিসিয়াল স্ট্যাবল মডেল gemini-2.5-flash ব্যবহার করা হচ্ছে
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            if response and response.text:
                lines = [line.strip() for line in response.text.strip().split("\n") if line.strip()]
                if len(lines) >= 1:
                    image_prompt = lines[0].replace("Line 1:", "").strip()
                if len(lines) >= 2:
                    caption = lines[1].replace("Line 2:", "").strip()
                print("Successfully generated content using Gemini API!")
        except Exception as e:
            print(f"Gemini API Exception ({e}). Switching to viral fallback template!")

    # জেমিনি কাজ না করলে বা রেসপন্স খালি থাকলে ফলব্যাক নেওয়া
    if not image_prompt or not caption:
        fallback = random.choice(FALLBACK_TEMPLATES)
        image_prompt = fallback["prompt"]
        caption = fallback["caption"]
        print("Using fallback template for prompt and caption.")

    return image_prompt, caption

def generate_and_download_image(image_prompt):
    """ছবি জেনারেট ও সঠিক ফরম্যাটে (JPG) লোকাল ফাইলে সেভ করা"""
    seed = random.randint(1, 999999)
    encoded_prompt = requests.utils.quote(f"masterpiece, high quality, 8k resolution, optical illusion, {image_prompt}")
    
    # Pollinations AI এর সরাসরি ইমেজ ইউআরএল
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&seed={seed}&nologo=true"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        res = requests.get(image_url, headers=headers, timeout=45)
        # নিশ্চিত করা ফাইলটা সত্যি ছবি (HTML বা অন্য কিছু নয়)
        if res.status_code == 200 and len(res.content) > 10000 and 'image' in res.headers.get('Content-Type', '').lower():
            with open("illusion.jpg", "wb") as f:
                f.write(res.content)
            print("Successfully downloaded and saved valid image as illusion.jpg!")
            return "illusion.jpg"
        else:
            print(f"Pollinations response invalid (Status: {res.status_code}, Type: {res.headers.get('Content-Type')}). Fetching reliable fallback image...")
    except Exception as e:
        print(f"Error fetching image from Pollinations: {e}. Fetching fallback image...")

    # Pollinations এ কোনো সমস্যা হলে Picsum থেকে গ্যারান্টিড ইমেজ নামানো
    fallback_url = f"https://picsum.photos/seed/{seed}/1080/1080"
    fb_res = requests.get(fallback_url, headers=headers, timeout=30)
    with open("illusion.jpg", "wb") as f:
        f.write(fb_res.content)
    print("Fallback image saved successfully as illusion.jpg!")
    return "illusion.jpg"

def post_to_facebook(image_path, caption):
    """মেটা গ্রাফ এপিআই দিয়ে ফেসবুকে সরাসরি ছবি আপলোড করা"""
    url = f"https://graph.facebook.com/v22.0/{FB_PAGE_ID}/photos"
    
    payload = {
        'caption': caption,
        'access_token': FB_PAGE_ACCESS_TOKEN
    }
    
    try:
        with open(image_path, 'rb') as img_file:
            files = {
                'source': ('illusion.jpg', img_file, 'image/jpeg')
            }
            res = requests.post(url, data=payload, files=files)
            
        if res.status_code == 200:
            print("SUCCESS: Posted optical illusion to Facebook Page!")
            print("Response:", res.json())
        else:
            print("FAILED to post to Facebook. Status Code:", res.status_code)
            print("Error Details:", res.text)
    except Exception as e:
        print(f"Exception while posting to Facebook: {e}")

if __name__ == "__main__":
    # ১. কন্টেন্ট জেনারেট করা
    prompt, fb_caption = generate_content()
    
    # ২. ছবি তৈরি ও লোকাল ফাইলে নামানো
    img_path = generate_and_download_image(prompt)
    
    # ৩. ফেসবুক পেজে পোস্ট করা
    post_to_facebook(img_path, fb_caption)
