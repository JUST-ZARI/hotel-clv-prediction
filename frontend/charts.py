"""Plotly figures styled to the dashboard design system."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

# Palette — matches the design tokens in style.py
INK_900, INK_500, INK_400 = "#0F1A15", "#5E6A64", "#96A09B"
LINE, TRACK = "#E3E9E5", "#EEF3F0"
BRAND = "#0C5D49"      # hotel green: brand
ORANGE = "#C2540A"     # High tier
SAGE = "#7DBE5A"       # Medium tier
SKY = "#6FA8DC"        # Low tier
PLAT = "#003F2B"       # Platinum (deep forest)
# Categorical series (e.g. one colour per prediction driver), in display order
SERIES = [ORANGE, BRAND, SKY, SAGE, "#F2A15C"]   # orange, green, soft blue, sage, apricot
TIER_COLORS = {"High": ORANGE, "Medium": SAGE, "Low": SKY, "Platinum": PLAT}
RISK_COLORS = {"High Risk": "#C0262D", "Medium Risk": "#F2A15C", "Low Risk": SAGE}
FONT = "'Times New Roman', Times, serif"


def warm_scale(n: int) -> list[str]:
    """n colours from the tier palette: orange through green to sky blue (ranked bars, highest first)."""
    stops = [(0xC2, 0x54, 0x0A), (0xF2, 0xA1, 0x5C), (0x7D, 0xBE, 0x5A), (0x6F, 0xA8, 0xDC)]
    out = []
    for i in range(n):
        t = i / max(1, n - 1) * (len(stops) - 1)
        k = min(int(t), len(stops) - 2)
        f = t - k
        a, b = stops[k], stops[k + 1]
        out.append("#%02X%02X%02X" % tuple(round(a[j] + (b[j] - a[j]) * f) for j in range(3)))
    return out


def _tint(hex_color: str, alpha: float = 0.08) -> str:
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


def _base(fig: go.Figure, height: int, margin: dict | None = None) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=margin or dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=14, color=INK_500),
        showlegend=False,
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=LINE, font=dict(family=FONT, color=INK_900, size=14)),
        bargap=0.35,
        transition=dict(duration=500, easing="cubic-in-out"),
    )
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    return fig


def show(fig: go.Figure, key: str, filename: str) -> None:
    """Render a chart inside a keyed container so export_menu() can find it."""
    with st.container(key=key):
        st.plotly_chart(fig, key=f"{key}_fig", theme=None, config={
            "displaylogo": False,
            "responsive": True,
            "modeBarButtonsToRemove": ["zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d",
                                       "autoScale2d", "resetScale2d", "hoverClosestCartesian",
                                       "hoverCompareCartesian", "toggleSpikelines"],
            "toImageButtonOptions": {"format": "png", "filename": filename, "scale": 2},
        })


def hbar_track(labels: list[str], values: list[float], colors: list[str], value_text: list[str],
               height: int | None = None, max_value: float | None = None) -> go.Figure:
    """Horizontal bars on a light track, labels left and values right (wireframe style)."""
    top = max_value or (max(values) if values else 1)
    y = list(range(len(labels)))[::-1]
    fig = go.Figure()
    fig.add_bar(y=y, x=[top] * len(values), orientation="h", marker=dict(color=TRACK, cornerradius=6),
                hoverinfo="skip", width=0.52)
    fig.add_bar(y=y, x=values, orientation="h", marker=dict(color=colors, cornerradius=6), width=0.52,
                customdata=list(zip(labels, value_text)),
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>")
    fig.update_layout(barmode="overlay")
    tick = dict(tickmode="array", tickvals=y, showgrid=False, zeroline=False, fixedrange=True,
                ticks="", ticklabelstandoff=10, range=[-0.6, len(y) - 0.4], automargin=True)
    fig.update_yaxes(ticktext=labels, tickfont=dict(size=14, color=INK_500), **tick)
    fig.update_xaxes(visible=False, range=[0, top], fixedrange=True)
    # Right-hand value labels via a mirrored axis.
    fig.add_scatter(y=y, x=[None] * len(y), yaxis="y2", showlegend=False, hoverinfo="skip")
    fig.update_layout(yaxis2=dict(overlaying="y", side="right", ticktext=value_text,
                                  tickfont=dict(size=14, color=INK_900), **tick))
    return _base(fig, height or 34 * len(labels) + 10)


def vbar_tiers(tiers: list[str], values: list[float], dim: set[str]) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=tiers, y=values,
        marker=dict(color=[TIER_COLORS[t] for t in tiers],
                    opacity=[0.25 if t in dim else 1 for t in tiers], cornerradius=6),
        text=[f"KSh {v:,.0f}" for v in values], textposition="outside", cliponaxis=False,
        textfont=dict(color=INK_900, size=15, family=FONT),
        hovertemplate="%{x}: KSh %{y:,.0f}<extra></extra>",
    ))
    fig.update_yaxes(visible=False, fixedrange=True, range=[0, max(values or [1]) * 1.18])
    fig.update_xaxes(showgrid=False, fixedrange=True, tickfont=dict(color=INK_500, size=14))
    return _base(fig, 250, dict(l=0, r=0, t=24, b=0))


def donut(tiers: list[str], counts: list[int], total: int, dim: set[str]) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=tiers, values=counts, hole=0.64, sort=False, direction="clockwise",
        marker=dict(colors=[LINE if t in dim else TIER_COLORS[t] for t in tiers],
                    line=dict(color="#FFFFFF", width=3)),
        textinfo="none",
        hovertemplate="%{label}: %{value:,} (%{percent})<extra></extra>",
    ))
    fig.add_annotation(text=f"<b>{total:,}</b><br><span style='font-size:13px;color:{INK_500}'>Total Guests</span>",
                       showarrow=False, font=dict(size=24, color=INK_900, family=FONT))
    return _base(fig, 190, dict(l=0, r=0, t=0, b=0))


def tier_lines(timeline, dim: set[str]) -> go.Figure:
    fig = go.Figure()
    for tier in timeline.columns:
        color = TIER_COLORS[tier]
        fig.add_scatter(
            x=timeline.index, y=timeline[tier], name=tier, mode="lines+markers",
            line=dict(color=color, width=2.5, shape="spline", smoothing=0.6),
            fill="tozeroy", fillcolor=_tint(color),
            marker=dict(size=7, color=color, line=dict(color="#FFFFFF", width=1.5)),
            opacity=0.25 if tier in dim else 1,
            hovertemplate=f"{tier} · %{{x}}: %{{y:,}} guests<extra></extra>",
        )
    fig.update_xaxes(showgrid=False, fixedrange=True, tickmode="linear", dtick=1,
                     showline=False, tickfont=dict(color=INK_500, size=13))
    fig.update_yaxes(showgrid=True, gridcolor=LINE, zeroline=False, fixedrange=True,
                     tickformat=",", tickfont=dict(color=INK_400, size=12), rangemode="tozero")
    fig.update_layout(hovermode="x unified")
    return _base(fig, 260, dict(l=0, r=8, t=8, b=0))


OUTCOME_COLORS = {"Came back": BRAND, "Didn't come back": "#F2A15C", "Waiting": "#C9D3CE"}


def outcome_weeks(weekly) -> go.Figure:
    """Stacked bars: actions sent each week, split by outcome. `weekly` has a week index and outcome columns."""
    fig = go.Figure()
    for outcome, color in OUTCOME_COLORS.items():
        if outcome not in weekly.columns:
            continue
        fig.add_bar(
            x=weekly.index, y=weekly[outcome], name=outcome,
            marker=dict(color=color, cornerradius=4),
            hovertemplate=f"{outcome}: %{{y:,}}<extra></extra>",
        )
    fig.update_layout(barmode="stack", hovermode="x unified", showlegend=True,
                      legend=dict(orientation="h", y=1.12, x=0, traceorder="normal", font=dict(size=13, color=INK_500)))
    fig.update_xaxes(showgrid=False, fixedrange=True, tickformat="%d %b", ticklabelmode="period",
                     tickfont=dict(color=INK_500, size=13), hoverformat="Week of %d %b %Y")
    fig.update_yaxes(showgrid=True, gridcolor=LINE, zeroline=False, fixedrange=True, rangemode="tozero",
                     tickformat=",d", tickfont=dict(color=INK_400, size=12))
    fig = _base(fig, 270, dict(l=0, r=8, t=36, b=0))
    fig.update_layout(showlegend=True, bargap=0.45)
    return fig
