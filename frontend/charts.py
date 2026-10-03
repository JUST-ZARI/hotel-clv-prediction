"""Plotly figures styled to the dashboard design system."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

# Palette — matches the design tokens in style.py
INK_900, INK_500, INK_400 = "#0B0B0C", "#333336", "#6B6B70"
LINE, TRACK = "#E3E8E5", "#EDF1EE"
BRAND = "#0F3D3E"      # deep teal: primary series
SAGE = "#8BCF65"       # secondary series
SKY = "#6FA8DC"        # third series
NAVY = "#14213D"       # emphasis
# Categorical series (e.g. one colour per prediction driver), in display order
SERIES = [BRAND, SAGE, SKY, "#D9A441", "#C77B5B"]   # teal, sage, soft blue, ochre, terracotta
TIER_COLORS = {"High": BRAND, "Medium": SAGE, "Low": SKY, "Platinum": NAVY}
RISK_COLORS = {"High Risk": "#B5483B", "Medium Risk": "#D9A441", "Low Risk": SAGE}
FONT = "'Times New Roman', Times, serif"


def _base(fig: go.Figure, height: int, margin: dict | None = None) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=margin or dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=13, color=INK_500),
        showlegend=False,
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=LINE, font=dict(family=FONT, color=INK_900, size=13)),
        bargap=0.35,
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
    fig.add_bar(y=y, x=[top] * len(values), orientation="h", marker=dict(color=TRACK, cornerradius=4),
                hoverinfo="skip", width=0.52)
    fig.add_bar(y=y, x=values, orientation="h", marker=dict(color=colors, cornerradius=4), width=0.52,
                customdata=list(zip(labels, value_text)),
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>")
    fig.update_layout(barmode="overlay")
    tick = dict(tickmode="array", tickvals=y, showgrid=False, zeroline=False, fixedrange=True,
                ticks="", ticklabelstandoff=10, range=[-0.6, len(y) - 0.4], automargin=True)
    fig.update_yaxes(ticktext=labels, tickfont=dict(size=13, color=INK_500), **tick)
    fig.update_xaxes(visible=False, range=[0, top], fixedrange=True)
    # Right-hand value labels via a mirrored axis.
    fig.add_scatter(y=y, x=[None] * len(y), yaxis="y2", showlegend=False, hoverinfo="skip")
    fig.update_layout(yaxis2=dict(overlaying="y", side="right", ticktext=value_text,
                                  tickfont=dict(size=13, color=INK_900), **tick))
    return _base(fig, height or 34 * len(labels) + 10)


def vbar_tiers(tiers: list[str], values: list[float], dim: set[str]) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=tiers, y=values,
        marker=dict(color=[TIER_COLORS[t] for t in tiers],
                    opacity=[0.25 if t in dim else 1 for t in tiers], cornerradius=6),
        text=[f"KSh {v:,.0f}" for v in values], textposition="outside", cliponaxis=False,
        textfont=dict(color=INK_900, size=14, family=FONT),
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
