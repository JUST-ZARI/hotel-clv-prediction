"""
style.py — Design system for the Hotel CLV Decision Support System.

One set of tokens (colour, type, radius, shadow, motion) drives the landing page,
the authentication screens and the dashboard. Pages add only layout CSS.
"""

import html

import streamlit as st

# ---------------------------------------------------------------------------
# Icon helpers — Font Awesome 6 Free
# ---------------------------------------------------------------------------

def icon(name: str, extra_class: str = "", color: str = None, size: str = None) -> str:
    """Return an FA6-free solid icon as an HTML string."""
    cls = f"fa-solid fa-{name} {extra_class}".strip()
    styles = []
    if color:
        styles.append(f"color: {color};")
    if size:
        styles.append(f"font-size: {size};")
    style_attr = f' style="{" ".join(styles)}"' if styles else ""
    return f'<i class="{cls}"{style_attr}></i>'


def icon_reg(name: str, extra_class: str = "", color: str = None, size: str = None) -> str:
    """Return an FA6-free regular (outline) icon as an HTML string."""
    return icon(name, extra_class, color, size).replace("fa-solid", "fa-regular", 1)


ICONS = {
    "gear":         icon("gear"),
    "login":        icon("right-to-bracket"),
    "dashboard":    icon("table-cells-large"),
    "search":       icon("magnifying-glass"),
    "pie":          icon("chart-pie"),
    "warning":      icon("triangle-exclamation"),
    "bar_chart":    icon("chart-bar"),
    "users":        icon("users"),
    "user_plus":    icon("user-plus"),
    "star":         icon("star"),
    "coins":        icon("coins"),
    "clock":        icon("clock"),
    "bolt":         icon("bolt"),
    "arrow_up":     icon("arrow-trend-up"),
    "arrow_down":   icon("arrow-trend-down"),
    "download":     icon("download"),
    "send":         icon("paper-plane"),
    "pdf":          icon("file-pdf"),
    "lock":         icon("lock"),
    "logout":       icon("right-from-bracket"),
    "check":        icon("circle-check"),
    "circle":       icon_reg("circle"),
    "bed":          icon("bed"),
    "envelope":     icon("envelope"),
    "hotel":        icon("hotel"),
    "robot":        icon("robot"),
    "chart_scatter": icon("chart-line"),
    "brain":        icon("brain"),
    "shield":       icon("shield-halved"),
    "refresh":      icon("rotate"),
}


# ---------------------------------------------------------------------------
# Small HTML components shared by every page
# ---------------------------------------------------------------------------

def brand_lockup(subtitle: str = "Decision Support System") -> str:
    """Logo tile + product name, as used in the top bar and sidebar."""
    return f"""
    <div class="ds-brand">
        <span class="ds-brand-mark">{icon("hotel")}</span>
        <span class="ds-brand-text">
            <span class="ds-brand-name">Hotel CLV</span>
            <span class="ds-brand-sub">{subtitle}</span>
        </span>
    </div>"""


_ALERT_ICONS = {
    "error": "circle-exclamation",
    "success": "circle-check",
    "info": "circle-info",
    "warning": "triangle-exclamation",
}


def alert(kind: str, message: str) -> None:
    """Design-system alert (replaces st.error / st.success on custom screens)."""
    st.markdown(
        f'<div class="ds-alert ds-alert-{kind}" role="alert">'
        f'{icon(_ALERT_ICONS[kind])}<span>{html.escape(message)}</span></div>',
        unsafe_allow_html=True,
    )


def field_error(message: str | None) -> None:
    """Inline validation message placed directly under an input."""
    if message:
        st.markdown(
            f'<div class="ds-field-error">{icon("circle-exclamation")}'
            f'<span>{html.escape(message)}</span></div>',
            unsafe_allow_html=True,
        )




# ---------------------------------------------------------------------------
# Photography (Unsplash licence, free for commercial use; loaded from Unsplash's CDN)
# ---------------------------------------------------------------------------

def _photo(photo_id: str, width: int) -> str:
    return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w={width}&q=75"


PHOTO_AUTH = _photo("photo-1721617864119-611e4544ff07", 1200)    # resort pool and palms at sunset
PHOTO_ROOM = _photo("photo-1771775529138-a7a20ba7e032", 1600)    # hotel room with a city view
PHOTO_RESORT = _photo("photo-1596178060810-72f53ce9a65c", 1400)  # tropical resort pool deck
PHOTO_LOBBY = _photo("photo-1759038086832-795644825e3a", 900)    # hotel lobby and reception


# ---------------------------------------------------------------------------
# Global stylesheet
# ---------------------------------------------------------------------------

