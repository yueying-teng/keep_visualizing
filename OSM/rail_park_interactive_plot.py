
from bokeh.plotting import figure, save
from bokeh.io import show, output_file
from bokeh.models import ColumnDataSource, HoverTool
import geopandas as gpd
import pysal as ps

import json
import numpy as np
import shapely.geometry as geom
import random
import pandas as pd

rail_gpd = gpd.read_file('./rail_tokyo.geojson')
park_gpd = gpd.read_file('./park_tokyo.geojson')

# shapefile of japan
file = './japan_ver81/japan_ver81.shp'
jp = gpd.read_file(file)



# ### processs geojson data 

# some parks are too far away from the center of tokyo, remove them

# get the latitude of all parks 
lat_list = []
for i, row in park_gpd.iterrows():
    lat = row.geometry.centroid.coords.xy[-1][0]
    lat_list.append(lat)
    
park_gpd['centroid_lat'] = lat_list


# remove the point geometry from the rail_gpd
no_point_rail_gpd = rail_gpd[rail_gpd['geometry'].geom_type != 'Point']
# remove those lines without names 
no_point_rail_gpd = no_point_rail_gpd[no_point_rail_gpd['name'].notnull()]

# remove point geometry from park_gpd
no_point_park_gpd = park_gpd[park_gpd['geometry'].geom_type != 'Point']
no_point_park_gpd = no_point_park_gpd[no_point_park_gpd['centroid_lat'] > 35.0]


# create park centroid coord gpd
park_centroid = no_point_park_gpd.to_crs({'init': 'epsg:3857'})

# get the centroids of parks
centroid_list = []
for i, row in park_centroid.iterrows():
    centroid = [x[0] for x in row.geometry.centroid.coords.xy]
    centroid_list.append(geom.Point(centroid))


clean_name = []

for i in range(no_point_rail_gpd.shape[0]):
    name = no_point_rail_gpd['name'].iloc[i]
    string = name.split(' ')
    repalce_nanme = string[0].replace('JR', '')
    clean_name.append(repalce_nanme)

no_point_rail_gpd['clean_name'] = clean_name


# keep only JR lines
jr_line_name = ['山手線', '総武線', '青梅線', '中央線', '京浜東北線', '南武線', '埼京線', '中央本線', '常磐線', '五日市線', '湘南新宿ライン', 
                '京葉線', '八高線', '横浜線', '武蔵野線', '総武本線', '横須賀線', '東北本線', '東海道本線', '高崎線', '上越新幹線', '上野東京ライン',
                '北陸新幹線', '東北新幹線', '東海道新幹線']

jr_gpd = no_point_rail_gpd[no_point_rail_gpd['clean_name'].isin(jr_line_name)]


# generate one color for each line
random.Random(2019)
num_color = len(np.unique(jr_gpd['clean_name']))
color = ["#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
             for i in range(num_color)]

# create the color dict
color_dict = {}
line_name = np.unique(jr_gpd['clean_name'])
                     
for i in range(len(line_name)):
    color_dict[line_name[i]] = color[i]

color = []
for i in range(jr_gpd.shape[0]):
    c = color_dict[jr_gpd['clean_name'].iloc[i]]
    color.append(c)
    
jr_gpd['color'] = color



# keep the same crs for all layers 
print (jp.crs, jr_gpd.crs, no_point_park_gpd.crs)

jp['geometry'] = jp['geometry'].to_crs({'init': 'epsg:4326'})



