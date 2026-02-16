"""Main entry point for the Agent Builder UI."""

import argparse
import os

import streamlit as st

from ab_cli.config import load_config

# Parse command line arguments
parser = argparse.ArgumentParser(description="Agent Builder UI")
parser.add_argument("--config", type=str, help="Path to configuration file")
parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
parser.add_argument("--mock", action="store_true", help="Use mock data provider")
args = parser.parse_args()

# If mock flag is provided, set environment variable to force mock provider
if args.mock:
    import os

    os.environ["AB_UI_DATA_PROVIDER"] = "mock"
    print("Mock mode enabled via command line flag")

# Configure the page
st.set_page_config(
    page_title="Agent Builder",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Set up session state if it doesn't exist
if "config" not in st.session_state:
    st.session_state.config = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "Agents"  # Default page

if "api_client" not in st.session_state:
    st.session_state.api_client = None

if "agents" not in st.session_state:
    st.session_state.agents = []

if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = None

if "conversation" not in st.session_state:
    st.session_state.conversation = []

if "nav_intent" not in st.session_state:
    st.session_state.nav_intent = None

# Try to load the config
try:
    # First check if there's a config file specified
    settings = load_config(args.config) if args.config else load_config()

    # Store settings in session state
    st.session_state.config = settings

    # Store verbose flag in session state
    st.session_state.verbose = args.verbose

    # Log UI configuration if verbose is enabled
    if args.verbose and hasattr(settings, "ui") and settings.ui:
        print("\nUI Configuration:")
        print(f"  data_provider: {settings.ui.data_provider}")
        print(f"  mock_data_dir: {settings.ui.mock_data_dir or '(default)'}")

    # Create API client if config is valid
    from ab_cli.api.client import AgentBuilderClient

    # Pass settings directly to AgentBuilderClient
    st.session_state.api_client = AgentBuilderClient(settings)

except Exception as e:
    st.error(f"Error loading configuration: {str(e)}")
    st.info(
        """
        Please ensure you have a valid configuration file.

        You can specify a configuration file path using the '--config' parameter:
        ```
        streamlit run app.py -- --config /path/to/config.yaml
        ```
        """
    )

# Define CSS styles
st.markdown(
    """
    <style>
    .app-header {
        font-size: 2.5rem !important;
        font-weight: bold !important;
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
    }
    .navigation-button {
        margin-bottom: 10px;
    }
    .block {
       margin-top: 0px;
       margin-bottom: 0px;
    }
    .element-container {
       margin-top: 0px;
       margin-bottom: 0px;
       padding:0px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Use the local logo.png file instead of the external URL
logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
st.sidebar.image(logo_path, width=250)

# Add UI configuration indicator in sidebar if in verbose mode
if st.session_state.get("verbose", False):
    ui_config = (
        st.session_state.config.ui
        if hasattr(st.session_state.config, "ui") and st.session_state.config.ui
        else None
    )
    data_provider = (
        ui_config.data_provider if ui_config and hasattr(ui_config, "data_provider") else "cli"
    )

    st.sidebar.markdown(f"**UI Mode:** {data_provider.upper()}")
    st.sidebar.markdown("---")

# Navigation in sidebar
st.sidebar.title("Navigation")

# Determine which page to show
# Check if we have a navigation intent first (from another page)
if "nav_intent" in st.session_state and st.session_state.nav_intent:
    current_page = st.session_state.nav_intent
    # Clear the navigation intent after using it
    st.session_state.nav_intent = None
    # Update the current page in session state for persistence
    st.session_state.current_page = current_page
else:
    # Otherwise use the last known current page or the default
    current_page = st.session_state.get("current_page", "Agents")

# Add navigation buttons (instead of radio buttons)
col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button(
        "Agents",
        use_container_width=True,
        type="primary" if current_page == "Agents" else "secondary",
    ):
        st.session_state.current_page = "Agents"
        st.rerun()

with col2:
    if st.button(
        "Chat", use_container_width=True, type="primary" if current_page == "Chat" else "secondary"
    ):
        st.session_state.current_page = "Chat"
        st.rerun()

# Handle page navigation
if current_page == "Agents":
    from ab_cli.abui.views.agents import show_agents_page

    show_agents_page()
elif current_page == "Chat":
    from ab_cli.abui.views.chat import show_chat_page

    show_chat_page()
elif current_page == "AgentDetails":
    from ab_cli.abui.views.agent_details import show_agent_details_page

    show_agent_details_page()
elif current_page == "EditAgent":
    from ab_cli.abui.views.edit_agent import show_edit_agent_page

    show_edit_agent_page()
else:
    # Default to agents page if somehow we got an unknown page
    from ab_cli.abui.views.agents import show_agents_page

    show_agents_page()

# Show API connection status in sidebar
st.sidebar.markdown("---")
st.sidebar.write("API Status:")

if st.session_state.api_client:
    try:
        # Try to ping the API
        health = st.session_state.api_client.health_check()
        st.sidebar.success("✅ Connected to API")
    except Exception as e:
        st.sidebar.error(f"❌ API Error: {str(e)}")
else:
    st.sidebar.warning("⚠️ No API Client")
