from __future__ import annotations

import csv
import math
import os
import re
import unicodedata
from functools import lru_cache
from importlib.resources import files
from types import MappingProxyType
from typing import Any, Dict, List, Optional, Tuple, cast

import numpy as np
from numpy.typing import NDArray
from rapidfuzz import fuzz, process

from bookalimo.schemas.places import GooglePlace, ResolvedAirport

# ---------- Config ----------
CSV_PATH = os.environ.get(
    "AIRPORTS_CSV", str(files("airportsdata").joinpath("airports.csv"))
)
DEFAULT_MAX_RESULTS = 20  # number of airports to return
DIST_KM_SCALE = 200.0  # distance scale for proximity confidence

# Google types that clearly indicate “airport-ish” places
AIRPORTY_TYPES = {
    "airport",
    "international_airport",
    "airstrip",
    "heliport",
}


# ---------- Helpers ----------
def _norm(s: Optional[str]) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def _haversine_km_scalar_to_many(
    lat1_rad: float,
    lon1_rad: float,
    lat2_rad: NDArray[np.float64],
    lon2_rad: NDArray[np.float64],
) -> NDArray[np.float64]:
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0) ** 2
    )
    c: NDArray[np.float64] = 2.0 * np.arcsin(np.sqrt(a))
    return cast(NDArray[np.float64], 6371.0088 * c)  # mean Earth radius (km)


def _place_points(places: list[GooglePlace]) -> list[tuple[float, float]]:
    """
    Extract (lat, lon) from Places responses. Prefers 'location', then viewport center,
    then Plus Code (if the openlocationcode lib is available).
    """
    pts: list[tuple[float, float]] = []
    for p in places or []:
        # p.location (LatLng)
        loc = getattr(p, "location", None)
        if loc is not None and hasattr(loc, "latitude") and hasattr(loc, "longitude"):
            pts.append((float(loc.latitude), float(loc.longitude)))
            continue

        # p.viewport (Viewport -> center)
        vp = getattr(p, "viewport", None)
        if vp is not None and hasattr(vp, "high") and hasattr(vp, "low"):
            try:
                lat = (float(vp.high.latitude) + float(vp.low.latitude)) / 2.0
                lon = (float(vp.high.longitude) + float(vp.low.longitude)) / 2.0
                pts.append((lat, lon))
                continue
            except Exception:
                pass
    return pts


def _place_hints(places: list[GooglePlace]) -> list[str]:
    """
    Collect high-utility strings from Places to augment text matching.
    Prioritizes places whose types include airport-ish categories.
    """
    hints_prioritized: list[str] = []
    hints_general: list[str] = []

    for p in places or []:
        types = set(getattr(p, "types", []) or [])
        primary = getattr(p, "primary_type", None) or ""
        airporty = bool(types & AIRPORTY_TYPES) or (primary in AIRPORTY_TYPES)

        # Display name & address
        disp = getattr(p, "display_name", None)
        disp_txt = getattr(disp, "text", None) if disp is not None else None
        addr = getattr(p, "formatted_address", None)

        # A few relational names (areas/landmarks)
        adesc = getattr(p, "address_descriptor", None)
        area_names = []
        lm_names = []
        if adesc is not None:
            for a in (getattr(adesc, "areas", []) or [])[:2]:
                dn = getattr(a, "display_name", None)
                if dn and getattr(dn, "text", None):
                    area_names.append(dn.text)
            for lm in (getattr(adesc, "landmarks", []) or [])[:2]:
                dn = getattr(lm, "display_name", None)
                if dn and getattr(dn, "text", None):
                    lm_names.append(dn.text)

        # Gather hint candidates
        candidates = [disp_txt, addr, *area_names, *lm_names]
        candidates = [c for c in candidates if c]
        if not candidates:
            continue

        # Prioritize hints if the place is airport-ish
        (hints_prioritized if airporty else hints_general).extend(candidates[:2])

    # De-dup (by normalized form) and cap to keep RF calls small
    seen = set()

    def dedup_cap(items: list[str], cap: int) -> list[str]:
        out = []
        for s in items:
            k = _norm(s)
            if not k or k in seen:
                continue
            out.append(s)
            seen.add(k)
            if len(out) >= cap:
                break
        return out

    return dedup_cap(hints_prioritized, cap=3) + dedup_cap(hints_general, cap=2)


def _parse_coord(s: Optional[str]) -> float:
    """Return float value or NaN for None/blank/invalid strings."""
    if s is None:
        return float("nan")
    s = s.strip()
    if s == "":
        return float("nan")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def _frozen_np_float(arr_like: List[float]) -> NDArray[np.float64]:
    """Create a float64 numpy array and set writeable=False."""
    a = np.array(arr_like, dtype=np.float64)
    a.setflags(write=False)
    return a


