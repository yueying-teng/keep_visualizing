

forest_df = pd.read_csv('/Users/yueying.teng/Documents/local_folder_of_continuous_visualizing/world_happines/data/forest_coverage_percent.csv')
map_df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/2014_world_gdp_with_codes.csv')


forest_df = pd.merge(forest_df, map_df[['COUNTRY', 'CODE']], how = 'inner', left_on = 'country', right_on = 'COUNTRY')


country = forest_df['country']
country_rep = np.repeat(country, len(timestamp)).values

code = forest_df['CODE']
code_rep = np.repeat(code, len(timestamp)).values

timestamp = [str(i) for i in np.arange(1990, 2015, 2)]
y = [timestamp for i in range(len(country))]
year = [i for sub in y for i in sub]
cover = forest_df[timestamp].values.reshape(-1, 1)

forest = pd.DataFrame({'country': country_rep, 'year': np.array(year), 'forest': np.ravel(cover), 'code': code_rep})



forest['forest'].iloc[1:] - forest['forest']
forest['forest_shifted'] = forest['forest'].shift(-1)
forest['diff'] = forest['forest_shifted'] - forest['forest']


for i in range(forest.shape[0]):
    if i % 13 == 0:
        forest['diff'].iloc[i] = np.nan
        

mapped = []

for i in range(forest.shape[0]):
    if np.isnan(forest['diff'].iloc[i]):
        mapped.append(0)
    elif forest['diff'].iloc[i] == 0:
        mapped.append(0)
    elif forest['diff'].iloc[i] < 0:
         mapped.append(-1.)
    elif forest['diff'].iloc[i] > 0:
         mapped.append(1.)
    else:
        print (forest.iloc[i])

forest['diff_std'] = mapped



years = timestamp

# make figure
# figure = {'data': [], 'layout': {}, 'frames': []}
figure = {'layout': {}, 'frames': []}

# fill in most of layout
figure['layout']['geo'] = {'showframe': False, 'showcoastlines': False,
                         'projection': {'type': 'natural earth'}}

figure['layout']['sliders'] = {
    'args': [
        'transition', {
            'duration': 400,
            'easing': 'cubic-in-out'
        }
    ],
    'initialValue': '1990',
    'plotlycommand': 'animate',
    'values': years,
    'visible': True
}
figure['layout']['updatemenus'] = [
    {
        'buttons': [
            {
                'args': [None, {'frame': {'duration': 500, 'redraw': False},
                         'fromcurrent': True, 'transition': {'duration': 300, 'easing': 'quadratic-in-out'}}],
                'label': 'Play',
                'method': 'animate'
            },
            {
                'args': [[None], {'frame': {'duration': 0, 'redraw': False}, 'mode': 'immediate',
                'transition': {'duration': 0}}],
                'label': 'Pause',
                'method': 'animate'
            }
        ],
        'direction': 'left',
        'pad': {'r': 10, 't': 87},
        'showactive': False,
        'type': 'buttons',
        'x': 0.1,
        'xanchor': 'right',
        'y': 0,
        'yanchor': 'top'
    }
]

sliders_dict = {
    'active': 0,
    'yanchor': 'top',
    'xanchor': 'left',
    'currentvalue': {
        'font': {'size': 16},
        'prefix': 'Year:',
        'visible': True,
        'xanchor': 'right'
    },
    'transition': {'duration': 300, 'easing': 'cubic-in-out'},
    'pad': {'b': 10, 't': 50},
    'len': 0.9,
    'x': 0.1,
    'y': 0,
    'steps': []
}

# make data
year = '1990'
dataset_by_year = forest[forest['year'] == year]
data_dict = [{'type': 'choropleth', 'locations': dataset_by_year['code'].astype(str),
             'z': dataset_by_year['diff_std'].astype(float),
             'colorscale': [[0, "#C2A878"],
                            [0.5, "#F1F5F2"],
                            [1, "#355834"]]}
            ]
# figure['data'].append(data_dict)
figure['data'] = data_dict
    
# make frames
for year in years:
    frame = {'data': [], 'name': year}
    
    dataset_by_year = forest[forest['year'] == year]
