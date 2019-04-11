import overpy
import json


def overpass_load_points(iso_a2, tag_key='amenity', tage_value='cafe'):
    '''load points from OSM with overpy'''

    api = overpy.Overpass()
    r = api.query(
        """
        (area["ISO3166-1"="{0}"][admin_level=2];)->.searchArea;
        (node[{1}={2}](area.searchArea);
        way[{1}={2}](area.searchArea);
        relation[{1}={2}](area.searchArea);
        );
        out center;""".format(iso_a2, tag_key, tage_value)
    )

    print("Nodes: {}, Ways: {}, Relations: {}".format(
        len(r.nodes), len(r.ways), len(r.relations)))

    coords, names = [], []
    for node in r.nodes:
        coords.append((float(node.lon), float(node.lat)))
        if 'name' in node.tags:
            names.append(node.tags['name'])
        else:
            names.append(None)

    for way in r.ways:
        coords.append((float(way.center_lon), float(way.center_lat)))
        if 'name' in way.tags:
            names.append(way.tags['name'])
        else:
            names.append(None)

    for rel in r.relations:
        coords.append((float(rel.center_lon), float(rel.center_lat)))
        if 'name' in rel.tags:
            names.append(rel.tags['name'])
        else:
            names.append(None)

    return coords, names


def save_points(filepath, coords, names=None, wgs84=True):
    '''save points from OSM to GeoJSON file'''

    features = []
    for coord, name in zip(coords, names):
        feature = {}
        feature['type'] = 'Feature'
        feature['geometry'] = {}
        feature['geometry']['type'] = 'Point'
        feature['geometry']['coordinates'] = coord

        if names is not None and name is not None:
            feature['properties'] = {}
            feature['properties']['name'] = name

        features.append(feature)

    geojson = {}
    geojson['type'] = 'FeatureCollection'
    geojson['features'] = features

    if wgs84:
        # set CRS as WGS84
        geojson['crs'] = {"type": "name", "properties": {
            "name": "urn:ogc:def:crs:OGC:1.3:CRS84"}}

    with open(filepath, 'w') as f:
        json.dump(geojson, f, indent=4)


def load_points(filepath):
    '''load points from GeoJSON'''

    coords, names = [], []
    with open(filepath, 'r') as f:
        data = json.load(f)
        if data['type'] == 'Multipoint':
            coords = data['coordinates']
            names = [None] * len(coords)
        elif data['type'] == 'FeatureCollection':
            for feature in data['features']:
                coords.append(feature['geometry']['coordinates'])
                if 'properties' in feature and 'name' in feature['properties']:
                    names.append(feature['properties']['name'])
                else:
                    names.append(None)
        else:
            raise ValueError('Type \'' + data['type'] + '\' not supported')

    return coords, names
