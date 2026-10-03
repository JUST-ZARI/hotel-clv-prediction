import streamlit as st

import auth
from style import brand_lockup, icon, public_page_chrome

public_page_chrome()

st.html("""
<style>
/* Full-bleed sections with a 1120px content column */
.st-key-home_root { gap: 0 !important; }
.st-key-home_root > div { width: 100%; }
.st-key-home_nav, .st-key-home_hero {
    padding-left:  max(24px, calc((100% - 1120px) / 2)) !important;
    padding-right: max(24px, calc((100% - 1120px) / 2)) !important;
}
.home-inner { max-width: 1120px; margin: 0 auto; padding: 0 24px; }

/* ---------- Nav ---------- */
.st-key-home_nav {
    position: sticky; top: 0; z-index: 50;
    background: rgba(255,255,255,.92);
    backdrop-filter: saturate(180%) blur(8px);
    border-bottom: 1px solid var(--line);
    padding-top: 12px !important; padding-bottom: 12px !important;
    gap: 8px !important;
}
.st-key-home_nav button { min-height: 34px !important; font-size: 0.91rem !important; padding: 0 14px !important; }
.st-key-home_nav button[data-testid="stBaseButton-secondary"] {
    background: var(--brand-50) !important; border-color: var(--brand-50) !important; box-shadow: none !important;
}
.st-key-home_nav button[data-testid="stBaseButton-secondary"]:hover { border-color: var(--brand-200) !important; }

/* ---------- Hero ---------- */
.st-key-home_hero {
    background: linear-gradient(180deg, #FFFFFF 0%, #EDF4EF 100%);
    border-bottom: 1px solid var(--line);
    padding-top: 56px !important; padding-bottom: 56px !important;
}
.st-key-home_hero_left { gap: 0 !important; }
.hero-pill {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 5px 12px; margin-bottom: 20px;
    background: var(--surface); border: 1px solid var(--line); border-radius: 99px;
    font-size: 0.806rem; font-weight: 500; color: var(--ink-600);
    box-shadow: var(--shadow-xs);
}
.hero-pill .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--green-600); box-shadow: 0 0 0 3px var(--green-50); }
.hero-title {
    font-size: clamp(2rem, 3.4vw, 2.75rem) !important; line-height: 1.08 !important; font-weight: 800 !important;
    letter-spacing: 0 !important; color: var(--ink-900); margin: 0 0 18px !important; padding: 0 !important;
}
.hero-desc { font-size: 1.092rem; line-height: 1.65; color: var(--ink-500); max-width: 470px; margin-bottom: 26px; }
.st-key-home_hero_ctas { gap: 10px !important; }
.st-key-home_hero_ctas button { min-height: 42px !important; padding: 0 20px !important; }
.hero-trust {
    display: flex; flex-wrap: wrap; gap: 8px 22px;
    margin-top: 26px; padding-top: 18px; border-top: 1px solid var(--line);
    font-size: 0.84rem; font-weight: 500; color: var(--ink-500);
}
.hero-trust span { display: inline-flex; align-items: center; gap: 6px; }
.hero-trust i { color: var(--green-600); }

/* Product preview */
.pv { display: grid; grid-template-columns: 1.6fr 1fr; gap: 12px; }
.pv-card {
    background: var(--surface); border: 1px solid var(--line);
    border-radius: var(--r-lg); box-shadow: var(--shadow-card); padding: 16px;
}
.pv-main { grid-row: span 3; display: flex; flex-direction: column; }
.pv-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.pv-label { display: flex; align-items: center; gap: 8px; font-size: 0.806rem; font-weight: 500; color: var(--ink-500); }
.pv-ico {
    width: 22px; height: 22px; border-radius: 6px; display: inline-flex; align-items: center; justify-content: center;
    background: var(--brand-50); color: var(--brand-600); font-size: 0.728rem;
}
.pill { display: inline-flex; align-items: center; gap: 5px; padding: 2px 9px; border-radius: 99px; font-size: 0.762rem; font-weight: 600; }
.pill-green { background: var(--green-50); color: var(--green-700); border: 1px solid var(--green-200); }
.pill-green::before { content: ""; width: 5px; height: 5px; border-radius: 50%; background: currentColor; }
.pill-red   { background: var(--red-50); color: var(--red-600); border: 1px solid var(--red-200); }
.pill-amber { background: var(--amber-50); color: var(--amber-700); border: 1px solid var(--amber-200); }
.pv-value { font-size: 1.6rem; font-weight: 700; letter-spacing: 0; color: var(--ink-900); margin: 14px 0 2px; }
.pv-meta  { font-size: 0.784rem; color: var(--ink-400); }
.pv-bars { display: flex; align-items: flex-end; gap: 6px; height: 72px; margin: 18px 0 14px; }
.pv-bars span { flex: 1; border-radius: 3px 3px 0 0; background: var(--brand-100); }
.pv-bars span.on { background: var(--brand-600); }
.pv-foot { display: flex; justify-content: space-between; gap: 12px; font-size: 0.762rem; color: var(--ink-500); padding-top: 10px; border-top: 1px solid var(--line); }
.pv-foot b { color: var(--brand-600); font-weight: 600; }
.pv-flow {
    display: flex; align-items: center; justify-content: space-between; gap: 6px;
    margin-top: 12px; padding: 8px 10px; border: 1px solid var(--line); border-radius: var(--r-md);
    background: var(--subtle); font-size: 0.739rem; color: var(--ink-500);
}
.pv-flow i { font-size: 0.616rem; color: var(--ink-400); }
.pv-flow .cur { color: var(--brand-600); font-weight: 600; }
.pv-title { font-size: 1.064rem; font-weight: 700; color: var(--ink-900); margin-top: 8px; }
.pv-progress { display: flex; align-items: center; gap: 8px; margin-top: 10px; font-size: 0.739rem; color: var(--ink-500); }
.pv-progress .track { flex: 1; height: 4px; border-radius: 4px; background: var(--line); overflow: hidden; }
.pv-progress .track span { display: block; height: 100%; width: 24%; background: var(--brand-600); }
.pv-risk { border-color: var(--red-200); }
.pv-risk .pv-ico { background: var(--red-50); color: var(--red-600); }
.pv-desc { font-size: 0.784rem; line-height: 1.45; color: var(--ink-500); margin-top: 8px; }
.pv-action { background: linear-gradient(145deg, var(--brand-600), var(--brand-700)); border-color: var(--brand-700); color: #FFFFFF; }
.pv-action .pv-label { color: rgba(255,255,255,.8); }
.pv-action .pv-ico { background: rgba(184,242,138,.18); color: var(--lime-400); }
.pv-action .pv-title { color: #FFFFFF; }
.pv-action .pv-desc { color: rgba(255,255,255,.72); }
.pv-note { grid-column: 1 / -1; text-align: center; font-size: 0.762rem; color: var(--ink-400); margin-top: 4px; }

/* ---------- Sections ---------- */
.sec { padding: 64px 0; background: var(--surface); }
.sec-band { background: var(--canvas); border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.sec-eyebrow { text-align: center; font-size: 0.784rem; font-weight: 600; letter-spacing: .12em; text-transform: uppercase; color: var(--brand-600); margin-bottom: 8px; }
.sec-title, .cta-title { text-align: center; font-size: 1.6rem !important; font-weight: 700 !important; letter-spacing: 0 !important; color: var(--ink-900); padding: 0 !important; margin: 0 !important; }
.sec-desc { text-align: center; max-width: 520px; margin: 10px auto 0; font-size: 0.98rem; line-height: 1.6; color: var(--ink-500); }

.grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 36px; }
.feat {
    background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg);
    padding: 22px; box-shadow: var(--shadow-xs);
}
.tile {
    width: 34px; height: 34px; border-radius: 9px; display: inline-flex; align-items: center; justify-content: center;
    background: var(--brand-50); color: var(--brand-600); font-size: 0.952rem; border: 1px solid var(--brand-100);
}
.feat-title { font-size: 1.064rem; font-weight: 600; color: var(--ink-900); margin: 16px 0 6px; }
.feat-desc  { font-size: 0.91rem; line-height: 1.6; color: var(--ink-500); }

.steps { display: grid; grid-template-columns: 1fr 28px 1fr 28px 1fr; align-items: stretch; gap: 8px; margin-top: 36px; }
.step { position: relative; }
.step-num { position: absolute; top: 22px; right: 22px; font-size: 0.806rem; font-weight: 600; color: var(--ink-400); font-variant-numeric: tabular-nums; }
.step-arrow { align-self: center; text-align: center; color: var(--brand-600); font-size: 0.896rem; }

.flow { max-width: 440px; margin: 36px auto 0; display: flex; flex-direction: column; align-items: stretch; }
.flow-row {
    display: flex; align-items: center; gap: 14px;
    padding: 14px 16px; background: var(--surface);
    border: 1px solid var(--line); border-radius: var(--r-lg); box-shadow: var(--shadow-xs);
}
.flow-row .tile { flex-shrink: 0; }
.flow-row .t { font-size: 0.91rem; font-weight: 600; color: var(--ink-900); }
.flow-row .s { font-size: 0.806rem; color: var(--ink-500); margin-top: 2px; }
.flow-row .pill { margin-left: auto; }
.flow-join { text-align: center; color: var(--ink-400); font-size: 0.672rem; padding: 6px 0; }
.tile-green { background: var(--green-50); color: var(--green-600); border-color: var(--green-200); }
.tile-red   { background: var(--red-50);   color: var(--red-600);   border-color: var(--red-200); }
.tile-amber { background: var(--amber-50); color: var(--amber-600); border-color: var(--amber-200); }
.flow-note { text-align: center; font-size: 0.806rem; color: var(--ink-400); margin-top: 18px; }

/* ---------- CTA ---------- */
.st-key-home_cta_wrap { padding: 8px 24px 64px !important; background: var(--surface); }
.st-key-home_cta {
    width: 100%; max-width: 1072px; margin: 0 auto;
    padding: 48px 24px !important; gap: 0 !important;
    border: 1px solid var(--brand-100); border-radius: var(--r-xl);
    background: linear-gradient(180deg, #F6FAF4 0%, #DFEDE4 100%);
}
.cta-desc  { text-align: center; max-width: 520px; margin: 10px auto 24px; font-size: 0.98rem; line-height: 1.6; color: var(--ink-500); }
.st-key-home_cta_btns { gap: 10px !important; }
.st-key-home_cta_btns button { min-height: 40px !important; padding: 0 20px !important; }
.cta-note { text-align: center; margin-top: 18px; font-size: 0.806rem; color: var(--ink-400); }

/* ---------- Footer ---------- */
.foot { border-top: 1px solid var(--line); background: var(--surface); }
.foot .home-inner { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding-top: 20px; padding-bottom: 24px; }
.foot .ds-brand-mark { width: 26px; height: 26px; border-radius: 7px; font-size: 0.806rem; box-shadow: none; }
.foot .ds-brand-name { font-size: 0.91rem; }
.foot-meta { font-size: 0.806rem; color: var(--ink-400); }

/* ---------- Responsive ---------- */
@media (max-width: 900px) {
    .grid3 { grid-template-columns: 1fr; }
    .steps { grid-template-columns: 1fr; }
    .step-arrow { transform: rotate(90deg); }
    .pv { grid-template-columns: 1fr; }
    .pv-main { grid-row: auto; }
}
@media (max-width: 640px) {
    .st-key-home_nav .ds-brand-sub { display: none; }
    .st-key-home_hero { padding-top: 36px !important; padding-bottom: 36px !important; }
    .sec { padding: 48px 0; }
    .foot .home-inner { flex-direction: column; text-align: center; }
}
</style>
""")


