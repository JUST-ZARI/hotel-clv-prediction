import streamlit as st

import auth
from style import PHOTO_LOBBY, PHOTO_ROOM, brand_lockup, icon, public_page_chrome

public_page_chrome()

# Figures shown on this public page come from the latest prediction run (notebook 08).
# They are static here because signed-out visitors cannot read the database.
SAMPLE = {
    "guest": "G-076704", "clv": "KSh 4,670,546", "stays": 46,
    "total": "121,454", "high_share": 25, "at_risk": "29,597", "r2": "0.835",
    "drivers": [("Previous stays", 62), ("Length of stay", 20), ("Week nights", 10)],
}

st.html("""
<style>
/* Full-bleed sections with a 1200px content column */
.st-key-home_root { gap: 0 !important; zoom: .9; }
.st-key-home_root > div { width: 100%; }
.st-key-home_nav, .st-key-home_hero {
    padding-left:  max(24px, calc((100% - 1160px) / 2)) !important;
    padding-right: max(24px, calc((100% - 1160px) / 2)) !important;
}
.home-inner { max-width: 1160px; margin: 0 auto; padding: 0 24px; }

/* ---------- Nav ---------- */
.st-key-home_nav {
    position: sticky; top: 0; z-index: 50;
    background: rgba(255,255,255,.9);
    backdrop-filter: saturate(180%) blur(10px);
    border-bottom: 1px solid var(--line);
    padding-top: 14px !important; padding-bottom: 14px !important;
    gap: 10px !important;
}
.st-key-home_nav .ds-brand-name { font-size: 1.35rem; color: var(--brand-700); }
.st-key-home_nav button { min-height: 38px !important; padding: 0 18px !important; }

/* ---------- Hero ---------- */
.st-key-home_hero { padding-top: 28px !important; padding-bottom: 28px !important; }
.st-key-home_hero > div { gap: 24px !important; }
.st-key-home_hero_left {
    position: relative; overflow: hidden; border-radius: 20px; min-height: 420px; justify-content: center;
    padding: 40px 44px !important; gap: 0 !important;
    background:
        linear-gradient(90deg, rgba(0,46,32,.96) 0%, rgba(0,63,43,.86) 42%, rgba(0,63,43,.25) 78%, rgba(0,63,43,.05) 100%),
        var(--room-img) center / cover no-repeat, var(--brand-700);
    box-shadow: var(--shadow-pop);
    animation: hero-in 1s var(--ease) both;
}
@keyframes hero-in { from { opacity: 0; transform: scale(.985); } to { opacity: 1; transform: none; } }
.hero-pill {
    display: inline-flex; align-items: center; gap: 8px; width: fit-content;
    padding: 6px 14px; margin-bottom: 22px;
    background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.22); border-radius: 99px;
    font-size: 0.92rem; color: #FFFFFF; backdrop-filter: blur(6px);
}
.hero-pill i { color: var(--mint-300); }
.hero-title {
    font-size: clamp(2.2rem, 3.6vw, 3rem) !important; line-height: 1.04 !important; font-weight: 700 !important;
    color: #FFFFFF !important; margin: 0 0 18px !important; padding: 0 !important; text-shadow: 0 2px 18px rgba(0,0,0,.25);
}
.hero-title span { display: block; color: var(--mint-300); }
.hero-desc { font-size: 1.08rem; line-height: 1.55; color: rgba(255,255,255,.92); max-width: 500px; margin-bottom: 28px; }
.st-key-home_hero_ctas { gap: 12px !important; }
.st-key-home_hero_ctas button { min-height: 44px !important; padding: 0 22px !important; border-radius: 99px !important; }
.st-key-home_hero_ctas button p { font-size: 1.05rem !important; }
.stApp .st-key-home_hero_ctas button[data-testid="stBaseButton-secondary"] {
    background: rgba(255,255,255,.08) !important; border-color: rgba(255,255,255,.4) !important;
}
.stApp .st-key-home_hero_ctas button[data-testid="stBaseButton-secondary"] p { color: #FFFFFF !important; }
.stApp .st-key-home_hero_ctas button[data-testid="stBaseButton-secondary"]:hover { background: rgba(255,255,255,.18) !important; }
.stApp .st-key-home_hero_ctas button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(180deg, #2E9273, #1E7A60) !important; border-color: #2E9273 !important;
}

/* Product preview (real figures from the latest run) */
.pv { display: grid; grid-template-columns: 1.25fr 1fr; gap: 14px; height: 100%; }
.pv-card {
    background: var(--surface); border: 1px solid var(--line);
    border-radius: var(--r-lg); box-shadow: var(--shadow-card); padding: 18px;
    transition: transform .3s var(--ease), box-shadow .3s var(--ease);
    animation: ds-rise .6s var(--ease) both;
}
.pv-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-pop); }
.pv-card:nth-child(2) { animation-delay: .1s; } .pv-card:nth-child(3) { animation-delay: .2s; } .pv-card:nth-child(4) { animation-delay: .3s; }
.pv-main { grid-row: span 3; display: flex; flex-direction: column; }
.pv-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.pv-label { display: flex; align-items: center; gap: 8px; font-size: 0.98rem; color: var(--ink-700); }
.pv-ico {
    width: 30px; height: 30px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center;
    background: var(--brand-50); color: var(--brand-600); font-size: 0.85rem;
}
.pill { display: inline-flex; align-items: center; gap: 5px; padding: 3px 11px; border-radius: 99px; font-size: 0.85rem; font-weight: 700; }
.pill-green { background: var(--brand-50); color: var(--brand-600); }
.pill-green::before { content: "◆"; font-size: .6rem; }
.pill-red   { background: var(--red-50); color: var(--red-600); }
.pill-amber { background: var(--amber-50); color: var(--amber-700); border: 1px solid var(--amber-200); }
.pv-value { font-size: 1.7rem; font-weight: 700; color: var(--ink-900); margin: 16px 0 2px; }
.pv-meta  { font-size: 0.9rem; color: var(--ink-500); }
.pv-bars { display: flex; align-items: flex-end; gap: 6px; height: 80px; margin: 16px 0 12px; }
.pv-bars span { flex: 1; border-radius: 3px 3px 0 0; background: var(--brand-100); transform-origin: bottom; animation: bar-up .8s var(--ease) both; }
.pv-bars span.on { background: var(--brand-600); }
.pv-bars span.hi { background: var(--brand-700); }
@keyframes bar-up { from { transform: scaleY(0); } to { transform: scaleY(1); } }
.pv-foot { display: flex; justify-content: space-between; gap: 12px; font-size: 0.88rem; color: var(--ink-500); padding-top: 10px; border-top: 1px solid var(--line); }
.pv-foot b { color: var(--brand-600); }
.pv-flow {
    display: flex; align-items: center; justify-content: space-between; gap: 6px;
    margin-top: auto; padding: 10px 12px; border: 1px solid var(--line); border-radius: var(--r-md);
    background: var(--subtle); font-size: 0.85rem; color: var(--ink-500);
}
.pv-flow i { font-size: 0.65rem; color: var(--ink-400); }
.pv-flow .cur { color: var(--brand-600); font-weight: 700; }
.pv-title { font-size: 1.15rem; font-weight: 700; color: var(--ink-900); margin-top: 10px; }
.pv-progress { display: flex; align-items: center; gap: 10px; margin-top: 12px; font-size: 0.88rem; color: var(--ink-500); }
.pv-progress .track { flex: 1; height: 6px; border-radius: 6px; background: var(--line); overflow: hidden; }
.pv-progress .track span { display: block; height: 100%; background: var(--brand-600); border-radius: 6px; animation: grow 1.2s var(--ease) both; }
@keyframes grow { from { width: 0; } }
.pv-risk .pv-ico { background: var(--red-50); color: var(--red-600); }
.pv-desc { font-size: 0.92rem; line-height: 1.45; color: var(--ink-500); margin-top: 10px; }
.pv-action { background: linear-gradient(150deg, var(--brand-600), var(--brand-700)); border-color: var(--brand-700); color: #FFFFFF; }
.pv-action .pv-label { color: rgba(255,255,255,.85); }
.pv-action .pv-ico { background: rgba(255,255,255,.12); color: var(--mint-300); }
.pv-action .pv-title { color: #FFFFFF; }
.pv-action .pv-desc { color: rgba(255,255,255,.75); }

/* ---------- Feature strip ---------- */
.feats {
    display: grid; grid-template-columns: repeat(4, 1fr);
    background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg); box-shadow: var(--shadow-xs);
    margin-top: 4px;
}
.feats > div { padding: 20px 24px; border-left: 1px solid var(--line); transition: background-color .25s var(--ease); }
.feats > div:first-child { border-left: none; }
.feats > div:hover { background: var(--subtle); }
.feats .ico {
    width: 44px; height: 44px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
    background: linear-gradient(160deg, var(--brand-500), var(--brand-700)); color: #FFFFFF; font-size: 1.1rem;
    transition: transform .3s var(--ease);
}
.feats > div:hover .ico { transform: translateY(-3px); }
.feats .t { font-size: 1.1rem; font-weight: 700; color: var(--ink-900); margin: 14px 0 6px; }
.feats .d { font-size: 0.92rem; line-height: 1.5; color: var(--ink-500); }
.home-loc { display: flex; justify-content: flex-end; gap: 14px; align-items: center; margin: 14px 0 0; font-size: 0.92rem; color: var(--ink-500); }
.home-loc i { color: var(--brand-600); }
.home-loc b { width: 1px; height: 14px; background: var(--line-strong); }

/* ---------- Sections ---------- */
.sec { padding: 56px 0; background: var(--surface); }
.sec-band { background: var(--canvas); border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.sec-eyebrow { text-align: center; font-size: 0.85rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: var(--brand-600); margin-bottom: 8px; }
.sec-title, .cta-title { text-align: center; font-size: 1.8rem !important; font-weight: 700 !important; color: var(--brand-700) !important; padding: 0 !important; margin: 0 !important; }
.sec-desc { text-align: center; max-width: 560px; margin: 10px auto 0; font-size: 1.08rem; line-height: 1.6; color: var(--ink-500); }

.feat {
    background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg);
    padding: 24px; box-shadow: var(--shadow-xs); transition: transform .3s var(--ease), box-shadow .3s var(--ease);
}
.feat:hover { transform: translateY(-3px); box-shadow: var(--shadow-card); }
.tile {
    width: 42px; height: 42px; border-radius: 12px; display: inline-flex; align-items: center; justify-content: center;
    background: var(--brand-50); color: var(--brand-600); font-size: 1rem;
}
.feat-title { font-size: 1.2rem; font-weight: 700; color: var(--ink-900); margin: 16px 0 6px; }
.feat-desc  { font-size: 1rem; line-height: 1.55; color: var(--ink-500); }

.steps { display: grid; grid-template-columns: 1fr 28px 1fr 28px 1fr; align-items: stretch; gap: 8px; margin-top: 36px; }
.step { position: relative; }
.step-num { position: absolute; top: 24px; right: 24px; font-size: 0.95rem; font-weight: 700; color: var(--brand-300); }
.step-arrow { align-self: center; text-align: center; color: var(--brand-600); font-size: 0.95rem; }

.flow { max-width: 480px; margin: 36px auto 0; display: flex; flex-direction: column; align-items: stretch; }
.flow-row {
    display: flex; align-items: center; gap: 14px;
    padding: 14px 16px; background: var(--surface);
    border: 1px solid var(--line); border-radius: var(--r-lg); box-shadow: var(--shadow-xs);
    transition: transform .25s var(--ease), border-color .25s var(--ease);
}
.flow-row:hover { transform: translateX(4px); border-color: var(--brand-200); }
.flow-row .tile { flex-shrink: 0; }
.flow-row .t { font-size: 1.05rem; font-weight: 700; color: var(--ink-900); }
.flow-row .s { font-size: 0.92rem; color: var(--ink-500); margin-top: 2px; }
.flow-row .pill { margin-left: auto; }
.flow-join { text-align: center; color: var(--ink-400); font-size: 0.7rem; padding: 6px 0; }
.tile-green { background: var(--sage-50); color: var(--sage-700); }
.tile-red   { background: var(--red-50);   color: var(--red-600); }
.tile-amber { background: var(--amber-50); color: var(--amber-600); }
.flow-note { text-align: center; font-size: 0.92rem; color: var(--ink-500); margin-top: 18px; }


.pv-drv-k { margin-top: 14px; font-size: 0.85rem; font-weight: 700; color: var(--ink-700); }
.pv-drv { display: flex; flex-direction: column; gap: 8px; margin: 8px 0 14px; }
.pv-drv > div { display: grid; grid-template-columns: 110px 1fr 52px; align-items: center; gap: 10px; font-size: 0.85rem; color: var(--ink-600); }
.pv-drv em { height: 6px; border-radius: 6px; background: var(--brand-50); overflow: hidden; }
.pv-drv em i { display: block; height: 100%; border-radius: 6px; background: linear-gradient(90deg, var(--brand-500), var(--brand-700)); animation: grow 1s var(--ease) both; }
.pv-drv b { text-align: right; color: var(--brand-600); font-size: 0.82rem; }

/* ---------- Decision support: lobby photo + step list ---------- */
.ds-sec { padding: 56px 0; background: var(--surface); }
.ds-grid { display: grid; grid-template-columns: 0.8fr 1.6fr; gap: 40px; align-items: stretch; }
.ds-photo {
    position: relative; border-radius: 20px; overflow: hidden; min-height: 520px;
    background: linear-gradient(180deg, rgba(0,63,43,0) 55%, rgba(0,63,43,.85) 100%), var(--lobby-img) center / cover no-repeat;
    box-shadow: var(--shadow-card);
}
.ds-photo-cap { position: absolute; left: 24px; right: 24px; bottom: 22px; color: #FFFFFF; }
.ds-photo-cap b { display: block; font-size: 1.35rem; line-height: 1.2; }
.ds-photo-cap span { font-size: 0.95rem; color: rgba(255,255,255,.85); }
.ds-chip-eyebrow {
    display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 99px;
    background: var(--brand-50); color: var(--brand-700); font-size: 0.85rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
}
.ds-chip-eyebrow i { color: var(--brand-600); }
.ds-head-t { margin: 14px 0 8px !important; padding: 0 !important; font-size: 2.3rem !important; line-height: 1.1 !important; color: var(--brand-700) !important; }
.ds-head-d { max-width: 600px; font-size: 1.05rem; line-height: 1.55; color: var(--ink-500); margin-bottom: 22px; }
.ds-steps { display: flex; flex-direction: column; gap: 12px; }
.ds-step {
    display: flex; align-items: center; gap: 18px;
    padding: 16px 20px; background: var(--surface);
    border: 1px solid var(--line); border-left: 4px solid var(--brand-600); border-radius: var(--r-lg);
    box-shadow: var(--shadow-xs);
    transition: transform .25s var(--ease), box-shadow .25s var(--ease), border-color .25s var(--ease);
}
.ds-step:hover { transform: translateX(4px); box-shadow: var(--shadow-card); border-color: var(--brand-200); border-left-color: var(--brand-600); }
.ds-step-ico {
    width: 52px; height: 52px; flex-shrink: 0; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center;
    background: var(--brand-50); color: var(--brand-600); font-size: 1.25rem;
}
.ds-step-t { font-size: 1.2rem; font-weight: 700; color: var(--brand-700); }
.ds-step-d { margin-top: 3px; font-size: 0.95rem; color: var(--ink-500); }
.ds-step-go {
    margin-left: auto; flex-shrink: 0; width: 36px; height: 36px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
    background: var(--brand-50); color: var(--brand-600); transition: background-color .25s var(--ease), color .25s var(--ease), transform .25s var(--ease);
}
.ds-step:hover .ds-step-go { background: var(--brand-600); color: #FFFFFF; transform: translateX(2px); }
.ds-step-pill {
    margin-left: auto; flex-shrink: 0; display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 99px;
    background: var(--brand-50); color: var(--brand-700); font-weight: 700; font-size: 0.92rem;
}
.ds-tip {
    display: flex; align-items: center; gap: 14px; margin-top: 14px; padding: 14px 18px;
    border-radius: var(--r-lg); background: var(--brand-50); color: var(--ink-600); font-size: 0.95rem;
}
.ds-tip i { color: var(--brand-600); font-size: 1.1rem; padding-right: 14px; border-right: 1px solid var(--brand-200); }
@media (max-width: 900px) {
    .ds-grid { grid-template-columns: 1fr; }
    .ds-photo { min-height: 260px; }
}

/* ---------- CTA ---------- */
.st-key-home_cta_wrap { padding: 8px 24px 72px !important; background: var(--surface); }
.st-key-home_cta {
    width: 100%; max-width: 1152px; margin: 0 auto;
    padding: 56px 24px !important; gap: 0 !important; border-radius: var(--r-xl);
    background:
        linear-gradient(90deg, rgba(0,46,32,.94), rgba(0,63,43,.80)),
        var(--room-img) center / cover no-repeat;
}
.st-key-home_cta .cta-title { color: #FFFFFF !important; }
.cta-desc  { text-align: center; max-width: 560px; margin: 10px auto 26px; font-size: 1.08rem; line-height: 1.6; color: rgba(255,255,255,.85); }
.st-key-home_cta_btns { gap: 12px !important; }
.st-key-home_cta_btns button { min-height: 44px !important; padding: 0 24px !important; border-radius: 99px !important; }

/* ---------- Footer ---------- */
.foot { border-top: 1px solid var(--line); background: var(--surface); }
.foot .home-inner { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding-top: 20px; padding-bottom: 24px; }
.foot-meta { font-size: 0.92rem; color: var(--ink-500); }

/* ---------- Responsive ---------- */
@media (max-width: 1000px) {
    .feats { grid-template-columns: repeat(2, 1fr); }
    .feats > div:nth-child(3) { border-left: none; }
    .feats > div:nth-child(n+3) { border-top: 1px solid var(--line); }
}
@media (max-width: 900px) {
    .steps { grid-template-columns: 1fr; }
    .step-arrow { transform: rotate(90deg); }
    .pv { grid-template-columns: 1fr; }
    .pv-main { grid-row: auto; }
    .st-key-home_hero_left { padding: 32px 26px !important; min-height: 0; }
}
@media (max-width: 640px) {
    .st-key-home_nav .ds-brand-sub { display: none; }
    .st-key-home_nav { flex-wrap: nowrap !important; gap: 6px !important; }
    .st-key-home_nav .ds-brand-name { white-space: nowrap; font-size: 1.15rem; }
    .st-key-home_nav .ds-brand-mark { width: 32px; height: 32px; }
    .st-key-home_nav button { min-height: 34px !important; padding: 0 10px !important; }
    .st-key-home_nav button p { font-size: 0.85rem !important; }
    .st-key-home_hero_left { padding: 28px 22px !important; border-radius: 16px; }
    .hero-desc { font-size: 1rem; }
    .ds-head-t { font-size: 1.8rem !important; }
    .ds-step { padding: 12px 14px; gap: 12px; }
    .ds-step-ico { width: 42px; height: 42px; font-size: 1rem; }
    .ds-step-go { display: none; }
    .ds-step-t { font-size: 1.08rem; }
    .feats { grid-template-columns: 1fr; }
    .feats > div { border-left: none !important; border-top: 1px solid var(--line); }
    .feats > div:first-child { border-top: none; }
    .sec { padding: 52px 0; }
    .foot .home-inner { flex-direction: column; text-align: center; }
    .home-loc { justify-content: flex-start; flex-wrap: wrap; }
}
</style>
""")
st.html(f"<style>:root {{ --room-img: url('{PHOTO_ROOM}'); --lobby-img: url('{PHOTO_LOBBY}'); }}</style>")


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
    # Hero: photo panel + preview cards, then the feature strip
    # ------------------------------------------------------------------
    with st.container(key="home_hero"):
        left, right = st.columns([1.55, 1], gap="medium", vertical_alignment="center")

        with left, st.container(key="home_hero_left"):
            st.html(f"""
            <div class="hero-pill">{icon("chart-line")} Data-Driven Hospitality Revenue</div>
            <h1 class="hero-title">Smarter Decisions.<span>Higher Revenue.</span></h1>
            <p class="hero-desc">Turn guest booking data into actionable insights with Customer
                Lifetime Value prediction for hotels.</p>
            """)
            with st.container(key="home_hero_ctas", horizontal=True):
                if st.button("Get Started", key="hero_signup", type="primary", icon=":material/arrow_forward:"):
                    _to_signup()
                if st.button("Login", key="hero_signin"):
                    _to_login()

        with right:
            bars = [18, 24, 22, 32, 38, 36, 46, 52, 64, 76, 70, 88]
            bar_html = "".join(
                f'<span class="{"hi" if i in (9, 11) else "on" if i >= 7 else ""}" '
                f'style="height:{h}px; animation-delay:{i * 40}ms"></span>'
                for i, h in enumerate(bars)
            )
            s = SAMPLE
            drivers = "".join(
                f'<div><span>{n}</span><em><i style="width:{v}%; animation-delay:{k * 120}ms"></i></em><b>▲ {v}%</b></div>'
                for k, (n, v) in enumerate(s["drivers"]))
            st.html(f"""
            <div class="pv">
                <div class="pv-card pv-main">
                    <div class="pv-head">
                        <span class="pv-label"><span class="pv-ico">{icon("wallet")}</span>Predicted CLV</span>
                        <span class="pill pill-green">Platinum</span>
                    </div>
                    <div class="pv-value">{s["clv"]}</div>
                    <div class="pv-meta">Guest {s["guest"]} · {s["stays"]} previous stays</div>
                    <div class="pv-bars">{bar_html}</div>
                    <div class="pv-foot"><span>XGBoost model</span><b>R² {s["r2"]} on test data</b></div>
                    <div class="pv-drv-k">Top prediction drivers</div>
                    <div class="pv-drv">{drivers}</div>
                    <div class="pv-flow">
                        <span>Booking data</span>{icon("arrow-right")}
                        <span class="cur">CLV</span>{icon("arrow-right")}
                        <span>Segment</span>{icon("arrow-right")}
                        <span>Action</span>
                    </div>
                </div>
                <div class="pv-card">
                    <span class="pv-label"><span class="pv-ico">{icon("users")}</span>Guest Segment</span>
                    <div class="pv-title">High CLV</div>
                    <div class="pv-progress"><span class="track"><span style="width:{s["high_share"]}%"></span></span>{s["high_share"]}% of guests</div>
                </div>
                <div class="pv-card pv-risk">
                    <div class="pv-head">
                        <span class="pv-label"><span class="pv-ico">{icon("shield-halved")}</span>At-Risk Guests</span>
                        <span class="pill pill-red">{s["at_risk"]}</span>
                    </div>
                    <div class="pv-desc">High-value guests inactive for 60+ days</div>
                </div>
                <div class="pv-card pv-action">
                    <span class="pv-label"><span class="pv-ico">{icon("bolt")}</span>Recommended Action</span>
                    <div class="pv-title">Personal call from manager</div>
                    <div class="pv-desc">Reviewed by the Revenue Manager</div>
                </div>
            </div>
            """)

        st.html(f"""
        <div class="feats">
            <div><span class="ico">{icon("chart-column")}</span><div class="t">Predict CLV</div>
                 <div class="d">Identify high-value guests and future revenue potential.</div></div>
            <div><span class="ico">{icon("users")}</span><div class="t">Segment Guests</div>
                 <div class="d">Understand behaviour and tailor your strategies.</div></div>
            <div><span class="ico">{icon("bullseye")}</span><div class="t">Take Action</div>
                 <div class="d">Get recommended actions for better revenue management.</div></div>
            <div><span class="ico">{icon("arrow-trend-up")}</span><div class="t">Drive Growth</div>
                 <div class="d">Build lasting guest relationships and retain valuable guests.</div></div>
        </div>
        """)

    # ------------------------------------------------------------------
    # How it works
    # ------------------------------------------------------------------
    st.html(f"""
    <section class="sec sec-band"><div class="home-inner">
        <div class="sec-eyebrow">How it works</div>
        <h2 class="sec-title">From booking history to guest decisions</h2>
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
                <div class="feat-desc">Random Forest and XGBoost were compared; XGBoost predicts each guest's CLV.</div>
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
    # Decision support: lobby photo + the steps from data to action
    # ------------------------------------------------------------------
    steps = [
        ("calendar-days", "Guest Booking Behaviour", "Understand booking patterns, lead time and cancellation trends."),
        ("chart-column", "CLV Prediction", "Use machine learning to forecast each guest's lifetime value."),
        ("users", "CLV Tier", "Segment guests into High, Medium and Low value for targeted strategy."),
        ("triangle-exclamation", "Risk Indicator", "Identify at-risk high-value guests who need re-engagement."),
    ]
    go = f'<span class="ds-step-go">{icon("arrow-right")}</span>'
    items = "".join(
        f'<div class="ds-step"><span class="ds-step-ico">{icon(ic)}</span>'
        f'<div><div class="ds-step-t">{t}</div><div class="ds-step-d">{d}</div></div>{go}</div>'
        for ic, t, d in steps
    )
    items += (f'<div class="ds-step"><span class="ds-step-ico">{icon("bullhorn")}</span>'
              f'<div><div class="ds-step-t">Recommended Action</div>'
              f'<div class="ds-step-d">Get personalised retention and marketing actions for better results.</div></div>'
              f'<span class="ds-step-pill">Review {icon("arrow-right")}</span></div>')
    st.html(f"""
    <section class="ds-sec"><div class="home-inner ds-grid">
        <div class="ds-photo">
            <div class="ds-photo-cap"><b>Better guests.<br>Higher revenue.</b><span>Every recommendation is reviewed by hotel staff.</span></div>
        </div>
        <div>
            <span class="ds-chip-eyebrow">{icon("chart-line")} Decision support</span>
            <h2 class="ds-head-t">From prediction to informed action</h2>
            <p class="ds-head-d">The system surfaces predictions and risk signals — hotel teams stay in control
                of every guest decision.</p>
            <div class="ds-steps">{items}</div>
            <div class="ds-tip">{icon("lightbulb")}<span>Supports informed decision-making — managers review every recommendation.</span></div>
        </div>
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
        {brand_lockup()}
        <div class="foot-meta">Grand Regency Hotel · Nairobi County, Kenya</div>
    </div></footer>
    """)
