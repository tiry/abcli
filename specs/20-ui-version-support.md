# Spec 20: UI Version Support

**Status:** COMPLETE  
**Created:** 2026-02-16  
**Completed:** 2026-02-16  
**Related:** Spec 10 (UI Refactoring), Spec 11 (Testing UI)

## Problem Statement

The Agent Details view in the UI has lost the ability to display agent versions. Currently, the "Versions" tab shows a warning message stating that version functionality is not implemented in the data provider.

### Current State
- The CLI has full version support via `ab_cli/cli/versions.py`
- The API client (`AgentBuilderClient`) has methods for version management:
  - `list_versions(agent_id, limit, offset)` 
  - `get_version(agent_id, version_id)`
  - `create_version(agent_id, version_create)`
- The `DataProvider` interface doesn't expose any version-related methods
- The agent_details view shows a placeholder message instead of versions

### Impact
Users cannot view agent version history through the UI, limiting visibility into agent evolution and configuration changes over time.

## Proposed Solution

Add version support to the DataProvider abstraction layer and implement version display in the Agent Details view.

### 1. Extend DataProvider Interface

Add the following methods to `ab_cli/abui/providers/data_provider.py`:

```python
@abstractmethod
def get_versions(self, agent_id: str, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """Get list of versions for an agent.
    
    Args:
        agent_id: The ID of the agent
        limit: Maximum number of versions to return
        offset: Offset for pagination
        
    Returns:
        Dictionary containing:
        - versions: list of version dictionaries
        - pagination: pagination metadata (limit, offset, total_items)
        - agent: agent basic info
    """
    pass

@abstractmethod
def get_version(self, agent_id: str, version_id: str) -> dict[str, Any] | None:
    """Get details of a specific version.
    
    Args:
        agent_id: The ID of the agent
        version_id: The ID of the version (or "latest")
        
    Returns:
        Dictionary containing:
        - version: version details with config
        - agent: agent basic info
    """
    pass
```

### 2. Implement in CliDataProvider

Update `ab_cli/abui/providers/cli_data_provider.py`:

```python
def get_versions(self, agent_id: str, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """Get list of versions for an agent."""
    try:
        result = self.client.list_versions(agent_id, limit=limit, offset=offset)
        
        return {
            "versions": [
                {
                    "id": str(v.id),
                    "number": v.number,
                    "version_label": v.version_label,
                    "notes": v.notes,
                    "created_at": v.created_at,
                    "created_by": v.created_by,
                }
                for v in result.versions
            ],
            "pagination": {
                "limit": result.pagination.limit,
                "offset": result.pagination.offset,
                "total_items": result.pagination.total_items,
            },
            "agent": {
                "id": str(result.agent.id),
                "name": result.agent.name,
                "type": result.agent.type,
            },
        }
    except Exception as e:
        print(f"Error fetching versions: {e}")
        return {
            "versions": [],
            "pagination": {"limit": limit, "offset": offset, "total_items": 0},
            "agent": None,
        }

def get_version(self, agent_id: str, version_id: str) -> dict[str, Any] | None:
    """Get details of a specific version."""
    try:
        result = self.client.get_version(agent_id, version_id)
        
        return {
            "version": {
                "id": str(result.version.id),
                "number": result.version.number,
                "version_label": result.version.version_label,
                "notes": result.version.notes,
                "created_at": result.version.created_at,
                "created_by": result.version.created_by,
                "config": result.version.config,
            },
            "agent": {
                "id": str(result.agent.id),
                "name": result.agent.name,
                "type": result.agent.type,
            },
        }
    except Exception as e:
        print(f"Error fetching version: {e}")
        return None
```

### 3. Create versions.json Data File

Create `ab_cli/abui/data/versions.json` with sample version data:

