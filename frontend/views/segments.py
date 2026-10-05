import streamlit as st

import charts
import components as ui
from auth import require_auth
from data import repository as repo

require_auth()

ui.page_header("Guest Segment Distribution", "Overview of predicted CLV tiers across all guests")

# ---------------------------------------------------------------------------
# Filters — channel and guest type narrow the data; tier highlights one segment
# ---------------------------------------------------------------------------
with st.container(key="bar_seg", horizontal=True, vertical_alignment="center"):
    tier = ui.filter_select("CLV Tier", ["All Tiers"] + repo.TIERS, "seg_tier")
    channel = ui.filter_select("Booking Channel", ["All Channels"] + repo.BOOKING_CHANNELS, "seg_channel", width=290)
    gtype = ui.filter_select("Guest Type", ["All Types"] + repo.GUEST_TYPES, "seg_type", width=250)

df = repo.guests()
if channel != "All Channels":
    df = df[df["booking_channel"] == channel]
if gtype != "All Types":
    df = df[df["guest_type"] == gtype]
dim = set() if tier == "All Tiers" else set(repo.TIERS) - {tier}

stats = repo.segment_characteristics(df)
total = int(stats["guests"].fillna(0).sum())
counts = stats["guests"].fillna(0).astype(int)
share = (counts / total) if total else counts * 0

tone = {"High": "teal", "Medium": "sage", "Low": "sky"}
icons = {"High": "arrow-trend-up", "Medium": "users", "Low": "users"}
ui.kpi_row([
    ui.Kpi(f"{t}-Value Guests", f"{counts[t]:,}", f"{share[t]:.0%} of guests", icons[t], tone[t],
           trend=repo.TIER_TREND[t][1], trend_dir=repo.TIER_TREND[t][0], dimmed=t in dim)
    for t in repo.TIERS
], filled=True)

# ---------------------------------------------------------------------------
# Average CLV per tier + proportion donut
# ---------------------------------------------------------------------------
left, right = st.columns([2.2, 1], gap="small")
with left, ui.card("avg"):
    ui.card_title("Average Predicted CLV per Tier", fa="chart-simple")
    avg = stats["avg_clv"].fillna(0)
    charts.show(charts.vbar_tiers(repo.TIERS, avg.tolist(), dim), key="chart_avg", filename="avg_clv_per_tier")
    ui.note("Average CLV value in KSh by segment tier")

with right, ui.card("mix"):
    ui.card_title("Guest Proportion by Tier", fa="chart-pie")
    charts.show(charts.donut(repo.TIERS, counts.tolist(), total, dim), key="chart_mix", filename="guest_share_by_tier")
    rows = "".join(
        f'<div class="seg-legend-row{" ds-dim" if t in dim else ""}">'
        f'<span><i class="fa-solid fa-circle" style="color:{charts.TIER_COLORS[t]}"></i>{t} Value</span>'
        f'<b>{counts[t]:,}</b><em>({share[t]:.0%})</em></div>'
        for t in repo.TIERS)
    st.html(f'<div class="seg-legend">{rows}</div>')

# ---------------------------------------------------------------------------
# Tier distribution over time (downloadable)
# ---------------------------------------------------------------------------
timeline = repo.tier_timeline(df)
with ui.card("trend"):
    with st.container(horizontal=True, vertical_alignment="top"):
        years = f"{timeline.index.min()}–{timeline.index.max()}" if len(timeline) else ""
        ui.card_title("Guest Tier Distribution Over Time",
                      f"Number of guests per CLV tier by first booking period {years}", fa="arrow-trend-up")
        st.space("stretch")
        ui.export_menu("chart_trend", timeline.reset_index().rename(columns={"first_booking_year": "year"}),
                       "guest_tier_distribution")
    charts.show(charts.tier_lines(timeline, dim), key="chart_trend", filename="guest_tier_distribution")
    st.html('<div class="ds-legend">'
            + "".join(f'<span><i class="fa-solid fa-circle" style="color:{charts.TIER_COLORS[t]}"></i>{t}</span>'
                      for t in repo.TIERS) + "</div>")

# ---------------------------------------------------------------------------
# Segment characteristics
# ---------------------------------------------------------------------------
with ui.card("chars"):
    ui.card_title("Segment Characteristics")
    body = "".join(f"""
        <tr class="{'ds-dim' if t in dim else ''}">
            <td>{ui.tier_badge(t)}</td>
            <td class="ds-strong">{ui.ksh(r.avg_clv) if r.guests else '—'}</td>
            <td>{r.avg_stays:.1f}</td>
            <td>{ui.ksh(r.avg_adr) if r.guests else '—'}</td>
            <td class="muted">{r.avg_days:.0f} days</td>
            <td class="muted">{ui.esc(r.strategy)}</td>
        </tr>""" for t, r in stats.fillna(0).iterrows())
    st.html(f"""
    <table class="ds-table">
        <thead><tr><th>Segment</th><th>Avg. CLV</th><th>Avg. Stays</th><th>Avg. ADR</th>
        <th>Avg. Days Since Last Stay</th><th>Recommended Strategy</th></tr></thead>
        <tbody>{body}</tbody>
    </table>""")

ui.css("""
.seg-legend { display: flex; flex-direction: column; gap: 8px; }
.seg-legend-row { display: grid; grid-template-columns: 1fr auto 48px; align-items: center; gap: 8px; font-size: 0.952rem; color: var(--ink-700); }
.seg-legend-row span { display: inline-flex; align-items: center; gap: 8px; }
.seg-legend-row i { font-size: 0.672rem; }
.seg-legend-row b { font-weight: 600; color: var(--ink-900); font-variant-numeric: tabular-nums; }
.seg-legend-row em { font-style: normal; color: var(--ink-500); text-align: right; font-variant-numeric: tabular-nums; }
""")
