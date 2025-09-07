# Authentication

Complete guide to authentication and credential management for the Bookalimo SDK.

## Overview

The Book-A-Limo API uses a custom SHA256-based authentication system with user ID and password credentials. The SDK handles the complex password hashing automatically.

## Credential Creation

### Basic Setup

```python
from bookalimo.transport.auth import Credentials

# Create credentials with automatic hashing
credentials = Credentials.create(
    user_id="your_agency_id",
    password="your_password",
    is_customer=False  # Agency account
)

# For customer accounts
customer_credentials = Credentials.create(
    user_id="customer@example.com",
    password="customer_password", 
    is_customer=True
)
```

### Account Types

**Agency Accounts (`is_customer=False`)**
- Travel agencies and corporate accounts
- Access to commission features
- Charge account billing available
- Bulk reservation management

**Customer Accounts (`is_customer=True`)**
- Individual end customers
- Credit card payments required
- Personal booking management

## Environment-Based Configuration

### Using Environment Variables

```bash
# .env file
BOOKALIMO_USER_ID=AGENCY123
BOOKALIMO_PASSWORD=secure_password_123
BOOKALIMO_IS_CUSTOMER=false
```

```python
import os
from bookalimo.transport.auth import Credentials

def get_credentials_from_env():
    """Load credentials from environment variables."""
    user_id = os.getenv("BOOKALIMO_USER_ID")
    password = os.getenv("BOOKALIMO_PASSWORD") 
    is_customer = os.getenv("BOOKALIMO_IS_CUSTOMER", "false").lower() == "true"
    
    if not user_id or not password:
        raise ValueError("BOOKALIMO_USER_ID and BOOKALIMO_PASSWORD must be set")
    
    return Credentials.create(
        user_id=user_id,
        password=password,
        is_customer=is_customer
    )

# Usage
credentials = get_credentials_from_env()
```

### Production Configuration

```python
import os
import logging
from bookalimo import AsyncBookalimo
from bookalimo.transport.auth import Credentials

class BookalimoConfig:
    """Production configuration management."""
    
    def __init__(self):
        self.user_id = os.getenv("BOOKALIMO_USER_ID")
        self.password = os.getenv("BOOKALIMO_PASSWORD")
        self.is_customer = os.getenv("BOOKALIMO_IS_CUSTOMER", "false").lower() == "true"
        self.api_url = os.getenv("BOOKALIMO_API_URL", "https://www.bookalimo.com/web/api")
        self.google_places_key = os.getenv("GOOGLE_PLACES_API_KEY")
        
        self._validate()
    
    def _validate(self):
        """Validate required configuration."""
        if not self.user_id:
            raise ValueError("BOOKALIMO_USER_ID environment variable required")
        if not self.password:
            raise ValueError("BOOKALIMO_PASSWORD environment variable required")
    
    def get_credentials(self):
        """Get configured credentials."""
        return Credentials.create(
            user_id=self.user_id,
            password=self.password,
            is_customer=self.is_customer
        )
    
    def create_client(self):
        """Create configured client."""
        return AsyncBookalimo(
            credentials=self.get_credentials(),
            base_url=self.api_url,
            google_places_api_key=self.google_places_key
        )

# Usage
config = BookalimoConfig()
client = config.create_client()
```

## Security Best Practices

### Credential Storage

**✅ Secure Methods:**
```python
# Environment variables
credentials = Credentials.create(
    user_id=os.getenv("BOOKALIMO_USER_ID"),
    password=os.getenv("BOOKALIMO_PASSWORD")
)

# Key management services (AWS Secrets Manager, etc.)
import boto3

def get_credentials_from_secrets():
    client = boto3.client('secretsmanager')
    secret = client.get_secret_value(SecretId='bookalimo/credentials')
    secret_data = json.loads(secret['SecretString'])
    
    return Credentials.create(
        user_id=secret_data['user_id'],
        password=secret_data['password'],
        is_customer=secret_data.get('is_customer', False)
    )
```

