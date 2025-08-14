# Driving Route Simulator
Calculates a driving route using a start and an end address, simulates and displays progress along route, and lets user control speed and choose next direction at intersections.

## Live Demo
**Live Demo Link:** [https://route-planning-lz7t.onrender.com](https://route-planning-lz7t.onrender.com)

### Instructions
- Click link above
- Enter start and end address
- Click begin route
- Adjust speed with + and - buttons
- Toggle pause for junction choices to manually choose direction at intersections
  
### Entering Route
![Enter Route](assets/rp_er.png)

### In Route
![In Route](assets/rp_ir.png)

### Choosing Direction at Junction
![Choice at Junction](assets/rp_cj.png)


## Run Locally
1. Clone the repository:
   ```bash
   git clone https://github.com/tgreenwald5/route-planning.git
   cd route-planning
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set environment variable:
   - Obtain a Mapbox access token 
   - Create .env file in root folder
     ```bash
     MAPBOX_TOKEN=your_mapbox_access_token
     ```
4. Start app:
   ```bash
   python server.py
   ```
   Open http://127.0.0.1:5000 in browser


## Tech Used

### Frontend
- HTML, CSS, JavaScript
- [Tailwind CSS](https://tailwindcss.com/) + [DaisyUI](https://daisyui.com/)
- [Mapbox GL JS](https://docs.mapbox.com/mapbox-gl-js/guides)

### Backend
- [Flask](https://flask.palletsprojects.com/en/stable/)
- [OSMnx](https://osmnx.readthedocs.io/en/stable/)
- [Geopy](https://geopy.readthedocs.io/en/stable/)


## Graph Data Used
- The already included road network graph (graphs/ham_county_drive.pkl) contains street data just for Hamilton County, Ohio.
- However, this can be changed out for any other region using the instructions below.

  ### Changing Graph Region
  1. Open generate_graph.py
     - Change to your region of choice:
     ```bash
     PLACE_NAME = "Hamilton County, Ohio, USA"
     ```
  2. Run the script
     - In terminal run:
     ```bash
     python generate_graph.py
     ```
  3. Use the new graph
     - generate_graph.py will save the graph as a .pkl file inside the /graphs folder
     - Then update server.py if the filename is different from ham_county_drive.pkl, for example:
       ```bash
       with open("graphs/your_new_file.pkl", "rb") as f:
           PRELOADED_GRAPH = pickle.load(f)
     - Restart the server and then your new road network will be used


## Citations
  Boeing, G. (2025). Modeling and Analyzing Urban Networks and Amenities with OSMnx. 
  Geographical Analysis, published online ahead of print. doi:10.1111/gean.70009
  
  
