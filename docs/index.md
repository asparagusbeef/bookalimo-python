# Bookalimo Python SDK

Python client library for the Book-A-Limo transportation booking API with async/sync support, type safety, and Google Places integration.

## Getting Started

Install the SDK:
```bash
pip install bookalimo
# For Google Places integration:
pip install bookalimo[places]
```

The SDK provides two main clients:

- `AsyncBookalimo` - for async applications
- `Bookalimo` - for sync applications

Both clients expose the same services:

- `.pricing` - get quotes and update booking details
- `.reservations` - book, list, modify, and cancel reservations
- `.places` - Google Places search and geocoding (optional)

Jump to the [Quickstart](guide/quickstart.md) for a complete example.
