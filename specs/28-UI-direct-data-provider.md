# Spec 28: UI Direct Data Provider

## Context

The UI in ab_cli/abui uses `providers/data_provider.py` to access the needed data.

`data_provider.py` has 2 implementations:

- **mock**: Returns pre-recorded data from JSON files
- **cli**: Executes the CLI as an external process and parses stdout

The CLI implementation was initially seen as a good solution:

- Quick to implement
- Ensures the CLI is exposing all the needed commands

However, this approach has several drawbacks:

- **Latency**: Executing an external process and capturing stdout adds significant latency
- **Parsing**: The CLI stdout can contain debug statements, requiring additional parsing logic that increases latency
- **No strong typing**: The data_provider interface is not strongly typed because it mainly uses JSON parsing, returning `dict[str, Any]` instead of typed models

## Proposed Approach

Rather than calling the CLI code via a subprocess, we should call the CLI business logic directly in Python:

- **Eliminate subprocess overhead**: No external process creation
- **Remove stdout parsing**: Direct access to Python objects
- **Strong typing**: Return typed models from `ab_cli/models` instead of dicts

## Key Design Decisions (from requirements gathering)

1. **Call CLI business logic directly**: Extract core logic from CLI commands and call them directly, bypassing Click decorators entirely
2. **Full strong typing**: Update ALL DataProvider methods to return strongly typed models for full type safety
3. **Keep both implementations**: Maintain CLIDataProvider for backward compatibility, add DirectDataProvider as the new default
4. **Configuration-based selection**: Use existing `UISettings.data_provider` configuration mechanism (like mock provider)

## Current Architecture Analysis

### DataProvider Interface

**14 methods** with mixed return types:

#### Agent Operations (6 methods):
- `get_agents()` → `list[dict[str, Any]]`
- `get_agents_paginated(limit, offset)` → `PaginatedResult` (already typed!)
- `get_agent(agent_id)` → `dict[str, Any] | None`
- `create_agent(agent_data)` → `dict[str, Any]`
- `update_agent(agent_id, agent_data)` → `dict[str, Any]`
- `delete_agent(agent_id)` → `bool`

#### Invocation (1 method):
- `invoke_agent(agent_id, message, agent_type)` → `dict[str, Any] | str` (inconsistent!)

#### Version Operations (2 methods):
- `get_versions(agent_id, limit, offset)` → `dict[str, Any]`
- `get_version(agent_id, version_id)` → `dict[str, Any] | None`

#### Resource Operations (3 methods):
- `get_models(limit, offset)` → `dict[str, Any]`
- `get_guardrails(limit, offset)` → `dict[str, Any]`
- `get_knowledge_bases(limit, offset)` → `dict[str, Any]`

#### Configuration (2 methods):
- `get_config()` → `dict[str, Any]`
- `check_api_health()` → `bool`

### CLI Command Structure

Commands use Click decorators heavily:
- `@click.group()`, `@click.command()`, `@click.option()`, `@click.argument()`
- Most commands call API client methods: `client.agents.list_agents()`, `client.agents.get_agent()`, etc.
- CLI layer adds formatting, pagination handling, error handling, and output display

### Available Typed Models

**Agent models** (`ab_cli/models/agent.py`):
- `Agent`, `AgentList`, `AgentVersion`, `VersionList`, `AgentCreate`, `AgentUpdate`, `AgentPatch`

**Resource models** (`ab_cli/models/resources.py`):
- `LLMModel`, `LLMModelList`, `Guardrail`, `GuardrailList`, `KnowledgeBase`, `KnowledgeBaseList`

**Invocation models** (`ab_cli/models/invocation.py`):
- `InvocationRequest`, `InvocationResponse`, `StreamChunk`

**Pagination model** (`ab_cli/api/pagination.py`):
- `PaginatedResult` (generic with `results: list[T]`)

## Implementation Plan

**NOTE**: Phase order updated - we now refactor CLI to use services immediately after creating them (Phase 1b) to validate the service layer works correctly before building the DirectDataProvider.

### Phase 1: Create CLI Service Layer

**Goal**: Extract business logic from CLI commands into reusable service functions

#### 1.1 Create `ab_cli/services/__init__.py`
- New module to contain service layer

