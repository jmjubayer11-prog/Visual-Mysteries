import os
import sys
import time
import random
import requests

from urllib.parse import quote
from google import genai


# =========================================================
# CONFIGURATION
# =========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "").strip()
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()

GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION", "v22.0").strip()

# বর্তমান stable model আগে, বিকল্প model পরে।
GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash",
]

IMAGE_FILE = "illusion.jpg"
REQUEST_TIMEOUT = 45
MAX_RETRIES = 3

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "VisualMysteriesBot/2.0"
})


# =========================================================
# BACKUP CONTENT DATABASE
# =========================================================

FALLBACK_TEMPLATES = [
    {
        "prompt": (
            "Create a photorealistic optical illusion puzzle: "
            "a leopard naturally camouflaged among dry autumn leaves "
            "and rocky tree bark, the entire animal visible but difficult "
            "to spot, realistic natural textures, square composition, "
            "no text, no watermark."
        ),
        "caption": (
            "Can you spot the hidden leopard? 🐆 "
            "Tell us where it is! 👇 "
            "#OpticalIllusion #BrainTeaser"
        ),
    },
    {
        "prompt": (
            "Create a clever impossible triangle optical illusion "
            "made from realistic wooden beams, carefully aligned "
            "to create a physically impossible geometric structure, "
            "clean background, strong shadows, square composition, "
            "no text, no watermark."
        ),
        "caption": (
            "Is this shape actually possible? 🧠 "
            "Look closely and share your answer! 👇 "
            "#OpticalIllusion #MindBender"
        ),
    },
    {
        "prompt": (
            "Create a realistic hidden owl optical illusion, "
            "an owl naturally camouflaged within the rough bark "
            "of an old tree, detailed feathers blending into wood, "
            "believable natural lighting, square composition, "
            "no text, no watermark."
        ),
        "caption": (
            "Can you find the hidden owl? 🦉 "
            "Comment when you spot it! 👇 "
            "#OpticalIllusion #BrainTeaser"
        ),
    },
    {
        "prompt": (
            "Create a photorealistic mountain landscape optical illusion "
            "where the rock formations subtly form the face of a lion, "
            "pine trees and a waterfall, realistic natural details, "
            "the hidden face must be recognizable on closer inspection, "
            "square composition, no text, no watermark."
        ),
        "caption": (
            "Do you see a mountain or a lion? 🦁 "
            "Look again and tell us! 👇 "
            "#OpticalIllusion #MindBender"
        ),
    },
]


# =========================================================
# HTTP HELPERS
# =========================================================

