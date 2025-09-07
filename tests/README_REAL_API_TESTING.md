# Real API Integration Testing

This document explains how to set up and run real API integration tests that interact with the live Bookalimo API.

## 🔐 Credentials Setup

### Environment Variable Format

Set the `BOOKALIMO_TESTING_USER` environment variable with JSON credentials:

```bash
export BOOKALIMO_TESTING_USER='{"id": "your_user_id", "password": "your_password", "is_customer": "false"}'
```

### Credential Fields

- **`id`**: Your Bookalimo API user ID
- **`password`**: Your plain-text password (will be hashed automatically)
- **`is_customer`**: String `"true"` for customer accounts, `"false"` for agent accounts

### Security Notes

- **Never commit credentials to version control**
- Store credentials securely (environment variables, secrets managers)
- Use test/sandbox accounts when available
- The SDK automatically hashes passwords using the required algorithm

## 🧪 Running Real API Tests

### Quick Commands

```bash
# Run all real API integration tests
make test-real-api

# Run specific real API test file
pytest tests/test_real_api_integration.py -v

# Run with specific markers
pytest -m "integration and network" -v

# Run only real API performance tests
pytest tests/test_real_api_integration.py -m performance -v
```

### Test Categories

#### Standard Integration Tests (`@pytest.mark.integration @pytest.mark.network`)
- Basic API connectivity
- Authentication validation
- Pricing quote requests
- Reservation listing
- Error handling

#### Performance Tests (`@pytest.mark.performance @pytest.mark.slow`)
- Response time monitoring
- Concurrent request handling
- API rate limiting behavior
- Connection pooling validation

#### Authentication Tests
- Valid credential acceptance
- Invalid credential rejection
- Different account types (customer vs agent)

## 🏃‍♂️ Test Behavior

### Automatic Skipping
Tests automatically skip when credentials are not available:

```python
@pytest.mark.integration
@pytest.mark.network
def test_real_api_quote(skip_if_no_real_credentials):
    credentials = skip_if_no_real_credentials  # Auto-skips if None
    # Test implementation...
```

### Error Handling
Tests are designed to handle expected API errors gracefully:
- **Authentication errors (401/403)**: Cause test failures
- **Business logic errors (400/422)**: Expected and logged
- **Rate limiting (429)**: Expected for performance tests
- **Server errors (5xx)**: May indicate API issues

### Safe Test Comments
All real API requests include safe comments:
```python
customer_comment="SDK Integration Test - Safe to ignore"
```

## 🔧 CI/CD Integration

### GitHub Actions
The workflow automatically uses credentials from GitHub Secrets:

```yaml
env:
  BOOKALIMO_TESTING_USER: ${{ secrets.BOOKALIMO_TESTING_USER }}
```

### Local Development
For local development, set credentials in your shell:

```bash
# Option 1: Export in shell
export BOOKALIMO_TESTING_USER='{"id":"test_user","password":"test_pass","is_customer":"false"}'

# Option 2: Use .env file (add to .gitignore!)
echo 'BOOKALIMO_TESTING_USER={"id":"test_user","password":"test_pass","is_customer":"false"}' >> .env

# Option 3: Pass to specific test run
BOOKALIMO_TESTING_USER='...' pytest tests/test_real_api_integration.py
```

## 📊 Test Coverage

### API Endpoints Tested
- `POST /booking/price/` - Pricing quotes
- `POST /booking/reservation/list/` - Reservation listing  
- `POST /booking/details/` - Quote updates
- Authentication validation across all endpoints

### Scenarios Covered
- **Happy Path**: Successful API interactions
- **Error Cases**: Invalid requests, authentication failures
- **Performance**: Response times, concurrent requests
- **Edge Cases**: Timeout handling, connection errors

### Rate Types Tested
- Point-to-Point (P2P)
- Hourly bookings
- Different passenger/luggage combinations
- Various car class codes

## 🚨 Troubleshooting

### Common Issues

#### Tests Skip with "Real Bookalimo credentials not available"
```bash
# Check if environment variable is set
echo $BOOKALIMO_TESTING_USER

# Verify JSON format
python3 -c "import json, os; print(json.loads(os.environ['BOOKALIMO_TESTING_USER']))"
```

#### Authentication Errors (401/403)
- Verify user ID and password are correct
- Check account has API access
- Ensure using correct environment (sandbox vs production)

#### JSON Parsing Errors
```bash
# Validate JSON syntax
python3 -c "import json; json.loads('{\"id\":\"test\",\"password\":\"test\",\"is_customer\":\"false\"}')"
```

#### Connection/Timeout Errors
- Check network connectivity
- Verify API endpoint accessibility
- Review timeout settings in test configuration

### Debug Mode
Run with verbose output to see detailed error information:

```bash
pytest tests/test_real_api_integration.py -v -s --tb=long
```

## 🔒 Security Best Practices

### Credential Management
- Use dedicated test accounts (not production accounts)
- Rotate test credentials regularly
- Store in secure secrets management systems
- Never log full credentials in test output

### Test Safety
- All test requests include identifying comments
- Tests avoid creating real reservations when possible
- Use minimal viable test data
- Clean up any test data created

### CI/CD Security
- Store credentials as encrypted GitHub Secrets
- Use separate credentials for different environments
- Audit secret access regularly
- Monitor for credential exposure in logs

## 📈 Performance Expectations

### Response Times
- Pricing quotes: < 30 seconds (typically < 5 seconds)
- Reservation lists: < 15 seconds
- Authentication: < 10 seconds

### Concurrent Requests
- Limited concurrent testing (3 requests max)
- Respectful of API rate limits
- Exponential backoff for rate-limited requests

### Test Duration
- Full real API test suite: 2-5 minutes
- Performance tests: 1-3 minutes additional
- Individual API calls: 1-30 seconds each

## 🚀 Contributing

When adding new real API tests:

1. **Use the `skip_if_no_real_credentials` fixture**
2. **Add appropriate markers**: `@pytest.mark.integration @pytest.mark.network`
3. **Handle expected errors gracefully** (don't fail on business logic errors)
4. **Include safe, identifying comments** in API requests
5. **Test both success and failure scenarios**
6. **Respect API rate limits** in test design
7. **Document new test scenarios** in this README

### Example Test Pattern
```python
@pytest.mark.integration
@pytest.mark.network
@pytest.mark.slow
def test_new_api_feature(skip_if_no_real_credentials):
    """Test description."""
    credentials = skip_if_no_real_credentials
    
    with Bookalimo(credentials=credentials) as client:
        try:
            result = client.some_api_call(
                param="value",
                customer_comment="Test description - Safe to ignore"
            )
            # Assert expected behavior
            assert result.some_field
            
        except BookalimoHTTPError as e:
            # Handle expected errors
            if e.status_code in [401, 403]:
                pytest.fail(f"Authentication failed: {e}")
            # Log other errors but don't fail
            print(f"Expected API error: {e}")
```

This approach ensures robust, reliable real API testing while maintaining security and respecting API resources.