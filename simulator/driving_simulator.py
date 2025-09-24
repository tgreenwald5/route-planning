from simulator import geo_utils as gu
from simulator import route_handler as rh
import osmnx as ox

class DrivingSimulator:
    def __init__(self):
        self.graph = None
        self.route = None

        self.tick_interval = 0.2 

        self.current_node_index = 0 
        self.current_node = None 
        self.current_coords = None 

        self.current_speed = None 
        self.current_bearing = None 

        self.finished = False
        self.paused = False

        self.geometry_coords = []
        self.segment_index = 0
        self.progress_along_segment = 0 

        self.awaiting_junc_choice = False
        self.junc_options = []
        self.route_changed = False
        self.stop_at_junctions = True
         
    def start(self):
        if self.graph == None or self.route == None:
            raise ValueError("graph or route missing")
        if len(self.route) < 2:
            self.current_node_index = 0
            self.current_node = self.route[0]
            self.current_coords = gu.get_node_coords(self.graph, self.current_node)
            self.current_bearing = None
            self.current_speed = 0
            self.geometry_coords = [self.current_coords]
            self.segment_index = 0
            self.progress_along_segment = 0
            self.finished = True
            self.paused = False
            return
            
        self.current_node_index = 0
        self.current_node = self.route[self.current_node_index]
        next_node = self.route[self.current_node_index + 1]
        self.geometry_coords = gu.get_edge_geometry_coords(self.graph, self.current_node, next_node)
        self.segment_index = 0
        self.progress_along_segment = 0
        self.current_coords = self.geometry_coords[0]
        self.current_bearing = gu.get_bearing(self.geometry_coords[0], self.geometry_coords[1])
        self.finished = False
        self.paused = False

    def pause(self):
        self.paused = True
    
    def resume(self):
        self.paused = False
    
    def tick(self):
        if self.paused or self.finished: # check if route is paused or already finished
            return

        if self.tick_interval <= 0 or self.current_speed < 0: # check if valid tick and valid speed
            raise ValueError("tick and speed must be positive")

        distance_to_travel = self.tick_interval * self.current_speed
        while distance_to_travel > 0: # check if there is a next segment
            if self.segment_index + 1 >= len(self.geometry_coords):
                raise IndexError("segment index out of bounds - geometry_coords length")

            segment_start = self.geometry_coords[self.segment_index]
            segment_end = self.geometry_coords[self.segment_index + 1]
            segment_length = gu.get_geodesic_distance(segment_start, segment_end)
            if segment_length == 0:
                self.segment_index += 1
                continue
            remaining_segment_length = segment_length - self.progress_along_segment # calc length left in segment and curr bearing
            self.current_bearing = ox.bearing.calculate_bearing(segment_start[1], segment_start[0], segment_end[1], segment_end[0])

            if remaining_segment_length > distance_to_travel: # reached segment that can't be fully traveled (reached tick distance)
                self.progress_along_segment += distance_to_travel
                self.progress_along_segment = min(self.progress_along_segment, segment_length)
                self.current_coords = gu.interpolate_position(segment_start, self.progress_along_segment, self.current_bearing)
                break

            else:
                self.current_coords = segment_end
                distance_to_travel -= remaining_segment_length
                self.progress_along_segment = 0
                self.segment_index += 1
                if self.segment_index >= len(self.geometry_coords) - 1: # check if at end of curr edge
                    if self.current_node_index >= len(self.route) - 2:
                        self.finished = True
                        self.current_coords = self.geometry_coords[-1]
                        return

                    self.current_node_index += 1
                    self.current_node = self.route[self.current_node_index]
                    if not self.awaiting_junc_choice: # check if at junction
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
                                options.append({
                                    "node_id": s,
                                    "street": street,
                                    "bearing": bearing,
                                    "hint_coords": hint_coords
                                })
                            if options:
                                if self.stop_at_junctions:
                                    self.awaiting_junc_choice = True
                                    self.junc_options = options
                                    self.pause()
                                    return
                                else:
                                    self.awaiting_junc_choice = False
                                    self.junc_options = []

                    if self.current_node_index + 1 >= len(self.route):
                        raise IndexError("route ended early. no next node")
                    
                    next_node = self.route[self.current_node_index + 1]
                    self.geometry_coords = gu.get_edge_geometry_coords(self.graph, self.current_node, next_node)

                    if not self.geometry_coords or len(self.geometry_coords) < 2:
                        raise ValueError("edge geometry must have at least two coords")
                    
                    self.segment_index = 0
                    self.progress_along_segment = 0

                    self.current_coords = self.geometry_coords[0]
    
     # (m/s)
    def set_speed(self, speed_ms):
        if speed_ms < 0:
            raise ValueError("speed can't be negative")
        self.current_speed = speed_ms

    # load route and graph
    def load_route(self, graph, route):
        self.graph = graph
        self.route = route
    
    # at junction choose direction to proceed in
    def choose_junction_node(self, next_node): 
        if next_node not in [opt["node_id"] for opt in self.junc_options]:
            raise ValueError("invalid junc choice")

        old_speed = self.current_speed
        end_node = self.route[-1]
        if next_node != self.route[self.current_node_index + 1]: # user moves off current route
            partial_route = rh.calculate_route(self.graph, next_node, end_node)
            new_route = [self.current_node] + partial_route
            self.load_route(self.graph, new_route)
            self.current_node_index = 0
            self.current_node = self.route[0]
            self.route_changed = True
        else: # user stays on current route 
            self.current_node = self.route[self.current_node_index]

        next_edge_node = self.route[self.current_node_index + 1]
        self.geometry_coords = gu.get_edge_geometry_coords(self.graph, self.current_node, next_edge_node)
        self.segment_index = 0
        self.progress_along_segment = 0.0
        self.current_coords = self.geometry_coords[0]
        self.awaiting_junc_choice = False
        self.junc_options = []
        self.set_speed(old_speed)
        self.resume()

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
    
    def reset(self):
        self.graph = None
        self.route = None

        self.current_node_index = 0
        self.current_node = None
        self.current_coords = None

        #self.current_speed = 0
        self.current_bearing = None

        self.finished = False
        self.paused = True

        self.geometry_coords = []
        self.segment_index = 0
        self.progress_along_segment = 0

        self.awaiting_junc_choice = False
        self.junc_options = []
        self.route_changed = False
        self.stop_at_junctions = True 
