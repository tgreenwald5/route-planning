import osmnx as ox
from geopy.distance import geodesic

# return node's (lon, lat)
def get_node_coords(graph, node):
    lon = graph.nodes[node]['x']
    lat = graph.nodes[node]['y']
    return (lon, lat)

# return list[(lon, lat)] of points in the edge
def get_edge_geometry_coords(graph, node_1, node_2):
    edge_data = graph.get_edge_data(node_1, node_2)
    edge = list(edge_data.values())[0]

    coords = []
    if 'geometry' in edge:
        coords = list(edge['geometry'].coords)
    if len(coords) < 2:
        coords = [get_node_coords(graph, node_1), get_node_coords(graph, node_2)]
    return coords

# return bearing between two points
def get_bearing(start_coords, end_coords): # (lon, lat)
    start_lon = start_coords[0]
    start_lat = start_coords[1]
    end_lon = end_coords[0]
    end_lat = end_coords[1]
    return ox.bearing.calculate_bearing(start_lat, start_lon, end_lat, end_lon)

# return geodesic distance between two coordinates (lon, lat)
def get_geodesic_distance(*args):
    if len(args) == 2:
        (start_lon, start_lat), (end_lon, end_lat) = args
    elif len(args) == 3:
        graph, node_1, node_2 = args
        start_lon = graph.nodes[node_1]['x']
        start_lat = graph.nodes[node_1]['y']
        end_lon = graph.nodes[node_2]['x']
        end_lat = graph.nodes[node_2]['y']
    else:
        raise ValueError("invalid geodesic distance args")
    return geodesic((start_lat, start_lon), (end_lat, end_lon)).meters

# params: (lon, lat), meters
def interpolate_position(coords, dist, bear):
    interp_point = geodesic(meters=dist).destination((coords[1], coords[0]), bearing=bear)
    interp_coords = (interp_point.longitude, interp_point.latitude)
    return interp_coords