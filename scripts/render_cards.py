#!/usr/bin/env python3
"""Generate animated forest-green SVG cards for a GitHub profile README.

Usage:
    python scripts/render_cards.py
    STATIC=1 python scripts/render_cards.py

Optional assets:
    assets/portrait-sketch.png
    assets/Inter.ttf
    assets/FiraCode.ttf
    assets/InstrumentSerif-Regular.ttf
    assets/InstrumentSerif-Italic.ttf

The renderer intentionally uses fixed card dimensions and bounded text areas.
Long descriptions are wrapped, and project metadata is kept inside measured
columns so that text does not run into metric panels or card edges.
"""

import os
import json
import html
import base64
import calendar
import shutil
import subprocess
import textwrap

from pathlib import Path
from datetime import date, timedelta

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "cards"
DATA = ROOT / "data" / "contributions.json"
ASSETS = ROOT / "assets"

USERNAME = os.getenv("GITHUB_USERNAME", "RugvedBane")
NAME = os.getenv("PROFILE_NAME", "Rugved Bane")

HERO_LABEL = os.getenv(
    "HERO_LABEL",
    "FORMER AI ENGINEER INTERN · NIRIKSHAN AI"
)

TAGLINE_1 = os.getenv(
    "PROFILE_TAGLINE_1",
    "I build Machine Learning and GenAI systems."
)

TAGLINE_2 = os.getenv(
    "PROFILE_TAGLINE_2",
    "Open-source contributor · Kaggle Expert."
)

# Forest green + warm off-white palette. Keep these values consistent
# across all cards to preserve the profile's visual identity.
ACCENT = "#2F6B4F"
BG = "#F4F1E7"
PANEL = "#EAE6D9"
TEXT = "#173D32"
MUTED = "#587064"
BORDER = "#CCD5C9"
DARK_GREEN = "#173D32"
MID_GREEN = "#245744"
LIGHT_GREEN = "#A8C686"

STATIC = os.getenv("STATIC", "0") == "1"

# All claims below are based on the linked project READMEs. Keep the
# metrics tied to their evaluation context; avoid presenting them as
# universal or production-wide performance guarantees.
PROJECTS = [
    {
        "name": "Kwest",
        "subtitle": "Tool-using AI agent for Kaggle competitions",
        "description": (
            "Inspects data, analyzes features, generates model code, "
            "runs Kaggle kernels and submits predictions."
        ),
        "stack": ["Python", "LangGraph", "DeepSeek", "Kaggle CLI", "Streamlit"],
        "repo": f"https://github.com/{USERNAME}/Kwest",
        "primary_value": "0.94730",
        "primary_label": "PUBLIC SCORE · S6E11",
        "secondary_value": "8",
        "secondary_label": "PURPOSE-BUILT KAGGLE TOOLS",
        "footnote": "Manual baseline: 0.94579",
        "tag": "GENAI · AGENT SYSTEMS"
    },
    {
        "name": "Deepfake Audio Detector",
        "subtitle": "End-to-end synthetic audio detection",
        "description": (
            "EfficientNet-B0 on ASVspoof 2019 LA, with Grad-CAM, "
            "LLM explanations and a deployed FastAPI service."
        ),
        "stack": ["PyTorch", "EfficientNet-B0", "FastAPI", "Streamlit", "Grad-CAM"],
        "repo": f"https://github.com/{USERNAME}/deepfake-audio-detector",
        "primary_value": "8.23%",
        "primary_label": "EQUAL ERROR RATE · TEST SET",
        "secondary_value": "263s → 6s",
        "secondary_label": "INFERENCE LATENCY · RAILWAY",
        "footnote": "Evaluated on 71,237 test samples",
        "tag": "AUDIO · DEEP LEARNING"
    },
    {
        "name": "UFC Fight Predictor",
        "subtitle": "Time-aware fight outcome prediction",
        "description": (
            "Point-in-time fighter features and chronological evaluation "
            "to reduce leakage in future-fight predictions."
        ),
        "stack": ["Python", "Pandas", "scikit-learn", "LightGBM", "Streamlit"],
        "repo": f"https://github.com/{USERNAME}/UFC-Predictor",
        "primary_value": "67.5%",
        "primary_label": "BLENDED MODEL ACCURACY",
        "secondary_value": "1,015",
        "secondary_label": "FUTURE FIGHTS · TEST SET",
        "footnote": "+8.6 pp vs. untuned Elo baseline",
        "tag": "MACHINE LEARNING · SPORTS"
    }
]


