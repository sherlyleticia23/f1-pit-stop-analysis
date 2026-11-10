import requests
import pandas as pd

BASE = "https://api.jolpi.ca/ergast/f1"
SEASON = 2025

def get_json(url, params=None):
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def to_seconds(t):
    # converts "1:34.123" to 94.123
    m, s = t.split(":")
    return int(m) * 60 + float(s)

# 1. Find the Bahrain round
schedule = get_json(f"{BASE}/{SEASON}.json")
races = schedule["MRData"]["RaceTable"]["Races"]
race = next(r for r in races if "Bahrain" in r["raceName"])
rnd = race["round"]
print(race["raceName"], "- round", rnd)

# 2. Pit stops
pit_data = get_json(f"{BASE}/{SEASON}/{rnd}/pitstops.json", params={"limit": 100})
stops_df = pd.DataFrame(pit_data["MRData"]["RaceTable"]["Races"][0]["PitStops"])
stops_df["lap"] = stops_df["lap"].astype(int)

# 3. Lap times for every driver (100 rows per page)
rows = []
offset = 0
for _ in range(40):  # safety limit
    laps_data = get_json(f"{BASE}/{SEASON}/{rnd}/laps.json", params={"limit": 100, "offset": offset})
    race_entries = laps_data["MRData"]["RaceTable"]["Races"]
    laps_list = race_entries[0]["Laps"] if race_entries else []
    if not laps_list:
        break
    for lap in laps_list:
        for t in lap["Timings"]:
            if "time" in t:
                rows.append({"driverId": t["driverId"], "lap": int(lap["number"]), "time": to_seconds(t["time"])})
    offset += 100
    print("pages loaded so far, rows:", len(rows))
laps_df = pd.DataFrame(rows).drop_duplicates(subset=["driverId", "lap"])
print("Lap times loaded:", len(laps_df), "rows, laps", laps_df["lap"].min(), "to", laps_df["lap"].max())

# 4. Mark pit-related laps
pit_keys = set()
for _, s in stops_df.iterrows():
    pit_keys.add((s["driverId"], s["lap"]))
    pit_keys.add((s["driverId"], s["lap"] + 1))
laps_df["is_pit"] = [(d, l) in pit_keys for d, l in zip(laps_df["driverId"], laps_df["lap"])]

# 5. Baseline pace per driver
clean = laps_df[(laps_df["lap"] > 1) & (~laps_df["is_pit"])]
baseline = clean.groupby("driverId")["time"].median()

# 6. Pit loss per stop, skipping likely safety car laps
results = []
for _, s in stops_df.iterrows():
    d, l = s["driverId"], s["lap"]
    inlap = laps_df[(laps_df["driverId"] == d) & (laps_df["lap"] == l)]["time"]
    outlap = laps_df[(laps_df["driverId"] == d) & (laps_df["lap"] == l + 1)]["time"]
    if inlap.empty or outlap.empty or d not in baseline.index:
        continue
    # skip stops where a lap is much slower than normal (likely safety car / VSC)
    if inlap.iloc[0] > 1.3 * baseline[d] or outlap.iloc[0] > 1.3 * baseline[d]:
        continue
    loss = inlap.iloc[0] + outlap.iloc[0] - 2 * baseline[d]
    results.append({
        "driverId": d,
        "lap": l,
        "stop": s["stop"],
        "duration": float(s["duration"]),
        "pit_loss": round(loss, 3),
    })

loss_df = pd.DataFrame(results)
if loss_df.empty:
    print("No pit losses calculated. Lap rows loaded:", len(laps_df))
else:
    print(loss_df.sort_values("pit_loss").to_string(index=False))
    print("Median pit loss:", round(loss_df["pit_loss"].median(), 3))