# Base Models

Core Pydantic models that provide foundational functionality for the Bookalimo SDK.

## ApiModel

::: bookalimo.schemas.base.ApiModel

The `ApiModel` class serves as the foundation for all API data structures in the Bookalimo SDK. It provides:

- **Automatic field name conversion**: Python `snake_case` fields are automatically converted to API `camelCase` format
- **Bidirectional compatibility**: Accepts both snake_case and camelCase field names on input
- **Enum serialization**: Configurable enum output (by value or name)
- **Unknown field handling**: Ignores unknown fields from API responses

### Key Features

#### Field Name Conversion

All field names are automatically converted between Python conventions and API format:

```python
from bookalimo.schemas.base import ApiModel

class Example(ApiModel):
    user_name: str  # → userName in API
    date_time: str  # → dateTime in API
```

#### Enum Handling

Enums are serialized by value by default, but can be configured:

```python
# Default: serialize by value
data = model.model_dump()  

# Serialize by name
data = model.model_dump(context={"enum_out": "name"})
```

#### Input Flexibility

Models accept both field naming conventions:

```python
# Both work:
model = Example(user_name="john")
model = Example(userName="john")
```

### Configuration

The model uses Pydantic v2 configuration:

- `alias_generator=to_camel`: Auto-generates camelCase aliases
- `validate_by_alias=True`: Accepts camelCase input
- `validate_by_name=True`: Accepts snake_case input  
- `serialize_by_alias=True`: Uses camelCase in output
- `use_enum_values=False`: Custom enum handling via serializer
- `extra="ignore"`: Ignores unknown API fields

### Usage

All SDK models inherit from `ApiModel`:

```python
from bookalimo.schemas.booking import Location, LocationType
from bookalimo.schemas.base import ApiModel

# All booking models extend ApiModel
location = Location(
    type=LocationType.ADDRESS,
    address=address_data
)

# Serialization uses camelCase automatically
json_data = location.model_dump()
```