#### 1.2 Create `ab_cli/services/agent_service.py`
Extract logic from `cli/agents.py`:
```python
class AgentService:
    def __init__(self, client: APIClient):
        self.client = client
    
    def list_agents(self, limit: int | None = None, offset: int = 0, 
                    agent_type: str | None = None, name_pattern: str | None = None) -> AgentList
    
    def list_agents_paginated(self, limit: int, offset: int) -> PaginatedResult[Agent]
    
    def get_agent(self, agent_id: str) -> AgentVersion | None
    
    def create_agent(self, agent_data: dict) -> AgentVersion
    
    def update_agent(self, agent_id: str, agent_data: dict) -> AgentVersion
    
    def delete_agent(self, agent_id: str) -> bool
```

#### 1.3 Create `ab_cli/services/version_service.py`
Extract logic from `cli/versions.py`:
```python
class VersionService:
    def __init__(self, client: APIClient):
        self.client = client
    
    def list_versions(self, agent_id: str, limit: int, offset: int) -> VersionList
    
    def get_version(self, agent_id: str, version_id: str) -> VersionConfig | None
```

#### 1.4 Create `ab_cli/services/resource_service.py`
Extract logic from `cli/resources.py`:
```python
class ResourceService:
    def __init__(self, client: APIClient):
        self.client = client
    
    def list_models(self, limit: int, offset: int) -> LLMModelList
    
    def list_guardrails(self, limit: int, offset: int) -> GuardrailList
    
    def list_knowledge_bases(self, limit: int, offset: int) -> KnowledgeBaseList
```

#### 1.5 Create `ab_cli/services/invocation_service.py`
Extract logic from `cli/invoke.py`:
```python
class InvocationService:
    def __init__(self, client: APIClient):
        self.client = client
    
    def invoke_agent(self, agent_id: str, message: str, 
                     agent_type: str | None = None) -> InvocationResponse
```

### Phase 2: Update DataProvider Interface

#### 2.1 Update `ab_cli/abui/providers/data_provider.py`

**Change ALL return types to strongly typed models**:

```python
from abc import ABC, abstractmethod
from ab_cli.models.agent import Agent, AgentList, AgentVersion, VersionList, VersionConfig
from ab_cli.models.resources import LLMModelList, GuardrailList, KnowledgeBaseList
from ab_cli.models.invocation import InvocationResponse
from ab_cli.api.pagination import PaginatedResult

class DataProvider(ABC):
    """Abstract base class for data providers."""
    
    # Agent Operations
    @abstractmethod
    def get_agents(self) -> list[Agent]:
        """Get all agents."""
        pass
    
    @abstractmethod
    def get_agents_paginated(self, limit: int, offset: int) -> PaginatedResult[Agent]:
        """Get agents with pagination."""
        pass
    
    @abstractmethod
    def get_agent(self, agent_id: str) -> AgentVersion | None:
        """Get a specific agent with its current version."""
        pass
    
    @abstractmethod
    def create_agent(self, agent_data: dict) -> AgentVersion:
        """Create a new agent."""
        pass
    
    @abstractmethod
    def update_agent(self, agent_id: str, agent_data: dict) -> AgentVersion:
        """Update an agent (creates new version)."""
        pass
    
    @abstractmethod
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent."""
        pass
    
    # Invocation
    @abstractmethod
    def invoke_agent(self, agent_id: str, message: str, 
                     agent_type: str | None = None) -> InvocationResponse:
        """Invoke an agent with a message."""
        pass
    
    # Version Operations
    @abstractmethod
    def get_versions(self, agent_id: str, limit: int = 10, 
                     offset: int = 0) -> VersionList:
        """Get versions for an agent."""
        pass
    
    @abstractmethod
    def get_version(self, agent_id: str, version_id: str) -> VersionConfig | None:
        """Get a specific version with full configuration."""
        pass
    
    # Resource Operations
    @abstractmethod
    def get_models(self, limit: int = 100, offset: int = 0) -> LLMModelList:
        """Get available LLM models."""
        pass
    
    @abstractmethod
    def get_guardrails(self, limit: int = 100, offset: int = 0) -> GuardrailList:
        """Get available guardrails."""
        pass
    
    @abstractmethod
    def get_knowledge_bases(self, limit: int = 100, offset: int = 0) -> KnowledgeBaseList:
        """Get available knowledge bases."""
        pass
    
    # Configuration
    @abstractmethod
    def get_config(self) -> dict:
        """Get configuration (keep as dict for now - no model exists)."""
        pass
    
    @abstractmethod
    def check_api_health(self) -> bool:
        """Check if API is healthy."""
        pass
```

