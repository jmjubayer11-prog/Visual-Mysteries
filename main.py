
import random
import math
from PIL import Image, ImageDraw


# সম্পূর্ণ লোকাল কনটেন্ট: কোনো Gemini API দরকার নেই
LOCAL_CAPTIONS = [
    "Can you figure out this optical illusion? Look closely! 🧠 #OpticalIllusion #BrainTeaser",
    "Your eyes might be fooling you! What do you see? 👀 #MindBender #OpticalIllusion",
    "Take a closer look! Can you explain this strange pattern? 🔍 #BrainTeaser #MindGames",
    "Is this shape really possible? Share your answer below! 🤯 #OpticalIllusion #Puzzle",
]


def generate_content():
    """কোনো AI API ছাড়াই caption তৈরি করে।"""
    captions = LOCAL_CAPTIONS.copy()
    random.shuffle(captions)

    prompt = "Locally generated geometric optical illusion"
    caption = captions[0]

    print("Using free local content generator.")
    return prompt, caption


def generate_and_download_image(image_prompt=None):
    """Pillow দিয়ে 1080x1080 optical illusion JPEG তৈরি করে।"""

    size = 1080
    img = Image.new("RGB", (size, size), (12, 16, 35))
    draw = ImageDraw.Draw(img)

    palette = random.choice([
        [(18, 24, 55), (0, 220, 210), (245, 245, 255)],
        [(25, 15, 40), (255, 90, 80), (255, 220, 120)],
        [(15, 30, 28), (120, 255, 150), (240, 245, 220)],
        [(25, 20, 60), (180, 110, 255), (80, 220, 255)],
    ])

    bg, accent, light = palette
    img.paste(bg, (0, 0, size, size))
    draw = ImageDraw.Draw(img)

    # Randomly choose an illusion design.
    design = random.choice([
        "concentric",
        "spiral",
        "checker",
        "geometry",
    ])

    if design == "concentric":
        # Nested rings create a depth illusion.
        cx = random.randint(430, 650)
        cy = random.randint(430, 650)

        for radius in range(480, 15, -14):
            color = accent if (radius // 14) % 2 else light
            draw.ellipse(
                (cx-radius, cy-radius, cx+radius, cy+radius),
                outline=color,
                width=random.choice([3, 4, 6]),
            )

        for offset in range(-300, 301, 60):
            draw.ellipse(
                (
                    cx + offset - 18,
                    cy - 18,
                    cx + offset + 18,
                    cy + 18,
                ),
                fill=bg,
                outline=light,
                width=3,
            )

    elif design == "spiral":
        # Alternating expanding arcs create a spiral effect.
        cx, cy = size // 2, size // 2
        points = []

        for i in range(4200):
            angle = i * 0.035
            radius = 2 + i * 0.115
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            points.append((int(x), int(y)))

        for shift in range(-18, 19, 9):
            shifted = [
                (x + shift, y - shift)
                for x, y in points
            ]
            draw.line(
                shifted,
                fill=accent if shift % 2 else light,
                width=3,
            )

        draw.ellipse(
            (cx-14, cy-14, cx+14, cy+14),
            fill=light,
        )

    elif design == "checker":
        # Repeated offset squares create a visual distortion.
        cell = 54

        for y in range(-cell, size + cell, cell):
            for x in range(-cell, size + cell, cell):
                row = y // cell
                col = x // cell
                offset = int(18 * math.sin(row * 0.7))

                color = (
                    accent
                    if (row + col) % 2 == 0
                    else light
                )

                left = x + offset
                top = y

                draw.rectangle(
                    (left, top, left + cell - 3, top + cell - 3),
                    fill=color,
                )

        # Dark circles interrupt the regular grid.
        for y in range(100, size, 180):
            for x in range(100, size, 180):
                draw.ellipse(
                    (x-15, y-15, x+15, y+15),
                    fill=bg,
                )

    else:
        # Geometric impossible-looking connected structure.
        cx, cy = 540, 520
        radius = 300

        vertices = [
            (
                int(cx + radius * math.cos(a)),
                int(cy + radius * math.sin(a)),
            )
            for a in (
                -math.pi / 2,
                math.pi / 6,
                5 * math.pi / 6,
            )
        ]

        a, b, c = vertices

        # Draw thick interlocking triangular beams.
        draw.line([a, b], fill=light, width=38)
        draw.line([b, c], fill=accent, width=38)
        draw.line([c, a], fill=light, width=38)

        # Offset inner lines add a 3D-style visual effect.
        for p, q in [(a, b), (b, c), (c, a)]:
            draw.line(
                [
                    (p[0] + 9, p[1] + 9),
                    (q[0] + 9, q[1] + 9),
                ],
                fill=bg,
                width=5,
            )

        for x, y in vertices:
            draw.ellipse(
                (x-12, y-12, x+12, y+12),
                fill=accent,
            )

    # Add a clean border.
    draw.rectangle(
        (12, 12, size-13, size-13),
        outline=light,
        width=4,
    )

    # Save a real JPEG locally. No network calls.
    filename = "illusion.jpg"

    img.save(
        filename,
        format="JPEG",
        quality=95,
        optimize=True,
    )

    # Verify that the saved file can be reopened.
    with Image.open(filename) as check:
        check.verify()

    print(f"Local optical illusion created: {filename}")
    print(f"Design selected: {design}")

    return filename
