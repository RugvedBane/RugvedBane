
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
"""

import os
import json
import html
import base64
import calendar
import shutil
import subprocess

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
    "Open source contributor · Kaggle Expert."
)

# Forest green + warm off-white palette
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


# Featured repositories
PROJECTS = [
    {
        "name": "Kwest",
        "subtitle": "AI-powered Kaggle workspace",
        "description": (
            "Eight tools for Kaggle workflows, "
            "experiment memory and code visibility."
        ),
        "repo": f"https://github.com/{USERNAME}/Kwest",
        "tag": "GENAI"
    },
    {
        "name": "Deepfake Audio Detector",
        "subtitle": "Synthetic audio detection",
        "description": (
            "Machine learning project for "
            "detecting deepfake audio."
        ),
        "repo": f"https://github.com/{USERNAME}/deepfake-audio-detector",
        "tag": "MACHINE LEARNING"
    },
    {
        "name": "UFC Fight Predictor",
        "subtitle": "Sports prediction · ML",
        "description": (
            "Data-driven modelling for predicting "
            "UFC fight outcomes."
        ),
        "repo": f"https://github.com/{USERNAME}/UFC-Predictor",
        "tag": "MACHINE LEARNING"
    }
]


def esc(value):
    return html.escape(str(value), quote=True)


def load_data():
    if not DATA.exists():
        return {"total_contributions": 0, "days": []}

    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def calculate_stats(data):
    counts = {}

    for item in data.get("days", []):
        try:
            d = date.fromisoformat(item["date"])
            counts[d] = int(item.get("count", 0))
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
            value for d, value in counts.items()
            if d.year == year and d.month == month
        )

        months.append((calendar.month_abbr[month], total))

    busiest, peak = max(
        counts.items(),
        key=lambda item: item[1],
        default=(None, 0)
    )

    best_month = max(months, key=lambda item: item[1], default=("—", 0))

    return {
        "total": int(
            data.get("total_contributions", sum(counts.values()))
        ),
        "active": sum(v > 0 for v in counts.values()),
        "streak": streak,
        "busiest_date": busiest.isoformat() if busiest else "—",
        "busiest_count": peak,
        "months": months,
        "best_month": best_month,
        "days": data.get("days", [])[-371:]
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
    """Embed Instrument Serif regular and italic fonts."""

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


def svg_start(width, height, delay, font_data, show_status_dot=True):
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
            from {{
                opacity: 0;
                transform: translateY(18px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
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
            0% {{
                opacity: 0;
                transform: scale(.4) translateY(8px);
            }}
            75% {{
                opacity: 1;
                transform: scale(1.2) translateY(-3px);
            }}
            100% {{
                opacity: 1;
                transform: scale(1) translateY(0);
            }}
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
            82% {{
                transform: translateY(4px) rotate(1deg);
            }}
            100% {{
                opacity: 1;
                transform: translateY(0) rotate(0);
            }}
        }}

        @keyframes shine {{
            0%, 65% {{
                transform: translateX(-340px);
            }}
            85%, 100% {{
                transform: translateX(340px);
            }}
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
        smil = f"""
        <circle cx="{width - 28}" cy="26" r="3" fill="{ACCENT}">
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


def save_card(filename, body, width, height, delay, fonts, show_status_dot=True):
    OUT.mkdir(parents=True, exist_ok=True)

    content = (
        svg_start(width, height, delay, fonts, show_status_dot)
        + body
        + "</g></svg>"
    )

    (OUT / filename).write_text(content, encoding="utf-8")


def hero(fonts):
    """Top card: label, large serif name, tagline and optional portrait."""

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
        data = base64.b64encode(portrait_file.read_bytes()).decode()
        uri = f"data:image/png;base64,{data}"

        portrait = f"""
        <image x="510" y="-2" width="320" height="300"
               preserveAspectRatio="xMidYMid meet"
               xlink:href="{uri}"/>
        """

    body = f"""
    <style>
        {serif_css}
        .serif {{
            font-family: 'Instrument Serif', Georgia,
                         'Times New Roman', serif;
        }}
    </style>

    <circle cx="38" cy="46" r="3.5" fill="{ACCENT}"/>

    <text x="50" y="50" fill="{MUTED}" font-size="11"
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

    {portrait}
    """

    save_card("01-hero.svg", body, 860, 300, 0, fonts)


