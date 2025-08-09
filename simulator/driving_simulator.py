from simulator import geo_utils as gu
from simulator import route_handler as rh
import osmnx as ox
import shapely
from shapely.geometry import LineString, Point
from pyproj import Transformer
import geopandas as gpd

class DrivingSimulator:
    def __init__(self):
        self.graph = None
        self.route = None

        self.tick_interval = 0.2 
        self.elapsed_time = 0

        self.current_node_index = 0 
        self.current_node = None 
        self.current_coords = None 

        self.current_speed = None 
        self.current_bearing = None 

        self.on_route = True
        self.finished = False
        
        self.instruction = None
        self.eta = None 
        self.remaining_distance = None 
        self.segment_times = {} 

        self.paused = False
        
        self.travel_log = []

        self.geometry_coords = []
        self.segment_index = 0
        self.progress_along_segment = 0
        self.current_edge = None 

        self.awaiting_junc_choice = False
        self.junc_options = []
        self.route_changed = False
         
    def start(self):
        if self.graph == None or self.route == None:
            raise ValueError("Graph or route missing.")
        self.current_node_index = 0
        self.current_node = self.route[self.current_node_index]
        next_node = self.route[self.current_node_index + 1]
        self.geometry_coords = gu.get_edge_geometry_coords(self.graph, self.current_node, next_node)
        self.segment_index = 0
        self.progress_along_segment = 0
        self.current_coords = self.geometry_coords[0]
        self.current_bearing = gu.get_bearing(self.geometry_coords[0], self.geometry_coords[1])
        self.current_edge = list(self.graph.get_edge_data(self.current_node, next_node).values())[0]
        self.elapsed_time = 0
        self.finished = False
        self.paused = False
        self.travel_log.clear()

    def pause(self):
        self.paused = True
    
    def resume(self):
        self.paused = False
    
    def reset(self):
        self.current_coords = None
        self.current_node_index = 0
        self.elapsed_time = 0
        self.travel_log.clear()
        self.segment_index = 0
        self.progress_along_segment = 0
        self.current_edge = None
        self.geometry_coords = []
        self.current_speed = 0
        self.current_bearing = None
        self.finished = False
    
    def tick(self):
        # check if route is paused or already finished
        if self.paused or self.finished:
            return

        # check if valid tick and valid speed
        if self.tick_interval <= 0 or self.current_speed < 0:
            raise ValueError("tick and speed must be positive")

        distance_to_travel = self.tick_interval * self.current_speed # distance needed to travel in curr tick

        while distance_to_travel > 0:
            # check if there is a next segment
            if self.segment_index + 1 >= len(self.geometry_coords):
                raise IndexError("segment index out of bounds - geometry_coords length")
            
            # get length of curr segment
            segment_start = self.geometry_coords[self.segment_index]
            segment_end = self.geometry_coords[self.segment_index + 1]
            segment_length = gu.get_geodesic_distance(segment_start, segment_end)

            # ignore segments with no length
            if segment_length == 0:
                self.segment_index += 1
                continue
            
            # calc length left in segment and curr bearing
            remaining_segment_length = segment_length - self.progress_along_segment
            self.current_bearing = ox.bearing.calculate_bearing(segment_start[1], segment_start[0], segment_end[1], segment_end[0])
            
            # reached segment that can't be fully traveled (reached tick distance)
            if remaining_segment_length > distance_to_travel:
                self.progress_along_segment += distance_to_travel
                self.progress_along_segment = min(self.progress_along_segment, segment_length)
                self.current_coords = gu.interpolate_position(segment_start, self.progress_along_segment, self.current_bearing)
                break

            else:
                # move to end of segment
                self.current_coords = segment_end
                distance_to_travel -= remaining_segment_length
                self.progress_along_segment = 0
                self.segment_index += 1

                # check if at end of curr edge
                if self.segment_index >= len(self.geometry_coords) - 1:
                    # check if at route end
                    if self.current_node_index + 1 >= len(self.route):
                        self.finished = True
                        self.current_coords = self.geometry_coords[-1]
                        break

                    # go to next edge
                    self.current_node_index += 1
                    self.current_node = self.route[self.current_node_index]

                    # check if at junction
                    if not self.awaiting_junc_choice:
                        successors = list(self.graph.successors(self.current_node))
                        if len(successors) >= 2:
                            options = []
                            if self.current_node_index > 0:
                                prev_node = self.route[self.current_node_index - 1]
                            else:
                                prev_node = None
                            for s in successors:
                                if s == prev_node:
                                    continue
                                edge_data = list(self.graph.get_edge_data(self.current_node, s).values())[0]
                                street = edge_data.get("name", "Unnamed Road")
                                coords = gu.get_edge_geometry_coords(self.graph, self.current_node, s)
                                if len(coords) < 2:
                                    continue
                                bearing = gu.get_bearing(coords[0], coords[1])
                                try:
                                    step_m = 8.0
                                    hint_coords = gu.interpolate_position(coords[0], step_m, bearing)
                                except Exception:
                                    hint_coords = coords[1]
                                turn = gu.get_turn_dir(self.current_bearing, bearing)
                                options.append({
                                    "node_id": s,
                                    "street": street,
                                    "bearing": bearing,
                                    "turn": turn,
                                    "hint_coords": hint_coords
                                })
                            if options:
                                self.awaiting_junc_choice = True
                                self.junc_options = options
                                self.pause()
                                return

                    # check if there is a next node
                    if self.current_node_index + 1 >= len(self.route):
                        raise IndexError("route ended early. no next node")
                    
                    # get coords of edge between curr node and next node
                    next_node = self.route[self.current_node_index + 1]
                    self.geometry_coords = gu.get_edge_geometry_coords(self.graph, self.current_node, next_node)

                    # make sure edge coords exist and have more than a single coordinate
                    if not self.geometry_coords or len(self.geometry_coords) < 2:
                        raise ValueError("edge geometry must have at least two coords")
                    
                    # reset segment index and segment progress
                    self.segment_index = 0
                    self.progress_along_segment = 0

                    # current coords are at start of new edge
                    self.current_coords = self.geometry_coords[0]

    # set movement speed (m/s)     
    def set_speed(self, speed_ms):
        if speed_ms < 0:
            raise ValueError("speed can't be negative")
        self.current_speed = speed_ms

    # load graph and route
    def load_route(self, graph, route):
        self.graph = graph
        self.route = route
    
    # at junction, choose direction to proceed in
    def choose_junction_node(self, next_node):
        if next_node not in [opt["node_id"] for opt in self.junc_options]:
            raise ValueError("invalid junc choice")
        old_speed = self.current_speed
        end_node = self.route[-1]

        # if direction user chooses isn't apart of current route
        if next_node != self.route[self.current_node_index + 1]:
            partial_route = rh.calculate_route(self.graph, next_node, end_node)
            new_route = [self.current_node] + partial_route
            self.load_route(self.graph, new_route)
            self.current_node_index = 0
            self.current_node = self.route[0]
            self.route_changed = True

        # if direction user chooses is apart of current route
        else: 
            self.current_node = self.route[self.current_node_index]

        # set next edge
        next_edge_node = self.route[self.current_node_index + 1]
        self.geometry_coords = gu.get_edge_geometry_coords(self.graph, self.current_node, next_edge_node)
        self.segment_index = 0
        self.progress_along_segment = 0.0
        self.current_coords = self.geometry_coords[0]

        # reset and resume
        self.awaiting_junc_choice = False
        self.junc_options = []
        self.set_speed(old_speed)
        self.resume()
        
    # generate new route
    def trigger_reroute(self):
        start_node = rh.coords_to_node(self.graph, self.current_coords)
        end_node = self.route[-1]
        new_route = rh.calculate_route(self.graph, start_node, end_node)
        self.load_route(self.graph, new_route)
        self.start()
    
    # check if route is being followed
    def check_on_route(self, curr_position, segment_start, segment_end):
        gdf = gpd.GeoDataFrame(geometry=[Point(segment_start)], crs="EPSG:4326")
        utm_crs = gdf.estimate_utm_crs()
        transformer = Transformer.from_crs(4326, utm_crs, always_xy=True)
        crs_seg_line = shapely.transform(LineString([segment_start, segment_end]), transformer.transform)
        crs_curr_pos = shapely.transform(Point(curr_position[0], curr_position[1]), transformer.transform)
        if shapely.distance(crs_seg_line, crs_curr_pos) <= 20:
            self.on_route = True
        else:
            self.on_route = False

    # current status of sim
    def get_state(self):
        return {
            "coords": self.current_coords,
            "bearing": self.current_bearing,
            "finished": self.finished,
            "awaiting_junc_choice": self.awaiting_junc_choice,
            "junc_options": self.junc_options,
            "paused": self.paused,
            "route_changed": self.route_changed
        }
