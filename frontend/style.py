"""
style.py — Design system for the Hotel CLV Decision Support System.

One set of tokens (colour, type, radius, shadow) drives the landing page,
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
# Global stylesheet
# ---------------------------------------------------------------------------

_CSS = """
<link rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"
      integrity="sha512-DTOQO9RWCH3ppGqcWaEA1BIZOC6xxalwEsw9c2QQeAIftl+Vegovlnee1c9QX4TctnWMn13TZye+giMm8e2LwA=="
      crossorigin="anonymous" referrerpolicy="no-referrer" />

<style>
/* =========================================================
   TOKENS
   ========================================================= */
:root {
    /* Typography — Times New Roman throughout */
    --font: 'Times New Roman', Times, 'Liberation Serif', 'Nimbus Roman', serif;

    /* Brand: deep teal (primary actions, active states, main data) */
    --brand-700: #0A2C2D;
    --brand-600: #0F3D3E;
    --brand-500: #2A6A69;
    --brand-200: #BBD5CF;
    --brand-100: #D9E9E4;
    --brand-50:  #EDF5F1;
    --lime-400:  #B8F28A;            /* highlight on dark surfaces */
    --navy-900:  #14213D;            /* headings, key numbers, trend lines */

    /* Neutrals (slightly cool, tuned to the teal) */
    --ink-900: #0B0B0C;              /* headings, numbers, body text */
    --ink-700: #161617;              /* labels */
    --ink-600: #1F1F21;              /* secondary text */
    --ink-500: #333336;              /* captions, subtitles */
    --ink-400: #6B6B70;              /* placeholders, empty markers only */

    --line:        #E3E8E5;
    --line-strong: #CCD5D1;
    --canvas:      #F3F5F2;
    --subtle:      #F7F9F7;
    --surface:     #FFFFFF;

    /* CLV tiers: High = teal (brand), Medium = sage, Low = soft blue, Platinum = navy */
    --sage-700: #3F7424; --sage-600: #5E9D3B; --sage-500: #8BCF65; --sage-200: #D2EAC1; --sage-50: #F2F9EC;
    --sky-700:  #2B5F91; --sky-600:  #4A86C2; --sky-500:  #6FA8DC; --sky-200:  #CBDFF1; --sky-50:  #EFF5FB;
    --navy-700: #14213D; --navy-200: #C8CFDE; --navy-50: #EEF1F7;

    /* Status (muted to sit with the palette) */
    --green-700: #3F7424; --green-600: #5E9D3B; --green-50: #F2F9EC; --green-200: #D2EAC1;
    --amber-700: #865B14; --amber-600: #B9862F; --amber-50: #FBF5E8; --amber-200: #EEDCB3;
    --red-700:   #93352A; --red-600:   #B5483B; --red-50:   #FBEFEC; --red-200:   #EECAC3;

    /* Sidebar */
    --side-bg:     #0F3D3E;
    --side-ink:    rgba(255,255,255,.74);
    --side-muted:  rgba(255,255,255,.48);
    --side-line:   rgba(255,255,255,.10);
    --side-hover:  rgba(255,255,255,.06);
    --side-active: rgba(184,242,138,.14);

    --r-sm: 6px;
    --r-md: 8px;
    --r-lg: 14px;
    --r-xl: 18px;

    --shadow-xs:   0 1px 2px rgba(20,33,61,.04);
    --shadow-card: 0 1px 2px rgba(20,33,61,.04), 0 6px 18px -10px rgba(20,33,61,.12);
    --shadow-pop:  0 1px 3px rgba(20,33,61,.06), 0 18px 44px -18px rgba(20,33,61,.24);
    --ring:        0 0 0 3px rgba(15,61,62,.16);
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
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}
[data-testid="stAppViewContainer"],
[data-testid="stMain"] { background: var(--canvas); }

h1 { font-size: 1.75rem !important; font-weight: 700 !important; letter-spacing: -0.005em !important; color: var(--ink-900) !important; }
h2 { font-size: 1.35rem !important; font-weight: 700 !important; letter-spacing: 0 !important; color: var(--ink-900) !important; }
h3 { font-size: 1.12rem !important; font-weight: 700 !important; color: var(--ink-900) !important; }
[data-testid="stCaptionContainer"] p { color: var(--ink-500) !important; font-size: 0.85rem !important; }
hr { border-color: var(--line) !important; margin: 1rem 0 !important; }
::selection { background: var(--lime-400); color: var(--brand-700); }

