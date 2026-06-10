# python-garminconnect API Reference

## Authentication

```python
from garminconnect import Garmin
client = Garmin(email, password)
client.login()
# Tokens cached at ~/.garminconnect/
```

429 rate limit warnings on login are normal — library auto-fallbacks transport.

## Key Methods

### Date-range activity fetch
```python
# CORRECT — date range query
activities = client.get_activities_by_date(startdate="2026-06-01", enddate="2026-06-09")

# WRONG — get_activities does NOT accept startdate/enddate
# It takes: start (offset int), limit (int), activitytype (optional)
activities = client.get_activities(start=0, limit=20)
```

### Activity details
```python
details = client.get_activity_details(activity_id)
```

### Activity types
```python
types = client.get_activity_types()
# Returns list of dicts with typeId, typeKey, typeDisplay
```

## Garmin Activity Type IDs

### Cycling (keep)
2=cycling, 5=mountain_biking, 10=road_biking, 19=cyclocross, 21=track_cycling,
22=recumbent_cycling, 25=indoor_cycling, 143=gravel_cycling, 152=virtual_ride,
175=e_bike_mountain, 176=e_bike_fitness, 197=hand_cycling, 198=indoor_hand_cycling

### Walking/Hiking (dedup against cycling)
3=hiking, 9=walking, 15=casual_walking, 16=speed_walking

### Other (ignored by sync)
1=running, 4=other, 6=trail_running, 7=street_running, 8=track_running,
11=indoor_cardio, 13=strength_training, 18=treadmill_running, etc.
