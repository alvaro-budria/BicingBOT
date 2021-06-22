# Importing the necessary libraries.
import pandas as pd
import networkx as nx
from staticmap import StaticMap, CircleMarker, Line
from haversine import haversine
import geopy as geo
from math import ceil
import copy


def authors():
    message = '''
    This project was made by
    *Álvaro Francesc Budría Fernández*
    *Jaume Ros Alonso*
    '''
    return message


# Returns the number of nodes of a given graph.
def number_nodes(G):
    return G.number_of_nodes()


# Returns the number of edges of a given graph.
def number_edges(G):
    return G.number_of_edges()


# Returns the number of connected components of a given graph.
def number_components(G):
    return nx.number_connected_components(G)


# Returns the shortest path from "start" to "finish".
def compute_path(G, start, finish):
    # Connect the new edges to all others at walking speed
    for station in G.nodes():
        l1 = haversine(start, (G.node[station]['lat'], G.node[station]['lon']))
        l2 = haversine(finish, (G.node[station]['lat'], G.node[station]['lon']))
        G.add_edge("S", station, weight=l1/4)
        G.add_edge("F", station, weight=l2/4)

    # Compute the shortest path from S to F
    path = nx.dijkstra_path(G, "S", "F")

    return path


# Draws the path P.
def draw_path(G, P):
    map_bcn = StaticMap(600, 600)

    coord1 = (G.node[P[0]]["lon"], G.node[P[0]]["lat"])
    marker = CircleMarker(coord1, "red", 2)
    map_bcn.add_marker(marker)

    for i in range(1, len(P)):
        # Represent a station
        coord2 = (G.node[P[i]]["lon"], G.node[P[i]]["lat"])
        marker = CircleMarker(coord2, "red", 2)
        map_bcn.add_marker(marker)

        # Represent an edge
        line = Line([coord1, coord2], "blue", 4)
        coord1 = coord2
        map_bcn.add_line(line)

    # Obtain the final image
    image = map_bcn.render()
    image.save("path.png")


# Returns the coordinates of the two given addresses.
def get_coords(addresses):
    try:
        geolocator = geo.Nominatim(user_agent="bicing_bot")
        address1, address2 = addresses.split(',')
        location1 = geolocator.geocode(address1 + ', Barcelona')
        location2 = geolocator.geocode(address2 + ', Barcelona')
        return (location1.latitude, location1.longitude), (location2.latitude, location2.longitude)
    except:
        raise ValueError("Address not found")


# Creates an image with the shortest path from "start" to "finish".
def shortest_path(G, addresses):
    coords = get_coords(addresses)
    start, finish = coords
    if start == finish:
        raise ValueError("Both addresses are the same")

    # Add the two new nodes
    G.add_node("S", lat=start[0], lon=start[1])
    G.add_node("F", lat=finish[0], lon=finish[1])

    path = compute_path(G, start, finish)
    draw_path(G, path)

    # Return the graph to its original state
    G.remove_node("S")
    G.remove_node("F")


# Return the downloaded dataframe from the web.
def get_dataframe(flow=False):
    try:
        # The main dataframe with stations and coordinates
        url_info = 'https://api.bsmsa.eu/ext/api/bsm/gbfs/v2/en/station_information'
        stations = pd.DataFrame.from_records(pd.read_json(url_info)['data']['stations'], index='station_id')

        if flow:  # The dataframe for the distribute command
            url_status = 'https://api.bsmsa.eu/ext/api/bsm/gbfs/v2/en/station_status'
            bikes = pd.DataFrame.from_records(pd.read_json(url_status)['data']['stations'], index='station_id')
            return stations, bikes

        else:
            return stations

    except:
        raise ValueError("Could not download the data")


# Creates an image of the graph.
def draw_graph(G):
    map_bcn = StaticMap(600, 600)

    # Thinner lines if there are many edges
    rel_width = 5
    if G.number_of_edges() > 100:
        rel_width = int(G.number_of_nodes() / G.number_of_edges())

    # Represent edges
    for (u, v) in G.edges():
        coord1 = (G.node[u]["lon"], G.node[u]["lat"])
        coord2 = (G.node[v]["lon"], G.node[v]["lat"])
        line = Line([coord1, coord2], 'blue', rel_width)
        map_bcn.add_line(line)

    # Represent stations
    for u in G.nodes():
        marker = CircleMarker((G.node[u]["lon"], G.node[u]["lat"]), 'red', 2)
        map_bcn.add_marker(marker)

    image = map_bcn.render()
    image.save('stations.png')


