#!/usr/bin/env python3
"""Register a Brazil-states custom GeoJSON in Metabase so region (choropleth)
maps can be drawn, joined on the 2-letter UF code (sigla) used by our data.
"""
import json, urllib.request, urllib.error

MB = "http://localhost:3000"
EMAIL, PASS = "admin@dvd.local", "Dvdproj123!"
MAP_ID = "brazil_states"
GEOJSON_URL = ("https://raw.githubusercontent.com/codeforamerica/click_that_hood/"
               "master/public/data/brazil-states.geojson")


def api(method, path, body=None, tok=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(MB + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if tok:
        req.add_header("X-Metabase-Session", tok)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> {e.code}: {e.read().decode()[:400]}")


def main():
    tok = api("POST", "/api/session", {"username": EMAIL, "password": PASS})["id"]
    current = api("GET", "/api/setting/custom-geojson", tok=tok) or {}
    # keep any builtin/default entries, add ours
    current = {k: v for k, v in current.items() if not v.get("builtin")}
    current[MAP_ID] = {
        "name": "Brazil states",
        "url": GEOJSON_URL,
        "region_key": "sigla",
        "region_name": "name",
    }
    api("PUT", "/api/setting/custom-geojson", {"value": current}, tok=tok)
    print("Registered custom map:", MAP_ID)


if __name__ == "__main__":
    main()
