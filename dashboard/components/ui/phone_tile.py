from pathlib import Path
import streamlit as st
from PIL import Image, ImageOps

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def load_card_image(image_path, size=(420, 280)):
    if not image_path:
        return None

    full_path = PROJECT_ROOT / image_path

    if not full_path.exists():
        return None

    image = Image.open(full_path).convert("RGB")
    image = ImageOps.contain(image, size)

    background = Image.new("RGB", size, (17, 24, 32))
    x = (size[0] - image.width) // 2
    y = (size[1] - image.height) // 2
    background.paste(image, (x, y))

    return background


def phone_tile(phone, key_prefix="phone"):
    image_path = phone.get("image_local_path", "")
    phone_name = phone.get("phone_name", "Unknown Phone")
    brand = phone.get("brand", "")
    verdict = phone.get("consumer_verdict", "Not available")
    positive = phone.get("positive_percent", None)
    reviews = phone.get("review_count", None)
    phone_id = phone.get("phone_id", phone_name)

    with st.container(border=True):
        image = load_card_image(image_path)

        if image is not None:
            st.image(image, use_container_width=True)

        st.markdown(f"### {phone_name}")
        st.caption(brand)

        st.markdown(f"**{verdict}**")

        if positive is not None:
            st.markdown(f"## {positive:.1f}%")
            st.caption("Positive sentiment")

        if reviews is not None:
            st.caption(f"{int(reviews)} reviews analysed")

        if st.button(
            "View Details",
            use_container_width=True,
            key=f"view_{phone_id}",
        ):
            st.session_state["selected_phone_id"] = phone_id
            st.session_state["selected_phone_name"] = phone_name
            st.switch_page("pages/📱_Phone_Explorer.py")