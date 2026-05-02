import json, datetime

with open('trajectory_history/69991886_success.json', 'r') as f:
    data = json.load(f)

# Sort by timestamp
data.sort(key=lambda x: x['timestamp'])

# Last success
last = data[-1]
ts = datetime.datetime.fromtimestamp(last['timestamp'])
print("Last success:", ts)
print("  total_steps:", last["total_steps"])
print("  distance:", round(last["distance"], 1))
print("  trajectory_point_count:", last.get("trajectory_point_count", "N/A"))

# Compute stats
steps = [d['total_steps'] for d in data]
print()
print("All success records:", len(data))
print("Steps range:", min(steps), "-", max(steps))
print("Average steps:", round(sum(steps)/len(steps), 1))

# Check recent vs old
recent_cutoff = 1777400000  # approx April 27
old = [d for d in data if d['timestamp'] < recent_cutoff]
recent = [d for d in data if d['timestamp'] >= recent_cutoff]
print()
print("Old records (before Apr 27):", len(old))
print("Recent records (Apr 27+):", len(recent))

# Check what strategy was used (fast vs ultra_fast)
ultra_fast_count = sum(1 for d in data if d.get('trajectory_point_count', 0) < 15)
print("Ultra-fast trajectories (< 15 points):", ultra_fast_count)

# Show most recent timestamps
print()
print("Most recent 5 success timestamps:")
for d in data[-5:]:
    ts = datetime.datetime.fromtimestamp(d['timestamp'])
    print(f"  {ts}  steps={d['total_steps']}")
