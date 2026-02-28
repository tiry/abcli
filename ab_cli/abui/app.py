"""Main entry point for the Agent Builder UI."""

import argparse
import contextlib
import os

import streamlit as st

from ab_cli.config import load_config
from ab_cli.config.loader import get_available_profiles, load_config_with_profile

# Parse command line arguments
parser = argparse.ArgumentParser(description="Agent Builder UI")
parser.add_argument("--config", type=str, help="Path to configuration file")
parser.add_argument("--profile", type=str, help="Configuration profile to use")
parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
parser.add_argument(
    "--mock", action="store_true", help="Use mock data provider (deprecated, use --provider)"
)
parser.add_argument(
    "--provider", type=str, choices=["mock", "direct", "cli"], help="Data provider backend"
)
args = parser.parse_args()

# Set provider from either --provider or --mock flag (for backward compatibility)
if args.provider:
    os.environ["AB_UI_DATA_PROVIDER"] = args.provider
    if args.verbose:
        print(f"Data provider set to: {args.provider}")
elif args.mock:
    os.environ["AB_UI_DATA_PROVIDER"] = "mock"
    if args.verbose:
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

# Initialize profile-related session state (do NOT override if already set)
if "current_profile" not in st.session_state:
    st.session_state.current_profile = args.profile if args.profile else "default"
elif args.profile and st.session_state.current_profile != args.profile:
    # Only update if command line arg differs from session state (shouldn't happen in normal flow)
    st.session_state.current_profile = args.profile

if "available_profiles" not in st.session_state:
    st.session_state.available_profiles = []

if "config_path" not in st.session_state:
    st.session_state.config_path = args.config

# Try to load the config (ONLY ONCE - not on every rerun)
if st.session_state.config is None:
    try:
        # Load configuration with profile support
        config_path = args.config
        profile = args.profile

        if config_path:
            settings = load_config_with_profile(config_path, profile)
            # Get available profiles from config file
            try:
                st.session_state.available_profiles = get_available_profiles(config_path)
            except Exception:
                st.session_state.available_profiles = []
        else:
            # Use default config loading
            settings = load_config()
            st.session_state.available_profiles = []

        # Store config path for later use
        if hasattr(settings, "config_path"):
            st.session_state.config_path = settings.config_path
        elif config_path:
            st.session_state.config_path = config_path

        # Store settings in session state (both as 'config' and 'settings' for compatibility)
        st.session_state.config = settings
        st.session_state.settings = settings  # For provider_factory compatibility

        # Store verbose flag and profile in session state
        st.session_state.verbose = args.verbose
        if profile:
            st.session_state.current_profile = profile

        # Log UI configuration if verbose is enabled (only once at startup)
        if "config_logged" not in st.session_state:
            st.session_state.config_logged = True
            if args.verbose:
                print("\n=== Configuration Loaded ===")
                print(f"  Profile requested: {profile or '(none - using default)'}")
                print(f"  API Endpoint: {settings.api_endpoint}")
                print(f"  Client ID: {settings.client_id}")
                if hasattr(settings, "ui") and settings.ui:
                    print(f"  UI data_provider: {settings.ui.data_provider}")
                    print(f"  UI mock_data_dir: {settings.ui.mock_data_dir or '(default)'}")
                print("===========================\n")

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
    .stMainBlockContainer {
        padding-top: 2.6rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Use the local logo.png file instead of the external URL
logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
st.sidebar.image(logo_path, width=220)

# Add UI configuration indicator in sidebar if in verbose mode
if st.session_state.get("verbose", False) and st.session_state.config:
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


# Profile switcher UI (only for CLI and Direct providers, not Mock)
def handle_profile_change(new_profile: str) -> None:
    """Handle profile switching: reload config, reinit client, clear caches."""
    try:
        # Update session state
        st.session_state.current_profile = new_profile

        # Reload configuration with new profile
        config_path = st.session_state.get("config_path")
        profile_to_load = new_profile if new_profile != "default" else None

        if config_path:
            new_settings = load_config_with_profile(config_path, profile_to_load)
        else:
            new_settings = load_config()

        # Update both config and settings in session state
        st.session_state.config = new_settings
        st.session_state.settings = new_settings

        # Clear data provider cache FIRST (before reinitializing client)
        if "data_provider" in st.session_state:
            del st.session_state.data_provider

        # Reinitialize API client
        from ab_cli.api.client import AgentBuilderClient

        if st.session_state.api_client:
            # Close old client if needed
            with contextlib.suppress(Exception):
                st.session_state.api_client.__exit__(None, None, None)
        st.session_state.api_client = AgentBuilderClient(new_settings)

        # Clear session state caches
        st.session_state.agents = []
        st.session_state.selected_agent = None
        st.session_state.conversation = []

        # Clear data provider cache if available
        from ab_cli.abui.providers.provider_factory import get_data_provider

        with contextlib.suppress(Exception), get_data_provider(new_settings) as provider:  # type: ignore[attr-defined]
            if hasattr(provider, "clear_cache"):
                provider.clear_cache()

        # Show success message
        st.sidebar.success(f"✓ Switched to profile: {new_profile}")

        # Force rerun to refresh all data
        st.rerun()

    except Exception as e:
        st.sidebar.error(f"Failed to switch profile: {str(e)}")


# Show profile selector (DISABLED FOR NOW - use command line --profile instead)
# data_provider = os.environ.get("AB_UI_DATA_PROVIDER", "cli")
# if data_provider != "mock":
#     st.sidebar.markdown("---")
#     st.sidebar.write("**Profile:**")
#     st.sidebar.info(f"Profile: {st.session_state.get('current_profile', 'default')}")

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

# Show profile information above API Status
st.sidebar.markdown("---")
current_profile = st.session_state.get("current_profile", "default")
if current_profile and current_profile != "default":
    st.sidebar.info(f"📋 Profile: **{current_profile}**")
else:
    st.sidebar.info("📋 Profile: **default**")

# Show API connection status in sidebar
st.sidebar.markdown("---")
st.sidebar.write("API Status:")

if st.session_state.api_client:
    try:
        # Try to ping the API
        health = st.session_state.api_client.health_check()
        st.sidebar.success("✅ Connected to AB API")

        # Display data provider mode - detect actual provider in use
        data_provider = "unknown"

        # Get actual provider from session state if available
        if "data_provider" in st.session_state:
            provider_instance = st.session_state.data_provider
            provider_class_name = provider_instance.__class__.__name__

            # Map class names to provider types
            if "Mock" in provider_class_name:
                data_provider = "mock"
            elif "CLI" in provider_class_name:
                data_provider = "cli"
            elif "Direct" in provider_class_name:
                data_provider = "direct"
        else:
            # Fallback: check env var first, then config, then default
            data_provider = os.environ.get("AB_UI_DATA_PROVIDER")
            if not data_provider:
                ui_config = (
                    st.session_state.config.ui
                    if st.session_state.config
                    and hasattr(st.session_state.config, "ui")
                    and st.session_state.config.ui
                    else None
                )
                data_provider = (
                    ui_config.data_provider
                    if ui_config and hasattr(ui_config, "data_provider")
                    else "direct"
                )

        # Show provider mode with appropriate icon/color
        provider_display = {
            "mock": "🎭 Mock Data",
            "cli": "⚙️ CLI Provider",
            "direct": "🚀 Direct API",
        }
        st.sidebar.info(f"{provider_display.get(data_provider, f'📦 {data_provider}')}")

    except Exception as e:
        st.sidebar.error(f"❌ API Error: {str(e)}")
else:
    st.sidebar.warning("⚠️ No API Client")
