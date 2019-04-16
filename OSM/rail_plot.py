
import geopandas as gpd
import matplotlib.pyplot as plt 
get_ipython().run_line_magic('matplotlib', 'inline')
import overpy
import json
import networkx as nx
import osmnx as ox
from itertools import groupby
import requests
import geopandas as gpd


# download OSM data as JSON using overpass api

def osm_json_download(city_name, tag_key, tag_value):

    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query =  """
                    [out:json];
                    (area["name"="{0}"]["boundary"="administrative"];)->.searchArea;
                    (node[{1}={2}](area.searchArea);
                     way[{1}={2}](area.searchArea);
                     relation[{1}={2}](area.searchArea);
                    );
                    (._;>;);
                    out;""".format(city_name, tag_key, tag_value)

    response = requests.get(overpass_url, params={'data': overpass_query})
    data = response.json()

    return data


data = osm_json_download(city_name = '東京都', tag_key = 'railway', tag_value = 'rail')


# # save json to disk
# with open('rail_tokyo.json', 'w') as f:
#         json.dump(data, f, indent=4)
 


def get_node(element):
    """
    Convert an OSM node element(dict) into the format for a networkx node.
    """
    
    node = {}
    node['y'] = element['lat']
    node['x'] = element['lon']
    node['osmid'] = element['id']

    return node


def get_path(element):
    """
    Convert an OSM way element(dict) into the format for a networkx graph path.
    """
    
    path = {}
    path['osmid'] = element['id']

    # remove any consecutive duplicate elements in the list of nodes
    grouped_list = groupby(element['nodes'])
    path['nodes'] = [group[0] for group in grouped_list]
               
    return path



def parse_osm_nodes_paths(data):
    """
    Construct dicts of nodes and paths with key=osmid and value=dict of attributes.
    """
    
    nodes = {}
    paths = {}
    for element in data['elements']:
        if element['type'] == 'node':
            key = element['id']
            nodes[key] = get_node(element)
        elif element['type'] == 'way': # osm calls network paths 'ways'
            key = element['id']
            paths[key] = get_path(element)

    return nodes, paths



def add_paths(G, paths):
    """
    Add a collection of paths (extracted dict from OSM json data) to the graph.
    """
    
    for data in paths.values():
        # all train tracks are oneway
        data['nodes'] = list(reversed(data['nodes']))

        # extract the ordered list of nodes from this path element, then delete it
        # so it's not added as an attribute to the edge later
        path_nodes = data['nodes']
        del data['nodes']

        # zip together the path nodes to get tuples like (0,1), (1,2), (2,3)
        path_edges = list(zip(path_nodes[:-1], path_nodes[1:]))
        G.add_edges_from(path_edges, **data)

    return G



def create_graph(data, graph_name):
    """
    Create a networkx graph (multidigraph) from OSM data.
    """
    
    G = nx.MultiDiGraph(name=graph_name, crs={'init':'epsg:4326'})

    # extract nodes and paths from the downloaded osm data
    nodes, paths = parse_osm_nodes_paths(data)

    # add each osm node to the graph
    for node, data in nodes.items():
        G.add_node(node, **data)
    # add each osm way (aka, path) to the graph
    G = add_paths(G, paths)

    return G


G = create_graph(data, 'railway_graph')

fig, ax = ox.plot_graph(G, fig_height=12, node_size=0, edge_linewidth=0.5)

fig.savefig('rail_tokyo.png')


# # convert the graph to geopandas df
# edges = ox.graph_to_gdfs(G, nodes=False, fill_edge_geometry=True)
# edges.head()


# # save geopandas to geojson
# edges.to_file("tokyo_rail_graph.json", driver="GeoJSON")





