from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from aria_app.features.command_center import render_command_center
from aria_app.features.niche_lab import render_niche_lab
from aria_app.features.repertoire import render_repertoire
from aria_app.features.shorts_view import render_shorts_architect
from aria_app.features.vault import render_vault
from aria_app.navigation import PAGE_LABELS


@dataclass(frozen=True)
class AppPage:
    label: str
    render: Callable[[], None]


APP_PAGES: tuple[AppPage, ...] = tuple(
    AppPage(label, renderer)
    for label, renderer in zip(
        PAGE_LABELS,
        (
            render_command_center,
            render_niche_lab,
            render_repertoire,
            render_shorts_architect,
            render_vault,
        ),
        strict=True,
    )
)
PAGE_RENDERERS = {page.label: page.render for page in APP_PAGES}