def esc(value):
    """Escape text and attribute values before inserting them into SVG."""
    return html.escape(str(value), quote=True)


def load_data():
    if not DATA.exists():
        return {"total_contributions": 0, "days": []}

    with open(DATA, encoding="utf-8") as file:
        return json.load(file)


def calculate_stats(data):
    """Calculate contribution metrics for the latest rolling 12 months."""
    counts = {}

    for item in data.get("days", []):
        try:
            current_day = date.fromisoformat(item["date"])
            counts[current_day] = max(0, int(item.get("count", 0)))
        except (KeyError, ValueError, TypeError):
            continue

    today = date.today()
    cursor = today if counts.get(today, 0) else today - timedelta(days=1)

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
            value for current_day, value in counts.items()
            if current_day.year == year and current_day.month == month
        )
        months.append((calendar.month_abbr[month], total))

    busiest_day, busiest_count = max(
        counts.items(),
        key=lambda item: item[1],
        default=(None, 0)
    )
    best_month = max(months, key=lambda item: item[1], default=("—", 0))

    weekday_totals = [0] * 7
    for current_day, value in counts.items():
        weekday_totals[current_day.weekday()] += value

    most_active_weekday_index = max(
        range(7),
        key=lambda index: weekday_totals[index],
        default=0
    )
    most_active_weekday = calendar.day_name[most_active_weekday_index]

    active_days = sum(value > 0 for value in counts.values())
    total_from_days = sum(counts.values())
    total = int(data.get("total_contributions", total_from_days) or 0)
    average_per_active_day = total / active_days if active_days else 0.0

    days = data.get("days", [])
    if not isinstance(days, list):
        days = []

    return {
        "total": total,
        "active": active_days,
        "streak": streak,
        "busiest_date": busiest_day.isoformat() if busiest_day else "—",
        "busiest_count": busiest_count,
        "months": months,
        "best_month": best_month,
        "days": days[-371:],
        "most_active_weekday": most_active_weekday,
        "weekday_total": weekday_totals[most_active_weekday_index],
        "average_per_active_day": average_per_active_day
    }


def load_fonts():
    """Subset TTF files into WOFF and embed them as base64."""
    result = []

    for font in ("Inter", "FiraCode"):
        source = ASSETS / f"{font}.ttf"
        output = ASSETS / f"{font}.woff"
        uri = ""

        if source.exists() and shutil.which("pyftsubset"):
            subprocess.run([
                "pyftsubset",
                str(source),
                f"--output-file={output}",
                "--flavor=woff",
                "--unicodes=U+0000-00FF,U+2000-206F",
                "--layout-features=*"
            ], check=True)

            uri = (
                "data:font/woff;base64,"
                + base64.b64encode(output.read_bytes()).decode()
            )
        elif output.exists():
            uri = (
                "data:font/woff;base64,"
                + base64.b64encode(output.read_bytes()).decode()
            )

        result.append(uri)

    return result


def load_serif_fonts():
    """Embed Instrument Serif regular and italic fonts for the hero name."""
    glyphs = "".join(sorted(set(NAME)))
    uris = []

    for style in ("Regular", "Italic"):
        source = ASSETS / f"InstrumentSerif-{style}.ttf"
        output = ASSETS / f"InstrumentSerif-{style}.woff"
        uri = ""

        if source.exists() and shutil.which("pyftsubset"):
            subprocess.run([
                "pyftsubset",
                str(source),
                f"--text={glyphs}",
                f"--output-file={output}",
                "--flavor=woff",
                "--layout-features="
            ], check=True)

        if output.exists():
            uri = (
                "data:font/woff;base64,"
                + base64.b64encode(output.read_bytes()).decode()
            )

        uris.append(uri)

    return uris


def wrap_lines(value, max_chars, max_lines=2):
    """Wrap a short SVG label without allowing an unbounded text block."""
    value = " ".join(str(value).split())
    if not value:
        return []

    lines = textwrap.wrap(
        value,
        width=max_chars,
        break_long_words=False,
        break_on_hyphens=False
    )

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1].rstrip(" .")
        if len(last) > max_chars - 3:
            last = last[:max_chars - 3].rstrip()
        lines[-1] = last + "..."

    return lines


