
import geopandas as gpd
import matplotlib.pyplot as plt 
get_ipython().run_line_magic('matplotlib', 'inline')
import json
import numpy as np
import shapely.geometry as geom
import random
import pandas as pd
import pyproj


# # convert JSON to GeoJSON data 

# ! osmtogeojson park_tokyo.json > park_tokyo.geojson
# ! osmtogeojson rail_tokyo.json > rail_tokyo.geojson



# load park anda rail geojson data 
rail_gpd = gpd.read_file('./rail_tokyo.geojson')
park_gpd = gpd.read_file('./park_tokyo.geojson')

# shapefile of japan
file = './japan_ver81/japan_ver81.shp'
jp = gpd.read_file(file)



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



# create park centroid coord gpd
park_centroid = no_point_park_gpd.to_crs({'init': 'epsg:3857'})

# get the centroids of parks
centroid_list = []
for i, row in park_centroid.iterrows():
    centroid = [x[0] for x in row.geometry.centroid.coords.xy]
    centroid_list.append(geom.Point(centroid))

park_centroid_gpd = gpd.GeoDataFrame(park_centroid, geometry = centroid_list)
park_centroid_gpd.tail(3)



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





# generate one color ofr each line

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



# find all parks that are within 200m to the train track being studied

track_area_dict = {}

track_name = np.unique(jr_gpd['clean_name'])
points = park_centroid_gpd['geometry']

for name_idx in range(len(track_name)):
    print (track_name[name_idx])
    
    one_line = jr_gpd[jr_gpd['clean_name'] == track_name[name_idx]]
    lines = one_line['geometry'].to_crs({'init': 'epsg:3857'})
    kept_park_index = []
    sum_area = 0
    
    for i, line in enumerate(lines):
        all_park_to_line = [line.distance(point) for point in points]
        park_name = park_centroid_gpd['name'][np.array(all_park_to_line) < 200.]
        park_name_index = list(park_name.index)

        for j in range(len(park_name_index)):
            if park_name_index[j] in(kept_park_index):
                continue
            else:
                kept_park_index.append(park_name_index[j])
                area = no_point_park_gpd['geometry'].iloc[park_name_index].to_crs({'init': 'epsg:3857'}).area
                sum_area += np.sum(area)
                
    track_area_dict[track_name[name_idx]] = sum_area



greenest_line = sorted(track_area_dict.items(), key=lambda item: item[1], reverse = True)[0][0]
greenest_line



# plot all JR line and the greenest line in red
fig, ax = plt.subplots(figsize = (20,16)) 

tokyo_shp = jp[jp['KEN'] == '東京都']
tokyo_shp.iloc[:53, :].plot(ax = ax, linewidth=0.25, edgecolor='black', color = 'white')

no_point_park_gpd[no_point_park_gpd['centroid_lat'] > 35.0].plot(ax = ax, color = 'green')
jr_gpd.plot(ax = ax, linewidth= 1.2, color = jr_gpd['color'], alpha = 0.4)
jr_gpd[jr_gpd['clean_name'] == greenest_line].plot(ax = ax, linewidth= 2.0, color = 'red', alpha = 0.4, linestyle = '--')

fig.savefig('park_jr_tokyo.png', dpi = 720)