### Phase 3: Create DirectDataProvider

#### 3.1 Create `ab_cli/abui/providers/direct_data_provider.py`

```python
"""Direct data provider that calls CLI business logic directly."""

from ab_cli.abui.providers.data_provider import DataProvider
from ab_cli.api.client import APIClient
from ab_cli.services.agent_service import AgentService
from ab_cli.services.version_service import VersionService
from ab_cli.services.resource_service import ResourceService
from ab_cli.services.invocation_service import InvocationService
from ab_cli.config.settings import get_settings

class DirectDataProvider(DataProvider):
    """Data provider that calls CLI business logic directly (no subprocess)."""
    
    def __init__(self):
        """Initialize the direct data provider."""
        settings = get_settings()
        self.client = APIClient(
            base_url=settings.api_base_url,
            api_key=settings.api_key,
            timeout=settings.timeout
        )
        
        # Initialize service layer
        self.agent_service = AgentService(self.client)
        self.version_service = VersionService(self.client)
        self.resource_service = ResourceService(self.client)
        self.invocation_service = InvocationService(self.client)
    
    def get_agents(self) -> list[Agent]:
        """Get all agents."""
        agent_list = self.agent_service.list_agents()
        return agent_list.items
    
    def get_agents_paginated(self, limit: int, offset: int) -> PaginatedResult[Agent]:
        """Get agents with pagination."""
        return self.agent_service.list_agents_paginated(limit, offset)
    
    # ... implement all other methods
```

### Phase 4: Update Existing Providers

#### 4.1 Update `ab_cli/abui/providers/mock_data_provider.py`
- Update return types to match new interface
- Convert dict responses to typed models using Pydantic's `parse_obj()`

#### 4.2 Update `ab_cli/abui/providers/cli_data_provider.py`
- Update return types to match new interface
- Convert JSON responses to typed models
- Keep subprocess-based implementation for backward compatibility

### Phase 5: Update Provider Factory

#### 5.1 Update `ab_cli/abui/providers/provider_factory.py`

```python
def get_data_provider(provider_type: str | None = None) -> DataProvider:
    """Get data provider based on configuration."""
    if provider_type is None:
        settings = get_settings()
        provider_type = settings.ui.data_provider  # Read from UISettings
    
    if provider_type == "mock":
        return MockDataProvider()
    elif provider_type == "cli":
        return CLIDataProvider()
    elif provider_type == "direct":
        return DirectDataProvider()
    else:
        # Default to direct provider
        return DirectDataProvider()
```

#### 5.2 Update `ab_cli/config/settings.py`
- Ensure `UISettings.data_provider` accepts "direct" as a value
- Update default to "direct"

### Phase 6: Update UI Views

#### 6.1 Update all views to handle typed models
- `ab_cli/abui/views/agents.py` - Update to work with `Agent`, `AgentList`, `AgentVersion`
- `ab_cli/abui/views/agent_details.py` - Update to work with `AgentVersion`, `VersionList`
- `ab_cli/abui/views/chat.py` - Update to work with `InvocationResponse`
- `ab_cli/abui/views/edit_agent.py` - Update to work with `AgentVersion`

#### 6.2 Handle model conversions
- Add utility functions to convert models to dicts where needed for Streamlit display
- Use `.model_dump()` or `.dict()` for JSON serialization

### Phase 1b: Refactor CLI Commands to Use Service Layer (IMMEDIATELY)

**Goal**: Validate service layer works correctly in real CLI before building DirectDataProvider

#### 1b.1 Refactor `ab_cli/cli/agents.py` to use AgentService
- Replace direct `client.list_agents()` calls with `AgentService.list_agents()`
- Replace direct `client.get_agent()` calls with `AgentService.get_agent()`
- Replace direct `client.create_agent()` calls with `AgentService.create_agent()`
- Replace direct `client.update_agent()` calls with `AgentService.update_agent()`
- Replace direct `client.patch_agent()` calls with `AgentService.patch_agent()`
- Replace direct `client.delete_agent()` calls with `AgentService.delete_agent()`

#### 1b.2 Refactor `ab_cli/cli/versions.py` to use VersionService
- Replace direct `client.list_versions()` calls with `VersionService.list_versions()`
- Replace direct `client.get_version()` calls with `VersionService.get_version()`