def multiline_text(value, x, y, font_size=11, color=MUTED,
                   line_height=15, max_chars=90, max_lines=2,
                   weight=None):
    """Render wrapped text using explicit SVG tspans and line spacing."""
    lines = wrap_lines(value, max_chars=max_chars, max_lines=max_lines)
    if not lines:
        return ""

    weight_attr = f' font-weight="{weight}"' if weight else ""
    tspans = []
    for index, line in enumerate(lines):
        dy = 0 if index == 0 else line_height
        tspans.append(
            f'<tspan x="{x}" dy="{dy}">{esc(line)}</tspan>'
        )

    return (
        f'<text x="{x}" y="{y}" fill="{color}" '
        f'font-size="{font_size}"{weight_attr}>'
        + "".join(tspans)
        + "</text>"
    )


def svg_start(
    width, height, delay, font_data, show_status_dot=True,
    status_dot=None
):
    inter, fira = font_data
    font_css = ""

    if inter:
        font_css += (
            f"@font-face{{font-family:Inter;"
            f"src:url('{inter}') format('woff')}}"
        )

    if fira:
        font_css += (
            f"@font-face{{font-family:'Fira Code';"
            f"src:url('{fira}') format('woff')}}"
        )

    animation_css = ""
    if not STATIC:
        animation_css = f"""
        .card {{
            animation: enter .85s ease-out {delay}s both;
        }}

        .glow {{
            animation: glow 3.5s ease-in-out {delay}s infinite alternate;
        }}

        .bar {{
            transform-box: fill-box;
            transform-origin: bottom;
            animation: grow .9s ease-out {delay + .2}s both;
        }}

        .best-value {{
            opacity: 0;
            transform-box: fill-box;
            transform-origin: center;
            animation: pop .45s cubic-bezier(.2, 1.5, .4, 1)
                       {delay + 1.1}s forwards;
        }}

        .cell {{
            opacity: 0;
            animation: appear .25s ease-out both;
        }}

        .tile-card {{
            transform-box: fill-box;
            transform-origin: center bottom;
            animation: tile-enter .9s cubic-bezier(.2, 1.4, .4, 1)
                       both;
        }}

        .tile-shine {{
            animation: shine 4.5s ease-in-out infinite;
        }}

        @keyframes enter {{
            from {{ opacity: 0; transform: translateY(18px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes glow {{
            from {{ opacity: .2; }}
            to {{ opacity: .9; }}
        }}

        @keyframes grow {{
            from {{ transform: scaleY(.02); }}
            to {{ transform: scaleY(1); }}
        }}

        @keyframes appear {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        @keyframes pop {{
            0% {{ opacity: 0; transform: scale(.4) translateY(8px); }}
            75% {{ opacity: 1; transform: scale(1.2) translateY(-3px); }}
            100% {{ opacity: 1; transform: scale(1) translateY(0); }}
        }}

        @keyframes tile-enter {{
            0% {{
                opacity: 0;
                transform: translateY(65px) rotate(8deg);
            }}
            65% {{
                opacity: 1;
                transform: translateY(-9px) rotate(-2deg);
            }}
            82% {{ transform: translateY(4px) rotate(1deg); }}
            100% {{
                opacity: 1;
                transform: translateY(0) rotate(0);
            }}
        }}

        @keyframes shine {{
            0%, 65% {{ transform: translateX(-340px); }}
            85%, 100% {{ transform: translateX(340px); }}
        }}
        """

    reduced_motion = """
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation: none !important;
            transition: none !important;
        }

        animate, set {
            display: none !important;
        }

        .card, .tile-card, .bar, .best-value, .cell {
            opacity: 1 !important;
            transform: none !important;
        }
    }
    """

    smil = ""
    if not STATIC and show_status_dot:
        # Default position is preserved for existing cards. Individual cards
        # can override it when their layout needs a slightly different anchor.
        dot_x, dot_y, dot_radius = status_dot or (width - 28, 26, 3)
        smil = f"""
        <circle cx="{dot_x}" cy="{dot_y}" r="{dot_radius}"
                fill="{ACCENT}">
            <animate
                attributeName="opacity"
                values=".3;1;.3"
                dur="2.8s"
                begin="{delay}s"
                repeatCount="indefinite"
            />
        </circle>
        """

    return f"""
    <svg xmlns="http://www.w3.org/2000/svg"
         xmlns:xlink="http://www.w3.org/1999/xlink"
         width="{width}"
         height="{height}"
         viewBox="0 0 {width} {height}">

        <title>Rugved Bane - GitHub Profile</title>

        <style>
            {font_css}

            text {{
                font-family: Inter, Arial, sans-serif;
            }}

            .mono {{
                font-family: 'Fira Code', monospace;
            }}

            {animation_css}
            {reduced_motion}
        </style>

        <rect width="100%" height="100%"
              rx="19" fill="{BG}"/>

        <rect x="1" y="1"
              width="{width - 2}"
              height="{height - 2}"
              rx="18"
              fill="none"
              stroke="{BORDER}"/>

        <g class="card">
            {smil}
    """


