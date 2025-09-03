from collections.abc import Iterable
from typing import Any

from _typeshed import Incomplete

FIPS_RE: Incomplete
ABBR_RE: Incomplete
DC_STATEHOOD: Incomplete

class State:
    abbr: str
    ap_abbr: str | None
    capital: str | None
    capital_tz: str | None
    fips: str | None
    is_territory: bool
    is_obsolete: bool
    is_contiguous: bool
    is_continental: bool
    name: str
    name_metaphone: str
    statehood_year: int | None
    time_zones: list[str]
    def __init__(self, **kwargs: Any) -> None: ...
    def shapefile_urls(self) -> dict[str, str] | None: ...

def lookup(
    val: Any, field: str | None = None, use_cache: bool = True
) -> State | None: ...
def mapping(
    from_field: str, to_field: str, states: Iterable[State] | None = None
) -> dict[Any, Any]: ...

AL: State
AK: State
AS: State
AZ: State
AR: State
CA: State
CO: State
CT: State
DK: State
DE: State
DC: State
FL: State
GA: State
GU: State
HI: State
ID: State
IL: State
IN: State
IA: State
KS: State
KY: State
LA: State
ME: State
MD: State
MA: State
MI: State
MN: State
MS: State
MO: State
MT: State
NE: State
NV: State
NH: State
NJ: State
NM: State
NY: State
NC: State
ND: State
MP: State
OH: State
OK: State
OR: State
OL: State
PA: State
PI: State
PR: State
RI: State
SC: State
SD: State
TN: State
TX: State
UT: State
VT: State
VI: State
VA: State
WA: State
WV: State
WI: State
WY: State
OBSOLETE: list[State]
TERRITORIES: list[State]
STATES: list[State]
STATES_CONTIGUOUS: list[State]
STATES_CONTINENTAL: list[State]
STATES_AND_TERRITORIES: list[State]
COMMONWEALTHS: list[State]
