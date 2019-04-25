

import geopandas as gpd
import matplotlib.pyplot as plt 
get_ipython().run_line_magic('matplotlib', 'inline')
import json
import numpy as np
import shapely.geometry as geom
import random
import pandas as pd


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



# create park centroid coord gpd
park_centroid = no_point_park_gpd

# get the centroids of parks
centroid_list = []
for i, row in park_centroid.iterrows():
    centroid = [x[0] for x in row.geometry.centroid.coords.xy]
    centroid_list.append(geom.Point(centroid))

park_centroid_gpd = gpd.GeoDataFrame(park_centroid, geometry = centroid_list)
# park_centroid_gpd.tail(3)



tokyo_shp = jp[jp['KEN'] == '東京都']
tokyo_shp = tokyo_shp.iloc[:53, :]
# find parks that are within each district polygon
park_ku = gpd.sjoin(park_centroid_gpd, tokyo_shp, how='left')
park_ku = park_ku[['name', 'SIKUCHOSON', 'centroid_lat']]


districts = np.unique(tokyo_shp['SIKUCHOSON'])
park_area_ku_dict = {}

# find total area of parks in each district 
for i in range(len(districts)):
    district = districts[i]
    sum_area = 0.
    park_in_district = park_ku[park_ku['SIKUCHOSON'] == district]
    for j in range(park_in_district.shape[0]):
        centroid = park_in_district['centroid_lat'].iloc[j]
        area = no_point_park_gpd[no_point_park_gpd['centroid_lat'] == centroid]['geometry'].to_crs({'init': 'epsg:3857'}).area
        sum_area += np.sum(area)
        
    park_area_ku_dict[district] = sum_area
        

# no_point_park_gpd
df = park_ku.groupby('SIKUCHOSON').count().reset_index()[['SIKUCHOSON', 'centroid_lat']]
df['sum_park_area'] = list(park_area_ku_dict.values())

ku_area = tokyo_shp[['SIKUCHOSON', 'geometry']]
ku_area['ku_area'] = ku_area['geometry'].to_crs({'init': 'epsg:3857'}).area

df2 = pd.merge(df, ku_area[['SIKUCHOSON', 'ku_area']], on = 'SIKUCHOSON', how = 'left')
df2['park_prop'] = df2['sum_park_area']/ df2['ku_area']
df2 = df2.sort_values('park_prop', ascending = False)



# tokyo_shp.plot(column=df['sum_area'], colormap='OrRd', legend=True)

fig, ax = plt.subplots(figsize = (18,18)) 

tokyo_shp = jp[jp['KEN'] == '東京都'].iloc[:53, :]
tokyo_shp = pd.merge(tokyo_shp, df2, on = 'SIKUCHOSON', how = 'left')

tokyo_shp.plot(ax = ax, linewidth=0.25, edgecolor='black', column='park_prop', colormap='Greens')
jr_gpd[jr_gpd['clean_name'] == '京浜東北線'].plot(ax = ax, linewidth=1.5, color = 'grey')