def save_card(filename, body, width, height, delay, fonts,
              show_status_dot=True, status_dot=None):
    OUT.mkdir(parents=True, exist_ok=True)

    content = (
        svg_start(
            width, height, delay, fonts, show_status_dot, status_dot
        )
        + body
        + "</g></svg>"
    )

    (OUT / filename).write_text(content, encoding="utf-8")


def hero(fonts):
    """Top profile card with name, positioning, focus areas and portrait."""
    serif_regular, serif_italic = load_serif_fonts()
    serif_css = ""

    if serif_regular:
        serif_css += (
            "@font-face{font-family:'Instrument Serif';"
            "font-style:normal;"
            f"src:url('{serif_regular}') format('woff')}}"
        )

    if serif_italic:
        serif_css += (
            "@font-face{font-family:'Instrument Serif';"
            "font-style:italic;"
            f"src:url('{serif_italic}') format('woff')}}"
        )

    parts = NAME.split()
    first = parts[0] if parts else NAME
    rest = " ".join(parts[1:])

    portrait = ""
    portrait_file = ASSETS / "portrait-sketch.png"
    if portrait_file.exists():
        image_data = base64.b64encode(portrait_file.read_bytes()).decode()
        image_uri = f"data:image/png;base64,{image_data}"
        # The portrait intentionally occupies the right side without a box,
        # divider or extra frame, preserving the existing hero composition.
        portrait = f"""
        <image x="500" y="-3" width="360" height="306"
               preserveAspectRatio="xMidYMid meet"
               xlink:href="{image_uri}"/>
        """

    body = f"""
    <style>
        {serif_css}
        .serif {{
            font-family: 'Instrument Serif', Georgia,
                         'Times New Roman', serif;
        }}
    </style>

    <circle cx="38" cy="41" r="3.5" fill="{ACCENT}"/>

    <text x="50" y="45" fill="{MUTED}" font-size="12"
          letter-spacing="1.5" class="mono">
        {esc(HERO_LABEL)}
    </text>

    <text x="34" y="128" fill="{TEXT}" font-size="92"
          letter-spacing="-1" class="serif">
        {esc(first)}
    </text>

    <text x="34" y="214" fill="{ACCENT}" font-size="92"
          font-style="italic" letter-spacing="-1" class="serif">
        {esc(rest)}
    </text>

    <text x="38" y="250" fill="{MUTED}" font-size="14">
        {esc(TAGLINE_1)}
    </text>

    <text x="38" y="270" fill="{MUTED}" font-size="14">
        {esc(TAGLINE_2)}
    </text>

    <line x1="38" y1="286" x2="112" y2="286"
          stroke="{ACCENT}" stroke-width="1.5"
          stroke-linecap="round" opacity=".72"/>

    {portrait}
    """

    save_card("01-hero.svg", body, 860, 300, 0, fonts)


def count_up_smil(target, begin):
    """Create 18 discrete SMIL text frames for a small tile counter."""
    if STATIC:
        return ""

    frames = []
    for index in range(1, 19):
        value = round(target * index / 18)
        start = begin + (index - 1) * 0.045
        frames.append(
            f'<set attributeName="textContent" '
            f'to="{value:02d}" '
            f'begin="{start:.3f}s" '
            f'dur="0.045s" fill="freeze"/>'
        )

    return "".join(frames)


