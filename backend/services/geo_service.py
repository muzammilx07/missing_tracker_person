"""
Geolocation service using Nominatim (OpenStreetMap geocoding, free, no API key).
Handles reverse geocoding, address search, and police station discovery.
"""

import requests
import time
import math
from typing import Optional, Dict, List
from config import settings


NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _get_headers() -> Dict[str, str]:
    """Get standard headers for Nominatim requests."""
    return {
        "User-Agent": settings.NOMINATIM_USER_AGENT
    }


def reverse_geocode(lat: float, lng: float) -> Dict:
    """
    Reverse geocode coordinates to address using Nominatim.
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Returns:
        Dict with keys: city, state, address (or all None on error)
    
    Note:
        Sleeps 1 second after call to respect Nominatim rate limits.
    """
    
    try:
        params = {
            "lat": lat,
            "lon": lng,
            "format": "json",
            "addressdetails": 1
        }
        
        response = requests.get(
            f"{NOMINATIM_BASE}/reverse",
            params=params,
            headers=_get_headers(),
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        address = data.get("address", {})
        
        # Extract components with fallbacks
        city = address.get("city") or address.get("town") or address.get("village")
        state = address.get("state")
        road = address.get("road", "")
        suburb = address.get("suburb", "")
        
        # Build full address string
        address_str = f"{road}, {suburb}".strip(", ")
        if not address_str:
            address_str = address.get("place_name", "")
        
        result = {
            "city": city,
            "state": state,
            "address": address_str
        }
        
    except Exception as e:
        print(f"[GEO] Reverse geocode error for ({lat}, {lng}): {str(e)}")
        result = {
            "city": None,
            "state": None,
            "address": None
        }
    
    time.sleep(1)  # Rate limit: 1 second between Nominatim calls
    return result


def geocode_address(address: str, city: str, state: str) -> Optional[Dict]:
    """
    Geocode address text to coordinates using Nominatim.
    
    Args:
        address: Street address
        city: City name
        state: State/province name
    
    Returns:
        Dict with lat/lng, or None on failure
    
    Note:
        Sleeps 1 second after call to respect rate limits.
    """
    
    try:
        search_str = f"{address}, {city}, {state}, India"
        
        params = {
            "q": search_str,
            "format": "json",
            "limit": 1
        }
        
        response = requests.get(
            f"{NOMINATIM_BASE}/search",
            params=params,
            headers=_get_headers(),
            timeout=10
        )
        response.raise_for_status()
        
        results = response.json()
        
        if results and len(results) > 0:
            return {
                "lat": float(results[0]["lat"]),
                "lng": float(results[0]["lon"])
            }
        
        return None
        
    except Exception as e:
        print(f"[GEO] Geocode address error for '{search_str}': {str(e)}")
        return None
    
    finally:
        time.sleep(1)


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two points using haversine formula.
    
    Args:
        lat1, lng1: Point 1 coordinates
        lat2, lng2: Point 2 coordinates
    
    Returns:
        Distance in kilometers
    """
    
    R = 6371.0  # Earth radius in km
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def find_police_stations(lat: float, lng: float, radius_meters: int = 5000) -> List[Dict]:
    """
    Find police stations near coordinates using Overpass API (OpenStreetMap data).
    Completely free, no API key needed.
    
    Args:
        lat: Center latitude
        lng: Center longitude
        radius_meters: Search radius in meters (default 5000)
    
    Returns:
        List of up to 5 police stations sorted by distance, each with:
        {
            "osm_id": str,
            "name": str,
            "address": str,
            "lat": float,
            "lng": float,
            "phone": Optional[str],
            "distance_km": float
        }
    
    Note:
        Overpass API can be slow (5-10 seconds) — that's normal.
    """
    
    results = []
    
    try:
        # Overpass QL query for police stations
        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"="police"](around:{radius_meters},{lat},{lng});
          way["amenity"="police"](around:{radius_meters},{lat},{lng});
        );
        out body center;
        """
        
        print(f"[GEO] Querying Overpass for police stations near ({lat}, {lng})")
        
        response = requests.post(
            OVERPASS_URL,
            data={"data": query},
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        elements = data.get("elements", [])
        
        print(f"[GEO] Found {len(elements)} police locations from Overpass")
        
        for element in elements:
            try:
                tags = element.get("tags", {})
                
                # Get name
                name = tags.get("name") or tags.get("name:en") or "Police Station"
                
                # Get coordinates
                if element["type"] == "node":
                    station_lat = element["lat"]
                    station_lng = element["lon"]
                elif element["type"] == "way" and "center" in element:
                    station_lat = element["center"]["lat"]
                    station_lng = element["center"]["lon"]
                else:
                    continue
                
                # Build address
                street = tags.get("addr:street", "")
                housenumber = tags.get("addr:housenumber", "")
                city = tags.get("addr:city", "")
                full_addr = f"{housenumber} {street}, {city}".strip(", ")
                
                if not full_addr:
                    full_addr = tags.get("addr:full", "Unknown")
                
                # Get phone
                phone = tags.get("phone") or tags.get("contact:phone")
                
                # Calculate distance
                distance_km = haversine(lat, lng, station_lat, station_lng)
                
                # Build result
                result = {
                    "osm_id": str(element["id"]),
                    "name": name,
                    "address": full_addr,
                    "lat": station_lat,
                    "lng": station_lng,
                    "phone": phone,
                    "distance_km": round(distance_km, 2)
                }
                
                results.append(result)
            
            except Exception as e:
                print(f"[GEO] Error parsing station: {str(e)}")
                continue
        
        # Sort by distance and return top 5
        results.sort(key=lambda x: x["distance_km"])
        results = results[:5]
        
        print(f"[GEO] Returning {len(results)} police stations")
        
        return results
    
    except requests.Timeout:
        print(f"[GEO] Overpass API timeout (expected for large areas, retry later)")
        return []
    
    except Exception as e:
        print(f"[GEO] Police station search error: {str(e)}")
        return []