# Prepares the DiGraph so that we can apply the network_simplex function on it later.
def add_nodes(G, demand, stations, bikes):
    G.add_node('TOP')

    nbikes = 'num_bikes_available'
    ndocks = 'num_docks_available'
    bikes = bikes[[nbikes, ndocks]]  # We only select the interesting columns

    requiredBikes, requiredDocks = demand  # Required number of bikes and docks

    demand = 0
    for st in bikes.itertuples():
        idx = st.Index
        if idx not in stations.index:
            continue  # We ignore this station.

        stridx = str(idx)

        # The blue (s), black (g) and red (t) nodes of the graph
        s_idx, g_idx, t_idx = 's'+stridx, 'g'+stridx, 't'+stridx
        G.add_node(g_idx, lat=stations["lat"][idx], lon=stations["lon"][idx])
        G.add_node(s_idx)
        G.add_node(t_idx)

        b, d = st.num_bikes_available, st.num_docks_available
        req_bikes = max(0, requiredBikes - b)
        req_docks = max(0, requiredDocks - d)

        # Sets the capacity of every edge
        G.add_edge('TOP', s_idx, capacity=b)
        G.add_edge(t_idx, 'TOP', capacity=d)
        G.add_edge(s_idx, g_idx, capacity=max(0, -requiredBikes+b))
        G.add_edge(g_idx, t_idx, capacity=max(0, -requiredDocks+d))

        # Sets the demand of every node
        if req_bikes > 0:
            demand += req_bikes
            G.node[t_idx]["demand"] = req_bikes
        elif req_docks > 0:
            demand -= req_docks
            G.node[s_idx]["demand"] = -req_docks

    G.nodes['TOP']['demand'] = -demand


# Returns the total transference cost and the maximum among the costs
# for transfering bikes through each edge of the edges.
def text_flow(G, bikes):
    err = False

    try:
        flowCost, flowDict = nx.network_simplex(G)

    except nx.NetworkXUnfeasible:
        err = True
        raise ValueError("impossible")

    if not err:
        total_cost = flowCost/1000  # in km
        edge_max_cost = (-1, -1, -1)  # we store the edge with the max cost of transference
        # (source, destiny, number of bikes * distance)
        cost = 0
        nbikes = 'num_bikes_available'
        ndocks = 'num_docks_available'
        # We update the status of the stations according to the calculated transportation of bicycles
        for src in flowDict:
            if src[0] != 'g':
                continue
            idx_src = int(src[1:])
            for dst, b in flowDict[src].items():
                if dst[0] == 'g' and b > 0:
                    idx_dst = int(dst[1:])
                    cost = G.edges[src, dst]["weight"] * b / 1000
                    if cost > edge_max_cost[2]:
                        edge_max_cost = (src, dst, cost)
                    bikes.at[idx_src, nbikes] -= b
                    bikes.at[idx_dst, nbikes] += b
                    bikes.at[idx_src, ndocks] += b
                    bikes.at[idx_dst, ndocks] -= b

        # Return the results formatted in markdown
        if total_cost == 0:
            return "*No transference of bikes was performed*"
        return "*Total cost: " + str(total_cost) + "*\n" + "Max cost edge: " +\
            str(edge_max_cost[0])[1:] + " -> " + str(edge_max_cost[1])[1:] + " with cost " + str(edge_max_cost[2]) + "."


# Returns the information of the cost of distributing the bycicles according to the demand.
def minflow(demand, dist, sts_bikes):
    G = nx.DiGraph()
    stations, bikes = sts_bikes
    add_nodes(G, demand, stations, bikes)

    G = build_graph(dist, G, flow=True)

    info = text_flow(G, bikes)
    return info


# Removes all edges of the graph without modifying the nodes
def clean_graph(G):
    G.remove_edges_from(copy.deepcopy(G.edges()))