def link_tiles(fonts):
    """Generate the LinkedIn and Kaggle profile link tiles."""
    links = [
        (
            "02-link-2.svg",
            "LINKEDIN",
            "AI/ML work and professional updates",
            "https://www.linkedin.com/in/rugvedbane/"
        ),
        (
            "02-link-3.svg",
            "KAGGLE",
            "Expert · Notebooks and competitions",
            f"https://www.kaggle.com/{USERNAME.lower()}"
        )
    ]

    old_card = OUT / "02-link-1.svg"
    if old_card.exists():
        old_card.unlink()

    for index, (filename, title, subtitle, url) in enumerate(links, 1):
        delay = 0.15 + index * 0.16
        number = f"{index:02d}"

        counter = (
            f'<text x="235" y="48" text-anchor="end" '
            f'fill="{ACCENT}" font-size="25" '
            f'class="mono">{number}'
            f'{count_up_smil(index, delay + 0.65)}'
            f'</text>'
        )

        shine = ""
        if not STATIC:
            shine = f"""
            <clipPath id="tile-clip-{index}">
                <rect x="1" y="1" width="278" height="128" rx="16"/>
            </clipPath>

            <g clip-path="url(#tile-clip-{index})">
                <rect class="tile-shine"
                      x="-340" y="0"
                      width="100" height="130"
                      fill="white" opacity=".18"
                      transform="skewX(-20)"/>
            </g>
            """

        subtitle_svg = multiline_text(
            subtitle, x=20, y=87, font_size=10, color=MUTED,
            line_height=12, max_chars=34, max_lines=2
        )

        body = f"""
        <g class="tile-card" style="animation-delay:{delay:.2f}s">
            <rect x="1" y="1" width="278" height="128"
                  rx="16" fill="{PANEL}" stroke="{BORDER}"/>

            <text x="20" y="28" fill="{ACCENT}"
                  font-size="9" class="mono">
                0{index} / PROFILE
            </text>

            <text x="20" y="63" fill="{TEXT}"
                  font-size="20" font-weight="720">
                {esc(title)}
            </text>

            <line x1="20" y1="74" x2="48" y2="74"
                  stroke="{ACCENT}" stroke-width="1.4"
                  stroke-linecap="round" opacity=".72"/>

            {subtitle_svg}

            <text x="20" y="113" fill="{ACCENT}" font-size="10"
                  class="mono">
                VIEW PROFILE
            </text>

            <text x="104" y="113" fill="{ACCENT}"
                  font-size="12">
                ↗
            </text>

            {counter}
            {shine}

            <a href="{esc(url)}">
                <rect x="1" y="1" width="278" height="128"
                      rx="16" fill="transparent"/>
            </a>
        </g>
        """

        save_card(
            filename,
            body,
            280,
            130,
            delay,
            fonts,
            show_status_dot=False
        )


def activity_card(stats, fonts):
    """Monthly contribution chart with five compact activity indicators."""
    max_value = max((value for _, value in stats["months"]), default=1) or 1
    chart_baseline = 213
    chart_height = 65
    best_month_name = stats["best_month"][0]

    bars = []
    for index, (month, value) in enumerate(stats["months"]):
        x = 45 + index * 65
        bar_height = max(3, round(chart_height * value / max_value))
        y = chart_baseline - bar_height
        is_best = month == best_month_name and value > 0
        label_class = " class='best-value'" if is_best and not STATIC else ""

        bars.append(f"""
        <rect class="bar"
              x="{x}" y="{y}"
              width="29" height="{bar_height}"
              rx="4" fill="{ACCENT}"
              style="animation-delay:{0.75 + index * 0.055:.3f}s"/>

        <text{label_class}
              x="{x + 14}" y="{max(139, y - 9)}"
              text-anchor="middle"
              fill="{ACCENT}" font-size="10"
              font-weight="700">
            {value if is_best else ""}
        </text>

        <text x="{x + 14}" y="238"
              text-anchor="middle"
              fill="{MUTED}" font-size="9">
            {esc(month)}
        </text>
        """)

    metrics = [
        (28, stats["total"], "TOTAL CONTRIBUTIONS"),
        (225, stats["streak"], "DAY STREAK"),
        (405, stats["active"], "ACTIVE DAYS"),
        (575, stats["busiest_count"], "BUSIEST DAY")
    ]

    metric_svg = []
    for x, value, label in metrics:
        metric_svg.append(f"""
        <text x="{x}" y="91" fill="{ACCENT if label == 'TOTAL CONTRIBUTIONS' else TEXT}"
              font-size="25" font-weight="740">
            {esc(f'{value:,}' if isinstance(value, int) else value)}
        </text>
        <text x="{x + 1}" y="108" fill="{MUTED}" font-size="8.5"
              letter-spacing=".35">
            {esc(label)}
        </text>
        """)

    body = f"""
    <text x="28" y="34" fill="{TEXT}"
          font-size="19" font-weight="720">
        Contribution activity
    </text>

    <text x="28" y="53" fill="{MUTED}" font-size="10">
        Monthly contributions · Rolling 12-month view
    </text>

    <text x="815" y="32" text-anchor="end" fill="{MUTED}"
          font-size="8.5" letter-spacing=".5" class="mono">
        BEST MONTH
    </text>
    <text x="815" y="51" text-anchor="end" fill="{ACCENT}"
          font-size="12" font-weight="700">
        {esc(best_month_name)} · {stats['best_month'][1]:,}
    </text>

    {''.join(metric_svg)}

    <text x="576" y="124" fill="{MUTED}" font-size="8.5">
        {esc(stats['busiest_date'])}
    </text>

    <line x1="38" y1="216" x2="822" y2="216"
          stroke="{BORDER}" stroke-width="1" opacity=".82"/>

    {''.join(bars)}
    """

    save_card(
        "03-activity.svg", body, 860, 250, .52, fonts,
        show_status_dot=False
    )


