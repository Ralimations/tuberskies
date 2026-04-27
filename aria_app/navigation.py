from __future__ import annotations


PAGE_LABELS = ["Command Center", "Creator Actions", "Niche Lab", "The Vault"]

SIDEBAR_TOOLS = [
    {
        "group": "Home",
        "items": [
            ("Ask A.R.I.A.", "comments", {"view": "Command Center", "command_center_section": "Dashboard"}),
            ("Analytics", "chart", {"view": "Command Center", "command_center_section": "Analytics"}),
            ("Creator Actions", "comments", {"view": "Creator Actions"}),
        ],
    },
    {
        "group": "More tools",
        "items": [
            ("Upload Lab", "upload", {"view": "Command Center", "command_center_section": "Upload Lab"}),
            ("Momentum", "target", {"view": "Command Center", "command_center_section": "Upload Lab", "upload_lab_section": "Momentum"}),
            ("Next Cover Radar", "spark", {"view": "Command Center", "command_center_section": "Upload Lab", "upload_lab_section": "Radar"}),
            ("Pattern Memory", "memory", {"view": "Command Center", "command_center_section": "Pattern Memory"}),
            ("Ideation", "spark", {"view": "Niche Lab"}),
            ("The Vault", "vault", {"view": "The Vault"}),
        ],
    },
]