**❌ Avoid These Methods:**
```python
# DON'T: Hard-coded credentials
credentials = Credentials.create(
    user_id="AGENCY123",  # Never hard-code credentials
    password="password123"
)

# DON'T: Unencrypted files
with open("credentials.txt") as f:
    password = f.read().strip()  # Insecure
```

### Password Security

```python
# The SDK handles password hashing automatically
credentials = Credentials.create(
    user_id="AGENCY123",
    password="my_secure_password"  # Plain text input
)

# Hash is computed automatically: SHA256(SHA256(password) + lower(user_id))
print(f"Hash: {credentials.password_hash}")  # Safe to log
```

## Client Integration

### Direct Credential Usage

```python
from bookalimo import AsyncBookalimo

credentials = Credentials.create(
    user_id="your_user_id",
    password="your_password"
)

async with AsyncBookalimo(credentials=credentials) as client:
    quote = await client.pricing.quote(...)
```

### Custom Transport

```python
from bookalimo.transport import AsyncTransport

# Transport with credentials
transport = AsyncTransport(
    credentials=credentials,
    base_url="https://www.bookalimo.com/web/api"
)

client = AsyncBookalimo(transport=transport)
```

### Credential Precedence

When both client and transport have credentials:

```python
# Transport credentials take precedence
transport = AsyncTransport(credentials=transport_creds)
client = AsyncBookalimo(
    credentials=client_creds,  # Ignored with warning
    transport=transport
)
# Uses transport_creds
```

## Authentication Errors

### Common Issues

**Invalid Credentials (HTTP 401)**
```python
from bookalimo.exceptions import BookalimoHTTPError

try:
    quote = await client.pricing.quote(...)
except BookalimoHTTPError as e:
    if e.status_code == 401:
        print("Authentication failed - check user ID and password")
        # Log error details
        if e.payload:
            print(f"Error details: {e.payload}")
```

**Missing Credentials**
```python
from bookalimo.exceptions import MissingCredentialsWarning
import warnings

# SDK warns about missing credentials
with warnings.catch_warnings():
    warnings.simplefilter("always")
    client = AsyncBookalimo()  # No credentials provided
    # Warning: No credentials provided; proceeding unauthenticated
```

### Debugging Authentication

```python
import logging

# Enable debug logging
logging.getLogger("bookalimo.transport").setLevel(logging.DEBUG)

async with AsyncBookalimo(credentials=credentials) as client:
    quote = await client.pricing.quote(...)
    # Debug logs will show if credentials are being sent
```

## Testing and Development

### Test Credentials

```python
def create_test_credentials():
    """Create credentials for testing."""
    return Credentials.create(
        user_id="TEST_AGENCY",
        password="test_password_123",
        is_customer=False
    )

# Use in tests
test_creds = create_test_credentials()
```

### Mock Authentication

```python
from unittest.mock import Mock
import pytest

@pytest.fixture
def mock_credentials():
    """Mock credentials for testing."""
    mock_creds = Mock(spec=Credentials)
    mock_creds.id = "TEST_AGENCY"
    mock_creds.password_hash = "mock_hash"
    mock_creds.is_customer = False
    return mock_creds

async def test_with_mock_auth(mock_credentials):
    client = AsyncBookalimo(credentials=mock_credentials)
    # Test client functionality
```

## Multiple Accounts

### Account Switching