def stack_pills(items, x=83, y=157, max_x=615):
    """Lay out short tech labels as compact pills with a safe right boundary."""
    output = []
    current_x = x
    current_y = y
    pill_height = 21
    gap = 7

    for item in items:
        label = str(item)
        pill_width = max(43, int(len(label) * 5.15 + 18))

        if current_x + pill_width > max_x:
            current_x = x
            current_y += pill_height + 4

        # Project stacks are intentionally short; if one is edited later,
        # its text is still constrained inside the pill.
        text_size = 8.2
        output.append(f"""
        <rect x="{current_x}" y="{current_y}"
              width="{pill_width}" height="{pill_height}"
              rx="10.5" fill="{PANEL}" stroke="{BORDER}"/>
        <text x="{current_x + pill_width / 2:.1f}"
              y="{current_y + 14.1:.1f}"
              text-anchor="middle" fill="{MUTED}"
              font-size="{text_size}" font-weight="600">
            {esc(label)}
        </text>
        """)
        current_x += pill_width + gap

    return "".join(output), current_y + pill_height


def project_cards(fonts):
    """Project cards with concise descriptions, stack chips and real metrics."""
    for old_card in OUT.glob("04-project-*.svg"):
        old_card.unlink()

    for index, project in enumerate(PROJECTS, 1):
        pills, _ = stack_pills(project["stack"])
        description_svg = multiline_text(
            project["description"],
            x=25,
            y=119,
            font_size=10.5,
            color=MUTED,
            line_height=15,
            max_chars=83,
            max_lines=2
        )

        # Use fixed panel coordinates and reserved text baselines. The
        # description and stack area cannot intrude into the metric panel.
        body = f"""
        <a href="{esc(project['repo'])}">
            <rect x="1" y="1" width="858" height="222"
                  rx="18" fill="transparent"/>

            <text x="24" y="29" fill="{ACCENT}"
                  font-size="9" class="mono" letter-spacing=".5">
                FEATURED PROJECT / {index:02d}
            </text>

            <text x="24" y="68" fill="{TEXT}"
                  font-size="25" font-weight="750">
                {esc(project['name'])}
            </text>

            <text x="25" y="92" fill="{ACCENT}" font-size="12"
                  font-weight="600">
                {esc(project['subtitle'])}
            </text>

            {description_svg}

            <line x1="24" y1="150" x2="616" y2="150"
                  stroke="{BORDER}" stroke-width="1"/>

            <text x="25" y="171" fill="{MUTED}"
                  font-size="8.2" class="mono" letter-spacing=".45">
                STACK
            </text>

            {pills}

            <text x="25" y="207" fill="{ACCENT}"
                  font-size="9.5" class="mono" letter-spacing=".2">
                VIEW REPOSITORY  >
            </text>

            <rect x="646" y="27" width="190" height="174"
                  rx="14" fill="{PANEL}" stroke="{BORDER}"/>

            <text x="663" y="49" fill="{MUTED}"
                  font-size="8" class="mono" letter-spacing=".55">
                PROJECT PROOF
            </text>

            <text x="663" y="88" fill="{TEXT}"
                  font-size="25" font-weight="760">
                {esc(project['primary_value'])}
            </text>

            <text x="664" y="105" fill="{MUTED}"
                  font-size="7.7" class="mono" letter-spacing=".1">
                {esc(project['primary_label'])}
            </text>

            <line x1="663" y1="117" x2="819" y2="117"
                  stroke="{BORDER}" stroke-width="1"/>

            <text x="663" y="148" fill="{ACCENT}"
                  font-size="18" font-weight="730">
                {esc(project['secondary_value'])}
            </text>

            <text x="664" y="164" fill="{MUTED}"
                  font-size="7.3" class="mono">
                {esc(project['secondary_label'])}
            </text>

            <text x="663" y="186" fill="{MUTED}"
                  font-size="7.8">
                {esc(project['footnote'])}
            </text>

            <line x1="631" y1="43" x2="631" y2="193"
                  stroke="{BORDER}" stroke-width="1"
                  opacity=".9"/>

            <text x="615" y="29" text-anchor="end" fill="{MUTED}"
                  font-size="7.2" class="mono">
                {esc(project['tag'])}
            </text>
        </a>
        """

        save_card(
            f"04-project-{index}.svg",
            body,
            860,
            224,
            .8 + index * .18,
            fonts,
            status_dot=(836, 22, 4)
        )


