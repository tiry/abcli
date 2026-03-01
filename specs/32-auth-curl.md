# Spec 32: Auth Command with curl/wget Examples

## Overview

Add an `auth` command to the CLI that retrieves an OAuth2 token and provides ready-to-use curl or wget examples for calling the Agent Builder API.

## Motivation

Users often need to:
- Test API authentication independently
- Integrate with scripts or external tools using curl/wget
- Quickly get a valid token for debugging
- See example API calls with proper authentication

This command bridges the gap between the CLI and direct API usage.

## Requirements

### Core Functionality

1. **Token Retrieval**
   - Similar to `ab check --auth-only`
   - Authenticate using configured credentials
   - Display the full OAuth2 access token

2. **Token Information**
   - Show the complete token (for copy/paste)
   - Display token expiry time if available (expires_in field)
   - Calculate and show expiration timestamp

3. **Example Generation**
   - Generate ready-to-use curl or wget commands
   - Support both GET and POST examples
   - Embed the actual token in the examples
   - Use real endpoint URLs from configuration

### Command Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--curl` | Flag | true | Generate curl example (default) |
| `--wget` | Flag | false | Generate wget example instead |
| `--get` | Flag | true | Show GET example (default) |
| `--post` | Flag | false | Show POST example instead |

**Note:** `--curl` and `--wget` are mutually exclusive. `--get` and `--post` are mutually exclusive.

### API Examples

**GET Example (List Agents):**
- Endpoint: `GET /v1/environments/{environment_id}/agents`
- Query parameters: `?limit=50&offset=0`

**POST Example (Invoke Agent):**
- Endpoint: `POST /v1/environments/{environment_id}/agents/<agent-id>/versions/<version-id>/invoke`
- Body: Simple JSON with placeholder values
- Content-Type: application/json

## Implementation Components

### Files to Create/Modify

1. **New file:** `ab_cli/cli/auth.py` - Auth command implementation
2. **Update:** `ab_cli/cli/main.py` - Register auth command  
3. **New file:** `tests/test_cli/test_auth_command.py` - Unit tests
4. **Update:** `USAGE.md` - Add auth command documentation in Configuration section

### Expected Command Usage

```bash
# Default: curl GET example
ab auth

# wget GET example  
ab auth --wget

# curl POST example
ab auth --post

# wget POST example
ab auth --wget --post
```

## Output Format Details

### Token Display

```
✓ Authentication successful!

Access Token:
<full-token-here>

Token Details:
  Expires in: <seconds> seconds (<human-readable>)
  Expires at: <timestamp> UTC
```

### curl GET Example

```bash
curl -X GET \
  "<api-endpoint>/v1/environments/<env-id>/agents?limit=50&offset=0" \
  -H "Authorization: Bearer <token>"
```

### curl POST Example

```bash
curl -X POST \
  "<api-endpoint>/v1/environments/<env-id>/agents/<agent-id>/versions/<version-id>/invoke" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, agent!"}'
```

### wget GET Example

```bash
wget --header="Authorization: Bearer <token>" \
  "<api-endpoint>/v1/environments/<env-id>/agents?limit=50&offset=0"
```

### wget POST Example

```bash
wget --header="Authorization: Bearer <token>" \
  --header="Content-Type: application/json" \
  --post-data='{"message": "Hello, agent!"}' \
  "<api-endpoint>/v1/environments/<env-id>/agents/<agent-id>/versions/<version-id>/invoke"
```

## Implementation Notes

1. **Token Expiry Calculation**
   - Parse `expires_in` from OAuth2 response (seconds)
   - Calculate expiration timestamp: `now + expires_in`
   - Display both seconds and human-readable format (e.g., "1 hour", "30 minutes")

2. **Error Handling**
   - Exit code 0 on success
   - Exit code 1 on authentication failure
   - Show clear error message if auth fails

3. **URL Construction**
   - Use API endpoint from the **active configuration** (respects profile if `--profile` is specified)
   - Use environment ID from the active configuration
   - Ensure proper URL formatting (trailing slashes, etc.)
   - Example: `ab --profile staging auth` should use staging API endpoint in generated examples

4. **Token Security**
   - Show full token for copy/paste convenience
   - User is responsible for securing the token
   - Token is only displayed to stdout, not stored

5. **Code Reuse - No Duplication**
   - **Must reuse** the authentication logic from `ab check --auth-only`
   - Do not duplicate token retrieval code
   - Consider extracting shared authentication logic into a helper function if needed
   - Use existing `AuthClient` for authentication
   - Use existing settings/configuration loading
   - Follow existing CLI patterns (common_options, etc.)

## Testing Strategy

1. **Unit Tests**
   - Test each tool/method combination
   - Test token expiry calculation and formatting
   - Test error handling
   - Mock auth client responses

2. **Integration Testing**
   - Test with real configuration
   - Verify generated commands are valid
   - Test with different API endpoints

3. **Edge Cases**
   - Missing expires_in in token response
   - Very long tokens
   - Special characters in URLs

## Success Criteria

- [ ] Command authenticates successfully
- [ ] Full token is displayed
- [ ] Token expiry information is shown
- [ ] curl GET example generated correctly
- [ ] curl POST example generated correctly
- [ ] wget GET example generated correctly
- [ ] wget POST example generated correctly
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Code passes linting and type checking
