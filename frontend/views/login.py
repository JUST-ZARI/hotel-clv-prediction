import streamlit as st

st.markdown(
    "<h1 style='text-align:center;'>Hotel CLV Dashboard</h1>"
    "<p style='text-align:center;color:gray;'>Enter credentials &rarr; select role &rarr; Login.</p>",
    unsafe_allow_html=True,
)

_, center, _ = st.columns([1, 2, 1])
with center:
    with st.container(border=True):
        st.markdown("<div style='text-align:center;font-size:2em;'>📊</div>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align:center;'>Welcome Back</h3>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align:center;color:gray;'>Sign in to access the Customer Lifetime "
            "Value Decision-Support Dashboard.</p>",
            unsafe_allow_html=True,
        )

        email = st.text_input("Email Address *", placeholder="Enter your email address")
        password = st.text_input("Password *", type="password", placeholder="Enter your password")
        role_choice = st.selectbox(
            "Role *",
            options=["Select role...", "Revenue Manager", "Marketing Team"],
        )
        st.caption("Select your authorized dashboard role.")

        if st.button("➔ Login", type="primary", width='stretch'):
            if not email or not password or role_choice == "Select role...":
                st.error("Please fill in all fields and select a role.")
            else:
                st.session_state.authenticated = True
                st.session_state.role = (
                    "revenue_manager" if role_choice == "Revenue Manager" else "marketing"
                )
                st.rerun()

        st.caption("🔒 Secure authentication • Authorized users only")
