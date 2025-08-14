import osmnx as ox
import pickle
import os

os.makedirs("graphs", exist_ok=True)

# Change this to region you want
REGION_NAME = "Hamilton County, Ohio, USA"

# Change this to filename you want
OUTPUT_FILE = "graphs/ham_county_drive.pkl"

G = ox.graph_from_place(REGION_NAME, network_type="drive")

with open(OUTPUT_FILE, "wb") as f:
    pickle.dump(G, f)

print(f"Graph saved: {OUTPUT_FILE}")