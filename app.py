from __future__ import annotations

import streamlit as st

from aria_app.pages import PAGE_RENDERERS
from aria_app.state import initialize_state
from aria_app.ui import inject_theme, render_header_navigation, render_hero, render_quick_jump_bar


st.set_page_config(layout="wide", page_title="Ralskies | Starlight Studio")


def main() -> None:
    initialize_state()
    inject_theme()
    render_hero()
    selected_view = render_header_navigation()
    render_quick_jump_bar(selected_view)
    PAGE_RENDERERS[selected_view]()


if __name__ == "__main__":
    main()
