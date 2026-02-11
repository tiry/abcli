# Phase 1: Foundation

**Status:** Complete  
**Spec Reference:** `specs/00-draft-spec.md`

---

## 1. Overview

This phase implements the foundational components of the Agent Builder CLI (`ab-cli`), setting up the project structure, configuration handling, authentication, and base API client.

### 1.1 Goals

- Set up project structure with proper packaging
- Implement configuration loading and validation
- Implement OAuth2 authentication
- Create base API client with error handling and retries
- Set up CLI entry point with basic commands

---

## 2. Project Setup

### 2.1 Directory Structure

```
ab-cli/
├── ab_cli/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── client.py
│   │   └── exceptions.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── loader.py
│   ├── models/
│   │   ├── __init__.py
│   └── utils/
│       ├── __init__.py
│       └── retry.py
├── tests/
│   ├── test_api/
│   ├── test_cli/
│   ├── test_config/
│   └── test_models/
├── pyproject.toml
├── config.example.yaml
└── README.md
```

### 2.2 Package Configuration

```toml
[project]
name = "ab-cli"
version = "0.1.0"
description = "Agent Builder CLI"
authors = [{name = "Your Name", email = "your.email@example.com"}]
requires-python = ">=3.9"
dependencies = [
    "click>=8.1",
    "httpx>=0.27",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "pyyaml>=6.0",
    "rich>=13.0",
]
```

---

## 3. Configuration

### 3.1 Settings Model

Create a Pydantic settings model to handle configuration:

```python
class ABSettings(BaseSettings):
    """Agent Builder CLI configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="AB_",
        env_file=".env",
        extra="ignore",
    )
    
    # Required identifiers
    environment_id: str
    account_id: str | None = None  # Optional, derived from environment
    
    # Authentication
    client_id: str
    client_secret: str
    
    # API Endpoints
    api_endpoint: str = "https://api.agentbuilder.experience.hyland.com/"
    auth_endpoint: str = "https://auth.hyland.com/connect/token"
    auth_scope: list[str] = ["hxp"]
    
    # Processing settings
    timeout: float = 30.0
    retry_backoff: float = 2.0
    max_retries: int = 3
```

### 3.2 Configuration Loading

Implement functions to:
- Load configuration from YAML file
- Validate configuration
- Apply environment variable overrides
- Search for configuration in standard locations

### 3.3 Config File Format

```yaml
# Agent Builder CLI Configuration

# HxP Environment
environment_id: "your-environment-id"

# Authentication (OAuth2 client credentials)
client_id: "your-client-id"
client_secret: "your-client-secret"  # Or use AB_CLIENT_SECRET env var

# API Endpoints
api_endpoint: "https://api.agentbuilder.dev.experience.hyland.com/"
auth_endpoint: "https://auth.iam.dev.experience.hyland.com/idp/connect/token"
auth_scope:
  - "hxp"
```

---

## 4. Authentication

### 4.1 OAuth2 Client Credentials Flow

Implement an OAuth2 client credentials flow handler in `api/auth.py`:

```python
class AuthClient:
    """OAuth2 client credentials authentication client."""

    def __init__(self, settings: ABSettings) -> None:
        """Initialize with configuration settings."""
        self.settings = settings
        self.token: str | None = None
        self.token_expiry: datetime | None = None

    def get_token(self) -> str:
        """Get a valid OAuth2 token, refreshing if needed."""
        # Check if token exists and is not expired
        if self.token and self.token_expiry and self.token_expiry > datetime.now():
            return self.token
        
        # Get a new token
        self._refresh_token()
        return self.token

    def _refresh_token(self) -> None:
        """Request a new OAuth2 token using client credentials."""
        # Prepare request data
        token_data = {
            "grant_type": "client_credentials",
            "client_id": self.settings.client_id,
            "client_secret": self.settings.client_secret,
            "scope": " ".join(self.settings.auth_scope),
        }
        
        # Make token request
        try:
            response = httpx.post(
                self.settings.auth_endpoint,
                data=token_data,
                timeout=self.settings.timeout,
            )
            response.raise_for_status()
            
            token_response = response.json()
            self.token = token_response["access_token"]
            
            # Calculate token expiry (with safety margin)
            expires_in = token_response.get("expires_in", 3600)  # Default 1 hour
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
            
        except httpx.HTTPStatusError as e:
            raise TokenError(f"Token request failed: {e.response.text}") from e
        except (httpx.RequestError, KeyError, ValueError) as e:
            raise TokenError(f"Token request failed: {str(e)}") from e
```