#     data_dict = [{'type': 'choropleth', 'locations': dataset_by_year['code'].astype(str),
#              'z': dataset_by_year['forest'].astype(float)}]
    data_dict = {'type': 'choropleth', 'locations': dataset_by_year['code'].astype(str),
             'z': dataset_by_year['diff_std'].astype(float)}

    frame['data'].append(data_dict)

    figure['frames'].append(frame)
    
    slider_step = {'args': [
        [year],
        {'frame': {'duration': 300, 'redraw': False},
         'mode': 'immediate',
       'transition': {'duration': 300}}
     ],
     'label': year,
     'method': 'animate'}
    sliders_dict['steps'].append(slider_step)
    
figure['layout']['sliders'] = [sliders_dict]

plotly.offline.iplot(figure)



# #### mortality, fertility, gender equality 

# maternal death, number of child death, size - gender equality, region 

# 0-5 year olds dying per 1000 born
mortality_df = pd.read_csv('/Users/yueying.teng/Documents/local_folder_of_continuous_visualizing/world_happines/data/child_mortality_0_5_year_olds_dying_per_1000_born.csv')
# children per women
fertility_df =  pd.read_csv('/Users/yueying.teng/Documents/local_folder_of_continuous_visualizing/world_happines/data/children_per_woman_total_fertility.csv')
# gender ratio of mean years in school women over men 25 to 34 years old
edu_ratio_df = pd.read_csv('/Users/yueying.teng/Documents/local_folder_of_continuous_visualizing/world_happines/data/mean_years_in_school_women_percent_men_25_to_34_years.csv')


# dataset with continent column
url = 'https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv'
dataset = pd.read_csv(url)



kept_country = set(edu_ratio_df['country']).intersection(dataset['country'])

edu_ratio_df = edu_ratio_df[edu_ratio_df['country'].isin(dataset['country'])]
mortality_df = mortality_df[mortality_df['country'].isin(dataset['country'])]
fertility_df = fertility_df[fertility_df['country'].isin(dataset['country'])]

# only keep data from 1970 - 2015
mortality_df = mortality_df[edu_ratio_df.columns]
fertility_df = fertility_df[edu_ratio_df.columns]

kept_dataset = dataset[dataset['country'].isin(list(kept_country))]


# create the df used to make the animated bubble plot with the following columns
# country, year, continent, mortality, fertility, education

df = pd.DataFrame({})

for gp, gp_df in kept_dataset.groupby('country'):
    df = df.append(gp_df[['country', 'continent']].iloc[0])
    
timestamp = [str(i) for i in np.arange(1970, 2020, 5)]
country = np.repeat(df['country'], len(timestamp)).values.reshape(-1, 1)
continent = np.repeat(df['continent'], len(timestamp)).values.reshape(-1, 1)
l = [timestamp for i in range(len(np.unique(df['country'])))]
year = [i for sub in l for i in sub]
mortality = mortality_df[timestamp].values.reshape(-1, 1)
edu_ratio = edu_ratio_df[timestamp].values.reshape(-1, 1)
fertility = fertility_df[timestamp].values.reshape(-1, 1)
    
cols = [country, year, continent, mortality, edu_ratio, fertility]
col_returned = []
for i in range(len(cols)):
    col_returned.append(np.ravel(cols[i]))
        
df = pd.DataFrame({'country': col_returned[0], 'year': col_returned[1], 'continent': col_returned[2],
                  'mortality': col_returned[3], 'edu_ratio': col_returned[4], 'fertility': col_returned[5]})


years = timestamp

# make list of continents
continents = []
for continent in df['continent']:
    if continent not in continents:
        continents.append(continent)

# make figure
figure = {'data': [], 'layout': {}, 'frames': []}