def _frozen_np_bool(arr_like: List[bool]) -> NDArray[np.bool_]:
    """Create a bool numpy array and set writeable=False."""
    a = np.array(arr_like, dtype=bool)
    a.setflags(write=False)
    return cast(NDArray[np.bool_], a)


# ---------- Data loading with immutable return + dual indexes ----------
@lru_cache(maxsize=1)
def _load_data() -> MappingProxyType[str, Any]:
    """
    Loads and caches airport rows and vectorized fields.
    Expects CSV columns: icao,iata,name,city,subd,country,elevation,lat,lon,tz,lid

    Returns an immutable mapping with:
      - rows: tuple[dict[str, Any]]          (each row dict should be treated as read-only)
      - lat_rad, lon_rad: np.ndarray (float64, write-protected)
      - keys: tuple[str]                     (normalized text used for fuzzy matching)
      - codes: tuple[tuple[str, str]]        (iata, icao)
      - has_coords: np.ndarray (bool, write-protected)
      - idx_iata: Mapping[str, int]          (UPPERCASE IATA -> row index)
      - idx_icao: Mapping[str, int]          (UPPERCASE ICAO -> row index)
    """
    rows_mut: List[Dict[str, Any]] = []
    lat_rad_mut: List[float] = []
    lon_rad_mut: List[float] = []
    keys_mut: List[str] = []
    codes_mut: List[Tuple[str, str]] = []
    has_coords_mut: List[bool] = []
    idx_iata_mut: Dict[str, int] = {}
    idx_icao_mut: Dict[str, int] = {}

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            name = (r.get("name") or "").strip()
            city = (r.get("city") or "").strip()
            iata = (r.get("iata") or "").strip() or None
            icao = (r.get("icao") or "").strip() or None

            lat = _parse_coord(cast(Optional[str], r.get("lat")))
            lon = _parse_coord(cast(Optional[str], r.get("lon")))
            valid = not (math.isnan(lat) or math.isnan(lon))

            idx = len(rows_mut)
            rows_mut.append(
                {
                    "name": name,
                    "city": city,
                    "iata": iata,
                    "icao": icao,
                    "lat": lat,
                    "lon": lon,
                }
            )

            # radians() propagates NaN; no conditional needed
            lat_rad_mut.append(math.radians(lat))
            lon_rad_mut.append(math.radians(lon))
            has_coords_mut.append(valid)

            code_bits = (
                " ".join([c for c in (iata, icao) if c]) if (iata or icao) else ""
            )
            keys_mut.append(_norm(f"{name} {city} {code_bits}"))
            codes_mut.append((iata or "", icao or ""))

            # Build dual indexes (first occurrence wins)
            if iata:
                iu = iata.upper()
                if iu not in idx_iata_mut:
                    idx_iata_mut[iu] = idx
            if icao:
                iu = icao.upper()
                if iu not in idx_icao_mut:
                    idx_icao_mut[iu] = idx

    # Freeze everything
    rows = tuple(rows_mut)
    lat_rad = _frozen_np_float(lat_rad_mut)
    lon_rad = _frozen_np_float(lon_rad_mut)
    keys = tuple(keys_mut)
    codes = tuple(codes_mut)
    has_coords = _frozen_np_bool(has_coords_mut)
    idx_iata = MappingProxyType(dict(idx_iata_mut))  # proxy ensures read-only
    idx_icao = MappingProxyType(dict(idx_icao_mut))

    # Return a read-only top-level mapping
    return MappingProxyType(
        {
            "rows": rows,
            "lat_rad": lat_rad,
            "lon_rad": lon_rad,
            "keys": keys,
            "codes": codes,
            "has_coords": has_coords,
            "idx_iata": idx_iata,
            "idx_icao": idx_icao,
        }
    )


# ---------- Convenience lookups (O(1) via dual indexes) ----------
def get_row_by_iata(code: str) -> Optional[dict[str, Any]]:
    """Return the airport row for an IATA code, or None if not found."""
    if not code:
        return None
    data = _load_data()
    idx = data["idx_iata"].get(code.upper())
    return data["rows"][idx] if idx is not None else None


def get_row_by_icao(code: str) -> Optional[dict[str, Any]]:
    """Return the airport row for an ICAO code, or None if not found."""
    if not code:
        return None
    data = _load_data()
    idx = data["idx_icao"].get(code.upper())
    return data["rows"][idx] if idx is not None else None