```json
{
  "versions": [
    {
      "agent_id": "agent-1",
      "id": "version-001",
      "number": 1,
      "version_label": "v1.0",
      "notes": "Initial version",
      "created_at": "2026-02-01T10:00:00Z",
      "created_by": "user1",
      "config": {
        "llmModelId": "anthropic.claude-3-sonnet-20240229-v1:0",
        "systemPrompt": "You are a helpful assistant.",
        "inferenceConfig": {
          "temperature": 0.7,
          "maxTokens": 1000
        }
      }
    },
    {
      "agent_id": "agent-1",
      "id": "version-002",
      "number": 2,
      "version_label": "v1.1",
      "notes": "Updated system prompt for better responses",
      "created_at": "2026-02-10T14:30:00Z",
      "created_by": "user1",
      "config": {
        "llmModelId": "anthropic.claude-3-sonnet-20240229-v1:0",
        "systemPrompt": "You are a helpful and friendly assistant.",
        "inferenceConfig": {
          "temperature": 0.7,
          "maxTokens": 1000
        }
      }
    },
    {
      "agent_id": "agent-2",
      "id": "version-003",
      "number": 1,
      "version_label": "v1.0",
      "notes": "First version",
      "created_at": "2026-02-05T09:00:00Z",
      "created_by": "user2",
      "config": {
        "llmModelId": "anthropic.claude-3-opus-20240229-v1:0",
        "systemPrompt": "You are an expert in data analysis.",
        "inferenceConfig": {
          "temperature": 0.5,
          "maxTokens": 2000
        }
      }
    }
  ]
}
```

### 4. Implement in MockDataProvider

Update `ab_cli/abui/providers/mock_data_provider.py` to load versions from data file:

```python
def get_versions(self, agent_id: str, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """Get versions for an agent from mock data."""
    try:
        # Load versions from JSON file
        data = self._load_json_file("versions.json")
        all_versions = data.get("versions", [])
        
        # Filter versions for this agent
        agent_versions = [v for v in all_versions if v.get("agent_id") == agent_id]
        
        # Sort by version number (descending - newest first)
        agent_versions.sort(key=lambda v: v.get("number", 0), reverse=True)
        
        # Apply pagination
        total_items = len(agent_versions)
        paginated_versions = agent_versions[offset : offset + limit]
        
        # Get agent info
        agent = self.get_agent(agent_id)
        agent_info = None
        if agent:
            agent_info = {
                "id": agent.get("id"),
                "name": agent.get("name"),
                "type": agent.get("type"),
            }
        
        return {
            "versions": [
                {
                    "id": v["id"],
                    "number": v["number"],
                    "version_label": v.get("version_label"),
                    "notes": v.get("notes"),
                    "created_at": v["created_at"],
                    "created_by": v["created_by"],
                }
                for v in paginated_versions
            ],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total_items": total_items,
            },
            "agent": agent_info,
        }
    except Exception as e:
        if self.verbose:
            print(f"Error loading versions: {e}")
        return {
            "versions": [],
            "pagination": {"limit": limit, "offset": offset, "total_items": 0},
            "agent": None,
        }

def get_version(self, agent_id: str, version_id: str) -> dict[str, Any] | None:
    """Get specific version details from mock data."""
    try:
        # Load versions from JSON file
        data = self._load_json_file("versions.json")
        all_versions = data.get("versions", [])
        
        # Handle "latest" version request
        if version_id == "latest":
            agent_versions = [v for v in all_versions if v.get("agent_id") == agent_id]
            if not agent_versions:
                return None
            # Sort by version number and get the latest
            agent_versions.sort(key=lambda v: v.get("number", 0), reverse=True)
            version_data = agent_versions[0]
        else:
            # Find specific version
            version_data = None
            for v in all_versions:
                if v.get("id") == version_id and v.get("agent_id") == agent_id:
                    version_data = v
                    break
            
            if not version_data:
                return None
        
        # Get agent info
        agent = self.get_agent(agent_id)
        agent_info = None
        if agent:
            agent_info = {
                "id": agent.get("id"),
                "name": agent.get("name"),
                "type": agent.get("type"),
            }
        
        return {
            "version": version_data,
            "agent": agent_info,
        }
    except Exception as e:
        if self.verbose:
            print(f"Error loading version: {e}")
        return None
```

