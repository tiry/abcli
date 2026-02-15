"""Debug utilities for the Streamlit app.

This file is prefixed with 'debug_' to exclude it from normal test runs.
It's kept as a developer tool for future UI work.
"""

from streamlit.testing.v1 import AppTest


def debug_app_content(streamlit_app: AppTest) -> None:
    """Test that prints the content of the Streamlit app for debugging."""
    # Run the app
    streamlit_app.run()
    
    # Debug output
    print("\n\n===== TITLE =====")
    if hasattr(streamlit_app, 'title'):
        print(f"Title: {streamlit_app.title}")
    
    print("\n===== TREE STRUCTURE =====")
    print(f"Tree type: {type(streamlit_app._tree)}")
    print(f"Tree dir: {dir(streamlit_app._tree)}")
    
    # Examine available attributes on the AppTest object
    print("\n===== APP TEST ATTRIBUTES =====")
    print(f"AppTest dir: {dir(streamlit_app)}")
    
    print("\n===== MARKDOWN =====")
    if hasattr(streamlit_app, 'markdown'):
        if isinstance(streamlit_app.markdown, list):
            for i, markdown in enumerate(streamlit_app.markdown):
                print(f"Markdown {i}: {markdown}")
        else:
            print(f"Markdown: {streamlit_app.markdown}")
    
    print("\n===== WRITE =====")
    if hasattr(streamlit_app, 'write'):
        if isinstance(streamlit_app.write, list):
            for i, write in enumerate(streamlit_app.write):
                print(f"Write {i}: {write}")
        else:
            print(f"Write: {streamlit_app.write}")
            
    print("\n===== TEXT =====")
    if hasattr(streamlit_app, 'text'):
        if isinstance(streamlit_app.text, list):
            for i, text in enumerate(streamlit_app.text):
                print(f"Text {i}: {text}")
        else:
            print(f"Text: {streamlit_app.text}")
    
    print("\n===== SUBHEADER =====")
    if hasattr(streamlit_app, 'subheader'):
        if isinstance(streamlit_app.subheader, list):
            for i, subheader in enumerate(streamlit_app.subheader):
                print(f"Subheader {i}: {subheader}")
        else:
            print(f"Subheader: {streamlit_app.subheader}")
            
    print("\n===== SESSION STATE KEYS =====")
    # Directly access known keys in session state
    for key in ["current_page", "data_provider", "config", "agents"]:
        if key in streamlit_app.session_state:
            print(f"Session state {key}: {streamlit_app.session_state[key]}")
        
    # Simple assertion to pass the test
    assert True