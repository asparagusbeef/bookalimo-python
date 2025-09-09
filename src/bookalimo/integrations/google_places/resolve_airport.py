from __future__ import annotations

import csv
import math
import os
import re
import unicodedata
from functools import lru_cache
from importlib.resources import files
from typing import Any, Optional, cast

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

# Small bonus when a candidate airport’s IATA/ICAO matches codes hinted by Places
CODE_BONUS_QUERY = 15.0  # user typed a code (strong)
CODE_BONUS_PLACES = 8.0  # code inferred from Places strings (softer)


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


def _looks_like_code(q: str) -> tuple[Optional[str], Optional[str]]:
    q = q.strip().upper()
    if re.fullmatch(r"[A-Z0-9]{3}", q):
        return (q, None)  # likely IATA
    if re.fullmatch(r"[A-Z0-9]{4}", q):
        return (None, q)  # likely ICAO
    return (None, None)


def _extract_codes_from_text(s: str) -> tuple[set[str], set[str]]:
    """
    Pull 3- or 4-char uppercase tokens that *could* be codes.
    We'll only use these with a small bonus and only if the place looks airport-ish.
    """
    tokens = set(re.findall(r"\b[A-Z0-9]{3,4}\b", s.upper()))
    iata = {t for t in tokens if re.fullmatch(r"[A-Z]{3}", t)}
    icao = {t for t in tokens if re.fullmatch(r"[A-Z0-9]{4}", t)}
    return iata, icao


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


def _place_hints_and_codes(
    places: list[GooglePlace],
) -> tuple[list[str], set[str], set[str]]:
    """
    Collect a few high-utility strings from Places to augment text matching,
    plus soft code candidates (IATA/ICAO) extracted from those strings.
    We prioritize places whose types include airport-ish categories.
    """
    hints_prioritized: list[str] = []
    hints_general: list[str] = []
    iata_cand: set[str] = set()
    icao_cand: set[str] = set()

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

        # Extract soft code candidates from the most descriptive strings
        for s in candidates[:2]:
            i3, i4 = _extract_codes_from_text(s)
            if airporty:
                iata_cand |= i3
                icao_cand |= i4

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

    hints = dedup_cap(hints_prioritized, cap=3) + dedup_cap(hints_general, cap=2)
    return hints, iata_cand, icao_cand


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


@lru_cache(maxsize=1)
def _load_data() -> dict[str, Any]:
    """
    Loads and caches airport rows and vectorized fields.
    Expects CSV columns: icao,iata,name,city,subd,country,elevation,lat,lon,tz,lid
    """
    rows: list[dict[str, Any]] = []
    lat_rad: list[float] = []
    lon_rad: list[float] = []
    keys: list[str] = []  # normalized text used for fuzzy matching
    codes: list[tuple[str, str]] = []  # (iata, icao)
    has_coords: list[bool] = []

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            name = (r.get("name") or "").strip()
            city = (r.get("city") or "").strip()
            iata = (r.get("iata") or "").strip() or None
            icao = (r.get("icao") or "").strip() or None

            # Robust coords: keep NaN if missing/invalid
            lat_s = cast(Optional[str], r.get("lat"))
            lon_s = cast(Optional[str], r.get("lon"))
            lat = _parse_coord(lat_s)
            lon = _parse_coord(lon_s)

            valid = not (math.isnan(lat) or math.isnan(lon))

            rows.append(
                {
                    "name": name,
                    "city": city,
                    "iata": iata,
                    "icao": icao,
                    "lat": lat,
                    "lon": lon,
                }
            )
            lat_rad.append(math.radians(lat) if valid else float("nan"))
            lon_rad.append(math.radians(lon) if valid else float("nan"))
            has_coords.append(valid)

            code_bits = (
                " ".join([c for c in (iata, icao) if c]) if (iata or icao) else ""
            )
            keys.append(_norm(f"{name} {city} {code_bits}"))
            codes.append((iata or "", icao or ""))

    return {
        "rows": rows,
        "lat_rad": np.array(lat_rad, dtype=float),
        "lon_rad": np.array(lon_rad, dtype=float),
        "keys": np.array(keys, dtype=object),
        "codes": codes,
        "has_coords": np.array(has_coords, dtype=bool),
    }


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
    hints, iata_from_places, icao_from_places = _place_hints_and_codes(places_response)
    q_variants = [_norm(query)] + [_norm(f"{query} {h}") for h in hints]
    # Single cdist call over up to 1+5 variants keeps things fast
    scores_matrix = process.cdist(q_variants, data["keys"], scorer=fuzz.token_set_ratio)
    text_scores = np.array(scores_matrix.max(axis=0), dtype=float)

    # ---- Code bonuses ----
    # 1) If the *user* typed a code, stronger bonus
    iata_q, icao_q = _looks_like_code(query)
    if iata_q or icao_q:
        if iata_q:
            text_scores += (
                np.fromiter(
                    ((1.0 if iata_q == iata else 0.0) for iata, _ in data["codes"]),
                    float,
                    count=n,
                )
                * CODE_BONUS_QUERY
            )
        if icao_q:
            text_scores += (
                np.fromiter(
                    ((1.0 if icao_q == icao else 0.0) for _, icao in data["codes"]),
                    float,
                    count=n,
                )
                * CODE_BONUS_QUERY
            )

    # 2) If Places hints include codes (e.g., “JFK Terminal 4”), soft bonus
    if iata_from_places:
        text_scores += (
            np.fromiter(
                (
                    (1.0 if (iata in iata_from_places) else 0.0)
                    for iata, _ in data["codes"]
                ),
                float,
                count=n,
            )
            * CODE_BONUS_PLACES
        )
    if icao_from_places:
        text_scores += (
            np.fromiter(
                (
                    (1.0 if (icao in icao_from_places) else 0.0)
                    for _, icao in data["codes"]
                ),
                float,
                count=n,
            )
            * CODE_BONUS_PLACES
        )

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