---

## 5. API Client

### 5.1 Exception Classes

Define exception hierarchy in `api/exceptions.py`:

```python
class APIError(Exception):
    """Base class for API errors."""

class AuthenticationError(APIError):
    """Authentication failed or access denied."""

class ConnectionError(APIError):
    """Failed to connect to API or request timed out."""

class ValidationError(APIError):
    """Request validation failed."""

class NotFoundError(APIError):
    """Resource not found."""

class RateLimitError(APIError):
    """Rate limit exceeded."""

class ServerError(APIError):
    """Server-side error."""

class TokenError(APIError):
    """Error obtaining or refreshing token."""
```

### 5.2 Base API Client

Implement a base HTTP client with authentication, error handling, and retries:

```python
class AgentBuilderClient:
    """HTTP client for the Agent Builder API.

    This client handles all HTTP communication with the Agent Builder API,
    including authentication, request/response handling, and error mapping.
    """

    def __init__(self, settings: ABSettings, auth_client: AuthClient | None = None) -> None:
        """Initialize the API client.

        Args:
            settings: Configuration settings.
            auth_client: Optional auth client (created if not provided).
        """
        self.settings = settings
        self.auth_client = auth_client or AuthClient(settings)
        self._client: httpx.Client | None = None

    @property
    def base_url(self) -> str:
        """Get the base URL for API requests."""
        return f"{self.settings.api_endpoint}v1"

    def _get_client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.settings.timeout,
                headers={"Accept": "application/json"},
            )
        return self._client

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        token = self.auth_client.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        # Implementation of error handling based on status codes

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method.
            path: URL path (relative to base URL).
            params: Query parameters.
            json: JSON body.

        Returns:
            Parsed JSON response.
        """
        # Implementation of request handling with retries
```

### 5.3 Utility Functions

Implement retry decorator in `utils/retry.py`:

```python
def retry(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    retry_on_exceptions: tuple[Type[Exception], ...] = (ConnectionError, ServerError),
    retry_on_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504),
) -> Callable:
    """Retry decorator with exponential backoff."""
    # Implementation
```

---

## 6. CLI Entry Point

### 6.1 Main CLI

Implement the main CLI entry point in `cli/main.py`:

```python
@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option(
    "-c", "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.version_option(__version__, prog_name="ab-cli")
@click.pass_context
def main(ctx: click.Context, verbose: bool, config: Path | None) -> None:
    """Agent Builder CLI - Manage and invoke AI agents.

    Use 'ab COMMAND --help' for more information about a command.
    """
    # Implementation
```

### 6.2 Command: Check

Implement a check command to verify API connectivity:

```python
@main.command()
@click.option("--auth-only", is_flag=True, help="Only check authentication (skip API test)")
@click.pass_context
def check(ctx: click.Context, auth_only: bool) -> None:
    """Test API connectivity with verbose output."""
    # Implementation
```

### 6.3 Command: Validate

Implement a validate command to verify configuration:

```python
@main.command()
@click.option("--show-config", is_flag=True, help="Show loaded configuration values")
@click.argument("config_file", type=click.Path(exists=True, path_type=Path), required=False)
@click.pass_context
def validate(ctx: click.Context, show_config: bool, config_file: Path | None) -> None:
    """Validate configuration file."""
    # Implementation
```

---

## 7. Files to Create

| File | Description |
|------|-------------|
| `ab_cli/__init__.py` | Package metadata and version |
| `ab_cli/api/auth.py` | OAuth2 authentication client |
| `ab_cli/api/client.py` | Base API client implementation |
| `ab_cli/api/exceptions.py` | API exception classes |
| `ab_cli/config/settings.py` | Pydantic settings model |
| `ab_cli/config/loader.py` | Configuration loading functions |
| `ab_cli/cli/main.py` | Main CLI entry point |
| `ab_cli/utils/retry.py` | Retry decorator |
| `config.example.yaml` | Example configuration file |

---

## 8. Testing Strategy

### Unit Tests

- Configuration loading and validation
- OAuth2 token acquisition
- API client request handling
- Error mapping from HTTP responses

### Integration Tests

- Configuration from files and environment variables
- API client connectivity with mock server
- CLI commands with test runner

---

*Document created: 2026-02-10*  
*Status: Complete*