
#!/usr/bin/env python3
"""Generate SVG cards for the GitHub profile README."""

from __future__ import annotations

import base64
import calendar
import html
import json
import os
import shutil
import subprocess
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "cards"
ASSETS = ROOT / "assets"
DATA = ROOT / "data" / "contributions.json"

USERNAME = os.getenv("GITHUB_USERNAME", "RugvedBane")
NAME = os.getenv("PROFILE_NAME", "Rugved Bane")

HERO_LABEL = os.getenv(
    "HERO_LABEL",
    "FORMER AI ENGINEER INTERN · NIRIKSHAN AI",
)
TAGLINE_1 = os.getenv(
    "PROFILE_TAGLINE_1",
    "I build Machine Learning and GenAI systems.",
)
TAGLINE_2 = os.getenv(
    "PROFILE_TAGLINE_2",
    "Open source contributor · Kaggle Expert.",
)

STATIC = os.getenv("STATIC", "0") == "1"

# Palette
ACCENT = "#2F6B4F"
BG = "#F4F1E7"
PANEL = "#EAE6D9"
TEXT = "#173D32"
MUTED = "#587064"
BORDER = "#CCD5C9"

PROJECTS = [
    {
        "name": "Kwest",
        "subtitle": "AI-powered Kaggle workspace",
        "description": (
            "Competition inspection, tool calling, code execution "
            "and persistent experiment memory."
        ),
        "details": "GENAI · AGENTIC WORKFLOWS · KAGGLE API",
    },
    {
        "name": "Deepfake Audio Detector",
        "subtitle": "Synthetic audio detection with EfficientNet-B0",
        "description": (
            "ASVspoof 2019 LA · 8.2% test EER · Grad-CAM "
            "· FastAPI and Streamlit."
        ),
        "details": "DEEP LEARNING · AUDIO CLASSIFICATION · PYTORCH",
    },
    {
        "name": "UFC Fight Predictor",
        "subtitle": "Machine learning for fight outcome prediction",
        "description": (
            "Historical fight data, feature engineering and "
            "predictive modelling · ~71% accuracy."
        ),
        "details": "MACHINE LEARNING · FEATURE ENGINEERING",
    },
]


def esc(value: object) -> str:
    """Escape text before inserting it into SVG."""
    return html.escape(str(value), quote=True)


def load_data() -> dict:
    """Load contribution data."""
    try:
        with DATA.open(encoding="utf-8") as file:
            payload = json.load(file)

        if isinstance(payload, dict):
            return payload

    except (OSError, json.JSONDecodeError):
        pass

    return {
        "total_contributions": 0,
        "days": [],
    }


def calculate_stats(data: dict) -> dict:
    """Calculate contribution statistics."""
    counts = {}

    for item in data.get("days", []):
        try:
            current_day = date.fromisoformat(item["date"])
            counts[current_day] = max(
                0,
                int(item.get("count", 0)),
            )
        except (KeyError, TypeError, ValueError):
            continue

    today = date.today()

    cursor = (
        today
        if counts.get(today, 0)
        else today - timedelta(days=1)
    )

    streak = 0

    while counts.get(cursor, 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)

    months = []

    for offset in range(11, -1, -1):
        year = today.year
        month = today.month - offset

        while month <= 0:
            year -= 1
            month += 12

        total = sum(
            count
            for day, count in counts.items()
            if day.year == year and day.month == month
        )

        months.append(
            (calendar.month_abbr[month], total)
        )

    busiest_day, busiest_count = max(
        counts.items(),
        key=lambda pair: pair[1],
        default=(None, 0),
    )

    return {
        "total": int(
            data.get(
                "total_contributions",
                sum(counts.values()),
            )
        ),
        "active": sum(
            count > 0
            for count in counts.values()
        ),
        "streak": streak,
        "busiest_date": (
            busiest_day.isoformat()
            if busiest_day
            else "—"
        ),
        "busiest_count": busiest_count,
        "months": months,
        "best_month": max(
            months,
            key=lambda pair: pair[1],
            default=("—", 0),
        ),
    }


