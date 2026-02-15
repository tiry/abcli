"""Wrapper functions for testing Streamlit UI components.

This module provides wrapper functions that allow Streamlit UI components
to be tested using the AppTest framework without encountering context errors.
"""

# The wrapper functions will be dynamically loaded by AppTest, so each function
# needs to include all necessary imports.

def display_agent_config_test():
    """Test wrapper for display_agent_config function."""
    # Import modules within function to ensure they're available when AppTest runs
    import streamlit as st
    from ab_cli.abui.views.agent_details import display_agent_config
    
    # Get test data from session state
    test_config = st.session_state.get("test_config", {})
    verbose = st.session_state.get("test_verbose", False)
    
    # Call the function with test data
    display_agent_config(test_config, verbose=verbose)


def show_agent_details_page_test():
    """Test wrapper for show_agent_details_page function.
    
    This wrapper ensures that all streamlit session state variables are properly
    initialized before calling the actual function.
    """
    # Import modules within function to ensure they're available when AppTest runs
    import streamlit as st
    from ab_cli.abui.views.agent_details import show_agent_details_page
    
    # Call the actual function with session state already set up by the test
    show_agent_details_page()


def show_edit_agent_page_test():
    """Test wrapper for show_edit_agent_page function.
    
    This wrapper ensures that all streamlit session state variables are properly
    initialized before calling the actual function.
    """
    # Import modules within function to ensure they're available when AppTest runs
    import streamlit as st
    from ab_cli.abui.views.edit_agent import show_edit_agent_page
    
    # Call the actual function with session state already set up by the test
    show_edit_agent_page()


def show_agents_page_test():
    """Test wrapper for show_agents_page function.
    
    This wrapper ensures that all streamlit session state variables are properly
    initialized before calling the actual function.
    """
    # Import modules within function to ensure they're available when AppTest runs
    import streamlit as st
    from ab_cli.abui.views.agents import show_agents_page
    
    # Call the actual function with session state already set up by the test
    show_agents_page()


def show_create_agent_page_test():
    """Test wrapper for show_edit_agent_page function when creating a new agent.
    
    This is functionally the same as show_edit_agent_page_test but with a different name
    to make tests more readable.
    """
    # Import modules within function to ensure they're available when AppTest runs
    import streamlit as st
    from ab_cli.abui.views.edit_agent import show_edit_agent_page
    
    # Call the actual function with session state already set up by the test
    show_edit_agent_page()
