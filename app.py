import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, zipfile, textwrap, os

FONT_PATHS = {
    "Barlow Condensed": "fonts/BarlowCondensed-Regular.ttf",
    "Bebas Neue": "fonts/BebasNeue-Regular.ttf",
    "DM Serif Display": "fonts/DMSerifDisplay-Regular.ttf",
    "Lato": "fonts/Lato-Regular.ttf",
    "Merriweather": "fonts/Merriweather-Regular.ttf",
    "Montserrat": "fonts/Montserrat-Regular.ttf",
    "Open Sans": "fonts/OpenSans-Regular.ttf",
    "Oswald": "fonts/Oswald-Regular.ttf",
    "Playfair Display": "fonts/PlayfairDisplay-Regular.ttf",
    "Raleway": "fonts/Raleway-Regular.ttf",
    "Roboto": "fonts/Roboto-Regular.ttf",
}

st.set_page_config(page_title="Quote Generator")

st.title("Bulk Quote Image Generator")

# -----------------------------
# SIDEBAR CONTROLS (NEW)
# -----------------------------
st.sidebar.header("Design Controls")

font_size = st.sidebar.slider("Font Size", 20, 200, 90)
font_color = st.sidebar.color_picker("Font Color", "#FFFFFF")
shadow_enabled = st.sidebar.checkbox("Enable Shadow", True)
shadow_color = st.sidebar.color_picker("Shadow Color", "#000000")

overlay_enabled = st.sidebar.checkbox("Enable Overlay", False)
overlay_color = st.sidebar.color_picker("Overlay Color", "#000000")
overlay_opacity = st.sidebar.slider("Overlay Strength", 0.0, 0.7, 0.3)

vertical_bias = st.sidebar.slider("Vertical Position", -0.5, 0.5, 0.0)
line_spacing = st.sidebar.slider("Line Spacing", 0, 30, 10)

box_padding = st.sidebar.slider("Text Padding", 0, 200, 60)

font_choice = st.sidebar.selectbox(
    "Font",
    list(FONT_PATHS.keys())
)

# -----------------------------
# FILE INPUTS
# -----------------------------
backgrounds = st.file_uploader(
    "Upload Background Images",
    type=["png","jpg","jpeg"],
    accept_multiple_files=True
)

quotes_file = st.file_uploader(
    "Upload quotes.txt",
    type=["txt"]
)

# -----------------------------
# FONT LOADER
# -----------------------------
def load_font(size):
    path = FONT_PATHS.get(font_choice)
    return ImageFont.truetype(path, size)

# -----------------------------
# TEXT FITTING
# -----------------------------
def fit_text(draw, text, max_width, max_height, size):
    font = load_font(size)

    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = word if current == "" else current + " " + word
        bbox = draw.textbbox((0,0), test, font=font)

        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    return font, lines

# -----------------------------
# MAIN GENERATION
# -----------------------------
if st.button("Generate Images"):

    if not backgrounds or not quotes_file:
        st.error("Upload backgrounds and quotes.txt")
    else:
        quotes = [
            q.strip()
            for q in quotes_file.read().decode("utf-8").splitlines()
            if q.strip()
        ]

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:

            count = 0

            for bg_file in backgrounds:
                bg_name = bg_file.name.rsplit(".",1)[0]

                base_img = Image.open(bg_file).convert("RGB")
                base_img = base_img.resize((1080,1080))

                for i, quote in enumerate(quotes, start=1):

                    img = base_img.copy()
                    draw = ImageDraw.Draw(img)

                    # -----------------------------
                    # OVERLAY (NEW)
                    # -----------------------------
                    if overlay_enabled:
                        overlay = Image.new("RGB", img.size, overlay_color)
                        img = Image.blend(img, overlay, overlay_opacity)
                        draw = ImageDraw.Draw(img)

                    # -----------------------------
                    # TEXT FIT
                    # -----------------------------
                    font, lines = fit_text(draw, quote, 950, 900, font_size)

                    # measure text
                    heights = []
                    widths = []

                    for line in lines:
                        bbox = draw.textbbox((0,0), line, font=font)
                        widths.append(bbox[2]-bbox[0])
                        heights.append(bbox[3]-bbox[1])

                    total_height = sum(heights) + (len(lines)-1)*line_spacing

                    # vertical bias control
                    center_y = (1080 - total_height) // 2
                    y = int(center_y + vertical_bias * 300)

                    # -----------------------------
                    # DRAW TEXT
                    # -----------------------------
                    for idx, line in enumerate(lines):

                        w = widths[idx]
                        h = heights[idx]
                        x = (1080 - w) // 2

                        # shadow
                        if shadow_enabled:
                            draw.text(
                                (x+3, y+3),
                                line,
                                font=font,
                                fill=shadow_color
                            )

                        # main text
                        draw.text(
                            (x, y),
                            line,
                            font=font,
                            fill=font_color
                        )

                        y += h + line_spacing

                    # -----------------------------
                    # SAVE
                    # -----------------------------
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="PNG")

                    filename = f"{bg_name}_quote_{i}.png"
                    zf.writestr(filename, img_bytes.getvalue())

                    count += 1

        zip_buffer.seek(0)

        st.success(f"Generated {count} images")

        st.download_button(
            "Download ZIP",
            data=zip_buffer,
            file_name="quote_images.zip",
            mime="application/zip"
        )