```python
class BookalimoAccountManager:
    """Manage multiple Bookalimo accounts."""
    
    def __init__(self):
        self.accounts = {}
    
    def add_account(self, name: str, user_id: str, password: str, is_customer: bool = False):
        """Add an account."""
        self.accounts[name] = Credentials.create(
            user_id=user_id,
            password=password,
            is_customer=is_customer
        )
    
    def get_client(self, account_name: str):
        """Get client for specific account."""
        if account_name not in self.accounts:
            raise ValueError(f"Account '{account_name}' not found")
        
        return AsyncBookalimo(credentials=self.accounts[account_name])

# Usage
manager = BookalimoAccountManager()
manager.add_account("agency", "AGENCY123", "agency_password")
manager.add_account("customer", "customer@example.com", "customer_password", is_customer=True)

# Use different accounts
async with manager.get_client("agency") as agency_client:
    # Agency operations
    pass

async with manager.get_client("customer") as customer_client:
    # Customer operations  
    pass
```

### Context-Based Authentication

```python
from contextvars import ContextVar

# Context variable for current credentials
current_credentials: ContextVar[Credentials] = ContextVar('current_credentials')

def set_credentials(credentials: Credentials):
    """Set credentials for current context."""
    current_credentials.set(credentials)

def get_current_client():
    """Get client with current context credentials."""
    try:
        credentials = current_credentials.get()
        return AsyncBookalimo(credentials=credentials)
    except LookupError:
        raise ValueError("No credentials set in current context")

# Usage
agency_creds = Credentials.create("AGENCY123", "password")
set_credentials(agency_creds)

client = get_current_client()  # Uses agency credentials
```

## Advanced Configuration

### Custom Authentication Headers

```python
from bookalimo.transport import AsyncTransport
import httpx

class CustomHeaderTransport(AsyncTransport):
    """Transport with custom authentication headers."""
    
    def __init__(self, credentials, custom_headers=None, **kwargs):
        super().__init__(credentials=credentials, **kwargs)
        if custom_headers:
            self.headers.update(custom_headers)

# Usage
custom_transport = CustomHeaderTransport(
    credentials=credentials,
    custom_headers={"X-Custom-Auth": "custom_value"}
)

client = AsyncBookalimo(transport=custom_transport)
```

### Credential Rotation

```python
import asyncio
from datetime import datetime, timedelta

class RotatingCredentials:
    """Handle credential rotation for security."""
    
    def __init__(self, primary_creds, fallback_creds, rotation_interval=timedelta(hours=24)):
        self.primary = primary_creds
        self.fallback = fallback_creds
        self.rotation_interval = rotation_interval
        self.last_rotation = datetime.now()
    
    def get_current_credentials(self):
        """Get current active credentials."""
        if datetime.now() - self.last_rotation > self.rotation_interval:
            # Rotate credentials
            self.primary, self.fallback = self.fallback, self.primary
            self.last_rotation = datetime.now()
        
        return self.primary

# Usage
rotating = RotatingCredentials(primary_creds, fallback_creds)
client = AsyncBookalimo(credentials=rotating.get_current_credentials())
```

## Troubleshooting

### Common Authentication Issues

1. **Wrong User ID Format**
   ```python
   # Ensure user ID matches your account format
   credentials = Credentials.create(
       user_id="AGENCY123",  # Agency format
       # OR
       user_id="user@example.com",  # Email format for customers
       password="password"
   )
   ```

2. **Account Type Mismatch**
   ```python
   # Make sure is_customer flag matches your account type
   agency_creds = Credentials.create(
       user_id="AGENCY123",
       password="password",
       is_customer=False  # Important for agencies
   )
   ```

3. **Password Special Characters**
   ```python
   # SDK handles special characters correctly
   credentials = Credentials.create(
       user_id="user",
       password="p@ssw0rd!#$",  # Special chars OK
       is_customer=False
   )
   ```

### Debug Authentication

```python
def debug_credentials(credentials):
    """Debug credential information."""
    print(f"User ID: {credentials.id}")
    print(f"Password Hash: {credentials.password_hash[:16]}...")  # Truncated
    print(f"Is Customer: {credentials.is_customer}")
    
    # Test hash generation
    test_hash = Credentials.create_hash("test_password", credentials.id)
    print(f"Test hash length: {len(test_hash)}")

debug_credentials(credentials)
```