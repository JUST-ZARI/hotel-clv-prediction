import streamlit as st

accounts = st.session_state.accounts_created
created_count = sum(accounts.values())
pct = int(created_count / 2 * 100)

_, center, _ = st.columns([1, 2, 1])
with center:
    with st.container(border=True):
        st.markdown("<div style='text-align:center;font-size:2em;'>⚙️</div>", unsafe_allow_html=True)
        st.warning("⚠️ Initial Setup Required")
        st.markdown("<h2 style='text-align:center;'>Create User Account</h2>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align:center;color:gray;'>Dashboard Setup — one-time setup</p>",
            unsafe_allow_html=True,
        )
        st.info("This screen is available only during initial system setup. "
                "Create one account for each authorized role.")

        with st.container(border=True):
            col1, col2 = st.columns([2, 1])
            col1.markdown(f"**{created_count} of 2 accounts created**")
            col2.markdown(f"<div style='text-align:right;'>{pct}% complete</div>", unsafe_allow_html=True)
            st.progress(pct / 100)

            b1, b2 = st.columns(2)
            rm_done = accounts["revenue_manager"]
            mk_done = accounts["marketing"]
            b1.button(("✅ " if rm_done else "◯ ") + "Revenue Manager", disabled=True,
                      width='stretch')
            b2.button(("✅ " if mk_done else "◯ ") + "Marketing Team", disabled=True,
                      width='stretch')

            if rm_done and not mk_done:
                st.success("Revenue Manager account created successfully. "
                           "Create the Marketing Team account to complete setup.")
            elif mk_done and not rm_done:
                st.success("Marketing Team account created successfully. "
                           "Create the Revenue Manager account to complete setup.")

        st.divider()

        full_name = st.text_input("Full Name *", placeholder="Enter full name")
        email = st.text_input("Email Address *", placeholder="Enter email address")

        remaining_roles = [r for r, done in accounts.items() if not done]
        role_display = {"revenue_manager": "Revenue Manager", "marketing": "Marketing Team"}
        role_choice = st.selectbox(
            "Role *",
            options=[role_display[r] for r in remaining_roles] if remaining_roles else ["All roles created"],
        )
        st.caption("Each role can have only one account.")

        password = st.text_input("Password *", type="password", placeholder="Enter password")
        confirm_password = st.text_input("Confirm Password *", type="password",
                                          placeholder="Re-enter password")

        if st.button("👤➕ Create Account", type="primary", width='stretch',
                      disabled=not remaining_roles):
            if not full_name or not email or not password:
                st.error("Please fill in all required fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                role_key = "revenue_manager" if role_choice == "Revenue Manager" else "marketing"
                st.session_state.accounts_created[role_key] = True
                if all(st.session_state.accounts_created.values()):
                    st.session_state.setup_complete = True
                st.rerun()
