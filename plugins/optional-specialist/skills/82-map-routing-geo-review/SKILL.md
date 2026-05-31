---
name: map-routing-geo-review
description: Use when you need to review maps, routing, geospatial data, markers, clustering, geocoding, and location privacy.
---

# Map, Routing & Geospatial Review

## Purpose
Review map integration code for correctness, performance, API key security, and location privacy. Covers Leaflet, Mapbox GL JS, Google Maps Platform, OpenLayers; routing and directions APIs; geocoding and reverse geocoding; marker rendering and clustering; coordinate handling; tile caching; and user location data.

## When to use
- Reviewing code that integrates a map library (Leaflet, Mapbox, Google Maps, OpenLayers, deck.gl).
- Auditing a routing or directions feature (turn-by-turn, isochrone, fleet routing).
- Evaluating geocoding or reverse geocoding API usage.
- Reviewing map performance with large marker sets (>200 markers).
- Checking how user location (`navigator.geolocation`) is collected, stored, or transmitted.
- Reviewing tile server configuration, caching headers, or self-hosted tile infrastructure.

## When not to use
- Pure database GIS query review (PostGIS, Spatialite) with no front-end map — use a backend/DB review skill.
- Data pipeline ETL of geospatial files (GeoJSON, Shapefile, GeoTIFF) with no map rendering.

## Procedure

### 1. API key security
- Google Maps Platform, Mapbox, and HERE all require API keys. Verify keys are:
 - Not hardcoded in client-side JavaScript bundles shipped to the browser without restriction.
 - Restricted by HTTP referrer (Google Maps) or allowed URL origins (Mapbox token scopes).
 - Stored in environment variables server-side for any backend geocoding or routing calls.
- Google Maps key restrictions: `Application restrictions → HTTP referrers` + `API restrictions → only the APIs used` (Maps JavaScript API, Geocoding API, Directions API — not "All APIs").
- Mapbox: tokens should have the minimum required scopes (e.g., `styles:read` + `tiles:read`), not the default secret token with write access.
- Check for keys leaked in browser network requests: any key visible in the URL query string `?key=...` must be referrer-restricted.

### 2. Map library initialization and version
- Verify the library version is recent and without known CVEs. Leaflet < 1.9 and older Mapbox GL JS versions have known issues.
- Confirm map container has an explicit pixel or percentage height — a map div with `height: 0` renders blank and is a common bug.
- Tile URLs must use HTTPS; mixed-content tiles are blocked by browsers.
- `maxZoom` and `minZoom` must be set to values supported by the tile provider to avoid blank tile errors.

### 3. Marker performance and clustering
- Rendering > 200 markers as individual DOM elements causes severe frame-rate drop. Verify clustering is implemented (Leaflet.markercluster, Supercluster, or Mapbox cluster layers).
- For very large datasets (> 5,000 points), use canvas rendering (Leaflet `CircleMarker` on a canvas layer, or Mapbox `circle` / `symbol` layers with GeoJSON source) instead of SVG/DOM markers.
- Dynamic marker updates: when data updates frequently, diff the marker set and add/remove only changed markers — do not clear-all and re-add on every update.
- Marker `z-index` stacking must be deterministic; overlapping markers must be clickable with a sensible priority order or a cluster popup listing all overlapping points.

### 4. Routing and directions API
- Client-side routing API calls: verify the API key is not exposed in the browser; proxy routing requests through a backend endpoint.
- Route requests must include error handling for: no route found (204 or empty legs array), API quota exceeded (429), and network failure.
- Waypoint limit: Google Directions API allows max 25 waypoints, Mapbox Directions API allows max 25 coordinates — validate server-side before calling.
- Display route polyline decoded from the API response, not a straight line between start and end.
- Distance and duration values from the API are in meters and seconds respectively — verify unit conversion before display.

### 5. Geocoding correctness
- Forward geocoding (address → coordinates): validate input before calling — empty or very short strings produce poor results and waste quota.
- Reverse geocoding (coordinates → address): rate-limit calls; do not fire on every `mousemove` or continuous GPS position update. Debounce at ≥ 500 ms.
- Do not cache geocoding results for user-entered addresses beyond the session — addresses change.
- Handle ambiguous results: when the API returns multiple candidates, show a disambiguation list rather than silently using the first result.
- Bias/region parameter: set `region` or `bounds` to the expected country/area to improve result relevance.

### 6. Coordinate handling
- Latitude range: -90 to +90. Longitude range: -180 to +180. Validate before sending to API or storing.
- WGS84 is the standard for web maps; confirm data from external sources (shapefiles, legacy systems) is projected correctly before display.
- Leaflet uses `[lat, lng]` order; GeoJSON uses `[lng, lat]` (longitude first). Mixing these is the most common geospatial bug — audit every coordinate array.
- Store coordinates as `DECIMAL(10, 8)` (latitude) and `DECIMAL(11, 8)` (longitude) in SQL — `FLOAT` loses precision at ~5 decimal places, causing ~1 m error.
- Do not round coordinates before storage; rounding to 2 decimal places introduces ~1 km error.

