from __future__ import annotations

import streamlit as st

from aria_app.features.command_center import render_command_center
from aria_app.features.niche_lab import render_niche_lab
from aria_app.features.repertoire import render_repertoire
from aria_app.features.shorts_view import render_shorts_architect
from aria_app.features.vault import render_vault
from aria_app.state import initialize_state
from aria_app.ui import inject_theme, render_hero, render_quick_jump_bar, render_sidebar


st.set_page_config(layout="wide", page_title="Ralskies | Starlight Studio")


def main() -> None:
    initialize_state()
    inject_theme()
    render_hero()
    selected_view = render_sidebar()
    render_quick_jump_bar(selected_view)

    if selected_view == "Command Center":
        render_command_center()
    elif selected_view == "Niche Lab":
        render_niche_lab()
    elif selected_view == "Repertoire":
        render_repertoire()
    elif selected_view == "Shorts Architect":
        render_shorts_architect()
    else:
        render_vault()


if __name__ == "__main__":
    main()
