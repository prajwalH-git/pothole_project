# generate_big_dataset.py
import csv, random, datetime

# Bengaluru bounding box (approx)
lat_min, lat_max = 12.85, 13.05
lon_min, lon_max = 77.5, 77.75

records = 10000  # change to 20000 if you want more

with open("big_potholes.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["title","description","lat","lon","reported_by","reported_at","city","severity"])
    for i in range(records):
        lat = round(random.uniform(lat_min, lat_max), 6)
        lon = round(random.uniform(lon_min, lon_max), 6)
        sev = random.randint(1,5)
        month = random.randint(1,11)
        day = random.randint(1,28)
        hour = random.randint(0,23)
        minute = random.randint(0,59)
        day_ts = f"2025-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00"
        writer.writerow([
            f"Pothole #{i}",
            random.choice(["Deep hole","Small crack","Damaged patch","Needs repair","Crater-like","Causes skidding"]),
            lat, lon,
            f"user{i%500}",
            day_ts,
            "Bengaluru",
            sev
        ])
print("✅ big_potholes.csv created with", records, "records.")
