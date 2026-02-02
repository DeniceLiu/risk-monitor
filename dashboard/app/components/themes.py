"""Theme management for dashboard."""

import streamlit as st


class ThemeManager:
    """Manages dashboard themes."""

    DARK_THEME = """
    <style>
        /* Dark theme styles */
        .stApp {
            background-color: #0e1117;
        }

        .metric-card {
            background-color: #1e1e1e;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #333;
        }

        h1, h2, h3 {
            color: #fafafa;
        }

        .stMetric {
            background-color: #262730;
            padding: 10px;
            border-radius: 5px;
        }

        [data-testid="stSidebar"] {
            background-color: #262730;
        }
    </style>
    """

    LIGHT_THEME = """
    <style>
        /* Light theme styles */
        .stApp {
            background-color: #ffffff;
        }

        .metric-card {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
        }

        h1, h2, h3 {
            color: #262730;
        }

        .stMetric {
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #dee2e6;
        }

        [data-testid="stSidebar"] {
            background-color: #f8f9fa;
        }
    </style>
    """

    def __init__(self):
        """Initialize theme manager."""
        if "theme" not in st.session_state:
            st.session_state.theme = "light"

    def render_toggle(self):
        """Render theme toggle in sidebar."""
        st.sidebar.subheader("Theme")

        theme = st.sidebar.radio(
            "Select Theme",
            options=["Light", "Dark"],
            index=0 if st.session_state.theme == "light" else 1,
            horizontal=True,
        )

        st.session_state.theme = theme.lower()

    def apply_theme(self):
        """Apply selected theme."""
        if st.session_state.theme == "dark":
            st.markdown(self.DARK_THEME, unsafe_allow_html=True)
        else:
            st.markdown(self.LIGHT_THEME, unsafe_allow_html=True)