def open_source_card(fonts):
    """Show selected merged/open PRs and the breadth of OSS work."""
    merged_pr_url = (
        f"https://github.com/search?"
        f"q=author%3A{USERNAME}+is%3Apr+is%3Amerged"
        f"&type=pullrequests"
    )

    prs = [
        (
            "scikit-learn/scikit-learn",
            "RFECV per-split ranking and support shapes · PR #35174",
            "MERGED"
        ),
        (
            "scikit-learn/scikit-learn",
            "HistGradientBoosting early-stopping fix · PR #35176",
            "MERGED"
        ),
        (
            "feature-engine/feature_engine",
            "Feature-engine contribution · PR #1120",
            "OPEN"
        ),
        (
            "philpaz/recusal",
            "Validation helper + 14 tests · PR #63",
            "MERGED"
        )
    ]

    rows = []
    for index, (repo, description, status) in enumerate(prs):
        y = 82 + index * 46
        status_color = ACCENT if status == "MERGED" else "#A36B20"
        status_bg = "#DDE8D9" if status == "MERGED" else "#F0E5CF"

        rows.append(f"""
        <rect x="27" y="{y - 16}" width="805" height="38"
              rx="7" fill="{PANEL if index % 2 == 0 else BG}"
              opacity=".62"/>

        <text x="40" y="{y}" fill="{TEXT}"
              font-size="11.5" font-weight="650">
            {esc(repo)}
        </text>

        <text x="40" y="{y + 14}" fill="{MUTED}"
              font-size="9.2">
            {esc(description)}
        </text>

        <rect x="756" y="{y - 11}" width="62" height="18"
              rx="9" fill="{status_bg}"/>
        <text x="787" y="{y + 1.5}" text-anchor="middle"
              fill="{status_color}" font-size="7.5"
              class="mono" font-weight="700">
            {esc(status)}
        </text>
        """)

    body = f"""
    <a href="{esc(merged_pr_url)}">
        <rect x="1" y="1" width="858" height="270"
              rx="18" fill="transparent"/>

        <text x="27" y="31" fill="{TEXT}"
              font-size="18" font-weight="720">
            Open-source contributions
        </text>

        <text x="27" y="49" fill="{MUTED}" font-size="9.5">
            Merged work across machine-learning and Python projects
        </text>

        <rect x="720" y="15" width="112" height="25"
              rx="12.5" fill="{PANEL}" stroke="{BORDER}"/>
        <line x1="27" y1="60" x2="832" y2="60"
              stroke="{BORDER}" stroke-width="1" opacity=".85"/>
        <text x="776" y="31" text-anchor="middle"
              fill="{ACCENT}" font-size="8.5"
              class="mono" font-weight="700">
            6+ PRs MERGED
        </text>

        {''.join(rows)}

        <text x="28" y="258" fill="{MUTED}"
              font-size="8.3" class="mono">
        </text>
    </a>
    """

    save_card(
        "09-open-source.svg", body, 860, 274, 1.8, fonts,
        show_status_dot=False
    )


