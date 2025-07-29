import math
from heapq import heappush, heappop
import osmnx as ox

class RouteHandler:
    def __init__(self):
        self.start = None
        self.end = None
        self.graph = None
        self.route = None

    def set_start(self, start):
        self.start = self.location_to_node(start)

    def set_end(self, end):
        self.end = self.location_to_node(end)
    
    def set_graph(self, graph):
        self.graph = ox.load_graphml(graph)
        ox.add_edge_speeds(self.graph, hwy_speeds=112, fallback=48) # 70mph, 30mph (optimize later)
        ox.add_edge_travel_times(self.graph)

    # Return nearest node from location (str input)
    def location_to_node(self, location):
        coords = ox.geocode(location)
        nearest_node = ox.nearest_nodes(self.graph, X=coords[1], Y=coords[0])
        return nearest_node

    # Return gc distance between nodes (meters)
    def haversine(self, node_1, node_2):
        start_lat = self.graph.nodes[node_1]['y']
        start_lon = self.graph.nodes[node_1]['x']
        end_lat = self.graph.nodes[node_2]['y']
        end_lon = self.graph.nodes[node_2]['x']

        phi_1 = math.radians(start_lat)
        lambda_1 = start_lon
        phi_2 = math.radians(end_lat)
        lambda_2 = end_lon
        delta_phi = phi_2 - phi_1
        delta_lambda = math.radians(lambda_2 - lambda_1)
        r = 6371000 # earth radius (m)
        d = 2 * r * math.sqrt((1 - math.cos(delta_phi) + (math.cos(phi_1) * math.cos(phi_2) * (1 - math.cos(delta_lambda)))) / 2)
        return d

    # Return travel time between two nodes (seconds)
    def edge_cost_travel_time(self, node_1, node_2):
        edges = self.graph.get_edge_data(node_1, node_2)
        if not edges:
            return float('inf')
        return min(d.get('travel_time', float('inf')) for d in edges.values())

    # Return array of neighbor nodes
    def get_neighbors(self, node):
        return list(self.graph.neighbors(node))

    def reconstruct_route(self, came_from, current):
        route = [current]
        while current in came_from:
            current = came_from[current]
            route.insert(0, current)
        return route

    # Calculate route (A*) and set route
    def calculate_route(self):
        if self.start is None or self.end is None or self.graph is None:
            raise ValueError("Start, end, or graph is missing")
        max_speed_mh = 112654 # m/hr (70 mph)
        m_per_sec = max_speed_mh / 3600 # m/s
        open_set = []
        start_heuristic = self.haversine(self.start, self.end) / m_per_sec
        heappush(open_set, (start_heuristic, self.start))
        open_set_lookup = {self.start}
        came_from = {}
        g_score = {self.start: 0}
        f_score = {self.start: start_heuristic}

        while open_set:
            _, current = heappop(open_set)
            open_set_lookup.remove(current)
            if current == self.end:
                route = self.reconstruct_route(came_from, current)
                self.route = route
                return route
            for neighbor in self.get_neighbors(current):
                travel_time = self.edge_cost_travel_time(current, neighbor)
                tentative_g = g_score[current] + travel_time
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    heuristic_time = self.haversine(neighbor, self.end) / m_per_sec
                    f_score[neighbor] = tentative_g + heuristic_time
                    if neighbor not in open_set_lookup:
                        heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_lookup.add(neighbor)
        return None