### 7. Tile server and caching
- Self-hosted tile server: verify tiles are served with `Cache-Control: public, max-age=86400` for static tiles (zoom ≤ 14) and shorter TTL for frequently updated data layers.
- Tile 404s: implement a fallback tile (e.g., ocean/background tile) to avoid visual gaps.
- CORS headers on the tile server must allow the app's origin if tiles are on a different domain.
- Rate limiting: tile servers must rate-limit by IP to prevent scraping of the full tileset.
- Retina/HiDPI tiles: use `@2x` tile URLs on retina displays; low-res tiles on retina look blurry.

### 8. User location and privacy
- `navigator.geolocation.getCurrentPosition()` requires user permission — never call it silently on page load without context.
- Location data must not be sent to analytics or third parties without explicit user consent (GDPR/CCPA).
- If storing trip or visit history, enforce a data retention policy and provide user deletion.
- Precise location (`enableHighAccuracy: true`) should only be used when genuinely needed (turn-by-turn navigation); use coarse location for "nearby search" to reduce battery drain.
- IP-based geolocation fallback: accuracy is city-level at best — display accordingly; do not claim it is GPS accuracy.
- Geofence triggers (enter/exit area): ensure the logic does not continuously poll location; use `watchPosition` with a minimum distance filter.

## Checklist

API keys:
- [ ] No unrestricted API keys in client-side code.
- [ ] Google Maps key restricted by HTTP referrer + API restriction.
- [ ] Mapbox token scoped to minimum permissions.
- [ ] Backend geocoding/routing calls use server-side env var keys.

Map rendering:
- [ ] Map container has explicit height.
- [ ] Tile URLs use HTTPS.
- [ ] `maxZoom`/`minZoom` within provider limits.

Markers and performance:
- [ ] Clustering enabled for > 200 markers.
- [ ] Canvas rendering used for > 5,000 points.
- [ ] Marker updates diff rather than clear-all.

Coordinates:
- [ ] Leaflet `[lat, lng]` vs GeoJSON `[lng, lat]` usage is consistent throughout.
- [ ] Lat/lng values validated before API calls and storage.
- [ ] DB coordinate columns use `DECIMAL(10,8)` / `DECIMAL(11,8)`.

Routing:
- [ ] API key not exposed in browser routing calls.
- [ ] Error handling for no-route, quota exceeded, network failure.
- [ ] Waypoint count validated before API call.

Privacy:
- [ ] `geolocation` API not called on page load without user trigger.
- [ ] Location data not sent to third parties without consent.
- [ ] Data retention policy in place for stored location history.

## Common issues & anti-patterns

- **`[lng, lat]` vs `[lat, lng]` confusion**: mixing Leaflet and GeoJSON coordinate order places markers in the wrong location (often in the ocean). This is the most frequent geospatial bug.
- **Unrestricted Google Maps API key**: any caller can use the key and drive up billing. Restrict by referrer and API.
- **No marker clustering**: 1,000 DOM-based markers lock the browser thread. Always cluster above ~200 markers.
- **Geocoding on every keystroke**: 26 API calls for a 26-character address. Debounce at 500 ms; trigger only after 3+ characters.
- **Floating-point coordinate storage**: `FLOAT` loses precision at the 6th decimal place (~11 cm). Use `DECIMAL` or store as integer microdegrees.
- **Routing with a straight-line polyline**: drawing a straight line between A and B ignores roads. Always decode and draw the polyline from the API response.
- **Tile CORS missing**: tiles from a self-hosted CDN on a different subdomain fail silently in the browser, showing blank tiles with no console error visible unless DevTools is open.
- **User location on page load with no context**: browsers now require a user gesture before the geolocation prompt; calling it on load will be silently denied in some contexts.
- **No tile cache headers**: every map pan re-fetches all tiles, slamming the tile server and causing slow UX.

## Required output

Return a structured report with:
- **Summary**: pass / needs fixes / blocked, primary risk (security, performance, privacy, correctness).
- **API key audit**: status of each key's restriction and exposure.
- **Coordinate audit**: `[lat,lng]` vs `[lng,lat]` consistency finding.
- **Findings table**: severity (critical / high / medium / low / info), category, file + line, description, remediation.
- **Performance assessment**: marker count, clustering status, rendering approach.
- **Privacy assessment**: geolocation consent, data retention, third-party sharing.
- **Next handoff**: specific test cases (marker count stress test, routing error cases, geolocation permission denial handling).

## Safety

- Never print or log raw API keys found during review — flag as critical finding requiring rotation.
- Do not make live geocoding or routing API calls during the review.
- If user location history is stored without consent mechanisms, flag as high severity (GDPR/CCPA risk).
- Do not access or export any real user location data during the review.