#### 1b.3 Refactor `ab_cli/cli/resources.py` to use ResourceService
- Replace direct `client.list_models()` calls with `ResourceService.list_models()`
- Replace direct `client.list_guardrails()` calls with `ResourceService.list_guardrails()`

#### 1b.4 Refactor `ab_cli/cli/invoke.py` to use InvocationService
- Replace direct `client.invoke_agent()` calls with `InvocationService.invoke_agent()`
- Replace direct `client.invoke_task()` calls with `InvocationService.invoke_task()`

**Benefits**:
- Validates service layer works in production CLI
- Reduces code duplication NOW
- Ensures CLI and UI will use identical business logic
- Makes any service issues visible immediately via CLI testing

### Phase 8: Testing

#### 8.1 Create service layer tests
- `tests/test_services/test_agent_service.py`
- `tests/test_services/test_version_service.py`
- `tests/test_services/test_resource_service.py`
- `tests/test_services/test_invocation_service.py`

#### 8.2 Create DirectDataProvider tests
- `tests/test_abui/test_direct_data_provider.py`
- Test all methods return correct types
- Test error handling

#### 8.3 Update existing provider tests
- Update `tests/test_abui/test_data_provider.py` (MockTestingProvider)
- Update provider factory tests
- Update view tests to work with typed models

#### 8.4 Integration testing
- Test UI with all three providers (mock, cli, direct)
- Verify performance improvements with direct provider
- Test backward compatibility

### Phase 9: Documentation

#### 9.1 Update documentation files
- Update `ab-cli/UI.md` - Document new DirectDataProvider
- Update `ab-cli/CONFIG.md` - Document data_provider configuration options
- Update `ab-cli/TESTING.md` - Document testing approach for providers
- Update `ab-cli/README.md` - Mention performance improvements

#### 9.2 Add code documentation
- Docstrings for all service classes and methods
- Type hints throughout
- Examples in docstrings

## Expected Benefits

### Performance Improvements
- **Eliminate subprocess overhead**: No process creation, faster startup
- **Remove JSON parsing**: Direct object access instead of stdout parsing
- **No debug statement filtering**: Direct access to clean data

### Code Quality
- **Strong typing**: Full type safety with Pydantic models
- **Better IDE support**: Autocomplete and type checking
- **Reduced errors**: Type checking catches errors at development time
- **Code reuse**: Service layer can be used by both CLI and UI

### Maintainability
- **Single source of truth**: Business logic in service layer
- **Easier testing**: Mock service dependencies instead of subprocess calls
- **Clear separation**: CLI formatting separate from business logic

## Migration Strategy

1. **Phase 1-3**: Create new code without breaking existing functionality
2. **Phase 4-5**: Update interfaces and factory (backward compatible)
3. **Phase 6**: Update UI views incrementally
4. **Phase 7**: Optional CLI refactoring (can be done later)
5. **Phase 8-9**: Testing and documentation

**Configuration migration**:
- Default to "direct" for new installations
- Existing configs keep their current setting
- Document migration path in release notes

## Risks and Mitigations

### Risk: Breaking Changes
**Mitigation**: Keep all three providers (mock, cli, direct) functional, allow configuration selection

### Risk: API Client Initialization
**Mitigation**: Ensure DirectDataProvider properly initializes API client with correct settings

### Risk: Error Handling Differences
**Mitigation**: Ensure service layer handles errors consistently with CLI behavior

### Risk: Performance Regressions
**Mitigation**: Benchmark before/after, ensure direct provider is actually faster

### Risk: Type Conversion Issues
**Mitigation**: Thorough testing of model conversions, especially for complex nested structures

## Success Criteria

1. **DirectDataProvider implemented**: All 14 methods working with strong types
2. **Service layer created**: Reusable business logic extracted from CLI
3. **All providers updated**: Mock, CLI, and Direct all use new typed interface
4. **Tests passing**: Unit tests for services and providers, integration tests for UI
5. **Performance improved**: Measurable latency reduction (target: 50%+ faster than CLI provider)
6. **Documentation updated**: All docs reflect new architecture
7. **Backward compatibility**: Existing configurations still work

## Future Enhancements

1. **Caching in service layer**: Add intelligent caching for frequently accessed data
2. **Streaming support**: Add streaming invocation support to DirectDataProvider
3. **Batch operations**: Add batch API calls for improved performance
4. **Remove CLIDataProvider**: After direct provider is proven stable, consider removing subprocess-based provider
5. **Complete CLI refactoring**: Refactor all CLI commands to use service layer