# fill in most of layout
figure['layout']['xaxis'] = {'range': [0, 400], 'title': '0-5 year olds dying per 1000 born'}
figure['layout']['yaxis'] = {'range': [0, 10], 'title': 'children per women'}
figure['layout']['hovermode'] = 'closest'
figure['layout']['sliders'] = {
    'args': [
        'transition', {
            'duration': 400,
            'easing': 'cubic-in-out'
        }
    ],
    'initialValue': '1970',
    'plotlycommand': 'animate',
    'values': years,
    'visible': True
}
figure['layout']['updatemenus'] = [
    {
        'buttons': [
            {
                'args': [None, {'frame': {'duration': 500, 'redraw': False},
                         'fromcurrent': True, 'transition': {'duration': 300, 'easing': 'quadratic-in-out'}}],
                'label': 'Play',
                'method': 'animate'
            },
            {
                'args': [[None], {'frame': {'duration': 0, 'redraw': False}, 'mode': 'immediate',
                'transition': {'duration': 0}}],
                'label': 'Pause',
                'method': 'animate'
            }
        ],
        'direction': 'left',
        'pad': {'r': 10, 't': 87},
        'showactive': False,
        'type': 'buttons',
        'x': 0.1,
        'xanchor': 'right',
        'y': 0,
        'yanchor': 'top'
    }
]

sliders_dict = {
    'active': 0,
    'yanchor': 'top',
    'xanchor': 'left',
    'currentvalue': {
        'font': {'size': 16},
        'prefix': 'Year:',
        'visible': True,
        'xanchor': 'right'
    },
    'transition': {'duration': 300, 'easing': 'cubic-in-out'},
    'pad': {'b': 10, 't': 50},
    'len': 0.9,
    'x': 0.1,
    'y': 0,
    'steps': []
}

# make data
year = '1970'
for continent in continents:
    dataset_by_year = df[df['year'] == year]
    dataset_by_year_and_cont = dataset_by_year[dataset_by_year['continent'] == continent]

    hover_text_and_cont = []
    for i in range(dataset_by_year_and_cont.shape[0]):
        hover_text_and_cont.append(('Country: {}<br>'+ 'Gender Equality: {}').format(
            dataset_by_year_and_cont['country'].iloc[i], dataset_by_year_and_cont['edu_ratio'].iloc[i]))

    data_dict = {
        'x': list(dataset_by_year_and_cont['mortality']),
        'y': list(dataset_by_year_and_cont['fertility']),
        'mode': 'markers',
        'text': hover_text_and_cont,
#         list(dataset_by_year_and_cont['country']),
        'marker': {
            'sizemode': 'area',
            'sizeref': 0.1,
#             'color': dataset_by_year_and_cont['edu_ratio'],
            'size': list(dataset_by_year_and_cont['edu_ratio'])
        },
        'name': continent
    }
    figure['data'].append(data_dict)
    
# make frames
for year in years:
    frame = {'data': [], 'name': year}
    for continent in continents:
        dataset_by_year = df[df['year'] == year]
        dataset_by_year_and_cont = dataset_by_year[dataset_by_year['continent'] == continent]

        hover_text_and_cont = []
        for i in range(dataset_by_year_and_cont.shape[0]):
            hover_text_and_cont.append(('Country: {}<br>'+ 'Gender Equality: {}').format(
                dataset_by_year_and_cont['country'].iloc[i], dataset_by_year_and_cont['edu_ratio'].iloc[i]))

        data_dict = {
            'x': list(dataset_by_year_and_cont['mortality']),
            'y': list(dataset_by_year_and_cont['fertility']),
            'mode': 'markers',
            'text': hover_text_and_cont,
#             list(dataset_by_year_and_cont['country']),
            'marker': {
                'sizemode': 'area',
                'sizeref': 0.1,
#                 'color': dataset_by_year_and_cont['edu_ratio'],
                'size': list(dataset_by_year_and_cont['edu_ratio'])
            },
            'name': continent
        }
        frame['data'].append(data_dict)

    figure['frames'].append(frame)
    slider_step = {'args': [
        [year],
        {'frame': {'duration': 300, 'redraw': False},
         'mode': 'immediate',
       'transition': {'duration': 300}}
     ],
     'label': year,
     'method': 'animate'}
    sliders_dict['steps'].append(slider_step)

    
figure['layout']['sliders'] = [sliders_dict]

plotly.offline.iplot(figure)