/* Streamlit chrome */
/* CSS-only st.markdown / st.html blocks shouldn't take up layout space */
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
    padding: 0 1rem;
    border-radius: var(--r-md) !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    box-shadow: var(--shadow-xs);
    transition: background-color .18s var(--ease), border-color .18s var(--ease),
                box-shadow .18s var(--ease), transform .12s var(--ease);
}
.stApp button[data-testid^="stBaseButton"]:active:not(:disabled) { transform: translateY(1px); }
.stApp button[data-testid^="stBaseButton-primary"] {
    background: var(--brand-600) !important;
    border: 1px solid var(--brand-600) !important;
    color: #FFFFFF !important;
}
.stApp button[data-testid^="stBaseButton-primary"]:hover {
    background: var(--brand-700) !important; border-color: var(--brand-700) !important;
    box-shadow: 0 4px 12px -6px rgba(15,61,62,.55);
}
.stApp button[data-testid^="stBaseButton-primary"] p { color: #FFFFFF !important; font-weight: 700 !important; }
.stApp button[data-testid^="stBaseButton-secondary"] {
    background: var(--surface) !important;
    border: 1px solid var(--line-strong) !important;
    color: var(--ink-900) !important;
}
.stApp button[data-testid^="stBaseButton-secondary"]:hover {
    background: var(--brand-50) !important; border-color: var(--brand-200) !important; color: var(--brand-600) !important;
}
.stApp button[data-testid^="stBaseButton-secondary"] p { font-weight: 700 !important; }
.stApp button[data-testid^="stBaseButton"]:focus-visible { box-shadow: var(--ring) !important; outline: none !important; }
.stApp button[data-testid^="stBaseButton"]:disabled { opacity: .5; }
.stApp button[data-testid="stBaseButton-tertiary"] { color: var(--ink-600) !important; font-weight: 600 !important; transition: color .15s var(--ease); }
.stApp button[data-testid="stBaseButton-tertiary"]:hover { color: var(--brand-600) !important; }

/* =========================================================
   FORM CONTROLS
   ========================================================= */
[data-testid="stWidgetLabel"] p {
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    color: var(--ink-700) !important;
}
.stTextInput [data-testid="stTextInputRootElement"],
.stTextArea [data-testid="stTextAreaRootElement"],
.stSelectbox [role="group"] {
    background: var(--surface) !important;
    border: 1px solid var(--line-strong) !important;
    border-radius: var(--r-md) !important;
    box-shadow: var(--shadow-xs);
    transition: border-color .15s ease, box-shadow .15s ease;
}
.stTextInput [data-testid="stTextInputRootElement"] { min-height: 40px; }
.stTextInput [data-baseweb="base-input"],
.stTextInput input, .stTextArea textarea {
    background: transparent !important;
    color: var(--ink-900) !important;
    font-size: 0.95rem !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: var(--ink-400) !important; }
.stTextInput [data-testid="stTextInputRootElement"]:focus-within,
.stTextArea [data-testid="stTextAreaRootElement"]:focus-within,
.stSelectbox [role="group"]:focus-within {
    border-color: var(--brand-600) !important;
    box-shadow: var(--ring) !important;
}
.stSelectbox [role="group"] { min-height: 40px; font-size: 0.95rem; color: var(--ink-900); }
.stSelectbox [role="group"]:hover, .stTextInput [data-testid="stTextInputRootElement"]:hover { border-color: var(--brand-200) !important; }
.stTextInput button { color: var(--ink-400) !important; }
.stTextInput button:hover { color: var(--ink-700) !important; }
[data-testid="InputInstructions"] { display: none !important; }

/* Field with an error — wrap it in st.container(key="err_<name>") */
[class*="st-key-err_"] .stTextInput [data-testid="stTextInputRootElement"],
[class*="st-key-err_"] .stSelectbox [role="group"] { border-color: var(--red-600) !important; }
[class*="st-key-err_"] .stTextInput [data-testid="stTextInputRootElement"]:focus-within { box-shadow: 0 0 0 3px rgba(181,72,59,.16) !important; }
[class*="st-key-err_"], [class*="st-key-ok_"] { gap: 6px !important; }
.stTextInput [data-testid="stTextInputIcon"], .stTextInput [data-testid="stTextInputRootElement"] > div:first-child span[data-testid="stIconMaterial"] { color: var(--ink-400) !important; }

/* =========================================================
   FEEDBACK
   ========================================================= */
.ds-alert {
    display: flex; gap: 10px; align-items: flex-start;
    padding: 10px 12px;
    border-radius: var(--r-md);
    border: 1px solid;
    font-size: 0.92rem; line-height: 1.45; font-weight: 400;
}
.ds-alert i { margin-top: 2px; font-size: 0.875rem; }
.ds-alert-error   { background: var(--red-50);   border-color: var(--red-200);   color: var(--red-700); }
.ds-alert-success { background: var(--green-50); border-color: var(--green-200); color: var(--green-700); }
.ds-alert-info    { background: var(--brand-50);  border-color: var(--brand-200);  color: var(--brand-700); }
.ds-alert-warning { background: var(--amber-50); border-color: var(--amber-200); color: var(--amber-700); }

.ds-field-error {
    display: flex; gap: 6px; align-items: center;
    color: var(--red-600);
    font-size: 0.85rem; font-weight: 400;
}
.ds-field-error i { font-size: 0.72rem; }

[data-testid="stAlert"] { border-radius: var(--r-md) !important; font-size: 0.85rem !important; }

/* =========================================================
   BRAND
   ========================================================= */
.ds-brand { display: flex; align-items: center; gap: 10px; }
.ds-brand-mark {
    width: 34px; height: 34px; flex-shrink: 0;
    display: inline-flex; align-items: center; justify-content: center;
    border-radius: 9px;
    background: var(--brand-600); color: var(--lime-400);
    font-size: 0.95rem;
    box-shadow: 0 2px 6px -2px rgba(15,61,62,.5);
}
.ds-brand-text { display: flex; flex-direction: column; line-height: 1.15; }
.ds-brand-name { font-size: 1.05rem; font-weight: 700; color: var(--ink-900); }
.ds-brand-sub  { font-size: 0.74rem; font-weight: 400; color: var(--ink-500); letter-spacing: .02em; }

/* =========================================================
   SIDEBAR (dashboard) — width set by set_page_config(initial_sidebar_state=…)
   ========================================================= */
[data-testid="stSidebar"] {
    background: var(--side-bg) !important;
    border-right: none !important;
}
[data-testid="stSidebarHeader"] { padding: 14px 12px 4px !important; min-height: 0 !important; height: auto !important; }
[data-testid="stSidebarContent"] { padding: 0 !important; background: transparent !important; }
[data-testid="stSidebarUserContent"] { padding: 0 12px 14px !important; }
[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] {
    min-height: calc(100vh - 64px); gap: 2px !important;
}
[data-testid="stLayoutWrapper"]:has(> .st-key-sb_user) { margin-top: auto; }
.st-key-sb_user { gap: 10px !important; padding-top: 14px; border-top: 1px solid var(--side-line); }

/* Brand on the dark panel */
[data-testid="stSidebar"] .ds-brand-mark { background: var(--lime-400); color: var(--brand-600); box-shadow: none; }
[data-testid="stSidebar"] .ds-brand-name { color: #FFFFFF; }
[data-testid="stSidebar"] .ds-brand-sub  { color: var(--side-muted); }

/* Collapse (inside the dark panel) and expand (on the light page) toggles */
[data-testid="stSidebarCollapseButton"] { display: flex !important; visibility: visible !important; opacity: 1 !important; }
[data-testid="stSidebarCollapseButton"] button {
    width: 30px !important; height: 30px !important; min-height: 30px !important; padding: 0 !important;
    border: 1px solid var(--side-line) !important; border-radius: var(--r-md) !important;
    background: transparent !important; color: var(--side-ink) !important;
    transition: background-color .15s var(--ease), color .15s var(--ease);
}
[data-testid="stSidebarCollapseButton"] button:hover { background: var(--side-hover) !important; color: var(--lime-400) !important; }
[data-testid="stExpandSidebarButton"] {
    width: 30px !important; height: 30px !important; min-height: 30px !important; padding: 0 !important;
    border: 1px solid var(--line) !important; border-radius: var(--r-md) !important;
    background: var(--surface) !important; color: var(--brand-600) !important; box-shadow: var(--shadow-xs) !important;
}
[data-testid="stExpandSidebarButton"]:hover { border-color: var(--brand-200) !important; background: var(--brand-50) !important; }

.ds-nav-label {
    margin: 22px 0 8px 10px;
    font-size: 0.7rem; font-weight: 700; letter-spacing: .12em;
    text-transform: uppercase; color: var(--side-muted);
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
    padding: 8px 10px !important; min-height: 38px;
    border-radius: var(--r-md) !important; margin: 0 !important; gap: 10px;
    transition: background-color .15s var(--ease);
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a p,
[data-testid="stSidebar"] [data-testid="stPageLink"] a span {
    font-size: 0.95rem !important; font-weight: 400 !important; color: var(--side-ink) !important;
    transition: color .15s var(--ease);
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover { background: var(--side-hover) !important; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover p { color: #FFFFFF !important; }
[class*="st-key-navon_"] a { background: var(--side-active) !important; }
[class*="st-key-navon_"] a p { color: #FFFFFF !important; font-weight: 700 !important; }
[class*="st-key-navon_"] a [data-testid="stIconMaterial"] { color: var(--lime-400) !important; }

/* Count badge on a nav item (content set per render by render_sidebar) */
[class*="st-key-nav"] a::after {
    margin-left: auto; padding: 1px 8px; border-radius: 99px;
    background: var(--red-600); color: #FFFFFF; font-size: 0.72rem; font-weight: 700; line-height: 1.5;
    font-family: var(--font);
}

.ds-user-card { display: flex; align-items: center; gap: 10px; padding: 2px 4px 0; }
.ds-avatar {
    width: 34px; height: 34px; flex-shrink: 0;
    display: inline-flex; align-items: center; justify-content: center;
    border-radius: 50%;
    background: var(--lime-400); color: var(--brand-600);
    font-size: 0.8rem; font-weight: 700;
}
.ds-user-meta { min-width: 0; line-height: 1.3; }
.ds-user-name { font-size: 0.92rem; font-weight: 700; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ds-user-role { font-size: 0.78rem; color: var(--side-muted); }
.stApp .st-key-sb_user button[data-testid^="stBaseButton"] {
    min-height: 36px !important; font-size: 0.9rem !important;
    background: transparent !important; border: 1px solid var(--side-line) !important;
    color: var(--side-ink) !important; box-shadow: none !important;
}
.stApp .st-key-sb_user button[data-testid^="stBaseButton"] p,
.stApp .st-key-sb_user button[data-testid^="stBaseButton"] span { color: var(--side-ink) !important; }
.stApp .st-key-sb_user button[data-testid^="stBaseButton"]:hover { background: var(--side-hover) !important; border-color: rgba(255,255,255,.24) !important; }
.stApp .st-key-sb_user button[data-testid^="stBaseButton"]:hover :is(p, span) { color: #FFFFFF !important; }

/* =========================================================
   DASHBOARD LAYOUT
   ========================================================= */
.stMain [data-testid="stMainBlockContainer"] { padding: 22px 28px 32px !important; max-width: 1440px; }
.stMain [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { gap: 16px; }

/* Zero-height helper iframes (chart export) must not take space */
[data-testid="stElementContainer"]:has(iframe[height="0"]) { position: absolute !important; width: 0; height: 0; overflow: hidden; }

.ds-page-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; flex-wrap: wrap; }
.ds-page-title { margin: 0 !important; padding: 0 !important; font-size: 2rem !important; font-weight: 700 !important; letter-spacing: -0.005em !important; line-height: 1.15 !important; }
.ds-page-sub { margin: 6px 0 0; font-size: 1rem; color: var(--ink-500); }
.ds-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.ds-chip {
    display: inline-flex; align-items: center; gap: 6px; height: 30px; padding: 0 12px;
    border: 1px solid var(--line); border-radius: var(--r-md); background: var(--surface);
    font-size: 0.85rem; font-weight: 400; color: var(--ink-600); white-space: nowrap;
}
.ds-chip i { font-size: 0.75rem; }
.ds-chip-model   { background: var(--brand-600); border-color: var(--brand-600); color: #FFFFFF; font-weight: 700; }
.ds-chip-model i { color: var(--lime-400); }
.ds-chip-role-rm { background: var(--sky-50);   border-color: var(--sky-200);   color: var(--sky-700);   font-weight: 700; }
.ds-chip-role-mt { background: var(--sage-50);  border-color: var(--sage-200);  color: var(--sage-700);  font-weight: 700; }

/* KPI cards */
.ds-kpi-grid { display: grid; grid-template-columns: repeat(var(--cols, 4), minmax(0, 1fr)); gap: 14px; }
.ds-kpi {
    position: relative;
    background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg);
    padding: 18px 20px; box-shadow: var(--shadow-xs);
    transition: opacity .2s var(--ease), border-color .2s var(--ease), box-shadow .2s var(--ease), transform .2s var(--ease);
}
.ds-kpi:hover { border-color: var(--line-strong); box-shadow: var(--shadow-card); transform: translateY(-1px); }
.ds-kpi-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.ds-kpi-label { font-size: 0.74rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-600); }
.ds-kpi-head i {
    width: 34px; height: 34px; flex-shrink: 0; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 0.9rem; color: var(--brand-600); background: var(--brand-50);
}
.ds-kpi-value { margin-top: 6px; font-size: 2.15rem; font-weight: 700; line-height: 1.05; color: var(--ink-900); font-variant-numeric: tabular-nums lining-nums; }
.ds-kpi-caption { margin-top: 6px; font-size: 0.88rem; color: var(--ink-600); }
.ds-kpi-trend { margin-top: 6px; font-size: 0.82rem; font-weight: 700; display: flex; align-items: center; gap: 5px; }
.ds-kpi-trend i { font-size: 0.7rem; }

/* Tones: a coloured top rule + value/icon colour; "filled" tints the card */
.ds-kpi:not(.ds-kpi-neutral)::before {
    content: ""; position: absolute; left: 0; right: 0; top: -1px; height: 3px;
    border-radius: var(--r-lg) var(--r-lg) 0 0; background: var(--tone);
}
.ds-kpi-teal  { --tone: var(--brand-600); --tone-ink: var(--brand-600); --tone-soft: var(--brand-50);  --tone-line: var(--brand-200); }
.ds-kpi-sage  { --tone: var(--sage-500);  --tone-ink: var(--sage-700);  --tone-soft: var(--sage-50);   --tone-line: var(--sage-200); }
.ds-kpi-sky   { --tone: var(--sky-500);   --tone-ink: var(--sky-700);   --tone-soft: var(--sky-50);    --tone-line: var(--sky-200); }
.ds-kpi-navy  { --tone: var(--navy-700);  --tone-ink: var(--navy-700);  --tone-soft: var(--navy-50);   --tone-line: var(--navy-200); }
.ds-kpi-green { --tone: var(--green-600); --tone-ink: var(--green-700); --tone-soft: var(--green-50);  --tone-line: var(--green-200); }
.ds-kpi-amber { --tone: var(--amber-600); --tone-ink: var(--amber-700); --tone-soft: var(--amber-50);  --tone-line: var(--amber-200); }
.ds-kpi-red   { --tone: var(--red-600);   --tone-ink: var(--red-700);   --tone-soft: var(--red-50);    --tone-line: var(--red-200); }
.ds-kpi:not(.ds-kpi-neutral) .ds-kpi-value { color: var(--tone-ink); }
.ds-kpi:not(.ds-kpi-neutral) .ds-kpi-head i { color: var(--tone-ink); background: var(--tone-soft); }
.ds-kpi-filled { background: var(--tone-soft); border-color: var(--tone-line); }
.ds-kpi-filled :is(.ds-kpi-label, .ds-kpi-caption, .ds-kpi-trend) { color: var(--tone-ink); }
.ds-kpi-filled .ds-kpi-head i { background: var(--surface); }
.ds-dim { opacity: .4; }

/* Impact summary line (Action Board) */
.ds-impact {
    display: flex; flex-wrap: wrap; align-items: center; gap: 10px 26px;
    padding: 12px 18px; border-radius: var(--r-lg);
    background: var(--brand-600); color: rgba(255,255,255,.82); font-size: 0.97rem;
}
.ds-impact-k {
    font-size: 0.72rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;
    color: var(--lime-400); padding-right: 6px;
}
.ds-impact-i { display: inline-flex; align-items: center; gap: 8px; white-space: nowrap; }
.ds-impact-i b { color: #FFFFFF; font-weight: 700; }
.ds-impact-i i { color: var(--lime-400); font-size: 0.82rem; }

/* Cards */
[class*="st-key-card_"] {
    background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg);
    padding: 20px 22px !important; box-shadow: var(--shadow-xs); gap: 12px !important;
    transition: box-shadow .2s var(--ease), border-color .2s var(--ease);
}
[class*="st-key-card_"]:hover { box-shadow: var(--shadow-card); }
.ds-card-head { min-width: 0; }
.ds-card-title { margin: 0 !important; padding: 0 !important; display: flex; align-items: center; gap: 8px;
    font-size: 1.18rem !important; font-weight: 700 !important; letter-spacing: 0 !important; color: var(--ink-900) !important; }
.ds-card-ico { color: var(--brand-500); font-size: 0.9rem; }
.ds-card-sub { margin: 4px 0 0; font-size: 0.9rem; color: var(--ink-500); }
.ds-note { margin: 0; display: flex; align-items: center; gap: 6px; font-size: 0.85rem; color: var(--ink-500); }
.ds-note i { color: var(--brand-500); }
.ds-legend { display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 0.88rem; color: var(--ink-600); }
.ds-legend span { display: inline-flex; align-items: center; gap: 6px; }
.ds-legend i { font-size: 0.55rem; }

/* Popover trigger (Export) */
[data-testid="stPopover"] button { min-height: 34px !important; font-size: 0.88rem !important; padding: 0 12px !important; }
[data-testid="stPopoverBody"] { padding: 8px !important; min-width: 190px; }
[data-testid="stPopoverBody"] button { justify-content: flex-start !important; box-shadow: none !important; border-color: transparent !important; }
[data-testid="stPopoverBody"] button:hover { background: var(--subtle) !important; }

/* Hide Plotly's toolbar; exports are driven from our Export menu */
.stPlotlyChart .modebar-container { display: none !important; }
[data-testid="stElementToolbar"] { display: none !important; }

/* Filters: select with an inline "Label:" prefix */
[class*="st-key-flt_"] [role="group"]::before {
    padding-left: 12px; margin-right: 4px; white-space: nowrap;
    font-size: 0.92rem; color: var(--ink-500);
}
[class*="st-key-flt_"] [role="group"] { display: flex; align-items: center; }
[class*="st-key-flt_"] [role="group"] input { font-weight: 600 !important; color: var(--ink-900) !important; }
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-srch_"]) { flex: 1 1 220px; min-width: 200px; }
[class*="st-key-bar_"] { gap: 10px !important; }

/* Tables */
[class*="st-key-tbl_"] { gap: 0 !important; }
[class*="st-key-tblhead_"] { padding: 6px 0 10px; border-bottom: 1px solid var(--line); }
[class*="st-key-tblrow_"] {
    padding: 4px 0; min-height: 52px; justify-content: center; border-bottom: 1px solid var(--line);
    transition: background-color .15s var(--ease);
}
[class*="st-key-tblrow_"]:hover { background: var(--brand-50); }
.ds-th { display: block; font-size: 0.74rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-500); }
.ds-td { display: block; font-size: 0.97rem; color: var(--ink-900); font-variant-numeric: tabular-nums lining-nums; }
.ds-right { text-align: right; }
.ds-strong { font-weight: 700; }
[class*="st-key-lnk_"] button { min-height: 0 !important; padding: 0 !important; }
[class*="st-key-lnk_"] button p { color: var(--brand-500) !important; font-weight: 700 !important; font-size: 0.97rem !important; }
[class*="st-key-lnk_"] button:hover p { color: var(--brand-600) !important; }
[class*="st-key-lnk_"] button:hover p { text-decoration: underline; }
[class*="st-key-view_"] button { min-height: 32px !important; padding: 0 12px !important; font-size: 0.88rem !important; }
.ds-empty { padding: 28px 0; text-align: center; font-size: 0.85rem; color: var(--ink-400); }

/* Static summary tables */
.ds-table { width: 100%; border-collapse: collapse; font-size: 0.97rem; color: var(--ink-900); }
.ds-table th {
    padding: 8px 10px 10px; text-align: left; border-bottom: 1px solid var(--line);
    font-size: 0.74rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-500);
}
.ds-table td { padding: 12px 10px; border-bottom: 1px solid var(--line); font-variant-numeric: tabular-nums lining-nums; }
.ds-table tbody tr { transition: background-color .15s var(--ease); }
.ds-table tbody tr:hover { background: var(--brand-50) !important; }
.ds-table tbody tr:nth-child(even) { background: var(--subtle); }
.ds-table .muted { color: var(--ink-500); }

/* Pills & coloured text */
.ds-pill {
    display: inline-flex; align-items: center; padding: 2px 9px; border-radius: 99px; border: 1px solid;
    font-size: 0.8rem; font-weight: 700; white-space: nowrap; line-height: 1.45;
}
.ds-pill-teal    { background: var(--brand-50);  color: var(--brand-600); border-color: var(--brand-200); }
.ds-pill-sage    { background: var(--sage-50);   color: var(--sage-700);  border-color: var(--sage-200); }
.ds-pill-sky     { background: var(--sky-50);    color: var(--sky-700);   border-color: var(--sky-200); }
.ds-pill-navy    { background: var(--navy-50);   color: var(--navy-700);  border-color: var(--navy-200); }
.ds-pill-green   { background: var(--green-50);  color: var(--green-700); border-color: var(--green-200); }
.ds-pill-amber   { background: var(--amber-50);  color: var(--amber-700); border-color: var(--amber-200); }
.ds-pill-red     { background: var(--red-50);    color: var(--red-700);   border-color: var(--red-200); }
.ds-pill-neutral { background: var(--subtle);    color: var(--ink-600);   border-color: var(--line); }
.ds-text-teal   { color: var(--brand-600); font-weight: 700; }
.ds-text-sage   { color: var(--sage-700);  font-weight: 700; }
.ds-text-sky    { color: var(--sky-700);   font-weight: 700; }
.ds-text-navy   { color: var(--navy-700);  font-weight: 700; }
.ds-text-green  { color: var(--green-700); font-weight: 700; }
.ds-text-amber  { color: var(--amber-700); font-weight: 700; }
.ds-text-red    { color: var(--red-600);   font-weight: 700; }
.ds-text-neutral{ color: var(--ink-700);   font-weight: 700; }

/* Segmented control (e.g. Sort by) */
button[data-variant="segmented_control"] { min-height: 30px !important; font-size: 0.88rem !important; font-weight: 400 !important; color: var(--ink-600) !important; }
button[data-variant="segmented_control"][data-selected="true"] {
    background: var(--brand-600) !important; border-color: var(--brand-600) !important; color: #FFFFFF !important; font-weight: 700 !important;
}

/* Pagination */
[class*="st-key-pager_"] { padding-top: 12px; gap: 6px !important; }
[class*="st-key-pager_"] button { min-height: 32px !important; min-width: 32px; padding: 0 8px !important; font-size: 0.9rem !important; box-shadow: none !important; }
.ds-pager-info { font-size: 0.92rem; color: var(--ink-500); white-space: nowrap; }
.ds-pager-gap { color: var(--ink-400); padding: 0 2px; }
/* In horizontal rows, HTML blocks size to content so st.space("stretch") can push items apart */
[data-testid="stHorizontalBlock"] > [data-testid="stElementContainer"]:has(> [data-testid="stHtml"]) { flex: 0 1 auto; width: auto !important; }

/* Entrance: sections rise in once when a page mounts (reruns reuse the DOM, so this
   does not replay on every interaction). */
@keyframes ds-rise { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
.stMain [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > * { animation: ds-rise .35s var(--ease) both; }
.stMain [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > :nth-child(2) { animation-delay: .03s; }
.stMain [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > :nth-child(3) { animation-delay: .06s; }
.stMain [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > :nth-child(4) { animation-delay: .09s; }
.stMain [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > :nth-child(n+5) { animation-delay: .12s; }
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation: none !important; transition: none !important; }
}

@media (max-width: 1100px) {
    .ds-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 640px) {
    .stMain [data-testid="stMainBlockContainer"] { padding: 16px !important; }
    .ds-kpi-grid { grid-template-columns: 1fr; }
    .ds-page-title { font-size: 1.4rem !important; }
}
</style>
"""


def inject_global_css() -> None:
    """Call once in app.py after set_page_config to apply the design system."""
    st.markdown(_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Public (signed-out) page chrome: landing, login, signup
# ---------------------------------------------------------------------------

_PUBLIC_CSS = """
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"], [data-testid="stHeader"] { display: none !important; }
[data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: none !important; }
[data-testid="stMain"] { padding: 0 !important; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { gap: 0 !important; }
</style>
"""

_AUTH_CSS = """
<style>
[data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background:
        radial-gradient(1200px 520px at 85% -10%, #DDEBE4 0%, rgba(221,235,228,0) 60%),
        radial-gradient(900px 480px at -10% 110%, #EAF3E2 0%, rgba(234,243,226,0) 60%),
        var(--canvas) !important;
}
[data-testid="stMainBlockContainer"] { padding: 0 24px 40px !important; }

/* Top bar */
.st-key-auth_topbar {
    max-width: 1120px; margin: 0 auto; padding: 18px 0 !important;
}

/* Card */
[class*="st-key-auth_card"] {
    max-width: 440px; margin: 3vh auto 0;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: var(--r-xl);
    box-shadow: var(--shadow-pop);
    padding: 32px 32px 28px !important;
    gap: 0.9rem !important;
}
.st-key-auth_card_wide { max-width: 520px; }
[class*="st-key-auth_card"] [data-testid="stForm"] { border: none !important; padding: 0 !important; }
[class*="st-key-auth_card"] [data-testid="stForm"] [data-testid="stVerticalBlock"] { gap: 0.9rem; }

.auth-head { text-align: center; margin-bottom: 0.6rem; }
.auth-head .auth-mark {
    width: 44px; height: 44px; margin: 0 auto 14px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 12px;
    background: var(--brand-50); color: var(--brand-600);
    border: 1px solid var(--brand-100);
    font-size: 1.05rem;
}
.auth-title { font-size: 1.85rem; font-weight: 700; color: var(--ink-900); line-height: 1.2; }
.auth-sub   { margin-top: 6px; font-size: 1rem; color: var(--ink-500); line-height: 1.5; }

.auth-switch {
    display: flex; align-items: center; gap: 12px;
    color: var(--ink-400); font-size: 0.85rem; font-weight: 400;
    margin-top: 0.35rem;
}
.auth-switch::before, .auth-switch::after { content: ""; flex: 1; height: 1px; background: var(--line); }

.auth-foot {
    max-width: 440px; margin: 18px auto 0;
    display: flex; justify-content: center; align-items: center; gap: 8px;
    color: var(--ink-500); font-size: 0.85rem; text-align: center;
}
.auth-foot i { color: var(--ink-400); }

/* Password checklist */
.pw-rules {
    display: grid; grid-template-columns: 1fr 1fr; gap: 4px 12px;
    margin-bottom: 2px;
    font-size: 0.85rem; color: var(--ink-500);
}
.pw-rules span { display: flex; align-items: center; gap: 6px; }
.pw-rules i { font-size: 0.72rem; color: var(--line-strong); width: 12px; }
.pw-rules .ok   { color: var(--green-700); }
.pw-rules .ok i { color: var(--green-600); }
.pw-rules .bad   { color: var(--red-600); }
.pw-rules .bad i { color: var(--red-600); }

.field-hint { margin-top: -0.35rem; font-size: 0.75rem; color: var(--ink-500); }

@media (max-width: 560px) {
    [class*="st-key-auth_card"] { padding: 24px 20px 20px !important; margin-top: 8px; }
    .pw-rules { grid-template-columns: 1fr; }
}
</style>
"""


def public_page_chrome() -> None:
    """Hide the sidebar/header and let the page own the full viewport."""
    st.markdown(_PUBLIC_CSS, unsafe_allow_html=True)


def auth_page_chrome() -> None:
    """Public chrome + the shared login/signup card layout."""
    public_page_chrome()
    st.markdown(_AUTH_CSS, unsafe_allow_html=True)


def hide_sidebar() -> None:
    """Backwards-compatible alias used by older views."""
    public_page_chrome()