def contribution_graph(stats, fonts):
    """Contribution heatmap with month labels and a small weekly insight."""
    colors = [
        "#E5E8DD",
        "#C6D8C2",
        "#83AD8B",
        "#477D5A",
        "#245744"
    ]

    cells = []
    month_labels = []
    days = stats["days"]

    for index, day in enumerate(days):
        col, row = divmod(index, 7)
        x = 28 + col * 12
        y = 67 + row * 12

        try:
            current_date = date.fromisoformat(day.get("date", ""))
            day_count = max(0, int(day.get("count", 0)))
            if current_date.day <= 7:
                month_labels.append((x, calendar.month_abbr[current_date.month]))
        except (TypeError, ValueError):
            day_count = 0

        level = max(0, min(4, int(day.get("level", 0) or 0)))
        reveal_delay = col * 0.045 + row * 0.008
        cell_animation = ""
        if not STATIC:
            cell_animation = f'style="animation-delay:{reveal_delay:.3f}s"'

        cells.append(f"""
        <rect class="cell"
              {cell_animation}
              x="{x}" y="{y}"
              width="8" height="8"
              rx="2" fill="{colors[level]}">
            <title>
                {esc(day.get('date', ''))}: {day_count} contributions
            </title>
        </rect>
        """)

    labels_seen = set()
    month_svg = []
    for x, month in month_labels:
        if month in labels_seen:
            continue
        labels_seen.add(month)
        month_svg.append(f"""
        <text x="{x}" y="59" fill="{MUTED}"
              font-size="7.8">
            {esc(month)}
        </text>
        """)

    legend = "".join(
        f'<rect x="{58 + index * 14}" y="178" width="9" height="9" '
        f'rx="2" fill="{color}"/>'
        for index, color in enumerate(colors)
    )

    weekday = stats["most_active_weekday"]
    average = stats["average_per_active_day"]

    body = f"""
    <text x="28" y="29" fill="{TEXT}"
          font-size="18" font-weight="720">
        Contribution graph
    </text>

    <text x="28" y="44" fill="{MUTED}" font-size="9">
        Past year · Contribution intensity in forest green
    </text>

    {''.join(month_svg)}
    {''.join(cells)}

    <line x1="674" y1="54" x2="674" y2="160"
          stroke="{BORDER}" stroke-width="1" opacity=".9"/>

    <rect x="690" y="54" width="146" height="105"
          rx="12" fill="{PANEL}" stroke="{BORDER}"/>

    <text x="705" y="74" fill="{MUTED}"
          font-size="7.8" class="mono" letter-spacing=".3">
        WEEKLY PATTERN
    </text>

    <text x="705" y="103" fill="{ACCENT}"
          font-size="19" font-weight="730">
        {esc(weekday[:3])}
    </text>

    <text x="705" y="117" fill="{MUTED}" font-size="8">
        MOST ACTIVE WEEKDAY
    </text>

    <line x1="705" y1="126" x2="821" y2="126"
          stroke="{BORDER}" stroke-width="1"/>

    <text x="705" y="145" fill="{TEXT}"
          font-size="12" font-weight="700">
        {average:.1f}
    </text>

    <text x="750" y="145" fill="{MUTED}" font-size="7.5">
        PER ACTIVE DAY
    </text>

    <text x="28" y="186" fill="{MUTED}" font-size="9">
        Less
    </text>

    {legend}

    <text x="131" y="186" fill="{MUTED}" font-size="9">
        More
    </text>
    """

    save_card("10-contributions.svg", body, 860, 205, 2.25, fonts)


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    data = load_data()
    stats = calculate_stats(data)
    font_data = load_fonts()

    hero(font_data)
    link_tiles(font_data)
    activity_card(stats, font_data)
    project_cards(font_data)
    open_source_card(font_data)
    contribution_graph(stats, font_data)

    generated = sorted(OUT.glob("*.svg"))
    print(f"Generated {len(generated)} SVG cards.")

    if STATIC:
        print("Static mode enabled. Animations are disabled.")


if __name__ == "__main__":
    main()
