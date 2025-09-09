# Authentication

Book-A-Limo API uses SHA256-based authentication with automatic password hashing.

## Creating Credentials

### Basic Setup

```python
from bookalimo.transport.auth import Credentials

# Agency account
credentials = Credentials.create("AGENCY123", "password", is_customer=False)

# Customer account
credentials = Credentials.create("user@email.com", "password", is_customer=True)
```

### Account Types

- **Agency** (`is_customer=False`) - Travel agencies, corporate accounts
  - Access to commission features
  - Charge account billing available

- **Customer** (`is_customer=True`) - Individual end customers
  - Credit card payments required

### Password Hashing

The SDK automatically handles the required double-SHA256 algorithm:

```
hash = SHA256(SHA256(password) + toLowerCase(user_id))
```

You can also create hashes manually:

```python
# Manual hash creation
password_hash = Credentials.create_hash("mypassword", "user123")
credentials = Credentials(id="user123", password_hash=password_hash, is_customer=False)
```

## Environment Configuration

Store credentials securely using environment variables:

```bash
# .env file
BOOKALIMO_USER_ID=AGENCY123
BOOKALIMO_PASSWORD=secure_password
BOOKALIMO_IS_CUSTOMER=false
```

```python
import os


def get_credentials_from_env():
    user_id = os.getenv("BOOKALIMO_USER_ID")
    password = os.getenv("BOOKALIMO_PASSWORD")
    is_customer = os.getenv("BOOKALIMO_IS_CUSTOMER", "false").lower() == "true"

    if not user_id or not password:
        raise ValueError("BOOKALIMO_USER_ID and BOOKALIMO_PASSWORD required")

    return Credentials.create(user_id, password, is_customer)


credentials = get_credentials_from_env()
```

## Credential Warnings

The SDK issues warnings for credential configuration issues:

### DuplicateCredentialsWarning

When both client and transport provide credentials:

```python
import warnings
from bookalimo.exceptions import DuplicateCredentialsWarning

# Suppress if intentional
warnings.filterwarnings("ignore", category=DuplicateCredentialsWarning)

transport = AsyncTransport(credentials=transport_creds)
client = AsyncBookalimo(
    credentials=client_creds, transport=transport  # Ignored with warning
)
# Uses transport_creds
```

### MissingCredentialsWarning

When no credentials are provided:

```python
from bookalimo.exceptions import MissingCredentialsWarning

client = AsyncBookalimo()  # Warning issued
# Most API calls will fail with HTTP 401
```

## Authentication Errors

Common authentication issues:

```python
from bookalimo.exceptions import BookalimoHTTPError

try:
    quote = await client.pricing.quote(...)
except BookalimoHTTPError as e:
    if e.status_code == 401:
        print("Authentication failed - check credentials")
    elif e.status_code == 403:
        print("Access forbidden - check account permissions")
```