# Classifies each node in G into its corresponding cell in M
# according to latitude and longitude.
def classify_nodes(M, G, dist_lat, dist_lon, min_lat, min_lon):

    for node, attr in G.nodes(data=True):
        if str(node)[0] not in ["s", "t", "T"]:  # we only deal with nodes in the geometric graph
            i = int((attr["lat"] - min_lat) // dist_lat)
            j = int((attr["lon"] - min_lon) // dist_lon)
            if (i, j) not in M:
                M[(i, j)] = list()
            M[(i, j)].append(node)


# Connects the nodes contained in list_nodes.
def connect_cell(list_nodes, G, dist, dist_lat, dist_lon, flow=False):

    # Compare the distance between all pairs of stations in list_nodes
    for i in range(len(list_nodes)):
        coord1 = (G.node[list_nodes[i]]["lat"], G.node[list_nodes[i]]["lon"])
        j = i + 1

        while j < len(list_nodes):
            coord2 = (G.node[list_nodes[j]]["lat"], G.node[list_nodes[j]]["lon"])

            if (abs(coord1[0] - coord2[0]) < dist_lat and
                    abs(coord1[1] - coord2[1]) < dist_lon):
                l = haversine(coord1, coord2)

                if l <= dist:
                    if not flow:
                        G.add_edge(list_nodes[i], list_nodes[j], weight=l/10)
                    else:
                        G.add_edge(list_nodes[i], list_nodes[j], weight=int(l*1000))
                        G.add_edge(list_nodes[j], list_nodes[i], weight=int(l*1000))
            j += 1


def check_neighbours(M, G, n_lat, n_lon, node, dist, i, j, dist_lat, dist_lon, flow=False):
    i_j_list = [(-1, 0), (-1, 1), (-1, -1), (0, 1), (0, -1), (1, 1), (1, 0), (1, -1)]
    # with this list of pairs, we can access all the node's neighbouring cells

    coord1 = (G.node[node]["lat"], G.node[node]["lon"])
    for i_j in i_j_list:
        if (i+i_j[0], j+i_j[1]) in M:
            for vert in M[(i+i_j[0], j+i_j[1])]:
                coord2 = (G.node[vert]["lat"], G.node[vert]["lon"])
                if (abs(coord1[0] - coord2[0]) < dist_lat and
                        abs(coord1[1] - coord2[1]) < dist_lon):
                    l = haversine(coord1, coord2)
                    if l <= dist:
                        if not flow:
                            G.add_edge(node, vert, weight=l/10)
                        else:
                            G.add_edge(node, vert, weight=int(l*1000))
                            G.add_edge(vert, node, weight=int(l*1000))


# Returns the coordinate with the left-most, down-most coordinates, and
# the coordinate with the right-most, upper-most coordinates
def find_extremes(G):
    bott_left = [42, 2.5]
    upper_right = [41, 2.0]
    for node, attr in G.nodes(data=True):
        if str(node)[0] in ["s", "t", "T"]:  # only deal with the geometric graph
            continue
        if attr["lat"] < bott_left[0]:
            bott_left[0] = attr["lat"]
        elif attr["lat"] > upper_right[0]:
            upper_right[0] = attr["lat"]

        if attr["lon"] < bott_left[1]:
            bott_left[1] = attr["lon"]
        elif attr["lon"] > upper_right[1]:
            upper_right[1] = attr["lon"]

    for i in range(2):  # let us have a safety margin
        bott_left[i] -= 1e-5
        upper_right[i] -= 1e-5

    return bott_left, upper_right


# Connects all nodes that are closer than distance dist to each other.
def connect_graph(G, dist, flow=False):
    lat = "lat"
    lon = "lon"

    dist = dist / 1000  # to km
    dist_lon = dist / 83  # to variation of longitude coordinate
    dist_lat = dist / 111  # to variation of latitude coordinate

    bott_left, upper_right = find_extremes(G)

    incr_lat = upper_right[0] - bott_left[0]
    incr_lon = upper_right[1] - bott_left[1]

    n_lat = int(ceil(incr_lat / dist_lat))  # number of rows
    n_lon = int(ceil(incr_lon / dist_lon))  # number of columns

    # Classify the nodes in a matrix laid out on Barcelona
    M = {}
    classify_nodes(M, G, dist_lat, dist_lon, bott_left[0], bott_left[1])

    for i_j in M:
        connect_cell(M[i_j], G, dist, dist_lat, dist_lon, flow)
        for node in M[i_j]:
            check_neighbours(M, G, n_lat, n_lon, node, dist, i_j[0], i_j[1], dist_lat, dist_lon, flow)


# Creates a graph without edges
def initialize_graph():
    BicingData = get_dataframe()

    G = nx.Graph()
    for st in BicingData.itertuples():
        G.add_node(st.Index, lat=st.lat, lon=st.lon)

    return G


# Constructs a graph according to the given distance or modifies one, when a graph is provided
def build_graph(dist=1000, G=None, flow=False):
    if G is None and not flow:
        G = initialize_graph()
    elif not flow:
        clean_graph(G)

    # No need to connect if distance is 0
    if float(dist) > 0:
        connect_graph(G, float(dist), flow)

    return G

