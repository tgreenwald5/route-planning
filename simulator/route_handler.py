from heapq import heappush, heappop
from simulator import geo_utils as gu
import osmnx as ox
import shapely
from shapely.geometry import LineString

def load_graph_from_file(filepath):
    graph = ox.load_graphml(filepath)
    ox.add_edge_speeds(graph, hwy_speeds=112, fallback=48) # 70mph, 30mph
    ox.add_edge_travel_times(graph)
    ox.add_edge_bearings(graph)
    return graph

# return nearest node from location (str input)
def location_to_node(graph, location_str):
    coords = ox.geocode(location_str)
    nearest_node = ox.nearest_nodes(graph, X=coords[1], Y=coords[0])
    return nearest_node

def coords_to_node(graph, coords):
    lon, lat = coords
    return ox.nearest_nodes(graph, X=lon, Y=lat)

# return array of neighbor nodes
def get_neighbors(graph, node):
    return list(graph.neighbors(node))

# return travel time between two nodes (seconds)
def edge_cost_travel_time(graph, node_1, node_2):
    edges = graph.get_edge_data(node_1, node_2)
    if not edges:
        return float('inf')
    return min(d.get('travel_time', float('inf')) for d in edges.values())

def reconstruct_route(came_from, current):
    route = [current]
    while current in came_from:
        current = came_from[current]
        route.insert(0, current)
    return route

# calculate route (A*) and set route
def calculate_route(graph, start_node, end_node):
    max_speed_mph = 70 # miles per hour
    max_speed_mps = (max_speed_mph * 1609.34) / 3600 # meters per second
    open_set = []
    start_heuristic = gu.get_geodesic_distance(graph, start_node, end_node) / max_speed_mps
    heappush(open_set, (start_heuristic, start_node))
    open_set_lookup = {start_node}
    came_from = {}
    g_score = {start_node: 0}
    f_score = {start_node: start_heuristic}

    while open_set:
        _, current = heappop(open_set)
        open_set_lookup.remove(current)
        if current == end_node:
            return reconstruct_route(came_from, current)
        for neighbor in get_neighbors(graph, current):
            travel_time = edge_cost_travel_time(graph, current, neighbor)
            tentative_g = g_score[current] + travel_time
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                heuristic_time = gu.get_geodesic_distance(graph, neighbor, end_node) / max_speed_mps
                f_score[neighbor] = tentative_g + heuristic_time
                if neighbor not in open_set_lookup:
                    heappush(open_set, (f_score[neighbor], neighbor))
                    open_set_lookup.add(neighbor)
    return None

# route display
def get_route_geometry(graph, route):
    if not graph or not route:
        return []
    coords = []
    for i in range(len(route) - 1):
        edge_coords = gu.get_edge_geometry_coords(graph, route[i], route[i + 1])
        coords.extend(edge_coords)
    return coords