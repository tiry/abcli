"""Debug utilities for examining specific Streamlit elements.

This file is prefixed with 'debug_' to exclude it from normal test runs.
It's kept as a developer tool for future UI work.
"""

from streamlit.testing.v1 import AppTest


def debug_element_contents(streamlit_app: AppTest) -> None:
    """Test that examines the contents of specific Streamlit elements."""
    # Run the app
    streamlit_app.run()
    
    # Debug output of subheader elements
    print("\n\n===== DETAILED SUBHEADER CONTENT =====")
    if hasattr(streamlit_app, 'subheader'):
        for i, subheader in enumerate(streamlit_app.subheader):
            print(f"Subheader {i}: {subheader}")
            print(f"Subheader {i} type: {type(subheader)}")
            print(f"Subheader {i} dir: {dir(subheader)}")
            if hasattr(subheader, 'value'):
                print(f"Subheader {i} value: {subheader.value}")
            if hasattr(subheader, 'tag'):
                print(f"Subheader {i} tag: {subheader.tag}")
            if hasattr(subheader, 'children'):
                print(f"Subheader {i} children: {subheader.children}")
            print("-----")
    
    # Debug output of markdown elements
    print("\n\n===== DETAILED MARKDOWN CONTENT =====")
    if hasattr(streamlit_app, 'markdown'):
        for i, markdown in enumerate(streamlit_app.markdown):
            print(f"Markdown {i}: {markdown}")
            print(f"Markdown {i} type: {type(markdown)}")
            print(f"Markdown {i} dir: {dir(markdown)}")
            if hasattr(markdown, 'value'):
                print(f"Markdown {i} value: {markdown.value}")
            if hasattr(markdown, 'body'):
                print(f"Markdown {i} body: {markdown.body}")
            print("-----")
            
    # Debug test data provider agents
    print("\n\n===== DATA PROVIDER AGENTS =====")
    if "data_provider" in streamlit_app.session_state:
        provider = streamlit_app.session_state["data_provider"]
        agents = provider.get_agents()
        for i, agent in enumerate(agents):
            print(f"Agent {i}: {agent}")
    else:
        print("No data provider found in session state")
        
    # Simple assertion to pass the test
    assert True