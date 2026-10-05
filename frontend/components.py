"""
Dashboard UI components shared by every protected screen.

Visual rules live in style.py (dashboard section); this module only emits
markup and wires Streamlit widgets to it.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from typing import Callable

import pandas as pd
import streamlit as st

from style import icon

LOOKUP_PAGE = "views/guest_lookup.py"
PAGE_SIZE = 8

TIER_TONE = {"Platinum": "navy", "High": "teal", "Medium": "sage", "Low": "sky"}
RISK_TONE = {"High Risk": "red", "Medium Risk": "amber", "Low Risk": "green"}
OUTCOME_TONE = {"Came back": "green", "Didn't come back": "red", "Waiting": "neutral"}


def esc(value) -> str:
    return html.escape(str(value))


def ksh(value: float) -> str:
    return f"KSh {value:,.0f}"


def is_revenue_manager() -> bool:
    return st.session_state.get("role") == "revenue_manager"


def css(rules: str) -> None:
    """Page-scoped CSS (rendered into a zero-height element)."""
    st.html(f"<style>{rules}</style>")


# ---------------------------------------------------------------------------
# Badges & inline text
# ---------------------------------------------------------------------------

def pill(text: str, tone: str = "neutral") -> str:
    return f'<span class="ds-pill ds-pill-{tone}">{esc(text)}</span>'


def tier_badge(tier: str) -> str:
    return pill(tier, TIER_TONE.get(tier, "neutral"))


def action_tone(action: str) -> str:
    a = action.lower()
    if "win-back" in a or "personal call" in a:
        return "red"
    if "upsell" in a:
        return "navy"
    if "re-engagement" in a or "retention" in a or "bonus" in a:
        return "amber"
    if "vip" in a or "loyalty" in a:
        return "teal"
    return "neutral"


def action_text(action: str) -> str:
    return f'<span class="ds-text-{action_tone(action)}">{esc(action)}</span>'


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

def page_header(title: str, subtitle: str) -> None:
    st.html(f"""
    <header class="ds-page-head">
        <div>
            <h1 class="ds-page-title">{esc(title)}</h1>
            <p class="ds-page-sub">{esc(subtitle)}</p>
        </div>
    </header>""")


# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------

@dataclass
class Kpi:
    label: str
    value: str
    caption: str
    icon: str
    tone: str = "neutral"          # neutral | teal | sage | sky | navy | green | amber | red
    trend: str | None = None       # optional second caption line
    trend_dir: str = "flat"        # up | down | flat
    dimmed: bool = False


def kpi_row(items: list[Kpi], filled: bool = False) -> None:
    arrows = {"up": "arrow-up", "down": "arrow-down", "flat": "minus"}
    cards = []
    for k in items:
        trend = (f'<div class="ds-kpi-trend">{icon(arrows[k.trend_dir])} {esc(k.trend)}</div>'
                 if k.trend else "")
        cls = f"ds-kpi ds-kpi-{k.tone}{' ds-kpi-filled' if filled else ''}{' ds-dim' if k.dimmed else ''}"
        cards.append(f"""
        <div class="{cls}">
            <div class="ds-kpi-head"><span class="ds-kpi-label">{esc(k.label)}</span>{icon(k.icon)}</div>
            <div class="ds-kpi-value">{esc(k.value)}</div>
            <div class="ds-kpi-caption">{esc(k.caption)}</div>{trend}
        </div>""")
    st.html(f'<div class="ds-kpi-grid" style="--cols:{len(items)}">{"".join(cards)}</div>')


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------

def card(key: str, **kwargs):
    """White surface; everything rendered inside belongs to the card."""
    return st.container(key=f"card_{key}", **kwargs)


def card_title(title: str, subtitle: str | None = None, fa: str | None = None) -> None:
    ico = f'<span class="ds-card-ico">{icon(fa)}</span>' if fa else ""
    sub = f'<p class="ds-card-sub">{esc(subtitle)}</p>' if subtitle else ""
    st.html(f'<div class="ds-card-head"><h3 class="ds-card-title">{ico}{esc(title)}</h3>{sub}</div>')


def note(text: str) -> None:
    st.html(f'<p class="ds-note">{icon("circle-info")} {esc(text)}</p>')


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

def filter_select(label: str, options: list, key: str, format_func: Callable = str, index: int = 0,
                  width: int = 210, **kwargs):
    """Select with an inline 'Label: value' look, as in the wireframes. Extra kwargs go to st.selectbox."""
    with st.container(key=f"flt_{key}", width="content"):
        css(f'.st-key-flt_{key} [role="group"]::before {{ content: {json.dumps(label + ":")}; }}')
        return st.selectbox(label, options, index=index, key=key, format_func=format_func,
                            label_visibility="collapsed", width=width, **kwargs)


def search_box(key: str, placeholder: str = "Search Guest ID…") -> str:
    with st.container(key=f"srch_{key}"):
        return st.text_input("Search", key=key, type="search", placeholder=placeholder,
                             label_visibility="collapsed", live=True) or ""


def reset_page_on_change(table_key: str, *filters) -> None:
    """Go back to page 1 whenever the filter values change."""
    sig = repr(filters)
    if st.session_state.get(f"_{table_key}_sig") != sig:
        st.session_state[f"_{table_key}_sig"] = sig
        st.session_state[f"_{table_key}_page"] = 1


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

@dataclass
class Col:
    header: str
    width: float
    render: Callable[[pd.Series], str] | None = None   # returns HTML
    kind: str = "html"                                  # html | guest_link | view_button
    align: str = "left"


def view_guest(guest_id: str) -> None:
    st.session_state["lookup_guest_id"] = guest_id
    st.switch_page(LOOKUP_PAGE)


def data_table(key: str, rows: pd.DataFrame, cols: list[Col], empty: str = "No guests match these filters.") -> None:
    widths = [c.width for c in cols]
    with st.container(key=f"tbl_{key}", gap=None):
        with st.container(key=f"tblhead_{key}", horizontal=False):
            head = st.columns(widths, gap="small", vertical_alignment="center")
            for c, col in zip(cols, head):
                col.html(f'<span class="ds-th ds-{c.align}">{esc(c.header)}</span>')
        if rows.empty:
            st.html(f'<div class="ds-empty">{icon("magnifying-glass")} {esc(empty)}</div>')
            return
        for i, (_, row) in enumerate(rows.iterrows()):
            with st.container(key=f"tblrow_{key}_{i}"):
                cells = st.columns(widths, gap="small", vertical_alignment="center")
                for c, cell in zip(cols, cells):
                    gid = row["guest_id"]
                    if c.kind == "guest_link":
                        with cell, st.container(key=f"lnk_{key}_{i}"):
                            if st.button(gid, key=f"{key}_id_{gid}", type="tertiary"):
                                view_guest(gid)
                    elif c.kind == "view_button":
                        with cell, st.container(key=f"view_{key}_{i}", horizontal_alignment="right"):
                            if st.button("View Guest", key=f"{key}_view_{gid}"):
                                view_guest(gid)
                    else:
                        cell.html(f'<span class="ds-td ds-{c.align}">{c.render(row)}</span>')


def paginate(key: str, total: int, page_size: int = PAGE_SIZE) -> tuple[int, int]:
    """Return the (start, end) slice for the current page."""
    pages = max(1, -(-total // page_size))
    page = min(max(1, st.session_state.get(f"_{key}_page", 1)), pages)
    st.session_state[f"_{key}_page"] = page
    return (page - 1) * page_size, min(page * page_size, total)


def pagination_bar(key: str, total: int, page_size: int = PAGE_SIZE) -> None:
    pages = max(1, -(-total // page_size))
    page = st.session_state.get(f"_{key}_page", 1)
    start = 0 if total == 0 else (page - 1) * page_size + 1
    end = min(page * page_size, total)

    def go(p: int) -> None:
        st.session_state[f"_{key}_page"] = p

    if pages <= 5:
        shown = list(range(1, pages + 1))
    else:
        shown = sorted({1, 2, 3, page - 1, page, page + 1, pages} & set(range(1, pages + 1)))

    with st.container(key=f"pager_{key}", horizontal=True, vertical_alignment="center"):
        st.html(f'<span class="ds-pager-info">Showing {start}–{end} of {total:,}</span>')
        st.space("stretch")
        st.button("", icon=":material/chevron_left:", key=f"{key}_prev", disabled=page <= 1,
                  on_click=go, args=(page - 1,))
        prev = 0
        for p in shown:
            if p - prev > 1:
                st.html('<span class="ds-pager-gap">…</span>')
            st.button(str(p), key=f"{key}_p{p}", type="primary" if p == page else "secondary",
                      on_click=go, args=(p,))
            prev = p
        st.button("", icon=":material/chevron_right:", key=f"{key}_next", disabled=page >= pages,
                  on_click=go, args=(page + 1,))


# ---------------------------------------------------------------------------
# Downloads & chart export
# ---------------------------------------------------------------------------

def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def download_csv(label: str, df: pd.DataFrame, filename: str, key: str, primary: bool = True) -> None:
    st.download_button(label, csv_bytes(df), file_name=filename, mime="text/csv", key=key,
                       icon=":material/download:", type="primary" if primary else "secondary",
                       on_click="ignore")


def _trigger_png(chart_key: str) -> None:
    """Click the (hidden) Plotly 'download png' modebar button of a chart."""
    n = st.session_state.get("_png_nonce", 0) + 1     # new content each click, so the script runs again
    st.session_state["_png_nonce"] = n
    st.html(f"""<script>/* {n} */
    const btn = document.querySelector('.st-key-{chart_key} .modebar-btn[data-title*="png" i]');
    if (btn) btn.dispatchEvent(new MouseEvent('click', {{bubbles: true}}));
    </script>""", unsafe_allow_javascript=True)


def export_menu(chart_key: str, data: pd.DataFrame, filename: str, label: str = "Export") -> None:
    """'Export' popover offering the chart as PNG and its data as CSV."""
    slot = st.container(key=f"pngslot_{chart_key}")
    with st.popover(label, icon=":material/download:", key=f"exp_{chart_key}"):
        png = st.button("Chart as PNG", icon=":material/image:", key=f"png_{chart_key}", width="stretch")
        st.download_button("Data as CSV", csv_bytes(data), file_name=f"{filename}.csv", mime="text/csv",
                           icon=":material/table_view:", key=f"csv_{chart_key}", width="stretch",
                           on_click="ignore")
    if png:
        with slot:
            _trigger_png(chart_key)