_CSS = """
<link rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"
      integrity="sha512-DTOQO9RWCH3ppGqcWaEA1BIZOC6xxalwEsw9c2QQeAIftl+Vegovlnee1c9QX4TctnWMn13TZye+giMm8e2LwA=="
      crossorigin="anonymous" referrerpolicy="no-referrer" />

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">

<style>
/* =========================================================
   TOKENS
   ========================================================= */
:root {
    /* Typography: Inter (falls back to Segoe UI / the system font) */
    --font: Inter, 'Segoe UI', system-ui, sans-serif;

    /* Brand: deep hotel green */
    --brand-800: #002E20;
    --brand-700: #003F2B;            /* deep forest: dark surfaces, hover */
    --brand-600: #0C5D49;            /* primary: buttons, accents */
    --brand-500: #1E7A60;
    --brand-300: #8CC5AE;
    --brand-200: #C3E0D2;
    --brand-100: #DCEEE4;
    --brand-50:  #EAF4ED;            /* soft sage: subtle backgrounds */
    --mint-300:  #A8E0BE;            /* highlight on dark green */

    /* Neutrals (cool, tuned to the green) */
    --ink-900: #0F1A15;
    --ink-800: #1D2A24;
    --ink-700: #2B3833;
    --ink-600: #45524C;
    --ink-500: #5E6A64;
    --ink-400: #96A09B;              /* placeholders only */

    --line:        #E3E9E5;
    --line-strong: #D0DAD4;
    --canvas:      #F4F7F5;
    --subtle:      #F7FAF8;
    --surface:     #FFFFFF;

    /* CLV tiers (chart palette): Platinum = forest, High = orange, Medium = green, Low = sky */
    --plat-700:   #003F2B; --plat-600:   #0C5D49; --plat-200:   #C3E0D2; --plat-50:   #EAF4ED;
    --orange-700: #9A4208; --orange-600: #C2540A; --orange-500: #E06A12; --orange-200: #F6CDA9; --orange-50: #FFF3E8;
    --sage-700: #3F7424; --sage-600: #5E9D3B; --sage-500: #7DBE5A; --sage-200: #D4EBC4; --sage-50: #F2F9EC;
    --sky-700:  #2B5F91; --sky-600:  #4A86C2; --sky-500:  #6FA8DC; --sky-200:  #CFE1F2; --sky-50:  #EFF6FC;
    --navy-700: #23345C; --navy-200: #CDD4E3; --navy-50: #EFF2F8;

    /* Status */
    --green-700: #1F6B3A; --green-600: #2E8B4E; --green-50: #EEF8F1; --green-200: #C7E8D2;
    --amber-700: #8A5A0E; --amber-600: #C08A26; --amber-50: #FDF6E7; --amber-200: #F0DDB0;
    --red-700:   #9B1C1C; --red-600:   #C0262D; --red-50:   #FEF1F1; --red-200:   #F7CACA;

    /* Sidebar: deep green panel */
    --side-bg:     linear-gradient(180deg, #0C5D49 0%, #003F2B 100%);
    --side-ink:    rgba(255,255,255,.80);
    --side-muted:  rgba(255,255,255,.55);
    --side-line:   rgba(255,255,255,.12);
    --side-hover:  rgba(255,255,255,.07);
    --side-active: rgba(255,255,255,.14);

    --card-shadow: 0 3px 9px rgba(37,63,47,.03);
    --card-hover-line: #89A97B;

    --r-sm: 6px;
    --r-md: 8px;
    --r-lg: 14px;
    --r-xl: 20px;

    --shadow-xs:   0 1px 2px rgba(12,43,33,.05);
    --shadow-card: 0 1px 2px rgba(12,43,33,.05), 0 12px 28px -16px rgba(12,43,33,.22);
    --shadow-pop:  0 2px 4px rgba(12,43,33,.05), 0 28px 56px -24px rgba(12,43,33,.35);
    --ring:        0 0 0 3px rgba(12,93,73,.18);
    --ease:        cubic-bezier(.2,.7,.2,1);
}

/* =========================================================
   BASE
   ========================================================= */
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea,
.stApp button, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
.stApp th, .stApp td, [data-testid="stMarkdownContainer"],
[data-baseweb="select"], [data-baseweb="popover"] li, [role="listbox"] li, [role="option"] {
    font-family: var(--font) !important;
}
.stApp {
    color: var(--ink-900);
    font-size: 1rem;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}
/* Text scale: every rem-based size follows this (16px -> 12.5px makes all text about 22% smaller) */
html { font-size: 12.5px !important; }
[data-testid="stAppViewContainer"],
[data-testid="stMain"] { background: var(--canvas); }

h1 { font-size: 1.85rem !important; font-weight: 700 !important; letter-spacing: -0.01em !important; color: var(--ink-900) !important; }
h2 { font-size: 1.35rem !important; font-weight: 700 !important; letter-spacing: 0 !important; color: var(--ink-900) !important; }
h3 { font-size: 1.12rem !important; font-weight: 700 !important; color: var(--ink-900) !important; }
[data-testid="stCaptionContainer"] p { color: var(--ink-500) !important; font-size: 0.88rem !important; }
hr { border-color: var(--line) !important; margin: 1rem 0 !important; }
::selection { background: var(--brand-100); color: var(--brand-700); }

/* Streamlit chrome */
[data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] [data-testid="stMarkdownContainer"] > style),
[data-testid="stElementContainer"]:has(> [data-testid="stHtml"] > style:first-child),
[data-testid="stElementContainer"]:has(> [data-testid="stHtml"] > script:first-child) { display: none !important; }
[data-testid="stStatusWidget"], [data-testid="stDecoration"],
[data-testid="stToolbarActions"], [data-testid="stAppDeployButton"], [data-testid="stMainMenu"] { display: none !important; }
[data-testid="stHeader"] { background: transparent !important; }

/* =========================================================
   BUTTONS
   ========================================================= */
.stApp button[data-testid^="stBaseButton-primary"],
.stApp button[data-testid^="stBaseButton-secondary"] {
    min-height: 40px;
    padding: 0 18px;
    border-radius: var(--r-md) !important;
    font-size: 0.95rem !important;
    box-shadow: var(--shadow-xs);
    transition: background .25s var(--ease), border-color .25s var(--ease), color .25s var(--ease),
                box-shadow .25s var(--ease), transform .15s var(--ease);
}
.stApp button[data-testid^="stBaseButton"] p { font-size: 0.95rem !important; font-weight: 700 !important; }
.stApp button[data-testid^="stBaseButton"]:active:not(:disabled) { transform: translateY(1px) scale(.99); }
.stApp button[data-testid^="stBaseButton-primary"] {
    background: linear-gradient(180deg, #0F6A53 0%, var(--brand-600) 100%) !important;
    border: 1px solid var(--brand-600) !important;
    color: #FFFFFF !important;
}
.stApp button[data-testid^="stBaseButton-primary"]:hover {
    background: linear-gradient(180deg, var(--brand-600) 0%, var(--brand-700) 100%) !important; border-color: var(--brand-700) !important;
    box-shadow: 0 8px 18px -10px rgba(0,63,43,.7);
    transform: translateY(-1px);
}
.stApp button[data-testid^="stBaseButton-primary"] p { color: #FFFFFF !important; }
.stApp button[data-testid^="stBaseButton-secondary"] {
    background: var(--surface) !important;
    border: 1px solid var(--line-strong) !important;
    color: var(--ink-800) !important;
}
.stApp button[data-testid^="stBaseButton-secondary"]:hover {
    background: var(--brand-50) !important; border-color: var(--brand-300) !important; color: var(--brand-700) !important;
}
.stApp button[data-testid^="stBaseButton"]:focus-visible { box-shadow: var(--ring) !important; outline: none !important; }
.stApp button[data-testid^="stBaseButton"]:disabled { opacity: .45; transform: none !important; }
.stApp button[data-testid="stBaseButton-tertiary"] { color: var(--ink-600) !important; transition: color .2s var(--ease); }
.stApp button[data-testid="stBaseButton-tertiary"]:hover { color: var(--brand-600) !important; }

/* =========================================================
   FORM CONTROLS
   ========================================================= */
[data-testid="stWidgetLabel"] p {
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    color: var(--ink-700) !important;
}
.stTextInput [data-testid="stTextInputRootElement"],
.stTextArea [data-testid="stTextAreaRootElement"],
.stNumberInput [data-testid="stNumberInputContainer"],
.stDateInput [data-baseweb="input"],
.stSelectbox [role="group"],
.stMultiSelect [data-baseweb="select"] > div {
    background: var(--surface) !important;
    border: 1px solid var(--line-strong) !important;
    border-radius: var(--r-md) !important;
    box-shadow: none;
    transition: border-color .2s var(--ease), box-shadow .2s var(--ease);
}
.stTextInput [data-testid="stTextInputRootElement"] { min-height: 42px; }
.stTextInput [data-baseweb="base-input"], .stNumberInput [data-baseweb="base-input"],
.stNumberInput [data-baseweb="input"], .stDateInput [data-baseweb="base-input"],
.stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input {
    background: transparent !important;
    color: var(--ink-900) !important;
    font-size: 0.98rem !important;
}
.stNumberInput [data-baseweb="input"] { border: none !important; }
.stNumberInput button { background: transparent !important; color: var(--ink-500) !important; transition: color .15s var(--ease), background-color .15s var(--ease); }
.stNumberInput button:hover { background: var(--brand-50) !important; color: var(--brand-700) !important; }
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: var(--ink-400) !important; }
.stTextInput [data-testid="stTextInputRootElement"]:focus-within,
.stTextArea [data-testid="stTextAreaRootElement"]:focus-within,
.stNumberInput [data-testid="stNumberInputContainer"]:focus-within,
.stDateInput [data-baseweb="input"]:focus-within,
.stSelectbox [role="group"]:focus-within {
    border-color: var(--brand-600) !important;
    box-shadow: var(--ring) !important;
}
.stSelectbox [role="group"] { min-height: 42px; font-size: 0.98rem; color: var(--ink-900); }
.stSelectbox [role="group"]:hover, .stTextInput [data-testid="stTextInputRootElement"]:hover,
.stNumberInput [data-testid="stNumberInputContainer"]:hover { border-color: var(--brand-300) !important; }
.stTextInput button { color: var(--ink-400) !important; }
.stTextInput button:hover { color: var(--ink-700) !important; }
[data-testid="InputInstructions"] { display: none !important; }
.stCheckbox label p { font-size: 0.95rem !important; }
[data-baseweb="tag"] { border-radius: 99px !important; background: var(--brand-600) !important; }
[data-baseweb="tag"] span { color: #FFFFFF !important; }

/* Field with an error — wrap it in st.container(key="err_<name>") */
[class*="st-key-err_"] .stTextInput [data-testid="stTextInputRootElement"],
[class*="st-key-err_"] .stSelectbox [role="group"] { border-color: var(--red-600) !important; }
[class*="st-key-err_"] .stTextInput [data-testid="stTextInputRootElement"]:focus-within { box-shadow: 0 0 0 3px rgba(192,38,45,.14) !important; }
[class*="st-key-err_"], [class*="st-key-ok_"] { gap: 6px !important; }
.stTextInput [data-testid="stTextInputIcon"], .stTextInput [data-testid="stTextInputRootElement"] > div:first-child span[data-testid="stIconMaterial"] { color: var(--ink-400) !important; }

/* Expanders */
[data-testid="stExpander"] details { border: 1px solid var(--line) !important; border-radius: var(--r-md) !important; background: var(--surface); }
[data-testid="stExpander"] summary { transition: background-color .2s var(--ease); border-radius: var(--r-md); }
[data-testid="stExpander"] summary p { font-weight: 700 !important; color: var(--ink-700) !important; font-size: 0.95rem !important; }
[data-testid="stExpander"] summary:hover { background: var(--subtle); }
[data-testid="stExpander"] summary:hover p { color: var(--brand-600) !important; }

/* =========================================================
   FEEDBACK
   ========================================================= */
.ds-alert {
    display: flex; gap: 10px; align-items: flex-start;
    padding: 10px 12px;
    border-radius: var(--r-md);
    border: 1px solid;
    font-size: 0.95rem; line-height: 1.45;
    animation: ds-fade .3s var(--ease) both;
}
.ds-alert i { margin-top: 3px; font-size: 0.85rem; }
.ds-alert-error   { background: var(--red-50);   border-color: var(--red-200);   color: var(--red-700); }
.ds-alert-success { background: var(--green-50); border-color: var(--green-200); color: var(--green-700); }
.ds-alert-info    { background: var(--brand-50); border-color: var(--brand-200); color: var(--brand-700); }
.ds-alert-warning { background: var(--amber-50); border-color: var(--amber-200); color: var(--amber-700); }

.ds-field-error { display: flex; gap: 6px; align-items: center; color: var(--red-600); font-size: 0.85rem; }
.ds-field-error i { font-size: 0.72rem; }

[data-testid="stAlert"] { border-radius: var(--r-md) !important; font-size: 0.9rem !important; }

/* =========================================================
   BRAND
   ========================================================= */
.ds-brand { display: flex; align-items: center; gap: 10px; }
.ds-brand-mark {
    width: 36px; height: 36px; flex-shrink: 0;
    display: inline-flex; align-items: center; justify-content: center;
    border-radius: 10px;
    background: linear-gradient(160deg, var(--brand-500), var(--brand-700)); color: #FFFFFF;
    font-size: 1rem;
    box-shadow: 0 4px 10px -4px rgba(0,63,43,.6);
}
.ds-brand-text { display: flex; flex-direction: column; line-height: 1.15; }
.ds-brand-name { font-size: 1.15rem; font-weight: 700; color: var(--ink-900); }
.ds-brand-sub  { font-size: 0.78rem; color: var(--ink-500); }

/* =========================================================
   SIDEBAR (dashboard) — width set by set_page_config(initial_sidebar_state=…)
   ========================================================= */
[data-testid="stSidebar"] {
    background:
        radial-gradient(420px 260px at -20% 100%, rgba(168,224,190,.16), rgba(168,224,190,0) 70%),
        var(--side-bg) !important;
    border-right: none !important;
}
/* Slim sidebar: Streamlit's smallest setting is 200px, so the open width is narrowed here */
[data-testid="stSidebar"][aria-expanded="true"] {
    width: 256px !important; min-width: 256px !important; max-width: 256px !important;
}
/* Nothing in the sidebar is cut off: long labels and names wrap onto a second line */
[data-testid="stSidebar"] [data-testid="stPageLink"] a *,
[data-testid="stSidebar"] .ds-brand-sub,
[data-testid="stSidebar"] .ds-user-name {
    white-space: normal !important; overflow: visible !important; text-overflow: clip !important;
}
[data-testid="stSidebar"] .ds-user-name { overflow-wrap: anywhere; }
[data-testid="stSidebarHeader"] { padding: 14px 12px 4px !important; min-height: 0 !important; height: auto !important; }
[data-testid="stSidebarContent"] { padding: 0 !important; background: transparent !important; }
[data-testid="stSidebarUserContent"] { padding: 0 12px 14px !important; }
[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] {
    min-height: calc(100vh - 64px); gap: 3px !important;
}
[data-testid="stLayoutWrapper"]:has(> .st-key-sb_user) { margin-top: auto; }
.st-key-sb_user {
    gap: 10px !important; padding: 12px !important;
    border: 1px solid var(--side-line); border-radius: var(--r-lg); background: rgba(255,255,255,.06);
}

/* Brand on the dark panel */
[data-testid="stSidebar"] .ds-brand-mark { background: rgba(255,255,255,.12); color: #FFFFFF; box-shadow: none; border: 1px solid var(--side-line); }
[data-testid="stSidebar"] .ds-brand-name { color: #FFFFFF; }
[data-testid="stSidebar"] .ds-brand-sub  { color: var(--side-muted); }

/* Collapse (inside the dark panel) and expand (on the light page) toggles */
[data-testid="stSidebarCollapseButton"] { display: flex !important; visibility: visible !important; opacity: 1 !important; }
[data-testid="stSidebarCollapseButton"] button {
    width: 30px !important; height: 30px !important; min-height: 30px !important; padding: 0 !important;
    border: 1px solid var(--side-line) !important; border-radius: var(--r-md) !important;
    background: transparent !important; color: var(--side-ink) !important;
    transition: background-color .2s var(--ease), color .2s var(--ease);
}
[data-testid="stSidebarCollapseButton"] button:hover { background: var(--side-hover) !important; color: var(--mint-300) !important; }
[data-testid="stExpandSidebarButton"] {
    width: 30px !important; height: 30px !important; min-height: 30px !important; padding: 0 !important;
    border: 1px solid var(--line) !important; border-radius: var(--r-md) !important;
    background: var(--surface) !important; color: var(--brand-600) !important; box-shadow: var(--shadow-xs) !important;
}
[data-testid="stExpandSidebarButton"]:hover { border-color: var(--brand-200) !important; background: var(--brand-50) !important; }

.ds-nav-label {
    margin: 22px 0 8px 10px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: .12em;
    text-transform: uppercase; color: var(--side-muted);
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
    padding: 9px 12px !important; min-height: 42px;
    border-radius: var(--r-md) !important; margin: 0 !important; gap: 10px;
    transition: background-color .2s var(--ease);
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a p,
[data-testid="stSidebar"] [data-testid="stPageLink"] a span {
    font-size: 0.92rem !important; color: var(--side-ink) !important;
    transition: color .2s var(--ease);
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover { background: rgba(255,255,255,.10) !important; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover :is(p, span) { color: #FFFFFF !important; }
/* Current page: pale green with dark text and an arrow on the right */
.stApp [class*="st-key-navon_"] a, .stApp [class*="st-key-navon_"] a:hover {
    background: #D9E9BD url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23234331' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m9 18 6-6-6-6'/%3E%3C/svg%3E") no-repeat right 8px center !important; padding-left: 10px !important; padding-right: 26px !important;
}
.stApp [class*="st-key-navon_"] a :is(p, span) { color: #234331 !important; font-weight: 600 !important; }
.stApp [class*="st-key-navon_"] a [data-testid="stIconMaterial"] { color: #234331 !important; }
/* Hovering the current page keeps the dark text readable on the pale green */
.stApp [data-testid="stSidebar"] [class*="st-key-navon_"] a:hover :is(p, span),
.stApp [data-testid="stSidebar"] [class*="st-key-navon_"] a:hover [data-testid="stIconMaterial"] { color: #234331 !important; }
.stApp [data-testid="stSidebar"] [class*="st-key-navon_"] a:hover { background-color: #CFE3AE !important; }

/* Count badge on a nav item (content set per render by render_sidebar) */
[class*="st-key-nav"] a::after {
    margin-left: auto; flex-shrink: 0; padding: 0 7px; border-radius: 99px;
    background: var(--red-600); color: #FFFFFF; font-size: 0.72rem; font-weight: 700; line-height: 1.6;
    font-family: var(--font);
}

.ds-user-card { display: flex; align-items: center; gap: 10px; }
.ds-avatar {
    width: 36px; height: 36px; flex-shrink: 0;
    display: inline-flex; align-items: center; justify-content: center;
    border-radius: 50%;
    background: var(--mint-300); color: var(--brand-700);
    font-size: 0.85rem; font-weight: 700;
}
.ds-user-meta { min-width: 0; line-height: 1.3; }
.ds-user-name { font-size: 0.95rem; font-weight: 700; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ds-user-role { font-size: 0.8rem; color: var(--side-muted); }
.stApp .st-key-sb_user button[data-testid^="stBaseButton"] {
    min-height: 36px !important;
    background: rgba(255,255,255,.08) !important; border: 1px solid var(--side-line) !important; box-shadow: none !important;
}
.stApp .st-key-sb_user button[data-testid^="stBaseButton"] :is(p, span) { color: var(--side-ink) !important; }
.stApp .st-key-sb_user button[data-testid^="stBaseButton"]:hover { background: rgba(255,255,255,.16) !important; border-color: rgba(255,255,255,.28) !important; }
.stApp .st-key-sb_user button[data-testid^="stBaseButton"]:hover :is(p, span) { color: #FFFFFF !important; }

/* =========================================================
   DASHBOARD LAYOUT
   ========================================================= */
.stMain [data-testid="stMainBlockContainer"] { padding: 26px 32px 40px !important; max-width: 1480px; }
/* Same 90% scale as the home page, so every page has the same density (desktop and tablet) */
.stMain [data-testid="stMainBlockContainer"], [data-testid="stSidebarContent"] { zoom: .9; }
/* Plotly works out hover positions without CSS zoom, so charts are scaled back to 100% */
.stMain [data-testid="stMainBlockContainer"] .stPlotlyChart { zoom: 1.1111; }
/* Streamlit fixes the chart box to the figure height; let it grow so the scaled-back chart is not cut off */
.stMain [data-testid="stMainBlockContainer"] [data-testid="stElementContainer"]:has(> div > .stPlotlyChart) {
    height: auto !important; flex: 0 0 auto !important; overflow: visible !important;
}
.stMain [data-testid="stMainBlockContainer"] div:has(> .stPlotlyChart),
.stMain [data-testid="stMainBlockContainer"] .stPlotlyChart { height: auto !important; }
.stMain [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { gap: 20px; }

/* Zero-height helper iframes (chart export) must not take space */
[data-testid="stElementContainer"]:has(iframe[height="0"]) { position: absolute !important; width: 0; height: 0; overflow: hidden; }

/* Page header with a resort photo fading in from the right */
.ds-page-head {
    position: relative; display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; flex-wrap: wrap;
    min-height: 104px; padding: 4px 0 6px;
}
.ds-page-head > div { position: relative; z-index: 1; max-width: 62%; }
.ds-page-head::after {
    content: ""; position: absolute; z-index: 0; top: -26px; right: -32px; bottom: -8px; width: 52%;
    background: var(--hero-img) center 60% / cover no-repeat;
    -webkit-mask-image: linear-gradient(90deg, transparent 0%, rgba(0,0,0,.55) 28%, #000 60%);
            mask-image: linear-gradient(90deg, transparent 0%, rgba(0,0,0,.55) 28%, #000 60%);
    border-bottom-left-radius: 48px;
    animation: ds-fade .9s var(--ease) both;
}
.ds-page-title { margin: 0 !important; padding: 0 !important; font-size: 2.15rem !important; font-weight: 600 !important; letter-spacing: -0.03em !important; line-height: 1.15 !important; color: var(--brand-700) !important; }
.ds-page-sub { margin: 6px 0 0; font-size: 1.05rem; color: var(--ink-600); }
.ds-eyebrow { margin: 0 0 6px; font-size: 0.92rem; color: var(--ink-600); }
.ds-eyebrow b { color: var(--brand-600); font-weight: 700; }
.ds-eyebrow i { font-style: normal; color: var(--ink-400); padding: 0 6px; }
.ds-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.ds-chip {
    display: inline-flex; align-items: center; gap: 6px; height: 30px; padding: 0 12px;
    border: 1px solid var(--line); border-radius: 99px; background: var(--surface);
    font-size: 0.85rem; color: var(--ink-600); white-space: nowrap;
}
.ds-chip i { font-size: 0.75rem; }
.ds-chip-model   { background: var(--brand-50); border-color: var(--brand-200); color: var(--brand-700); font-weight: 700; }
.ds-chip-model i { color: var(--brand-600); }
.ds-chip-role-rm { background: var(--sky-50);  border-color: var(--sky-200);  color: var(--sky-700);  font-weight: 700; }
.ds-chip-role-mt { background: var(--sage-50); border-color: var(--sage-200); color: var(--sage-700); font-weight: 700; }

/* KPI cards: round icon on the left, figures on the right */
.ds-kpi-grid { display: grid; grid-template-columns: repeat(var(--cols, 4), minmax(0, 1fr)); gap: 16px; }
.ds-kpi {
    position: relative; display: flex; align-items: flex-start; gap: 14px;
    background: var(--surface); border: 1px solid var(--line); border-radius: 12px;
    padding: 20px; box-shadow: var(--card-shadow);
    transition: opacity .25s var(--ease), border-color .2s var(--ease);
}
.ds-kpi:hover { border-color: var(--card-hover-line); }
.ds-kpi-ico {
    width: 48px; height: 48px; flex-shrink: 0; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 1.1rem; color: var(--brand-600); background: var(--brand-50);
}
.ds-kpi-body { min-width: 0; flex: 1; }
.ds-kpi-label { font-size: 0.98rem; font-weight: 700; color: var(--ink-800); }
.ds-kpi-value { margin-top: 4px; font-size: 2.05rem; font-weight: 700; line-height: 1.1; color: var(--ink-900); font-variant-numeric: tabular-nums lining-nums; }
.ds-kpi-caption { margin-top: 6px; font-size: 0.88rem; color: var(--ink-500); }
.ds-kpi-trend { margin-top: 6px; font-size: 0.85rem; font-weight: 700; display: flex; align-items: center; gap: 5px; color: var(--ink-600); }
.ds-kpi-trend i { font-size: 0.7rem; }

.ds-kpi-orange { --tone: var(--orange-600); --tone-ink: var(--orange-700); --tone-soft: var(--orange-50); --tone-line: var(--orange-200); }
.ds-kpi-brand  { --tone: var(--brand-600);  --tone-ink: var(--brand-700);  --tone-soft: var(--brand-50);  --tone-line: var(--brand-200); }
.ds-kpi-plat   { --tone: var(--plat-600);   --tone-ink: var(--plat-700);   --tone-soft: var(--plat-50);   --tone-line: var(--plat-200); }
.ds-kpi-sage   { --tone: var(--sage-600);   --tone-ink: var(--sage-700);   --tone-soft: var(--sage-50);   --tone-line: var(--sage-200); }
.ds-kpi-sky    { --tone: var(--sky-600);    --tone-ink: var(--sky-700);    --tone-soft: var(--sky-50);    --tone-line: var(--sky-200); }
.ds-kpi-navy   { --tone: var(--navy-700);   --tone-ink: var(--navy-700);   --tone-soft: var(--navy-50);   --tone-line: var(--navy-200); }
.ds-kpi-green  { --tone: var(--green-600);  --tone-ink: var(--green-700);  --tone-soft: var(--green-50);  --tone-line: var(--green-200); }
.ds-kpi-amber  { --tone: var(--amber-600);  --tone-ink: var(--amber-700);  --tone-soft: var(--amber-50);  --tone-line: var(--amber-200); }
.ds-kpi-red    { --tone: var(--red-600);    --tone-ink: var(--red-700);    --tone-soft: var(--red-50);    --tone-line: var(--red-200); }
.ds-kpi:not(.ds-kpi-neutral) .ds-kpi-ico { color: var(--tone); background: var(--tone-soft); }
.ds-kpi-red .ds-kpi-value { color: var(--red-600); }
.ds-kpi-filled { background: linear-gradient(160deg, var(--tone-soft), var(--surface) 75%); border-color: var(--tone-line); }
.ds-kpi-filled .ds-kpi-value { color: var(--tone-ink); }
.ds-kpi-filled .ds-kpi-ico { background: var(--surface); }
.ds-dim { opacity: .4; }

/* Impact summary bar (Action Board) */
.ds-impact {
    display: flex; flex-wrap: wrap; align-items: center; gap: 10px 0;
    padding: 10px 14px; border-radius: 12px;
    background: var(--surface); border: 1px solid var(--line); box-shadow: var(--card-shadow);
    color: var(--ink-700); font-size: 0.98rem;
}
.ds-impact-k {
    display: inline-flex; align-items: center; gap: 8px; height: 34px; padding: 0 14px; margin-right: 8px; border-radius: var(--r-md);
    background: var(--brand-50); color: var(--brand-700); font-weight: 700;
}
.ds-impact-k i { color: var(--brand-600); }
.ds-impact-i { display: inline-flex; align-items: center; gap: 8px; white-space: nowrap; padding: 0 20px; border-left: 1px solid var(--line); }
.ds-impact-i b { color: var(--ink-900); font-weight: 700; font-variant-numeric: tabular-nums; }
.ds-impact-i i { color: var(--brand-600); font-size: 0.9rem; }

/* Cards */
[class*="st-key-card_"] {
    background: var(--surface); border: 1px solid var(--line); border-radius: 12px;
    padding: 22px 24px !important; box-shadow: var(--card-shadow); gap: 14px !important;
    transition: border-color .2s var(--ease);
}
[class*="st-key-card_"]:hover { border-color: var(--card-hover-line); }
.ds-card-head { min-width: 0; }
.ds-card-title { margin: 0 !important; padding: 0 !important; display: flex; align-items: center; gap: 10px;
    font-size: 1.2rem !important; font-weight: 600 !important; letter-spacing: -0.01em !important; color: var(--ink-900) !important; }
.ds-card-ico { color: var(--brand-600); font-size: 1rem; }
.ds-card-sub { margin: 4px 0 0; font-size: 0.95rem; color: var(--ink-500); }
.ds-note { margin: 0; display: flex; align-items: center; gap: 6px; font-size: 0.88rem; color: var(--ink-500); }
.ds-note i { color: var(--brand-600); }
.ds-legend { display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 0.92rem; color: var(--ink-600); }
.ds-legend span { display: inline-flex; align-items: center; gap: 6px; }
.ds-legend i { font-size: 0.55rem; }

/* Popover trigger (Export) */
[data-testid="stPopover"] button { min-height: 36px !important; padding: 0 14px !important; }
[data-testid="stPopoverBody"] { padding: 6px !important; min-width: 190px; border-radius: var(--r-md) !important; }
[data-testid="stPopoverBody"] button { justify-content: flex-start !important; box-shadow: none !important; border-color: transparent !important; }
[data-testid="stPopoverBody"] button:hover { background: var(--brand-50) !important; }

/* Hide Plotly's toolbar; exports are driven from our Export menu */
.stPlotlyChart .modebar-container { display: none !important; }
[data-testid="stElementToolbar"] { display: none !important; }
.stPlotlyChart { animation: ds-fade .7s var(--ease) both; }

/* Filters: select with an inline "Label:" prefix */
[class*="st-key-flt_"] [role="group"]::before {
    padding-left: 12px; margin-right: 4px; white-space: nowrap;
    font-size: 0.92rem; color: var(--ink-500);
}
[class*="st-key-flt_"] [role="group"] { display: flex; align-items: center; }
[class*="st-key-flt_"] [role="group"] input { font-weight: 700 !important; color: var(--ink-900) !important; }
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-srch_"]) { flex: 1 1 220px; min-width: 200px; }
[class*="st-key-bar_"] { gap: 10px !important; }

/* Tables — tinted header band, hairline rows */
[class*="st-key-tbl_"] { gap: 0 !important; }
[class*="st-key-tblhead_"] {
    padding: 11px 14px; background: var(--brand-50);
    border: 1px solid var(--brand-100); border-radius: var(--r-md) var(--r-md) 0 0;
}
[class*="st-key-tblrow_"] {
    padding: 4px 14px; min-height: 54px; justify-content: center; border-bottom: 1px solid var(--line);
    transition: background-color .2s var(--ease);
    animation: ds-fade .4s var(--ease) both;
}
[class*="st-key-tblrow_"]:hover { background: var(--subtle); }
.ds-th { display: block; font-size: 0.78rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--brand-700); }
.ds-td { display: block; font-size: 0.98rem; color: var(--ink-800); font-variant-numeric: tabular-nums lining-nums; }
.ds-right { text-align: right; }
.ds-strong { font-weight: 700; color: var(--ink-900); }
[class*="st-key-lnk_"] button { min-height: 0 !important; padding: 0 !important; }
[class*="st-key-lnk_"] button p { color: var(--ink-900) !important; font-size: 0.98rem !important; transition: color .2s var(--ease); }
[class*="st-key-lnk_"] button:hover p { color: var(--brand-600) !important; text-decoration: underline; text-underline-offset: 3px; }
.stApp [class*="st-key-view_"] button[data-testid^="stBaseButton"] {
    min-height: 32px !important; padding: 0 14px !important; border-radius: 6px !important;
    background: var(--surface) !important; border: 1px solid var(--line-strong) !important; box-shadow: none !important;
}
.stApp [class*="st-key-view_"] button[data-testid^="stBaseButton"] p { font-size: 0.88rem !important; color: var(--ink-500) !important; }
.stApp [class*="st-key-view_"] button[data-testid^="stBaseButton"]:hover {
    background: var(--brand-600) !important; border-color: var(--brand-600) !important;
    box-shadow: 0 6px 14px -8px rgba(0,63,43,.7) !important; transform: translateY(-1px);
}
.stApp [class*="st-key-view_"] button[data-testid^="stBaseButton"]:hover p { color: #FFFFFF !important; }
/* Guest tables (At-Risk Guest List, Guest Action List): quiet header band across the card,
   lighter text and soft square tags */
:is(.st-key-card_ar_list, .st-key-card_actions) [class*="st-key-tbl_"] {
    width: calc(100% + 48px) !important; max-width: none !important; flex: 0 0 auto !important; margin: 0 -24px;
}
:is(.st-key-card_ar_list, .st-key-card_actions) [class*="st-key-tblhead_"] {
    background: #F7F9F6; border: none; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line);
    border-radius: 0; padding: 12px 24px;
}
:is(.st-key-card_ar_list, .st-key-card_actions) .ds-th { font-size: 0.72rem; font-weight: 600; letter-spacing: .06em; color: #7A857C; }
:is(.st-key-card_ar_list, .st-key-card_actions) [class*="st-key-tblrow_"] { padding: 4px 24px; min-height: 52px; border-bottom: 1px solid #EEF1EB; }
:is(.st-key-card_ar_list, .st-key-card_actions) [class*="st-key-tblrow_"]:hover { background: #F7FAF3; }
:is(.st-key-card_ar_list, .st-key-card_actions) [class*="st-key-lnk_"] button p { font-weight: 600 !important; font-size: 0.92rem !important; }
:is(.st-key-card_ar_list, .st-key-card_actions) .ds-td { font-size: 0.92rem; color: #3C5144; }
.stApp :is(.st-key-pager_ar, .st-key-pager_ab) button[data-testid="stBaseButton-primary"] { background: #1F3A2F !important; border-color: #1F3A2F !important; }
.gt-num { font-weight: 500; color: var(--ink-900); }
.gt-days { display: inline-flex; align-items: center; gap: 8px; color: #3C5144; }
.gt-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.gt-dot-red { background: #E26A6A; } .gt-dot-amber { background: #D9A441; } .gt-dot-green { background: #3BAA74; }
.gt-muted { color: #627D98; }
.gt-tag {
    display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 4px; border: 1px solid transparent;
    font-size: 0.78rem; font-weight: 500; line-height: 1.6; white-space: nowrap;
}
.gt-tag-red    { background: #FDF0F0; color: #C24141; border-color: #F6DADA; }
.gt-tag-amber  { background: #FEF7E8; color: #94641A; border-color: #F3E2BC; }
.gt-tag-green  { background: #EDF7F0; color: #2F7A4C; border-color: #D2EADB; }
.gt-tag-action { background: #FFF9F0; color: #8A5A1E; border-color: #F1DDBD; }
.ds-empty { padding: 32px 0; text-align: center; font-size: 0.92rem; color: var(--ink-500); }

/* Static summary tables */
.ds-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 0.98rem; color: var(--ink-800); }
.ds-table th {
    padding: 11px 12px; text-align: left; background: var(--brand-50);
    border-top: 1px solid var(--brand-100); border-bottom: 1px solid var(--brand-100);
    font-size: 0.78rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--brand-700);
}
.ds-table th:first-child { border-left: 1px solid var(--brand-100); border-top-left-radius: var(--r-md); }
.ds-table th:last-child { border-right: 1px solid var(--brand-100); border-top-right-radius: var(--r-md); }
.ds-table td { padding: 12px; border-bottom: 1px solid var(--line); font-variant-numeric: tabular-nums lining-nums; }
.ds-table tbody tr { transition: background-color .2s var(--ease); }
.ds-table tbody tr:hover { background: var(--subtle) !important; }
.ds-table .muted { color: var(--ink-500); }

/* Pills (rounded, no outline) & coloured text */
.ds-pill {
    display: inline-flex; align-items: center; padding: 2px 9px; border-radius: 4px; border: 1px solid transparent;
    font-size: 0.82rem; font-weight: 700; white-space: nowrap; line-height: 1.5;
}
.ds-pill-plat    { background: var(--plat-600);  color: #FFFFFF; }
.ds-pill-orange  { background: var(--orange-50); color: var(--orange-700); border-color: var(--orange-200); }
.ds-pill-brand   { background: var(--brand-50);  color: var(--brand-700); border-color: var(--brand-200); }
.ds-pill-sage    { background: var(--sage-50);   color: var(--sage-700);  border-color: var(--sage-200); }
.ds-pill-sky     { background: var(--sky-50);    color: var(--sky-700);   border-color: var(--sky-200); }
.ds-pill-navy    { background: var(--navy-50);   color: var(--navy-700);  border-color: var(--navy-200); }
.ds-pill-green   { background: var(--green-50);  color: var(--green-700); border-color: var(--green-200); }
.ds-pill-amber   { background: var(--amber-50);  color: var(--amber-700); border-color: var(--amber-200); }
.ds-pill-red     { background: var(--red-50);    color: var(--red-700);   border-color: var(--red-200); }
.ds-pill-neutral { background: var(--subtle);    color: var(--ink-600);   border-color: var(--line); }
.ds-text-orange { color: var(--orange-700); font-weight: 700; }
.ds-text-brand  { color: var(--brand-600);  font-weight: 700; }
.ds-text-plat   { color: var(--plat-600);   font-weight: 700; }
.ds-text-sage   { color: var(--sage-700);   font-weight: 700; }
.ds-text-sky    { color: var(--sky-700);    font-weight: 700; }
.ds-text-navy   { color: var(--navy-700);   font-weight: 700; }
.ds-text-green  { color: var(--green-700);  font-weight: 700; }
.ds-text-amber  { color: var(--amber-700);  font-weight: 700; }
.ds-text-red    { color: var(--red-600);    font-weight: 700; }
.ds-text-neutral{ color: var(--ink-700);    font-weight: 700; }

/* Segmented control (e.g. Sort by): white thumb on a soft track */
[data-testid="stButtonGroup"] { background: var(--brand-50); padding: 3px; border-radius: var(--r-md); width: fit-content; }
button[data-variant="segmented_control"] {
    min-height: 32px !important; border: none !important; background: transparent !important; border-radius: 6px !important;
    font-size: 0.92rem !important; color: var(--ink-600) !important;
    transition: background-color .2s var(--ease), color .2s var(--ease), box-shadow .2s var(--ease);
}
button[data-variant="segmented_control"]:hover { color: var(--brand-700) !important; }
button[data-variant="segmented_control"][data-selected="true"] {
    background: var(--surface) !important; color: var(--brand-700) !important; font-weight: 700 !important;
    box-shadow: 0 1px 3px rgba(12,43,33,.16) !important;
}

/* Pagination */
[class*="st-key-pager_"] { padding-top: 14px; gap: 6px !important; }
[class*="st-key-pager_"] button { min-height: 34px !important; min-width: 34px; padding: 0 8px !important; box-shadow: none !important; }
[class*="st-key-pager_"] button p { font-size: 0.9rem !important; }
.ds-pager-info { font-size: 0.92rem; color: var(--ink-500); white-space: nowrap; }
.ds-pager-gap { color: var(--ink-400); padding: 0 2px; }
/* In horizontal rows, HTML blocks size to content so st.space("stretch") can push items apart */
[data-testid="stHorizontalBlock"] > [data-testid="stElementContainer"]:has(> [data-testid="stHtml"]) { flex: 0 1 auto; width: auto !important; }

/* Motion: sections rise in once when a page mounts (reruns reuse the DOM, so this
   does not replay on every interaction). */
@keyframes ds-rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
@keyframes ds-fade { from { opacity: 0; } to { opacity: 1; } }
.stMain [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > * { animation: ds-rise .5s var(--ease) both; }
.stMain [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > :nth-child(2) { animation-delay: .05s; }
.stMain [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > :nth-child(3) { animation-delay: .10s; }
.stMain [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > :nth-child(4) { animation-delay: .15s; }
.stMain [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > :nth-child(n+5) { animation-delay: .2s; }
.ds-kpi-grid > .ds-kpi { animation: ds-rise .5s var(--ease) both; }
.ds-kpi-grid > .ds-kpi:nth-child(2) { animation-delay: .06s; }
.ds-kpi-grid > .ds-kpi:nth-child(3) { animation-delay: .12s; }
.ds-kpi-grid > .ds-kpi:nth-child(4) { animation-delay: .18s; }
html { scroll-behavior: smooth; }
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
}

@media (max-width: 1100px) {
    .ds-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .ds-page-head::after { width: 40%; }
}
@media (max-width: 760px) {
    .ds-page-head::after { display: none; }
    .ds-page-head > div { max-width: none; }
    .ds-impact-i { border-left: none; padding: 0 12px 0 0; }
}
@media (max-width: 640px) {
    :is(.st-key-card_ar_list, .st-key-card_actions) [class*="st-key-tbl_"] { width: calc(100% + 32px) !important; margin: 0 -16px; }
    :is(.st-key-card_ar_list, .st-key-card_actions) :is([class*="st-key-tblhead_"], [class*="st-key-tblrow_"]) { padding-left: 16px; padding-right: 16px; }
    .stMain [data-testid="stMainBlockContainer"], [data-testid="stSidebarContent"] { zoom: 1; }
    .stMain [data-testid="stMainBlockContainer"] .stPlotlyChart { zoom: 1; }
    .stMain [data-testid="stMainBlockContainer"] { padding: 16px !important; }
    .stMain [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { gap: 14px; }
    .ds-page-title { font-size: 1.5rem !important; }
    .ds-page-sub { font-size: 0.95rem; }
    .ds-page-head { min-height: 0; }

    /* Cards: less padding */
    [class*="st-key-card_"] { padding: 16px !important; }
    .ds-card-title { font-size: 1.12rem !important; }
    .ds-impact { padding: 10px 12px; gap: 8px 0; }
    .ds-impact-k { width: 100%; justify-content: center; margin-right: 0; }

    /* Tables keep one row per guest and scroll sideways instead of stacking cells */
    [class*="st-key-tbl_"] { overflow-x: auto; -webkit-overflow-scrolling: touch; padding-bottom: 4px; }
    [class*="st-key-tblhead_"], [class*="st-key-tblrow_"] { min-width: 640px; }
    [class*="st-key-tbl_"] [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
    [class*="st-key-tbl_"] [data-testid="stColumn"] { min-width: 0 !important; }
    .ds-table { display: block; overflow-x: auto; white-space: nowrap; }

    /* Filters and search use the full width */
    [class*="st-key-bar_"] { flex-direction: column; align-items: stretch !important; }
    [class*="st-key-flt_"], [class*="st-key-flt_"] .stSelectbox,
    [class*="st-key-flt_"] [data-testid="stElementContainer"],
    [data-testid="stLayoutWrapper"]:has(> [class*="st-key-flt_"]),
    [data-testid="stLayoutWrapper"]:has(> [class*="st-key-srch_"]) { width: 100% !important; max-width: 100% !important; flex: 1 1 auto; }
    [class*="st-key-bar_"] [data-testid="stDownloadButton"], [class*="st-key-bar_"] [data-testid="stDownloadButton"] button { width: 100% !important; }

    /* Pagination wraps onto a second line when needed */
    [class*="st-key-pager_"] { flex-wrap: wrap; row-gap: 8px; }
    [class*="st-key-pager_"] > [data-testid="stElementContainer"]:first-child { width: 100% !important; flex: 1 1 100% !important; }

    /* KPI cards two per row, figures scaled to fit */
    .ds-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .ds-kpi { flex-direction: column; gap: 8px; padding: 12px; }
    .ds-kpi-ico { width: 34px; height: 34px; font-size: 0.85rem; }
    .ds-kpi-label { font-size: 0.88rem; }
    .ds-kpi-value { font-size: 1.3rem; margin-top: 2px; }
    .ds-kpi-caption { font-size: 0.8rem; }

    /* Stacked rows (e.g. the Administration lists) read as separate cards */
    [class*="st-key-card_adm_"] [data-testid="stHorizontalBlock"] {
        padding-bottom: 12px; margin-bottom: 4px; border-bottom: 1px solid var(--line);
    }
    button[data-variant="segmented_control"] { font-size: 0.85rem !important; }
}
</style>
"""


