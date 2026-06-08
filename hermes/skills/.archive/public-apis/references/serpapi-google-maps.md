# SerpApi Google Maps Engine — Restaurant Lookup Reference

Tested June 2026. SerpApi's `google_maps` engine returns structured Google Maps data
without needing the paid Google Places API. Free tier: 250 searches/month.

## Query Pattern

```
https://serpapi.com/search?api_key={key}&engine=google_maps&q={query}&type=search&hl=en
```

**Tips for best results:**
- Use specific: `"Restaurant Name, Area, London"`
- Avoid apostrophes — `"Englands Lane"` works, `"England's Lane"` may return empty `place_results`
- If `place_results` is empty, check `local_results` as fallback

## Example Response: England's Lane, Belsize Park

```json
{
  "place_results": {
    "title": "England's Lane",
    "rating": 4.1,
    "reviews": 473,
    "rating_summary": [
      {"stars": 1, "amount": 53},
      {"stars": 2, "amount": 24},
      {"stars": 3, "amount": 33},
      {"stars": 4, "amount": 57},
      {"stars": 5, "amount": 306}
    ],
    "price": "£10–20",
    "type": ["Cafe"],
    "address": "2 England's Ln, Belsize Park, London NW3 4TG, United Kingdom",
    "phone": "+44 20 7483 1410",
    "website": "https://www.englandslanecafe.com/",
    "gps_coordinates": {"latitude": 51.546813, "longitude": -0.1610696},
    "hours": [
      {"saturday": "8 AM–5:30 PM"},
      {"sunday": "8 AM–5 PM"},
      {"monday": "7:30 AM–5:30 PM"},
      {"tuesday": "7:30 AM–5:30 PM"},
      {"wednesday": "7:30 AM–5:30 PM"},
      {"thursday": "7:30 AM–5:30 PM"},
      {"friday": "7:30 AM–5:30 PM"}
    ],
    "open_state": "Closed · Opens 8 AM Sun",
    "extensions": [
      {"highlights": ["Great coffee", "Great dessert", "Great tea selection"]}
    ],
    "place_id": "ChIJ...",
    "description": "..."
  }
}
```

## Example Response: Dishoom King's Cross

```json
{
  "place_results": {
    "title": "Dishoom King's Cross",
    "rating": 4.8,
    "reviews": 19501,
    "price": "£20–60",
    "type": ["Indian restaurant", "Breakfast restaurant", "Halal restaurant",
             "Indian takeaway", "Takeout Restaurant", "Modern Indian restaurant",
             "Restaurant", "South Asian restaurant", "Vegan restaurant",
             "Vegetarian restaurant"],
    "type_ids": ["indian_restaurant", "breakfast_restaurant"],
    "address": "5 Stable St, London N1C 4AB, United Kingdom",
    "phone": "+44 20 7420 9321",
    "website": "https://www.dishoom.com/kings-cross",
    "gps_coordinates": {"latitude": 51.536207, "longitude": -0.125499},
    "hours": [
      {"saturday": "9 AM–11 PM"},
      {"sunday": "9 AM–11 PM"},
      {"monday": "8 AM–11 PM"},
      {"tuesday": "8 AM–11 PM"},
      {"wednesday": "8 AM–11 PM"},
      {"thursday": "8 AM–12 AM"},
      {"friday": "8 AM–12 AM"}
    ],
    "open_state": "Open · Closes 11 PM",
    "rating_summary": [
      {"stars": 1, "amount": 260},
      {"stars": 2, "amount": 190},
      {"stars": 3, "amount": 484},
      {"stars": 4, "amount": 2201},
      {"stars": 5, "amount": 16366}
    ],
    "extensions": [
      {"highlights": ["Great cocktails", "Great coffee", "Great dessert",
                      "Great tea selection", "Great wine list"]},
      {"popular_for": ["Breakfast", "Lunch", "Dinner", "Solo dining"]},
      {"accessibility": ["Wheelchair accessible entrance"]}
    ]
  }
}
```

## Building Google Maps URL

From GPS coordinates in the response:
```
https://www.google.com/maps/place/{name}/@{lat},{lon},17z
```

Example: `https://www.google.com/maps/place/Englands+Lane/@51.546813,-0.1610696,17z`

## Direct Google Scraping — Does NOT Work

Google search and Google Maps pages are fully JS-rendered. `urllib` returns a consent/
captcha page with no structured data. JSON-LD blocks are absent. Do not attempt direct
scraping of Google — use SerpApi instead.

## Cost

- Free tier: 250 searches/month (already configured in Geeves with `SERPAPI_KEY`)
- Each restaurant lookup = 1 search
- At ~10 restaurants/week = ~40/month — well within free tier