def _to_login():
    st.switch_page(auth.LOGIN_PAGE)


def _to_signup():
    st.switch_page(auth.SIGNUP_PAGE)


with st.container(key="home_root"):

    # ------------------------------------------------------------------
    # Nav
    # ------------------------------------------------------------------
    with st.container(key="home_nav", horizontal=True, vertical_alignment="center"):
        st.html(brand_lockup())
        st.space("stretch")
        if st.button("Login", key="nav_signin"):
            _to_login()
        if st.button("Create Account", key="nav_signup", type="primary"):
            _to_signup()

    # ------------------------------------------------------------------
    # Hero
    # ------------------------------------------------------------------
    with st.container(key="home_hero"):
        left, right = st.columns([1, 1.05], gap="large", vertical_alignment="center")

        with left, st.container(key="home_hero_left"):
            st.html("""
            <div class="hero-pill"><span class="dot"></span>
                Customer Lifetime Value Prediction for Strategic Revenue Management in Hotels</div>
            <h1 class="hero-title">Turn Guest Booking Data Into Customer Lifetime Value Insights</h1>
            <p class="hero-desc">Use historical hotel booking behaviour and machine-learning predictions
                to identify high-value guests, recognise at-risk guests, and support targeted
                retention decisions.</p>
            """)
            with st.container(key="home_hero_ctas", horizontal=True):
                if st.button("Get Started", key="hero_signup", type="primary"):
                    _to_signup()
                if st.button("Login", key="hero_signin"):
                    _to_login()
            st.html(f"""
            <div class="hero-trust">
                <span>{icon("circle-check")} Random Forest</span>
                <span>{icon("circle-check")} XGBoost</span>
                <span>{icon("circle-check")} Built for Revenue &amp; Marketing teams</span>
            </div>
            """)

        with right:
            bars = [22, 30, 26, 38, 34, 44, 40, 62, 56, 70, 64, 72]
            bar_html = "".join(
                f'<span class="{"on" if i >= 7 else ""}" style="height:{h}px"></span>'
                for i, h in enumerate(bars)
            )
            st.html(f"""
            <div class="pv">
                <div class="pv-card pv-main">
                    <div class="pv-head">
                        <span class="pv-label"><span class="pv-ico">{icon("wallet")}</span>Predicted CLV</span>
                        <span class="pill pill-green">High Value</span>
                    </div>
                    <div class="pv-value">KES 125,400</div>
                    <div class="pv-meta">Guest #H-0482 · Stay history: 11 nights</div>
                    <div class="pv-bars">{bar_html}</div>
                    <div class="pv-foot"><span>Random Forest · XGBoost ensemble</span><b>+12.4% vs. segment avg</b></div>
                    <div class="pv-flow">
                        <span>Booking Data</span>{icon("arrow-right")}
                        <span class="cur">CLV Prediction</span>{icon("arrow-right")}
                        <span>Segmentation</span>{icon("arrow-right")}
                        <span>Action</span>
                    </div>
                </div>
                <div class="pv-card">
                    <span class="pv-label"><span class="pv-ico">{icon("users")}</span>Guest Segment</span>
                    <div class="pv-title">High CLV</div>
                    <div class="pv-progress"><span class="track"><span></span></span>24% of guests</div>
                </div>
                <div class="pv-card pv-risk">
                    <div class="pv-head">
                        <span class="pv-label"><span class="pv-ico">{icon("shield-halved")}</span>At-Risk Guests</span>
                        <span class="pill pill-red">18</span>
                    </div>
                    <div class="pv-desc">High-value guests requiring attention</div>
                </div>
                <div class="pv-card pv-action">
                    <span class="pv-label"><span class="pv-ico">{icon("wand-magic-sparkles")}</span>Recommended Action</span>
                    <div class="pv-title">Retention Offer</div>
                    <div class="pv-desc">Model Performance · RF + XGBoost</div>
                </div>
                
            """)

    # ------------------------------------------------------------------
    # Core capabilities
    # ------------------------------------------------------------------
    st.html(f"""
    <section class="sec"><div class="home-inner">
        <div class="sec-eyebrow">Core capabilities</div>
        <h2 class="sec-title">Everything you need to act on guest value</h2>
        <div class="grid3">
            <div class="feat">
                <span class="tile">{icon("chart-line")}</span>
                <div class="feat-title">Predict Guest Value</div>
                <div class="feat-desc">Estimate Customer Lifetime Value using historical booking behaviour and machine-learning models.</div>
            </div>
            <div class="feat">
                <span class="tile">{icon("users")}</span>
                <div class="feat-title">Identify Guest Segments</div>
                <div class="feat-desc">Classify guests into CLV tiers and identify high-value guests who may require retention attention.</div>
            </div>
            <div class="feat">
                <span class="tile">{icon("bullseye")}</span>
                <div class="feat-title">Support Targeted Actions</div>
                <div class="feat-desc">Use CLV, risk indicators and recommended actions to support informed guest engagement decisions.</div>
            </div>
        </div>
    </div></section>
    """)

    # ------------------------------------------------------------------
    # How it works
    # ------------------------------------------------------------------
    st.html(f"""
    <section class="sec sec-band"><div class="home-inner">
        <h2 class="sec-title">How It Works</h2>
        <p class="sec-desc">From harmonised booking data to review-ready recommendations.</p>
        <div class="steps">
            <div class="feat step">
                <span class="tile">{icon("database")}</span><span class="step-num">01</span>
                <div class="feat-title">Historical Booking Data</div>
                <div class="feat-desc">Two public hotel booking datasets are harmonised and prepared for analysis.</div>
            </div>
            <div class="step-arrow">{icon("arrow-right")}</div>
            <div class="feat step">
                <span class="tile">{icon("microchip")}</span><span class="step-num">02</span>
                <div class="feat-title">CLV Prediction</div>
                <div class="feat-desc">Random Forest and XGBoost models generate guest-level CLV predictions.</div>
            </div>
            <div class="step-arrow">{icon("arrow-right")}</div>
            <div class="feat step">
                <span class="tile">{icon("compass")}</span><span class="step-num">03</span>
                <div class="feat-title">Decision Support</div>
                <div class="feat-desc">Predictions, guest segments, risk indicators and recommended actions support hotel decision-making.</div>
            </div>
        </div>
    </div></section>
    """)

    # ------------------------------------------------------------------
    # Decision support flow
    # ------------------------------------------------------------------
    flow = [
        ("calendar-days", "", "Guest Booking Behaviour", "Stays · lead time · cancellations", ""),
        ("microchip", "", "CLV Prediction", "RF + XGBoost regression", ""),
        ("layer-group", "tile-green", "CLV Tier", "High · Medium · Low value", ""),
        ("flag", "tile-red", "Risk Indicator", "At-risk high-value guests", ""),
        ("bullhorn", "tile-amber", "Recommended Action", "Retention offer for review",
         '<span class="pill pill-amber">Review</span>'),
    ]
    join = f'<div class="flow-join">{icon("chevron-down")}</div>'
    rows = join.join(
        f'<div class="flow-row"><span class="tile {tone}">{icon(ic)}</span>'
        f'<div><div class="t">{t}</div><div class="s">{s}</div></div>{extra}</div>'
        for ic, tone, t, s, extra in flow
    )
    st.html(f"""
    <section class="sec"><div class="home-inner">
        <div class="sec-eyebrow">Decision support</div>
        <h2 class="sec-title">From prediction to informed action</h2>
        <p class="sec-desc">The system surfaces predictions and risk signals — hotel teams stay in control of every guest decision.</p>
        <div class="flow">{rows}</div>
        <p class="flow-note">Supports informed decision-making — managers review every recommendation.</p>
    </div></section>
    """)

    # ------------------------------------------------------------------
    # CTA
    # ------------------------------------------------------------------
    with st.container(key="home_cta_wrap"):
        with st.container(key="home_cta"):
            st.html("""
            <h2 class="cta-title">Ready to explore guest value?</h2>
            <p class="cta-desc">Access the Hotel CLV Decision Support System to explore predicted guest value,
                segments, risk indicators and recommended actions.</p>
            """)
            with st.container(key="home_cta_btns", horizontal=True, horizontal_alignment="center"):
                if st.button("Create Account", key="cta_signup", type="primary"):
                    _to_signup()
                if st.button("Sign In", key="cta_signin"):
                    _to_login()
            

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------
    st.html(f"""
    <footer class="foot"><div class="home-inner">
        <div class="ds-brand"><span class="ds-brand-mark">{icon("hotel")}</span><span class="ds-brand-name">Hotel CLV</span></div>
        <div class="foot-meta">· Hotel CLV Decision Support System</div>
    </div></footer>
    """)