def count_up_smil(target, begin):
    """Create 18 discrete SMIL text frames for a number."""

    if STATIC:
        return ""

    frames = []

    for i in range(1, 19):
        value = round(target * i / 18)
        start = begin + (i - 1) * 0.045

        frames.append(
            f'<set attributeName="textContent" '
            f'to="{value:02d}" '
            f'begin="{start:.3f}s" '
            f'dur="0.045s" fill="freeze"/>'
        )

    return "".join(frames)


def link_tiles(fonts):
    """Generate two centered profile link cards: LinkedIn and Kaggle."""

    links = [
        (
            "02-link-2.svg",
            "LINKEDIN",
            "Professional profile",
            "https://www.linkedin.com/in/rugvedbane/"
        ),
        (
            "02-link-3.svg",
            "KAGGLE",
            "Competitions & notebooks",
            "https://www.kaggle.com/rugvedbane"
        )
    ]

    old_card = OUT / "02-link-1.svg"
    if old_card.exists():
        old_card.unlink()

    for i, (filename, title, subtitle, url) in enumerate(links, 1):
        delay = 0.15 + i * 0.16
        number = f"{i:02d}"

        counter = (
            f'<text x="235" y="48" text-anchor="end" '
            f'fill="{ACCENT}" font-size="25" '
            f'class="mono">{number}'
            f'{count_up_smil(i, delay + 0.65)}'
            f'</text>'
        )

        shine = ""

        if not STATIC:
            shine = f"""
            <clipPath id="tile-clip-{i}">
                <rect x="1" y="1" width="278" height="128" rx="16"/>
            </clipPath>

            <g clip-path="url(#tile-clip-{i})">
                <rect class="tile-shine"
                      x="-340" y="0"
                      width="100" height="130"
                      fill="white" opacity=".18"
                      transform="skewX(-20)"/>
            </g>
            """

        body = f"""
        <g class="tile-card"
           style="animation-delay:{delay:.2f}s">

            <rect x="1" y="1"
                  width="278" height="128"
                  rx="16" fill="{PANEL}"
                  stroke="{BORDER}"/>

            <text x="20" y="28" fill="{ACCENT}"
                  font-size="9" class="mono">
                0{i} / PROFILE
            </text>

            <text x="20" y="63" fill="{TEXT}"
                  font-size="20" font-weight="720">
                {esc(title)}
            </text>

            <text x="20" y="87" fill="{MUTED}" font-size="10">
                {esc(subtitle)}
            </text>

            <text x="20" y="112" fill="{ACCENT}" font-size="10"
                  class="mono">
                OPEN
            </text>

            <text x="55" y="112" fill="{ACCENT}"
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
    max_value = max(
        (v for _, v in stats["months"]),
        default=1
    ) or 1

    bars = []

    chart_baseline = 213
    chart_height = 65

    best_month = stats["best_month"][0]

    for i, (month, value) in enumerate(stats["months"]):
        x = 45 + i * 65
        height = max(3, round(chart_height * value / max_value))
        y = chart_baseline - height

        is_best = month == best_month and value > 0

        bars.append(f"""
        <rect class="bar"
              x="{x}" y="{y}"
              width="29" height="{height}"
              rx="4" fill="{ACCENT}"
              style="animation-delay:{0.75 + i * 0.055:.3f}s"/>

        {"<text class='best-value' " if is_best and not STATIC else "<text "}
              x="{x + 14}" y="{max(135, y - 9)}"
              text-anchor="middle"
              fill="{ACCENT}" font-size="10"
              font-weight="700">
            {value if is_best else ""}
        </text>

        <text x="{x + 14}" y="238"
              text-anchor="middle"
              fill="{MUTED}" font-size="9">
            {month}
        </text>
        """)

    body = f"""
    <text x="28" y="34" fill="{TEXT}"
          font-size="19" font-weight="720">
        Contribution activity
    </text>

    <text x="28" y="53" fill="{MUTED}" font-size="10">
        Monthly contributions · Last 12 months
    </text>

    <text x="28" y="91" fill="{ACCENT}"
          font-size="26" font-weight="750">
        {stats['total']:,}
    </text>

    <text x="29" y="108" fill="{MUTED}" font-size="9">
        TOTAL CONTRIBUTIONS
    </text>

    <text x="302" y="91" fill="{TEXT}" font-size="23">
        {stats['streak']}
    </text>

    <text x="303" y="108" fill="{MUTED}" font-size="9">
        DAY STREAK
    </text>

    <text x="452" y="91" fill="{TEXT}" font-size="23">
        {stats['active']}
    </text>

    <text x="453" y="108" fill="{MUTED}" font-size="9">
        ACTIVE DAYS
    </text>

    <text x="625" y="91" fill="{TEXT}" font-size="23">
        {stats['busiest_count']}
    </text>

    <text x="626" y="108" fill="{MUTED}" font-size="9">
        BUSIEST DAY
    </text>

    <text x="626" y="124" fill="{MUTED}" font-size="9">
        {esc(stats['busiest_date'])}
    </text>

    {''.join(bars)}
    """

    save_card("03-activity.svg", body, 860, 250, .52, fonts)


def project_cards(fonts):
    # Delete stale project SVGs before generating the current set.
    for old_card in OUT.glob("04-project-*.svg"):
        old_card.unlink()

    for i, project in enumerate(PROJECTS, 1):
        body = f"""
        <a href="{esc(project['repo'])}">
            <rect x="1" y="1" width="858" height="198"
                  rx="18" fill="transparent"/>

            <text x="24" y="30" fill="{ACCENT}"
                  font-size="9" class="mono">
                FEATURED PROJECT / {i:02d}
            </text>

            <text x="24" y="72" fill="{TEXT}"
                  font-size="25" font-weight="750">
                {esc(project['name'])}
            </text>

            <text x="25" y="98" fill="{ACCENT}" font-size="12">
                {esc(project['subtitle'])}
            </text>

            <text x="25" y="128" fill="{MUTED}" font-size="11">
                {esc(project['description'])}
            </text>

            <text x="25" y="163" fill="{ACCENT}"
                  font-size="10" class="mono">
                SOURCE REPOSITORY ↗
            </text>

            <text x="690" y="30" fill="{MUTED}"
                  font-size="9" class="mono">
                {esc(project['tag'])}
            </text>
        </a>
        """

        save_card(
            f"04-project-{i}.svg",
            body,
            860,
            200,
            .8 + i * .18,
            fonts
        )


def open_source_card(fonts):
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

    for i, (repo, description, status) in enumerate(prs):
        y = 63 + i * 48

        status_color = (
            "#2F6B4F" if status == "MERGED"
            else "#A36B20"
        )

        rows.append(f"""
        <text x="27" y="{y}" fill="{TEXT}"
              font-size="13">
            {esc(repo)}
        </text>

        <text x="27" y="{y + 16}" fill="{MUTED}"
              font-size="10">
            {esc(description)}
        </text>

        <text x="817" y="{y + 5}" text-anchor="end"
              fill="{status_color}" font-size="9"
              class="mono" font-weight="700">
            {esc(status)}
        </text>
        """)

    body = f"""
    <a href="{esc(merged_pr_url)}">
    <rect x="1" y="1" width="858" height="258"
          rx="18" fill="transparent"/>

    <text x="27" y="31" fill="{TEXT}"
          font-size="18" font-weight="720">
        Open-source contributions
    </text>

    <text x="817" y="31" text-anchor="end"
          fill="{MUTED}" font-size="9" class="mono">
        6+ PRs MERGED
    </text>

    {''.join(rows)}
    </a>
    """

    save_card("09-open-source.svg", body, 860, 260, 1.8, fonts)


def contribution_graph(stats, fonts):
    colors = [
        "#E5E8DD",
        "#C6D8C2",
        "#83AD8B",
        "#477D5A",
        "#245744"
    ]

    cells = []

    for i, day in enumerate(stats["days"]):
        col, row = divmod(i, 7)

        x = 28 + col * 12
        y = 54 + row * 12

        level = max(0, min(4, int(day.get("level", 0))))

        reveal_delay = col * 0.045 + row * 0.008

        cell_animation = ""

        if not STATIC:
            cell_animation = (
                f'style="animation-delay:{reveal_delay:.3f}s"'
            )

        cells.append(f"""
        <rect class="cell"
              {cell_animation}
              x="{x}" y="{y}"
              width="8" height="8"
              rx="2" fill="{colors[level]}">

            <title>
                {esc(day.get('date', ''))}:
                {int(day.get('count', 0))} contributions
            </title>

        </rect>
        """)

    legend = "".join(
        f'<rect x="{58+i*14}" y="178" width="9" height="9" '
        f'rx="2" fill="{color}"/>'
        for i, color in enumerate(colors)
    )

    body = f"""
    <text x="28" y="29" fill="{TEXT}"
          font-size="18" font-weight="720">
        Contribution graph
    </text>

    <text x="28" y="44" fill="{MUTED}" font-size="9">
        Past year · Contribution intensity in forest green
    </text>

    {''.join(cells)}

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

    print(
        f"Generated {len(list(OUT.glob('*.svg')))} SVG cards."
    )

    if STATIC:
        print("Static mode enabled. Animations are disabled.")


if __name__ == "__main__":
    main()