def multipoly_to_poly(gdf, identifier):
    '''
    expand gpd multipolygon to rows of polygons
    gdf: the gpd df with both multipoly and polygon geom_type in geometry
    identifier: the name column to differentiate all the sub polygons in the multipolygon
    '''

    mulitpoly_name = []
    expend_name = []
    expend_geom = []

    for i, row in gdf.iterrows():
        if row['geometry'].geom_type == 'Polygon':
            continue

        elif row['geometry'].geom_type == 'MultiPolygon':
            # keep multipolygon city name to remove later 
            mulitpoly_name.append(row[identifier])
            split_multipoly = list(row['geometry'])

            for j in range(len(split_multipoly)):
                poly_name = row[identifier] + '_' + str(j)
                expend_name.append(poly_name)
                expend_geom.append(split_multipoly[j])
                
    to_exp = gpd.GeoDataFrame({identifier: expend_name, 'geometry': expend_geom})
    gdf = gdf[~gdf[identifier].isin(mulitpoly_name)]
    gdf = pd.concat([gdf, to_exp],)
    
    return gdf


tokyo_coord = jp[jp['KEN'] == '東京都'].iloc[:53, :][['SIKUCHOSON', 'geometry']]
tokyo_coord = multipoly_to_poly(tokyo_coord, 'SIKUCHOSON')

park_coord = no_point_park_gpd[['name', 'geometry']]
park_coord = park_coord[park_coord['name'].notnull()]
# remove geom with type linestring
park_coord = park_coord[park_coord['geometry'].geom_type != 'LineString']
park_coord = multipoly_to_poly(park_coord, 'name')



# parse x and y values for jp shp 

def getpolycoords(row, geom, coord_type):
    """
    returns the coordinates x and y instead of edges of polygon
    """
    exterior = row[geom].exterior
    
    if coord_type == 'x':
        return list(exterior.coords.xy[0])
    elif coord_type == 'y':
        return list(exterior.coords.xy[1])



def getlinecoords(row, geom, coord_type):
    """
    returns a list of coordinates x and y of a LineString geometry
    """
    
    if coord_type == 'x':
        return list(row[geom].coords.xy[0])
    elif coord_type == 'y':
        return list(row[geom].coords.xy[1])
    


# no_point_park_gpd, jr_gpd

tokyo_coord['x'] = tokyo_coord.apply(getpolycoords, geom = 'geometry', coord_type = 'x', axis = 1)
tokyo_coord['y'] = tokyo_coord.apply(getpolycoords, geom = 'geometry', coord_type = 'y', axis = 1)

park_coord['x'] = park_coord.apply(getpolycoords, geom = 'geometry', coord_type = 'x', axis = 1)
park_coord['y'] = park_coord.apply(getpolycoords, geom = 'geometry', coord_type = 'y', axis = 1)

jr_coord = jr_gpd[['name', 'geometry', 'color']]
jr_coord['x'] = jr_gpd.apply(getlinecoords, geom = 'geometry', coord_type = 'x', axis = 1)
jr_coord['y'] = jr_gpd.apply(getlinecoords, geom = 'geometry', coord_type = 'y', axis = 1)



# tokyo_coord, park_coord, jr_coord  

tokyo_plot = tokyo_coord.drop('geometry', axis = 1).copy()
tokyo_plot = ColumnDataSource(tokyo_plot)

park_plot = park_coord.drop('geometry', axis = 1).copy()
park_plot = ColumnDataSource(park_plot)

jr_coord.rename(columns = {'name': 'jr_name'}, inplace = True)
jr_plot = jr_coord.drop('geometry', axis = 1).copy()
jr_plot = ColumnDataSource(jr_plot)


### plot
output_file("park_jr_map.html", title = 'jr_park_tokyo')

p = figure(title = 'park_jr_map', active_scroll = "wheel_zoom",
          plot_height=400, plot_width=700)

# Plot grid
p.patches('x', 'y', source=tokyo_plot,
          color = 'grey',
          fill_alpha=0.7, line_color="white", line_width=0.05)

p.patches('x', 'y', source=park_plot,
         fill_color='green',
         fill_alpha=0.8, line_color="green", line_width=0.05)

p.multi_line('x', 'y', color = 'color', source = jr_plot, line_width = 1.2, line_alpha = 0.4)

# let's also add the hover over info tool
tooltip = HoverTool()
tooltip.tooltips = [('Name of the park', '@name'),
                    ('Name of the line', '@jr_name')]

p.add_tools(tooltip)

show(p)