def request_with_retries(method, url, **kwargs):
    """
    Retry only temporary network failures, rate limits,
    and server errors. Do not retry permanent HTTP errors.
    """

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = SESSION.request(
                method,
                url,
                timeout=REQUEST_TIMEOUT,
                **kwargs,
            )

            if response.status_code not in (429, 500, 502, 503, 504):
                return response

            last_error = (
                f"Temporary HTTP error: {response.status_code}"
            )

            if attempt < MAX_RETRIES - 1:
                retry_after = response.headers.get("Retry-After", "")
                try:
                    delay = min(max(int(retry_after), 1), 30)
                except (ValueError, TypeError):
                    delay = 2 ** attempt + random.random()

                print(
                    f"Temporary server error. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)

        except requests.RequestException as exc:
            last_error = str(exc)

            if attempt < MAX_RETRIES - 1:
                delay = 2 ** attempt + random.random()
                print(
                    f"Network error. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)

    raise RuntimeError(
        f"Request failed after {MAX_RETRIES} attempts: {last_error}"
    )


# =========================================================
# GEMINI CONTENT GENERATION
# =========================================================

def generate_content():
    """
    Generate image prompt and Facebook caption.
    If Gemini fails, use a verified local template.
    """

    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)

            instruction = """
You create original optical illusion puzzles for Facebook.

Generate exactly TWO non-empty lines.

LINE 1:
A detailed English image-generation prompt for one original,
visually understandable optical illusion. The image must be
square, realistic, suitable for Facebook, and contain no text
or watermark.

LINE 2:
A short engaging Facebook caption in English with a question
and exactly two relevant hashtags.

Do not add headings, numbering, quotation marks, or extra lines.
Do not use markdown.
"""

            for model_name in GEMINI_MODELS:
                try:
                    print(f"Trying Gemini model: {model_name}")

                    response = client.models.generate_content(
                        model=model_name,
                        contents=instruction,
                    )

                    if not response or not response.text:
                        print(f"{model_name}: Empty response.")
                        continue

                    lines = [
                        line.strip()
                        for line in response.text.splitlines()
                        if line.strip()
                    ]

                    # Malformed responses must not break the workflow.
                    if len(lines) < 2:
                        print(f"{model_name}: Invalid response format.")
                        continue

                    image_prompt = lines[0]
                    caption = " ".join(lines[1:])

                    image_prompt = image_prompt.removeprefix(
                        "Line 1:"
                    ).strip()

                    caption = caption.removeprefix(
                        "Line 2:"
                    ).strip()

                    if len(image_prompt) < 20 or len(caption) < 10:
                        print(f"{model_name}: Response too short.")
                        continue

                    print(
                        f"Content generated successfully "
                        f"using {model_name}."
                    )

                    return image_prompt, caption

                except Exception as exc:
                    # Model access, quota, and API errors should
                    # not prevent using the local backup database.
                    print(
                        f"Gemini model {model_name} failed: "
                        f"{type(exc).__name__}: {exc}"
                    )

        except Exception as exc:
            print(
                "Could not initialize Gemini: "
                f"{type(exc).__name__}: {exc}"
            )
    else:
        print("GEMINI_API_KEY is missing. Using backup content.")

    fallback = random.choice(FALLBACK_TEMPLATES)

    print("Using local fallback template.")

    return fallback["prompt"], fallback["caption"]


# =========================================================
# IMAGE GENERATION AND VALIDATION
# =========================================================

def generate_and_download_image(image_prompt):
    """
    Download an actual JPEG or PNG image.
    Never substitute an unrelated generic photograph.
    """

    seed = random.randint(1, 999999)

    full_prompt = (
        "High-quality optical illusion puzzle, "
        + image_prompt
    )

    image_url = (
        "https://image.pollinations.ai/prompt/"
        + quote(full_prompt, safe="")
        + f"?width=1080&height=1080&seed={seed}&nologo=true"
    )

    headers = {
        "Accept": "image/jpeg,image/png"
    }

    # Try a few different seeds if image generation fails.
    for attempt in range(3):
        try:
            current_seed = random.randint(1, 999999)

            current_url = (
                "https://image.pollinations.ai/prompt/"
                + quote(full_prompt, safe="")
                + f"?width=1080&height=1080"
                + f"&seed={current_seed}&nologo=true"
            )

            response = request_with_retries(
                "GET",
                current_url,
                headers=headers,
            )

            if response.status_code != 200:
                print(
                    "Image service returned HTTP "
                    f"{response.status_code}."
                )
                continue

            content_type = (
                response.headers.get("Content-Type", "")
                .split(";")[0]
                .strip()
                .lower()
            )

            content = response.content

            if len(content) < 10000:
                print("Image rejected: response is too small.")
                continue

            # Verify actual image signatures, not just the header.
            is_jpeg = content.startswith(b"\xff\xd8\xff")
            is_png = content.startswith(b"\x89PNG\r\n\x1a\n")

            if content_type == "image/jpeg" and is_jpeg:
                filename = "illusion.jpg"

            elif content_type == "image/png" and is_png:
                filename = "illusion.png"

            else:
                print(
                    "Image rejected: unsupported content type "
                    "or invalid image signature."
                )
                continue

            with open(filename, "wb") as image_file:
                image_file.write(content)

            print(f"Valid image saved: {filename}")

            return filename

        except Exception as exc:
            print(
                f"Image attempt {attempt + 1} failed: "
                f"{type(exc).__name__}: {exc}"
            )

        if attempt < 2:
            time.sleep(2)

    # Do not post a random image if the image service fails.
    raise RuntimeError(
        "Could not obtain a valid optical illusion image. "
        "Facebook posting has been cancelled."
    )


# =========================================================
# FACEBOOK PAGE PHOTO POSTING
# =========================================================

def post_to_facebook(image_path, caption):
    """
    Upload the generated image to the configured Facebook Page.
    Expired tokens and permission errors are reported clearly.
    """

    url = (
        f"https://graph.facebook.com/"
        f"{GRAPH_API_VERSION}/{FB_PAGE_ID}/photos"
    )

    payload = {
        "caption": caption,
        "access_token": FB_PAGE_ACCESS_TOKEN,
    }

    try:
        with open(image_path, "rb") as image_file:
            mime_type = (
                "image/png"
                if image_path.lower().endswith(".png")
                else "image/jpeg"
            )

            response = request_with_retries(
                "POST",
                url,
                data=payload,
                files={
                    "source": (
                        os.path.basename(image_path),
                        image_file,
                        mime_type,
                    )
                },
            )

        try:
            result = response.json()
        except ValueError:
            result = {}

        if response.ok and result.get("id"):
            print("SUCCESS: Facebook photo posted.")
            print(f"Facebook photo ID: {result['id']}")
            return result

        error = result.get("error", {})
        error_code = error.get("code")
        error_subcode = error.get("error_subcode")
        error_message = error.get(
            "message",
            response.text[:1000],
        )

        if error_code == 190:
            print("\nFACEBOOK TOKEN ERROR")
            print("The Page Access Token is invalid or expired.")
            print("Generate a valid token and update GitHub Secrets.")
            print(
                f"Facebook error code: {error_code}; "
                f"subcode: {error_subcode}"
            )

        elif error_code == 10 or response.status_code == 403:
            print("\nFACEBOOK PERMISSION ERROR")
            print("Check Page permissions and token access.")

        else:
            print(
                f"Facebook API error: HTTP {response.status_code}"
            )

        # Avoid printing the token or the full request URL.
        print(f"Error message: {error_message}")

        raise RuntimeError(
            "Facebook rejected the photo post. "
            "The workflow must not report success."
        )

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Facebook network request failed: {exc}"
        ) from exc


# =========================================================
# MAIN WORKFLOW
# =========================================================

def main():
    # Validate required credentials before doing any work.
    missing = []

    if not FB_PAGE_ID:
        missing.append("FB_PAGE_ID")

    if not FB_PAGE_ACCESS_TOKEN:
        missing.append("FB_PAGE_ACCESS_TOKEN")

    if missing:
        raise RuntimeError(
            "Missing required GitHub Secrets: "
            + ", ".join(missing)
        )

    # 1. Generate content or use the local backup.
    image_prompt, caption = generate_content()

    if not image_prompt or not caption:
        raise RuntimeError("Generated content is empty.")

    # 2. Generate and validate the image.
    image_path = generate_and_download_image(image_prompt)

    # 3. Post to Facebook and verify the returned photo ID.
    post_to_facebook(image_path, caption)

    print("WORKFLOW COMPLETED SUCCESSFULLY.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nWORKFLOW FAILED: {exc}")
        sys.exit(1)
    finally:
        SESSION.close()