def _try_direct_code_lookup(query: str) -> Optional[ResolvedAirport]:
    """
    Try to resolve the query as a direct IATA or ICAO code match.
    Returns ResolvedAirport with high confidence if found, None otherwise.
    """
    if not query:
        return None

    # Clean and normalize the query for code matching
    code = query.strip().upper()
    if not code:
        return None

    # Try IATA first (3 characters)
    if len(code) == 3:
        row = get_row_by_iata(code)
        if row:
            return ResolvedAirport(
                name=row["name"],
                city=row["city"],
                iata_code=row["iata"],
                icao_code=row["icao"],
                confidence=0.95,  # High confidence for exact code matches
            )

    # Try ICAO (4 characters)
    elif len(code) == 4:
        row = get_row_by_icao(code)
        if row:
            return ResolvedAirport(
                name=row["name"],
                city=row["city"],
                iata_code=row["iata"],
                icao_code=row["icao"],
                confidence=0.95,  # High confidence for exact code matches
            )

    return None


# ---------- Main ----------
def resolve_airport(
    query: str,
    places_response: list[GooglePlace],
    max_distance_km: Optional[float] = 200,
    max_results: Optional[int] = 5,
    confidence_threshold: Optional[float] = 0.5,
    text_weight: float = 0.5,
) -> list[ResolvedAirport]:
    """
    Resolve airport candidates given a query and a list of Places responses.
    Args:
        query: The text query to resolve an airport from.
        places_response: The list of Places responses to resolve an airport from.
        max_distance_km: The maximum distance in kilometers to any of the places to consider for proximity.
        max_results: The maximum number of results to return.
        confidence_threshold: The confidence threshold to consider for the results. Default is 0.5.
        text_weight: The weight for the text confidence.
    Returns:
        The list of resolved airports ordered by confidence.
    """

    # First, try direct IATA/ICAO code lookup for exact matches
    direct_match = _try_direct_code_lookup(query)
    if direct_match is not None:
        return [direct_match]

    data = _load_data()
    rows: list[dict[str, Any]] = data["rows"]
    n = len(rows)
    if n == 0:
        return []

    # ---- Proximity anchors from Places ----
    anchors = _place_points(places_response)
    min_dist = np.full(n, np.inf, dtype=float)
    if anchors:
        for lat, lon in anchors:
            lat1 = math.radians(lat)
            lon1 = math.radians(lon)
            d = _haversine_km_scalar_to_many(
                lat1, lon1, data["lat_rad"], data["lon_rad"]
            )
            np.nan_to_num(d, copy=False, nan=np.inf)  # NaN coords -> ∞
            np.minimum(min_dist, d, out=min_dist)

    prox = np.zeros(n, dtype=float)
    if anchors:
        prox = 100.0 * np.exp(-min_dist / float(DIST_KM_SCALE))

    # ---- Text score: best across augmented queries ----
    hints = _place_hints(places_response)
    q_variants = [_norm(query)] + [_norm(f"{query} {h}") for h in hints]
    # Single cdist call over up to 1+5 variants keeps things fast
    scores_matrix = process.cdist(q_variants, data["keys"], scorer=fuzz.token_set_ratio)
    text_scores = np.array(scores_matrix.max(axis=0), dtype=float)

    # Cap to 0..100
    text_scores = np.clip(text_scores, 0.0, 100.0)

    # ---- Blend + optional radius mask ----
    final = text_weight * text_scores + (1.0 - text_weight) * prox

    # Apply mask only if we have anchors and caller asked for one.
    # IMPORTANT: rows without coords are still included (mask keeps them).
    if anchors and max_distance_km is not None:
        mask = (~data["has_coords"]) | (min_dist <= float(max_distance_km))
    else:
        mask = np.ones(n, dtype=bool)

    final_masked = np.where(mask, final, -np.inf)
    order = np.argsort(-final_masked)
    top = order[: max_results or DEFAULT_MAX_RESULTS]

    results: list[ResolvedAirport] = []
    for idx in top:
        if final_masked[idx] == -np.inf:
            break
        r = rows[idx]
        text_confidence = float(text_scores[idx] / 100.0)
        proximity_confidence = float(prox[idx] / 100.0)
        if (
            confidence_threshold is not None
            and (text_confidence + proximity_confidence) / 2.0 < confidence_threshold
        ):
            continue
        results.append(
            ResolvedAirport(
                name=r["name"],
                city=r["city"],
                iata_code=r["iata"] or None,
                icao_code=r["icao"] or None,
                confidence=(text_confidence + proximity_confidence) / 2.0,
            )
        )

    results.sort(key=lambda x: x.confidence, reverse=True)

    return results