def load_fonts() -> list[str]:
    """Load and embed available WOFF fonts."""
    font_specs = [
        ("Inter.ttf", "Inter.woff"),
        ("FiraCode.ttf", "FiraCode.woff"),
        (None, "InstrumentSerif-Regular.woff"),
        (None, "InstrumentSerif-Italic.woff"),
    ]

    fonts = []

    for ttf_name, woff_name in font_specs:
        woff_path = ASSETS / woff_name

        ttf_path = (
            ASSETS / ttf_name
            if ttf_name
            else None
        )

        if (
            ttf_path
            and ttf_path.exists()
            and shutil.which("pyftsubset")
        ):
            try:
                subprocess.run(
                    [
                        "pyftsubset",
                        str(ttf_path),
                        f"--output-file={woff_path}",
                        "--flavor=woff",
                        "--unicodes=U+0000-00FF,U+2000-206F",
                        "--layout-features=*",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError:
                pass

        if woff_path.exists():
            encoded = base64.b64encode(
                woff_path.read_bytes()
            ).decode("ascii")

            fonts.append(
                f"data:font/woff;base64,{encoded}"
            )
        else:
            fonts.append("")

    return fonts


def font_css(fonts: list[str]) -> str:
    """Build font-face declarations."""
    specs = [
        ("Inter", "normal", fonts[0]),
        ("Fira Code", "normal", fonts[1]),
        ("Instrument Serif", "normal", fonts[2]),
        ("Instrument Serif", "italic", fonts[3]),
    ]

    return "".join(
        (
            f"@font-face{{font-family:'{family}';"
            f"font-style:{style};"
            f"src:url('{uri}') format('woff');}}"
        )
        for family, style, uri in specs
        if uri
    )


def save_card(
    filename: str,
    width: int,
    height: int,
    body: str,
    fonts: list[str],
) -> None:
    """Write a complete SVG card."""
    motion = ""

    if not STATIC:
        motion = """
        .card {
            animation: enter .65s ease-out both;
        }

        .bar {
            transform-box: fill-box;
            transform-origin: bottom;
            animation: grow .7s ease-out both;
        }

        @keyframes enter {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes grow {
            from {
                transform: scaleY(.05);
            }
            to {
                transform: scaleY(1);
            }
        }
        """

    document = f"""
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}"
     height="{height}"
     viewBox="0 0 {width} {height}">

<title>Rugved Bane - GitHub Profile</title>

<style>
{font_css(fonts)}

text {{
    font-family: Inter, Arial, sans-serif;
}}

.mono {{
    font-family: 'Fira Code', monospace;
}}

.serif {{
    font-family: 'Instrument Serif', Georgia, serif;
}}

{motion}

@media (prefers-reduced-motion: reduce) {{
    *,
    *::before,
    *::after {{
        animation: none !important;
    }}

    .card,
    .bar {{
        opacity: 1 !important;
        transform: none !important;
    }}
}}
</style>

<rect
    width="100%"
    height="100%"
    rx="19"
    fill="{BG}"
/>

<rect
    x="1"
    y="1"
    width="{width - 2}"
    height="{height - 2}"
    rx="18"
    fill="none"
    stroke="{BORDER}"
/>

<g class="card">
{body}
</g>

</svg>
"""

    OUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    (OUT / filename).write_text(
        document,
        encoding="utf-8",
    )


def render_hero(fonts: list[str]) -> None:
    """Generate the main profile hero."""
    name_parts = NAME.split()

    first_name = (
        name_parts[0]
        if name_parts
        else NAME
    )

    last_name = " ".join(name_parts[1:])

    portrait = ""

    portrait_path = ASSETS / "portrait-sketch.png"

    if portrait_path.exists():
        image_data = base64.b64encode(
            portrait_path.read_bytes()
        ).decode("ascii")

        portrait = f"""
        <image
            x="510"
            y="-2"
            width="320"
            height="300"
            preserveAspectRatio="xMidYMid meet"
            xlink:href="data:image/png;base64,{image_data}"
        />
        """

    body = f"""
<circle
    cx="38"
    cy="46"
    r="3.5"
    fill="{ACCENT}"
/>

<text
    x="50"
    y="50"
    fill="{MUTED}"
    font-size="11"
    letter-spacing="1.5"
    class="mono"
>{esc(HERO_LABEL)}</text>

<text
    x="34"
    y="128"
    fill="{TEXT}"
    font-size="92"
    letter-spacing="-1"
    class="serif"
>{esc(first_name)}</text>

<text
    x="34"
    y="214"
    fill="{ACCENT}"
    font-size="92"
    font-style="italic"
    letter-spacing="-1"
    class="serif"
>{esc(last_name)}</text>

<text
    x="38"
    y="250"
    fill="{MUTED}"
    font-size="14"
>{esc(TAGLINE_1)}</text>

<text
    x="38"
    y="270"
    fill="{MUTED}"
    font-size="14"
>{esc(TAGLINE_2)}</text>

{portrait}
"""

    save_card(
        "01-hero.svg",
        860,
        300,
        body,
        fonts,
    )


def render_link_cards(fonts: list[str]) -> None:
    """Generate LinkedIn and Kaggle cards."""
    links = [
        (
            "02-link-2.svg",
            "LINKEDIN",
            "Professional profile",
            "01",
        ),
        (
            "02-link-3.svg",
            "KAGGLE",
            "Competitions & notebooks",
            "02",
        ),
    ]

    for filename, title, subtitle, number in links:
        body = f"""
<rect
    x="1"
    y="1"
    width="278"
    height="128"
    rx="16"
    fill="{PANEL}"
    stroke="{BORDER}"
/>

<text
    x="20"
    y="28"
    fill="{ACCENT}"
    font-size="9"
    class="mono"
>{number} / PROFILE</text>

<text
    x="20"
    y="65"
    fill="{TEXT}"
    font-size="21"
    font-weight="700"
>{esc(title)}</text>

<text
    x="20"
    y="89"
    fill="{MUTED}"
    font-size="11"
>{esc(subtitle)}</text>

<text
    x="20"
    y="112"
    fill="{ACCENT}"
    font-size="9"
    class="mono"
>VIEW PROFILE</text>
"""

        save_card(
            filename,
            280,
            130,
            body,
            fonts,
        )


def render_activity_card(
    stats: dict,
    fonts: list[str],
) -> None:
    """Generate the monthly contribution activity card."""
    maximum = max(
        (value for _, value in stats["months"]),
        default=1,
    ) or 1

    bars = []

    baseline = 213
    chart_height = 65

    for index, (month, value) in enumerate(
        stats["months"]
    ):
        x = 45 + index * 65

        height = max(
            3,
            round(chart_height * value / maximum),
        )

        y = baseline - height

        is_best = (
            month == stats["best_month"][0]
            and value > 0
        )

        bars.append(
            f"""
<rect
    class="bar"
    x="{x}"
    y="{y}"
    width="29"
    height="{height}"
    rx="4"
    fill="{ACCENT}"
    style="animation-delay:{index * 0.04:.2f}s"
/>

<text
    x="{x + 14}"
    y="{max(135, y - 8)}"
    text-anchor="middle"
    fill="{ACCENT}"
    font-size="9"
    font-weight="700"
>{value if is_best else ""}</text>

<text
    x="{x + 14}"
    y="238"
    text-anchor="middle"
    fill="{MUTED}"
    font-size="9"
>{esc(month)}</text>
"""
        )

    body = f"""
<text
    x="28"
    y="34"
    fill="{TEXT}"
    font-size="19"
    font-weight="700"
>Contribution activity</text>

<text
    x="28"
    y="53"
    fill="{MUTED}"
    font-size="10"
>Monthly contributions · Last 12 months</text>

<text
    x="28"
    y="91"
    fill="{ACCENT}"
    font-size="26"
    font-weight="750"
>{stats["total"]:,}</text>

<text
    x="29"
    y="108"
    fill="{MUTED}"
    font-size="9"
>TOTAL CONTRIBUTIONS</text>

<text
    x="302"
    y="91"
    fill="{TEXT}"
    font-size="23"
>{stats["streak"]}</text>

<text
    x="303"
    y="108"
    fill="{MUTED}"
    font-size="9"
>DAY STREAK</text>

<text
    x="452"
    y="91"
    fill="{TEXT}"
    font-size="23"
>{stats["active"]}</text>

<text
    x="453"
    y="108"
    fill="{MUTED}"
    font-size="9"
>ACTIVE DAYS</text>

<text
    x="625"
    y="91"
    fill="{TEXT}"
    font-size="23"
>{stats["busiest_count"]}</text>

<text
    x="626"
    y="108"
    fill="{MUTED}"
    font-size="9"
>BUSIEST DAY</text>

<text
    x="626"
    y="124"
    fill="{MUTED}"
    font-size="9"
>{esc(stats["busiest_date"])}</text>

{"".join(bars)}
"""

    save_card(
        "03-activity.svg",
        860,
        250,
        body,
        fonts,
    )


def render_project_cards(fonts: list[str]) -> None:
    """Generate the three featured project cards."""
    for old_card in OUT.glob("04-project-*.svg"):
        old_card.unlink()

    for index, project in enumerate(
        PROJECTS,
        start=1,
    ):
        body = f"""
<text
    x="26"
    y="30"
    fill="{ACCENT}"
    font-size="9"
    class="mono"
>FEATURED PROJECT / {index:02d}</text>

<text
    x="26"
    y="72"
    fill="{TEXT}"
    font-size="25"
    font-weight="750"
>{esc(project["name"])}</text>

<text
    x="27"
    y="98"
    fill="{ACCENT}"
    font-size="12"
>{esc(project["subtitle"])}</text>

<text
    x="27"
    y="128"
    fill="{MUTED}"
    font-size="11"
>{esc(project["description"])}</text>

<text
    x="27"
    y="164"
    fill="{ACCENT}"
    font-size="9"
    class="mono"
>{esc(project["details"])}</text>

<text
    x="817"
    y="30"
    text-anchor="end"
    fill="{MUTED}"
    font-size="9"
    class="mono"
>OPEN REPOSITORY</text>
"""

        save_card(
            f"04-project-{index}.svg",
            860,
            200,
            body,
            fonts,
        )


def render_open_source_card(fonts: list[str]) -> None:
    """Generate the open-source contribution card."""
    pull_requests = [
        (
            "scikit-learn/scikit-learn",
            "RFECV per-split ranking and support shapes · PR #35174",
            "MERGED",
        ),
        (
            "scikit-learn/scikit-learn",
            "HistGradientBoosting early-stopping fix · PR #35176",
            "MERGED",
        ),
        (
            "feature-engine/feature_engine",
            "Feature-engine contribution · PR #1120",
            "OPEN",
        ),
        (
            "philpaz/recusal",
            "Validation helper and 14 tests · PR #63",
            "MERGED",
        ),
    ]

    rows = []

    for index, (repository, description, status) in enumerate(
        pull_requests
    ):
        y = 65 + index * 47

        status_color = (
            ACCENT
            if status == "MERGED"
            else "#A36B20"
        )

        rows.append(
            f"""
<text
    x="27"
    y="{y}"
    fill="{TEXT}"
    font-size="12"
>{esc(repository)}</text>

<text
    x="27"
    y="{y + 16}"
    fill="{MUTED}"
    font-size="10"
>{esc(description)}</text>

<text
    x="817"
    y="{y + 5}"
    text-anchor="end"
    fill="{status_color}"
    font-size="9"
    class="mono"
    font-weight="700"
>{esc(status)}</text>
"""
        )

    body = f"""
<text
    x="27"
    y="32"
    fill="{TEXT}"
    font-size="18"
    font-weight="720"
>Open-source contributions</text>

<text
    x="817"
    y="32"
    text-anchor="end"
    fill="{MUTED}"
    font-size="9"
    class="mono"
>6+ PRs MERGED</text>

{"".join(rows)}
"""

    save_card(
        "09-open-source.svg",
        860,
        255,
        body,
        fonts,
    )


def main() -> None:
    OUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    stats = calculate_stats(
        load_data()
    )

    fonts = load_fonts()

    render_hero(fonts)
    render_link_cards(fonts)
    render_activity_card(stats, fonts)
    render_project_cards(fonts)
    render_open_source_card(fonts)

    # The old heatmap duplicated the monthly activity card.
    old_graph = OUT / "10-contributions.svg"

    if old_graph.exists():
        old_graph.unlink()

    generated = sorted(
        path.name
        for path in OUT.glob("*.svg")
    )

    print(
        f"Generated {len(generated)} SVG cards:"
    )

    for filename in generated:
        print(f"  cards/{filename}")

    if STATIC:
        print("Static mode enabled.")


if __name__ == "__main__":
    main()