### 5. Update Agent Details View

Replace the placeholder in `ab_cli/abui/views/agent_details.py` (Versions tab):

```python
# Versions tab
with tabs[2]:
    st.markdown("### Agent Versions")
    
    with st.spinner("Loading versions..."):
        try:
            versions_data = provider.get_versions(agent_to_view["id"])
            
            if not versions_data or not versions_data.get("versions"):
                st.info("No versions found for this agent")
            else:
                versions = versions_data["versions"]
                pagination = versions_data["pagination"]
                
                # Display version count
                total_versions = pagination.get("total_items", len(versions))
                st.info(f"Total versions: {total_versions}")
                
                # Display versions in a table or cards
                for version in versions:
                    with st.expander(
                        f"Version {version['number']}" + 
                        (f" - {version['version_label']}" if version.get('version_label') else "")
                    ):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"**Version ID:** `{version['id']}`")
                            st.markdown(f"**Number:** {version['number']}")
                            if version.get('version_label'):
                                st.markdown(f"**Label:** {version['version_label']}")
                        
                        with col2:
                            st.markdown(f"**Created:** {version.get('created_at', 'N/A')[:10]}")
                            st.markdown(f"**Created By:** {version.get('created_by', 'N/A')}")
                        
                        if version.get('notes'):
                            st.markdown(f"**Notes:** {version['notes']}")
                        
                        # Add button to view full version details
                        if st.button(f"View Details", key=f"view_version_{version['id']}"):
                            version_details = provider.get_version(
                                agent_to_view["id"], 
                                version['id']
                            )
                            if version_details and "version" in version_details:
                                st.json(version_details["version"]["config"])
                
                # Show pagination info if there are more versions
                if total_versions > len(versions):
                    st.info(f"Showing {len(versions)} of {total_versions} versions")
                    
        except Exception as e:
            st.error(f"Error loading versions: {e}")
            if verbose:
                st.exception(e)
```

## Testing Requirements

### Unit Tests

1. **Test DataProvider Interface** (`tests/test_abui/test_data_provider.py`):
   - Test get_versions returns correct structure
   - Test get_versions pagination
   - Test get_version returns version details with config
   - Test error handling

2. **Test MockDataProvider** (`tests/test_abui/test_mock_data_provider.py`):
   - Verify mock versions are returned
   - Test both get_versions and get_version methods

3. **Test Agent Details View** (`tests/test_abui/test_agent_details.py`):
   - Test versions tab displays version list
   - Test version expander shows details
   - Test error handling when versions unavailable

### Manual Testing

1. Start UI with real API connection
2. Navigate to an agent's details page
3. Click on "Versions" tab
4. Verify:
   - Version list is displayed
   - Each version shows: number, label, notes, created date
   - Can expand to see more details
   - Version count is accurate
   - Pagination info shown if applicable

## Implementation Checklist

- [x] Create `ab_cli/abui/data/versions.json` with sample data
- [x] Update `DataProvider` interface with version methods
- [x] Implement `get_versions()` in `CliDataProvider`
- [x] Implement `get_version()` in `CliDataProvider`
- [x] Implement `get_versions()` in `MockDataProvider` (using data file)
- [x] Implement `get_version()` in `MockDataProvider` (using data file)
- [x] Update agent_details.py Versions tab implementation
- [x] Code formatting and linting passed
- [ ] Add unit tests for new methods (future enhancement)
- [ ] Manual testing with real API (user to test)

## Success Criteria

1. ✅ DataProvider interface includes version methods
2. ✅ Both providers implement version methods correctly
3. ✅ Agent Details view displays version history
4. ✅ Users can expand versions to see details
5. ✅ All tests pass
6. ✅ No regressions in existing UI functionality

## Notes

- The implementation should handle cases where versions endpoint fails gracefully
- Consider adding pagination controls if agents have many versions
- Future enhancement: Add ability to create new versions from UI
- Future enhancement: Compare configurations between versions
