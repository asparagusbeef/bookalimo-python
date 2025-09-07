# Authentication

Authentication and credential management for the Book-A-Limo API using SHA256-based password hashing.

## Credentials Model

::: bookalimo.transport.auth.Credentials

Pydantic model representing API authentication credentials.

### Fields

- `id`: User or agency identifier
- `password_hash`: SHA256-hashed password using Book-A-Limo algorithm
- `is_customer`: Boolean flag indicating customer vs. agent/agency account

### Hash Algorithm

The API uses a specific double-SHA256 algorithm:

```
hash = SHA256(SHA256(password) + toLowerCase(id))
```

### Creation Methods

#### Direct Hash Creation

::: bookalimo.transport.auth.Credentials.create_hash

Creates password hash using Book-A-Limo algorithm:

```python
# Manual hash creation
password_hash = Credentials.create_hash("mypassword", "user123")
credentials = Credentials(
    id="user123",
    password_hash=password_hash,
    is_customer=False
)
```

#### Automatic Creation

::: bookalimo.transport.auth.Credentials.create

Convenience method that handles hashing automatically:

```python
# Recommended: automatic hashing
credentials = Credentials.create(
    user_id="user123",
    password="mypassword", 
    is_customer=True
)
```

### Account Types

The `is_customer` flag differentiates account types:

- **`is_customer=True`**: End customer accounts
- **`is_customer=False`**: Travel agent/agency accounts (default)

This affects commission calculation and available features.

## Credential Injection

::: bookalimo.transport.auth.inject_credentials

Injects credentials into request payload when provided.

### Behavior

- **With credentials**: Adds `credentials` field to request data
- **Without credentials**: Request sent unauthenticated (may fail for protected endpoints)
- **Serialization**: Uses Pydantic model_dump() for proper format

```python
# Before injection
data = {"rateType": 0, "passengers": 2}

# After injection  
data = {
    "rateType": 0,
    "passengers": 2,
    "credentials": {
        "id": "user123",
        "passwordHash": "abc123...",
        "isCustomer": false
    }
}
```

### Transport Integration

Credentials are automatically injected by transport layer:

```python
class AsyncTransport:
    async def post(self, path, model, response_model):
        data = self.prepare_data(model)
        data = inject_credentials(data, self.credentials)  # Automatic injection
        # ... make request
```

## Usage Patterns

### Basic Authentication

```python
from bookalimo.transport.auth import Credentials
from bookalimo import AsyncBookalimo

# Create credentials
credentials = Credentials.create(
    user_id="your_agency_id",
    password="your_password",
    is_customer=False  # Travel agency
)

# Use with client
async with AsyncBookalimo(credentials=credentials) as client:
    quote = await client.pricing.quote(...)
```

### Customer vs Agency Accounts

```python
# Travel agency credentials
agency_creds = Credentials.create(
    user_id="AGENCY123",
    password="agency_password",
    is_customer=False
)

# End customer credentials  
customer_creds = Credentials.create(
    user_id="customer@email.com", 
    password="customer_password",
    is_customer=True
)
```

### Environment-Based Configuration

```python
import os
from bookalimo.transport.auth import Credentials

# Load from environment
credentials = Credentials.create(
    user_id=os.getenv("BOOKALIMO_USER_ID"),
    password=os.getenv("BOOKALIMO_PASSWORD"),
    is_customer=os.getenv("BOOKALIMO_IS_CUSTOMER", "false").lower() == "true"
)
```

### Pre-Hashed Credentials

If you already have the hashed password:

```python
# Using pre-computed hash
credentials = Credentials(
    id="user123",
    password_hash="your_precomputed_hash",
    is_customer=False
)
```

## Security Considerations

### Password Handling

- **No plaintext storage**: Passwords are immediately hashed
- **Deterministic hashing**: Same password+id produces same hash
- **Case sensitivity**: User ID is lowercased for hash calculation

### Transport Security

- **HTTPS required**: Always use HTTPS endpoints in production
- **Credential protection**: Credentials appear in request body, not URLs
- **Debug logging**: Credentials are excluded from debug logs

### Hash Algorithm Details

The double-SHA256 algorithm:

1. **Inner hash**: `SHA256(password)` produces first hash
2. **Concatenation**: Combine with lowercase user ID
3. **Outer hash**: `SHA256(inner_hash + lower(id))` produces final hash

```python
import hashlib

def bookalimo_hash(password: str, user_id: str) -> str:
    inner = hashlib.sha256(password.encode()).hexdigest()
    full_string = inner + user_id.lower()
    return hashlib.sha256(full_string.encode()).hexdigest()
```

## Error Handling

### Authentication Failures

Authentication errors manifest as API errors:

- **Invalid credentials**: API returns error response
- **Account type mismatch**: Certain endpoints require specific account types
- **Missing credentials**: Unauthenticated requests may fail

### Debugging Authentication

Enable debug logging to troubleshoot auth issues:

```python
import logging
logging.getLogger("bookalimo.transport").setLevel(logging.DEBUG)

# Debug logs will show:
# → [req_id] POST /booking/price/ body_keys=['credentials', 'rateType', ...]
# (credentials key present indicates auth is being sent)
```

### Validation Errors

Credential validation occurs at model creation:

```python
try:
    credentials = Credentials.create("", "password")  # Empty user_id
except ValidationError as e:
    # Handle validation error
    print(e.errors())
```

## Integration Examples

### With Custom Transport

```python
from bookalimo.transport import AsyncTransport
from bookalimo.transport.auth import Credentials

# Create transport with credentials
transport = AsyncTransport(
    credentials=Credentials.create("user", "pass"),
    base_url="https://api.bookalimo.com"
)

# Credentials automatically injected in all requests
```

### Multiple Credential Sets

```python
# Different credentials for different operations
agency_creds = Credentials.create("agency_id", "agency_pass", False)
customer_creds = Credentials.create("customer@email.com", "customer_pass", True)

# Use appropriate credentials per context
async with AsyncBookalimo(credentials=agency_creds) as agency_client:
    # Agency operations (get commission, etc.)
    pass

async with AsyncBookalimo(credentials=customer_creds) as customer_client:
    # Customer operations
    pass
```