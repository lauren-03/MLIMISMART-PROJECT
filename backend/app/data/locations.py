"""Tea growing areas of Thyolo and Mulanje, with coordinates for the weather API."""

LOCATIONS: dict[str, dict] = {
    # ------------------------------ Thyolo ---------------------------------
    "Thyolo":       {"lat": -16.0667, "lon": 35.1333, "district": "Thyolo",  "altitude_m": 780,  "kind": "boma"},
    "Luchenza":     {"lat": -16.0028, "lon": 35.3078, "district": "Thyolo",  "altitude_m": 820,  "kind": "trading_centre"},
    "Bvumbwe":      {"lat": -15.9167, "lon": 35.0667, "district": "Thyolo",  "altitude_m": 1150, "kind": "research_station"},
    "Thekerani":    {"lat": -16.2500, "lon": 35.2167, "district": "Thyolo",  "altitude_m": 700,  "kind": "trading_centre"},
    "Makwasa":      {"lat": -16.1167, "lon": 35.1000, "district": "Thyolo",  "altitude_m": 800,  "kind": "trading_centre"},
    "Khonjeni":     {"lat": -16.0300, "lon": 35.2200, "district": "Thyolo",  "altitude_m": 900,  "kind": "trading_centre"},
    "Masambanjati": {"lat": -16.1500, "lon": 35.1800, "district": "Thyolo",  "altitude_m": 750,  "kind": "trading_centre"},
    "Malamulo":     {"lat": -16.0900, "lon": 35.1500, "district": "Thyolo",  "altitude_m": 800,  "kind": "mission"},
    "Satemwa":      {"lat": -16.0500, "lon": 35.1000, "district": "Thyolo",  "altitude_m": 950,  "kind": "estate"},
    "Nchima":       {"lat": -16.0200, "lon": 35.1700, "district": "Thyolo",  "altitude_m": 900,  "kind": "estate"},
    "Goliati":      {"lat": -16.0400, "lon": 35.0000, "district": "Thyolo",  "altitude_m": 850,  "kind": "trading_centre"},
    # ------------------------------ Mulanje --------------------------------
    "Mulanje":      {"lat": -16.0319, "lon": 35.5075, "district": "Mulanje", "altitude_m": 650,  "kind": "boma"},
    "Chitakale":    {"lat": -16.0167, "lon": 35.5333, "district": "Mulanje", "altitude_m": 670,  "kind": "trading_centre"},
    "Mimosa":       {"lat": -16.0700, "lon": 35.5800, "district": "Mulanje", "altitude_m": 700,  "kind": "research_station"},
    "Lujeri":       {"lat": -16.0500, "lon": 35.6500, "district": "Mulanje", "altitude_m": 750,  "kind": "estate"},
    "Muloza":       {"lat": -16.1000, "lon": 35.6333, "district": "Mulanje", "altitude_m": 720,  "kind": "border_post"},
    "Chisitu":      {"lat": -16.0000, "lon": 35.6200, "district": "Mulanje", "altitude_m": 700,  "kind": "trading_centre"},
    "Limbuli":      {"lat": -16.1000, "lon": 35.5500, "district": "Mulanje", "altitude_m": 640,  "kind": "trading_centre"},
    "Thuchila":     {"lat": -15.9300, "lon": 35.4000, "district": "Mulanje", "altitude_m": 640,  "kind": "trading_centre"},
    "Chonde":       {"lat": -15.9500, "lon": 35.4500, "district": "Mulanje", "altitude_m": 650,  "kind": "trading_centre"},
    "Kambenje":     {"lat": -16.0400, "lon": 35.4000, "district": "Mulanje", "altitude_m": 700,  "kind": "trading_centre"},
    "Nkando":       {"lat": -16.1300, "lon": 35.4800, "district": "Mulanje", "altitude_m": 620,  "kind": "trading_centre"},
    "Milonde":      {"lat": -16.1700, "lon": 35.6300, "district": "Mulanje", "altitude_m": 650,  "kind": "trading_centre"},
}

DISTRICTS = ["Thyolo", "Mulanje"]

DEFAULT_LOCATION = "Thyolo"

# How each kind of place is described in the interface.
KIND_LABELS = {
    "boma": ("District headquarters", "Boma la boma"),
    "trading_centre": ("Trading centre", "Msika"),
    "research_station": ("Research station", "Malo ofufuza"),
    "estate": ("Tea estate area", "Dera la esiteti ya tiyi"),
    "mission": ("Mission", "Mishoni"),
    "border_post": ("Border area", "Malire"),
}


def areas_in(district: str) -> list[str]:
    """Area names in one district, in the order listed above."""
    return [name for name, place in LOCATIONS.items() if place["district"] == district]


def match(name: str | None) -> str | None:
    """The known area a farmer-entered name refers to, or None.

    Exact match first, then partial ("mulanje boma", "bvumbwe trading centre").
    Partial matching needs at least four letters so "ch" does not match
    Chitakale by accident.
    """
    cleaned = (name or "").strip().lower()
    if not cleaned:
        return None
    for key in LOCATIONS:
        if key.lower() == cleaned:
            return key
    if len(cleaned) < 4:
        return None
    for key in LOCATIONS:
        if key.lower() in cleaned or cleaned in key.lower():
            return key
    return None


def resolve(name: str | None) -> tuple[str, dict]:
    """Like match(), but falls back to the default district rather than failing,
    because farmers type village names freely and advice must always be given.
    """
    key = match(name) or DEFAULT_LOCATION
    return key, LOCATIONS[key]
