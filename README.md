# **Route Mapping & Driving Simulator**
An interactive driving simulator that calculates routes between two locations using A* pathfinding and visualizes real-time vehicle navigation on OpenStreetMap road networks.

## **Some Features**
- A* route calculation on real OpenStreetMap road graphs
- Real-time vehicle simulation with accurate geographic positioning
- Manual or automatic navigation at intersections with live re-routing
- Interactive map interface with speed control and directional cues


## **Live Demo**
- Note: This demo is limited to routing locations only within the bounds of Manhattan, New York as road network graphs tend to consume high amounts of RAM.
- Link: [https://route-planning-lz7t.onrender.com](https://route-planning-lz7t.onrender.com)

   **Instructions**
   - Click link above
   - Enter start and end addresses
   - Click begin route
   - Adjust speed with "+" and "-" buttons
   - Toggle Pause for junction choices to manually choose directions at intersections
  
Entering Route
![Enter Route](assets/rp_er.png)

In Route
![In Route](assets/rp_ir.png)

Choosing Direction at Junction
![Choice at Junction](assets/rp_cj.png)


## **Installation**
1. **Clone the Repository**
   ```bash
   git clone https://github.com/tgreenwald5/route-planning.git
   cd route-planning
   ```
2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**
   - Create a .env file at the project root:
     ```bash
     MAPBOX_TOKEN=your_mapbox_access_token
     GRAPH_PATH=graphs/Manhattan_New_York_USA_drive.pkl
     ``` 
   - Get a free Mapbox token: https://docs.mapbox.com/help/dive-deeper/access-tokens/
4. **Run Locally**
   ```bash
   python server.py
   ```
   - Open http://127.0.0.1:5000 in browser
   

## **Working With Graph Data**
- The already included road network graph (graphs/Manhattan_New_York_USA_drive.pkl) contains road network data just for Manhattan, New York.
- However, road network graphs for other regions can be downloaded and used as well with the instructions below.

   ### **Downloading Road Network Graphs**
   - Use the provided download_graph.py script to download and save a road network graph:
      ```bash
      python download_graph.py "[REGION_NAME]"
      ```
      - Example:
         ```bash
         python download_graph.py "Atlanta, Georgia, USA"
         ```
         This will create a pickle file in the graphs/ folder with the new road network graph:
         ```bash
         graphs/Atlanta_Georgia_USA_drive.pkl
         ```

   ### **Changing Active Road Network Graph**
   Update your .env file:
   ```bash
   GRAPH_PATH=graphs/[GRAPH_FILENAME].pkl
   ```
   - This will enable routing and simulation within that region.


## **Tech Used**
- **Frontend**
   - HTML, Tailwind CSS, JavaScript
   - Mapbox GL JS

- **Backend**
   - Python, Flask
   - OSMnx (graph extraction), Geopy (geocoding)


## **Citations**
  > Boeing, G. (2025). Modeling and Analyzing Urban Networks and Amenities with OSMnx. 
  > Geographical Analysis, published online ahead of print. doi:10.1111/gean.70009
