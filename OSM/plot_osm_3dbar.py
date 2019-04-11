
import imageio
import glob
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from pyproj import Proj
from matplotlib import cm
import utils_osm
import matplotlib.pyplot as plt
%matplotlib inline


def normalize_points(points):
    '''
    normalize points while preserving aspect ratio
    points are coordinates downloaded using overpass API
    '''

    data = np.array(points)

    minx, miny = np.min(data, axis=0)
    maxx, maxy = np.max(data, axis=0)
    rangex, rangey = maxx - minx, maxy - miny

    if rangex > rangey:
        data[:, 0] = (data[:, 0] - minx - 0.5*rangex) / rangex + 0.5
        data[:, 1] = (data[:, 1] - miny - 0.5*rangey) / rangex + 0.5
    else:
        data[:, 0] = (data[:, 0] - minx - 0.5*rangex) / rangey + 0.5
        data[:, 1] = (data[:, 1] - miny - 0.5*rangey) / rangey + 0.5

    return data


def heatmap_grid(data, sigma_sq=0.0001, n=20, m=2):
    '''create n x n grid from data with gaussian distribution'''

    X = np.ndarray((n, n), dtype=object)
    for idx in np.arange(len(data)):
        x, y = data[idx]
        i, j = int(x * (n - 1)), int(y * (n - 1))
        # grid assignment for all coordinates
        if X[i, j] is None:
            X[i, j] = [(x, y)]
        else:
            X[i, j].append((x, y))

    grid = np.zeros((n, n))
    for i0 in range(n):
        for j0 in range(n):
            x0, y0 = i0/(n-1), j0/(n-1)  # center of the grid (x0, y0)

            # sum all elements in the neighborhood
            for i in range(max(0, i0 - m), min(i0 + m, n)):
                for j in range(max(0, j0 - m), min(j0 + m, n)):
                    if X[i, j] is not None:
                        for x, y in X[i, j]:
                            grid[i0][j0] += np.exp(- ((x0 - x)**2) /
                                                   (2*sigma_sq) - ((y0 - y)**2)/(2*sigma_sq))

    return grid


# plot 3d bar chart

# download location data of cafes in Japan
# coords, names = utils_osm.overpass_load_points(
#     'JP', tag_key='amenity', tage_value='cafe')
# utils_osm.save_points('jp_cafe.json', coords, names=names)

# load the data
points, names = utils_osm.load_points('jp_cafe.json')

# Popular Visualisation CRS / Mercator
p = Proj(init="epsg:3785")
points = np.apply_along_axis(lambda x: p(*x), 1, points)
points = normalize_points(points)
grid = heatmap_grid(points, n=100, m=2)


fig = plt.figure(figsize=(20, 16))
ax = fig.add_subplot(111, projection='3d')

data_array = grid
x_data, y_data = np.meshgrid(
    np.arange(data_array.shape[1]), np.arange(data_array.shape[0]))

x_data = x_data.flatten()
y_data = y_data.flatten()
z_data = data_array.flatten()
bottom = np.zeros(len(z_data))
width = [1.0 for i in range(len(x_data))]
depth = [1.0 for i in range(len(x_data))]

cmap = cm.get_cmap('summer')
max_height = np.max(z_data)   # get range of colorbars for normalization
min_height = np.min(z_data)
# scale each z to [0,1], and get their rgb values
rgba = [cmap((k-min_height)/max_height) for k in z_data]

for i in range(z_data.shape[0]):
    if z_data[i] == 0:
        rgba[i] = '#ffffff'
    else:
        continue

# stretch the axes
x_scale = 1.2
y_scale = 1.2
z_scale = 1.2

scale = np.diag([x_scale, y_scale, z_scale, 1.0])
scale = scale*(1.0/scale.max())
ax.get_proj = np.dot(Axes3D.get_proj(ax), scale)

ax.bar3d(x_data, y_data, bottom, width, depth, z_data, color=rgba)
ax.set_axis_off()


# plot more with different angles to generate gif
angles = np.linspace(0, 360, 36)[:]
for i in range(len(angles)):
    ax.view_init(elev=None, azim=angles[i])
    ax.figure.savefig(
        './gif/jp_cafe_angle_{}.png'.format(angles[i]), transparent=True)

# create gif using the gif just plotted
files = glob.glob('./gif/jp_cafe_angle_*.png')
# order the files according to the value of the numerical number in the file name
filenames = sorted(files, key=lambda x: int(x.split('_')[-1].split('.')[0]))

images = []
for filename in filenames:
    images.append(imageio.imread(filename))
imageio.mimsave('./jp_cafe.gif', images)