def inject_global_css() -> None:
    """Call once in app.py after set_page_config to apply the design system."""
    st.markdown(_CSS + f"<style>:root {{ --hero-img: url('{PHOTO_RESORT}'); }}</style>",
                unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Public (signed-out) page chrome: landing, login, signup
# ---------------------------------------------------------------------------

_PUBLIC_CSS = """
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"], [data-testid="stHeader"] { display: none !important; }
[data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: none !important; zoom: 1 !important; }
[data-testid="stMain"] { padding: 0 !important; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { gap: 0 !important; }
</style>
"""

_AUTH_CSS = """
<style>
[data-testid="stMain"] { background: transparent !important; }
[data-testid="stAppViewContainer"] { background: #FAFBF9 !important; }
[data-testid="stMainBlockContainer"] { padding: 0 40px 40px !important; margin-left: 50vw !important; }

/* Left photo panel (wide screens): resort at sunset under a deep-green wash, with the
   product promise and four feature points. */
[data-testid="stElementContainer"]:has(.auth-panel) {
    position: fixed !important; top: 0; left: 0; bottom: 0; width: 50vw !important; z-index: 5;
    overflow: visible !important; animation: none !important; transform: none !important;
}
[data-testid="stElementContainer"]:has(.auth-panel) > [data-testid="stHtml"] { height: 100%; }
.auth-panel {
    position: absolute; inset: 0;
    display: flex; flex-direction: column; justify-content: space-between;
    padding: 48px 56px 36px; color: #FFFFFF; overflow: hidden;
    background:
        linear-gradient(180deg, rgba(0,46,32,.72) 0%, rgba(0,46,32,.38) 34%, rgba(0,46,32,.18) 50%, rgba(0,63,43,.82) 72%, #003F2B 100%),
        var(--auth-img) center / cover no-repeat, #0C5D49;
    animation: auth-zoom 1.4s var(--ease) both;
}
@keyframes auth-zoom { from { background-size: auto, 112%, auto; opacity: .4; } to { opacity: 1; } }
.auth-panel .ds-brand-mark { width: 42px; height: 42px; font-size: 1.15rem; background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.25); box-shadow: none; backdrop-filter: blur(6px); }
.auth-panel .ds-brand-name { font-size: 1.45rem; color: #FFFFFF; text-shadow: 0 2px 12px rgba(0,0,0,.25); }
.auth-panel .ds-brand-sub { font-size: 0.88rem; color: rgba(255,255,255,.88); }
.auth-panel-title {
    margin-top: 30px; font-size: clamp(1.9rem, 2.4vw, 2.5rem); line-height: 1.08; font-weight: 700;
    color: #FFFFFF; text-shadow: 0 2px 18px rgba(0,0,0,.28);
}
.auth-panel-title span { color: var(--mint-300); display: block; }
.auth-panel-desc { margin-top: 14px; max-width: 440px; font-size: 0.98rem; line-height: 1.55; color: rgba(255,255,255,.92); text-shadow: 0 1px 8px rgba(0,0,0,.3); }
.auth-feats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; }
.auth-feat { animation: ds-rise .6s var(--ease) both; }
.auth-feat:nth-child(2) { animation-delay: .1s; } .auth-feat:nth-child(3) { animation-delay: .2s; } .auth-feat:nth-child(4) { animation-delay: .3s; }
.auth-feat-ico {
    width: 42px; height: 42px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
    background: rgba(12,93,73,.85); border: 1px solid rgba(168,224,190,.35); color: #FFFFFF; font-size: 0.95rem;
    transition: transform .3s var(--ease), background-color .3s var(--ease);
}
.auth-feat:hover .auth-feat-ico { transform: translateY(-3px); background: var(--brand-500); }
.auth-feat-t { margin-top: 10px; font-size: 0.98rem; font-weight: 700; }
.auth-feat-d { margin-top: 4px; font-size: 0.82rem; line-height: 1.4; color: rgba(255,255,255,.8); }
.auth-loc { display: flex; gap: 14px; align-items: center; margin-top: 26px; padding-top: 18px; border-top: 1px solid rgba(255,255,255,.18); font-size: 0.85rem; color: rgba(255,255,255,.85); }
.auth-loc i { color: var(--mint-300); }
.auth-loc b { width: 1px; height: 16px; background: rgba(255,255,255,.3); }

/* Top bar (brand shown on the photo, so only the back link remains here) */
.st-key-auth_topbar { max-width: 400px; margin: 0 auto; padding: 24px 0 0 !important; }
.st-key-auth_topbar .ds-brand { visibility: hidden; }

/* Form: sits directly on the right-hand panel (no card around it) */
[class*="st-key-auth_card"] {
    width: 100% !important; max-width: min(400px, 100%) !important; margin: 6vh auto 0;
    background: transparent;
    padding: 0 !important;
    gap: 1rem !important;
    animation: ds-rise .6s var(--ease) both;
}
.st-key-auth_card_wide { margin-top: 1vh; }
[class*="st-key-auth_card"] [data-testid="stForm"] { border: none !important; padding: 0 !important; }
[class*="st-key-auth_card"] [data-testid="stForm"] [data-testid="stVerticalBlock"] { gap: 1rem; }

.auth-head { text-align: left; margin-bottom: 1rem; }
.auth-head .auth-mark { display: none; }
.auth-eyebrow { margin-bottom: 8px; font-size: 0.85rem; letter-spacing: .16em; text-transform: uppercase; color: var(--ink-500); }
.auth-sub.auth-sub-muted { margin-top: 4px; font-size: 0.95rem; color: var(--ink-500); }
.auth-title { font-size: 2rem; font-weight: 700; color: var(--brand-700); line-height: 1.15; }
.auth-sub   { margin-top: 8px; font-size: 1.08rem; color: var(--ink-600); line-height: 1.5; }

.auth-switch {
    display: flex; align-items: center; gap: 12px;
    color: var(--ink-500); font-size: 0.9rem;
    margin-top: 0.35rem;
}
.auth-switch::before, .auth-switch::after { content: ""; flex: 1; height: 1px; background: var(--line-strong); }

.auth-foot {
    max-width: 400px; margin: 18px auto 0;
    display: flex; justify-content: center; align-items: center; gap: 8px;
    color: var(--ink-500); font-size: 0.88rem; text-align: center;
}
.auth-foot i { color: var(--ink-400); }

/* Password checklist */
.pw-rules {
    display: grid; grid-template-columns: 1fr 1fr; gap: 4px 12px;
    margin-bottom: 2px;
    font-size: 0.88rem; color: var(--ink-500);
}
.pw-rules span { display: flex; align-items: center; gap: 6px; transition: color .2s var(--ease); }
.pw-rules i { font-size: 0.72rem; color: var(--line-strong); width: 12px; transition: color .2s var(--ease); }
.pw-rules .ok   { color: var(--green-700); }
.pw-rules .ok i { color: var(--green-600); }
.pw-rules .bad   { color: var(--red-600); }
.pw-rules .bad i { color: var(--red-600); }

.field-hint { margin-top: -0.35rem; font-size: 0.8rem; color: var(--ink-500); }

@media (max-width: 1100px) {
    .auth-feats { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 960px) {
    .auth-panel { display: none; }
    [data-testid="stMainBlockContainer"] { margin-left: 0 !important; padding: 0 20px 32px !important; }
    .st-key-auth_topbar .ds-brand { visibility: visible; }
}
@media (max-width: 560px) {
    [class*="st-key-auth_card"] { margin-top: 18px; }
    .st-key-auth_topbar { padding: 14px 0 0 !important; }
    .auth-title { font-size: 1.75rem; }
    .auth-sub { font-size: 0.98rem; }
    .pw-rules { grid-template-columns: 1fr; }
}
</style>
"""


def _auth_panel() -> str:
    feats = [
        ("chart-column", "Predict CLV", "Identify high-value guests and future revenue potential."),
        ("users", "Segment Guests", "Understand behaviour and tailor your strategies."),
        ("bullseye", "Take Action", "Act on recommendations for better revenue management."),
        ("arrow-trend-up", "Drive Growth", "Build lasting guest relationships."),
    ]
    items = "".join(
        f'<div class="auth-feat"><span class="auth-feat-ico">{icon(ic)}</span>'
        f'<div class="auth-feat-t">{t}</div><div class="auth-feat-d">{d}</div></div>'
        for ic, t, d in feats
    )
    return f"""
    <aside class="auth-panel" style="--auth-img: url('{PHOTO_AUTH}')">
        <div>
            {brand_lockup()}
            <div class="auth-panel-title">Smarter Decisions.<span>Higher Revenue.</span></div>
            <p class="auth-panel-desc">Turn guest booking data into actionable insights with Customer
                Lifetime Value prediction for hotels.</p>
        </div>
        <div>
            <div class="auth-feats">{items}</div>
            <div class="auth-loc">{icon("location-dot")} Nairobi County, Kenya <b></b> Grand Regency Hotel</div>
        </div>
    </aside>"""


def public_page_chrome() -> None:
    """Hide the sidebar/header and let the page own the full viewport."""
    st.markdown(_PUBLIC_CSS, unsafe_allow_html=True)


def auth_page_chrome() -> None:
    """Public chrome + the shared login/signup split layout (photo panel left, form right)."""
    public_page_chrome()
    st.markdown(_AUTH_CSS, unsafe_allow_html=True)
    st.html(_auth_panel())


def hide_sidebar() -> None:
    """Backwards-compatible alias used by older views."""
    public_page_chrome()
