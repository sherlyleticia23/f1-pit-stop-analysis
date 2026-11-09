# F1 Pit Loss Analysis
This project estimates how much time each Formula 1 pit stop costs. For each stop, it compares the in-lap and out-lap times with the driver's normal race pace. The difference is the pit loss.

# Data
All data comes from the [Jolpica-F1 API](https://api.jolpi.ca/ergast/f1/), a free, open replacement for the Ergast F1 API. No account or API key is needed.

# Setup
Requires Python 3.10 or newer.

# Method
1. Find the race and its round number in the season schedule.
2. Download the pit stops for that race.
3. Download lap times for every driver.
4. Set each driver's baseline pace as the median of their clean laps (excluding lap 1 and pit-related laps).
5. Pit loss = in-lap time + out-lap time − 2 × baseline.
6. Skip stops where either lap is more than 30% slower than baseline, since these are likely safety car or virtual safety car laps.

# Current status
- Analyzes one race at a time (currently Bahrain 2025)
- Safety car filter is a heuristic. Jolpica doesn't include track status data.

# Next steps
- Run the analysis across every race in a season
- Rank circuits by median pit loss
- Compare the cost of stops under safety car conditions with green-flag stops
- Run the analysis across every race in a season
- Rank circuits by median pit loss
- Compare the cost of stops under safety car conditions with green-flag stops
