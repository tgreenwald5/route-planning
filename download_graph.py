import osmnx as ox
import pickle
import os
import sys

def main():
    if len(sys.argv) < 2:
        print("Use format: python download_graph.py \"<REGION_NAME>\"")
        sys.exit(1)

    os.makedirs("graphs", exist_ok=True)

    region_name = sys.argv[1]
    print(f"Downloading graph for: {region_name}")
    graph = ox.graph_from_place(region_name, network_type="drive")

    base_name = region_name.replace(" ", "_")
    base_name = base_name.replace(",", "")
    pkl_file_path = os.path.join("graphs", base_name + "_drive" + ".pkl")

    with open(pkl_file_path, "wb") as f:
        pickle.dump(graph, f)
    
    print(f"Graph saved to: {pkl_file_path}")

if __name__ == "__main__":
    main()