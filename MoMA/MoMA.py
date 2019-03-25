
import pandas as pd 
import numpy as np
import re


from plotly import tools
import plotly.offline
import plotly.graph_objs as go
plotly.offline.init_notebook_mode(connected = True)


artist_df = pd.read_csv('/Users/yueying.teng/Documents/local_folder_of_continuous_visualizing/MoMA/data/artists.csv', dtype = 'object')
artwork_df = pd.read_csv('/Users/yueying.teng/Documents/local_folder_of_continuous_visualizing/MoMA/data/artworks.csv')

df = pd.merge(artwork_df, artist_df, on = 'Artist ID', how = 'inner')
df = df.drop('Name_y', axis = 1).rename(columns = {'Name_x': 'Name'})
df.head()


# check for NaN
df.columns[df.isnull().any(axis = 0)]



# ### age & acquisition 

# df['Birth Year'] - df['Date'] ot get the age of the artist when the work is created 
# extract sub df without NaN values in both birth year and date columns

year_info_df = df.dropna(subset = ['Date', 'Birth Year'], how = 'any')


# tidy up Date column

# tidy_idx = []
date_created = []

for i in range(year_info_df.shape[0]):
    s = year_info_df['Date'].iloc[i]
    match = re.findall('^([0-9]{4})$', s)
    
    # match for rows that do not have four digits year
    if len(match) != 1:
#         tidy_idx.append(i)
        first = re.findall('([0-9]{4})', s)
        if len(first) == 0:
            # where the entry is Unknown or non string integer value
            date_created.append(s)
        else:
            date_created.append(first[0])
    else:
        date_created.append(match[0])
        

year_info_df.insert(4, 'date_created', date_created)
year_info_df.shape


# find the age of the artist when the art is crearted 

age_at_creation = []

for i in range(year_info_df.shape[0]):

    yob = year_info_df.iloc[i]['Birth Year']
    yoc = year_info_df.iloc[i]['date_created']
    try:
        age = int(yoc) - int(yob)
        age_at_creation.append(int(age))
    except ValueError:
        age_at_creation.append('exp')

len(age_at_creation)


year_info_df.insert(4, 'age_at_creation', age_at_creation)

year_info_df = year_info_df[year_info_df['age_at_creation'] != 'exp']
year_info_df.shape


v, c = np.unique(year_info_df['age_at_creation'], return_counts = True)
value = v[np.argsort(-v)]
count = c[np.argsort(-v)]

# np.asarray((value, count/sum(count))).T
# np.asarray((value, count)).T


# filter for artists as human with concrete year of creattion 

smaller10 = year_info_df[year_info_df['age_at_creation'] < 20]
smaller10 = smaller10[smaller10['Gender'].notnull()]
people10 = smaller10.iloc[[i for i in range(smaller10.shape[0]) if len(smaller10['Date'].iloc[i]) == 4]]
people10 = people10[people10['age_at_creation'] > 0]


bigger80 = year_info_df[year_info_df['age_at_creation'] > 80]
bigger80 = bigger80[bigger80['Gender'].notnull()]
people80 = bigger80.iloc[[i for i in range(bigger80.shape[0]) if len(bigger80['Date'].iloc[i]) == 4]]
people80 = people80[people80['age_at_creation'] > 0]


middle = year_info_df[year_info_df['age_at_creation'] >= 20]
middle = middle[middle['age_at_creation'] <= 80]
middle.shape


# final df for age at creation
age_creation_df = pd.concat([people10, middle, people80])


# age_creation_df.to_csv('age_creation_df.csv', index = False)
age_creation_df = pd.read_csv('age_creation_df.csv')


age_creation_df = age_creation_df[age_creation_df['Gender'] != 'male']

pyramid_data = age_creation_df.groupby([pd.cut(age_creation_df['age_at_creation'], np.arange(0, 100, 5)), 'Gender']).count()
pyramid_data = pyramid_data['Artwork ID'].reset_index().rename(columns = {'Artwork ID': 'Number'})

women_bins = list(-1 * pyramid_data[pyramid_data['Gender'] == 'Female']['Number'])
men_bins = list(pyramid_data[pyramid_data['Gender'] == 'Male']['Number'])

y = list(range(0, 100, 5))

data = [go.Bar(y = y, x = men_bins, orientation = 'h',
               name = 'Male', hoverinfo = 'x', opacity = 0.8,
               marker = dict(color = 'rgb(127, 127, 127)')),
        go.Bar(y = y, x = women_bins, orientation = 'h',
               name = 'Female', hoverinfo = 'text', opacity = 0.8,
               text = -1 * np.array(women_bins).astype('int'),
               marker = dict(color = 'rgb(214, 39, 40)'))]

layout = dict(yaxis = dict(title = 'Age'), 
              xaxis = dict(range = [-4000, 16000],
              tickvals = list(np.arange(-4000, 16000, 1000)),
              ticktext = [-1 * i for i in np.arange(-4000, 16000, 1000) if i < 0] + 
                           [i for i in np.arange(-4000, 16000, 1000) if i >= 0], title = 'Number of artworks'),
              barmode = 'overlay', bargap = 0.05,
              title = 'Age of the artist when the acquired artwork is created')

fig = dict(data = data, layout = layout)

plotly.offline.iplot(fig, filename = 'bar_pyramid.html')
plotly.offline.plot(fig, filename = 'bar_pyramid.html')


### all classes in one plot subplot

data = []

for i in range(len(art_class)):
    current_class_df = age_creation_df[age_creation_df['Classification'] == art_class[i]]
    pyramid_data = current_class_df.groupby([pd.cut(current_class_df['age_at_creation'], np.arange(0, 100, 5)), 'Gender']).count()
    pyramid_data = pyramid_data['Artwork ID'].reset_index().rename(columns = {'Artwork ID': 'Number'})

    men_bins = list(pyramid_data[pyramid_data['Gender'] == 'Male']['Number'])
    women_bins = list(-1 * pyramid_data[pyramid_data['Gender'] == 'Female']['Number'])
    men_bins = np.nan_to_num(men_bins)
    women_bins = np.nan_to_num(women_bins)

    y = list(range(0, 100, 5))

    trace_first = go.Bar(y = y, x = men_bins, orientation = 'h', 
                    name = 'Male', hoverinfo = 'x+name', opacity = 0.8,
                    marker = dict(color = 'rgb(127, 127, 127)'))
    trace_second = go.Bar(y = y, x = women_bins, orientation = 'h',
                   name = 'Female', hoverinfo = 'text+name', opacity = 0.8,
                   text = -1 * np.array(women_bins).astype('int'),
                   marker = dict(color = 'rgb(214, 39, 40)'))

    data.append(trace_first)
    data.append(trace_second)


n_rows = 4
n_cols = 7

pos_pairs = []
for i in range(n_rows):
    for j in range(n_cols):
        cnt = 0
        while cnt != 2:
            pos_pairs.append([i + 1, j + 1])
            cnt += 1


fig = tools.make_subplots(rows = 4, cols = 7, subplot_titles = tuple(art_class), shared_yaxes = True)

for i in range(len(data)):
    fig.append_trace(data[i], pos_pairs[i][0], pos_pairs[i][1])

fig['layout'].update(height = 1200, width = 2000, showlegend = False,
                     barmode = 'overlay', bargap = 0.05,
                     title = 'Age of the artist when the acquired artwork is created')

plotly.offline.plot(fig, filename = 'all classes pyramis subplot')


