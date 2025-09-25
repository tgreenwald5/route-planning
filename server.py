from flask import Flask, request, jsonify, render_template
from simulator.driving_simulator import DrivingSimulator
from simulator import route_handler as rh
import requests
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv
import pickle

app = Flask(__name__)
sim = DrivingSimulator()

load_dotenv()
MAPBOX_TOKEN = os.environ.get("MAPBOX_TOKEN")
GRAPH_PATH = os.environ.get("GRAPH_PATH", "graphs/Manhattan_New_York_USA_drive.pkl")

with open(GRAPH_PATH, "rb") as f:
    PRELOADED_GRAPH = pickle.load(f)

def geocode(address):
    qp_address = quote_plus(address)
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{qp_address}.json"
    params = {
        "access_token": MAPBOX_TOKEN,
        "limit": 1
    }
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()
    if not data["features"]:
        raise ValueError(f"Address not found: {address}")
    return tuple(data["features"][0]["center"])

@app.route('/start', methods=['POST'])
def start_sim():
    try:
        data = request.json
        sim.reset()

        graph = PRELOADED_GRAPH
        start_coords = geocode(data['start_address'])
        end_coords = geocode(data['end_address'])
        start_node = rh.coords_to_node(graph, start_coords)
        end_node = rh.coords_to_node(graph, end_coords)
        route = rh.calculate_route(graph, start_node, end_node)
        sim.load_route(graph, route)
        sim.start()
        return jsonify({"message": "simulation started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/set_speed', methods=['POST'])
def set_speed():
    try:
        speed = request.json['speed']
        sim.set_speed(speed)
        return jsonify({"message": "speed set"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tick', methods=['POST'])
def tick():
    try:
        sim.tick()
        return jsonify({"message": "tick executed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/route', methods=['GET'])
def route():
    try:
        geometry = rh.get_route_geometry(sim.graph, sim.route)
        if (not geometry) and getattr(sim, "current_coords", None):
            geometry = [sim.current_coords]
        sim.route_changed = False
        return jsonify({"geometry": geometry})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/state', methods=['GET'])
def state():
    try:
        state = sim.get_state()
        return jsonify(state)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/junction_mode', methods=['POST'])
def junction_mode():
    try:
        manual = bool(request.json.get('manual', True))
        sim.stop_at_junctions = manual
        if not manual and sim.awaiting_junc_choice:
            sim.awaiting_junc_choice = False
            sim.junc_options = []
            sim.resume()
        return jsonify({"manual": sim.stop_at_junctions})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/choose_junction', methods=['POST'])
def choose_junction():
    try:
        next_node = request.json['next_node']
        sim.choose_junction_node(next_node)
        return jsonify({"message": "reroute successful"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/')
def index():
    return render_template('index.html', mapbox_token=MAPBOX_TOKEN)

@app.route('/reset', methods=['POST'])
def reset_sim():
    try:
        sim.reset()
        return jsonify({"message": "simulation reset"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()