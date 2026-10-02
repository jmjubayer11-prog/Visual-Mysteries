import os
import re
import sys
import time
import random
import requests
from google import genai

# ১. সিক্রেট চাবিগুলা নেওয়া (.strip() দিয়ে ভুল করে আসা স্পেস/নতুন লাইন কেটে ফেলা হচ্ছে)
GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or "").strip()
FB_PAGE_ID = (os.environ.get("FB_PAGE_ID") or "").strip()
FB_PAGE_ACCESS_TOKEN = (os.environ.get("FB_PAGE_ACCESS_TOKEN") or "").strip()

GEMINI_MODEL = "gemini-3.8-flash"
GRAPH_API_VERSION = "v22.0"

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

DEFAULT_CAPTION = "Can you spot the hidden secret? Comment below! 🧠 #OpticalIllusion #MindBender"


def clean_line(line):
    """জেমিনির লাইন থেকে 'Line 1:' বা মার্কডাউন তারকা চিহ্ন সরানো"""
    line = line.strip()
    line = re.sub(r"^[\*\-\s]*(Line\s*\d\s*:)\s*", "", line, flags=re.IGNORECASE)
    return line.strip().strip("*").strip()


def generate_content():
    # জেমিনি এআই দিয়ে ট্রাই করা (ব্যস্ত থাকলে ৩ বার চেষ্টা করবে)
    max_attempts = 3
    wait_times = [5, 15]

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

    for attempt in range(1, max_attempts + 1):
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )

            text = (response.text or "").strip() if response else ""
            lines = [ln for ln in text.split("\n") if ln.strip()]

            if lines:
                image_prompt = clean_line(lines[0])
                caption = clean_line(lines[1]) if len(lines) > 1 else DEFAULT_CAPTION
                if image_prompt:
                    print("Successfully generated content via Gemini API!")
                    return image_prompt, (caption or DEFAULT_CAPTION)

            print(f"Gemini attempt {attempt}/{max_attempts}: empty or invalid response.")

        except Exception as e:
            print(f"Gemini attempt {attempt}/{max_attempts} failed: {e}")

        if attempt < max_attempts:
            time.sleep(wait_times[attempt - 1])

    # গুগল এআই ডাউন থাকলে ব্যাকআপ টেমপ্লেট থেকে অটোম্যাটিক পিক করবে
    print("Gemini API currently busy or down. Using viral fallback template!")
    fallback = random.choice(FALLBACK_TEMPLATES)
    return fallback["prompt"], fallback["caption"]


def build_image_urls(image_prompt):
    # প্রম্পট খুব বড় হলে URL ভেঙে যেতে পারে, তাই ৫০০ অক্ষরে সীমিত
    image_prompt = image_prompt[:500]
    seed = random.randint(1, 999999)
    full_prompt = f"masterpiece, high quality, 8k resolution, viral optical illusion, {image_prompt}"
    encoded = requests.utils.quote(full_prompt, safe="")
    params = f"width=1080&height=1080&seed={seed}&model=flux&nologo=true"
    return [
        f"https://pollinations.ai/p/{encoded}?{params}",
        f"https://image.pollinations.ai/prompt/{encoded}?{params}",
    ]


def download_image(urls):
    """ছবি ডাউনলোড করে এবং আসলেই ছবি কিনা যাচাই করে"""
    for url in urls:
        for attempt in range(1, 3):
            try:
                r = requests.get(url, timeout=120)
                content_type = r.headers.get("Content-Type", "")
                if r.status_code == 200 and content_type.startswith("image/") and len(r.content) > 5000:
                    print("Image downloaded successfully!")
                    return r.content, content_type.split(";")[0].strip()
                print(f"Image download problem (status {r.status_code}, type '{content_type}', size {len(r.content)} bytes).")
            except requests.RequestException as e:
                print(f"Image download error: {e}")
            time.sleep(5)
    return None, None


def verify_page_token():
    """টোকেনটা সত্যিই এই Page-এর কিনা চেক করা (publish_actions এররের মূল কারণ এখানেই ধরা পড়বে)"""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/me"
    try:
        res = requests.get(
            url,
            params={"fields": "id,name", "access_token": FB_PAGE_ACCESS_TOKEN},
            timeout=30
        )
    except requests.RequestException as e:
        print("Could not reach Facebook to verify token:", e)
        return False

    if res.status_code != 200:
        print("Facebook token is invalid or expired:", res.text)
        return False

    data = res.json()
    if data.get("id") != FB_PAGE_ID:
        print(
            "TOKEN MISMATCH: this token belongs to "
            f"'{data.get('name')}' (id {data.get('id')}), not to Page id {FB_PAGE_ID}.\n"
            "Use the PAGE access token (from /me/accounts) and the correct PAGE ID, "
            "not a personal user token or profile ID."
        )
        return False

    print(f"Token OK: posting as Page '{data.get('name')}'.")
    return True


def post_to_facebook(img_data, mime_type, caption):
    # সরাসরি মেটা গ্রাফ এপিআই ফটোস বাইনারি আপলোড
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{FB_PAGE_ID}/photos"
    payload = {
        "caption": caption,
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    extension = "png" if mime_type == "image/png" else "jpg"
    files = {
        "source": (f"image.{extension}", img_data, mime_type)
    }

    try:
        res = requests.post(url, data=payload, files=files, timeout=120)
    except requests.RequestException as e:
        print("Failed to post (network error):", e)
        return False

    if res.status_code == 200 and "id" in res.json():
        print("Successfully posted viral optical illusion to Facebook!")
        return True

    print("Failed to post:", res.text)
    return False


if __name__ == "__main__":
    # দরকারি সিক্রেট আছে কিনা আগেই চেক
    missing = [name for name, value in [
        ("FB_PAGE_ID", FB_PAGE_ID),
        ("FB_PAGE_ACCESS_TOKEN", FB_PAGE_ACCESS_TOKEN),
    ] if not value]
    if missing:
        print(f"Missing required secrets: {', '.join(missing)}")
        sys.exit(1)

    if not verify_page_token():
        sys.exit(1)

    img_prompt, fb_caption = generate_content()
    image_urls = build_image_urls(img_prompt)

    image_bytes, image_mime = download_image(image_urls)
    if not image_bytes:
        print("Could not download a valid image. Aborting.")
        sys.exit(1)

    if not post_to_facebook(image_bytes, image_mime, fb_caption):
        sys.exit(1)
