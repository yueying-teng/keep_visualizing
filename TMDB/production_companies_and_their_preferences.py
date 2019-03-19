

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
get_ipython().run_line_magic('matplotlib', 'inline')
import re
import cpi

import plotly.offline
import plotly.graph_objs as go
plotly.offline.init_notebook_mode(connected = True)


# ### data preparation 
# source of the data https://www.kaggle.com/c/tmdb-box-office-prediction/data

train_df = pd.read_csv('./data/train.csv')
test_df = pd.read_csv('./data/test.csv')

df = pd.concat([train_df, test_df])
cols = ['original_title', 'title', 'genres', 'popularity', 'homepage', 'original_language', 'production_companies', 'runtime', 'release_date', 'budget']
df = df[cols]



def col_string_extraction(col_name):
  '''
  some columns have values stored in dictionary but the datatype is string
  '''

    col_name_list = []

    for i in range(df.shape[0]):
        st = df[col_name].iloc[i]
        # some movies have production compnaies as null
        if type(st) != str:
            col_name_list.append(['NaN'])
        
        else:
            subs = re.findall("\{(.*?)\}", str(st))

            col = []
            for j in range(len(subs)):
                extracted = re.findall("\: '(.*?)\'", subs[j])
                # some entries do not fit in the regex above
                if len(extracted) != 0:
                    col.append(extracted[0])
                else:
                    continue

            col_name_list.append(col)
    
    return col_name_list



# exteact release yearn genre and production company
production_company_list = col_string_extraction('production_companies')
# only look into the first genre if the movie has more than one genre
genre_list = col_string_extraction('genres')
one_genre_list = [genre_list[i][0] for i in range(len(genre_list))]

df.insert(2, 'genre', one_genre_list)
df.insert(4, 'production_company', production_company_list)

df = df.drop(['genres', 'production_companies'], axis = 1)


# extract release year and store in the following format xxxx
release_year = df['release_date'].apply(lambda x: str(x).split('/')[-1])

release_year_adj = []

for i in range(len(release_year)):
    
    if str(release_year.iloc[i]) == 'nan':
        release_year_adj.append('NaN')
    
    else:
        if 0 <= int(release_year.iloc[i]) <= 20:
            year = str(20) + str(release_year.iloc[i])
            release_year_adj.append(year)
        else:
            year = str(19) + str(release_year.iloc[i])
            release_year_adj.append(year)
        
df.insert(8, 'release_year', release_year_adj)



# ### Genre

# genre dist for the major production companies 
companies = df['production_company'].values
unique_companies = [i for sub in companies for i in sub]
v, c = np.unique(unique_companies, return_counts = True)
value = v[np.argsort(-c)]
count = c[np.argsort(-c)]

np.asarray((value, count)).T[: 11]


top_companies = value[: 11]
top_companies = np.delete(top_companies, 2)

genre = np.unique(df['genre'])
# remove NaN from the array of all genres
genre = [genre[i] for i in range(len(genre)) if genre[i] != 'NaN']

# create a dataframe with company name as row index and genre as column
starter = np.zeros((len(top_companies), len(genre)))
company_genre_df = pd.DataFrame(starter, columns = genre, index = top_companies)

for i in range(df.shape[0]):
    
    company_list = df['production_company'].iloc[i]
    genre = df['genre'].iloc[i]
    
    for j in range(len(company_list)):
        if company_list[j] not in top_companies:
            continue
        else:
            company_genre_df.loc[company_list[j]][genre] += 1
        

company_genre_df['num_movies'] = list(company_genre_df.sum(axis = 1))


# favouriate genre of the industry represented by these 10 production companies
print (np.argmax(company_genre_df.iloc[:, : -1].sum(axis = 0)))

# favouriate genre of each company 
company_genre_df.iloc[:, :-1].idxmax(axis = 1)


# pie chart of genre dist for four major production companies
genre_list = company_genre_df.columns[: -1]

fig = {'data': [
        {
            'labels': genre_list,
            'values': company_genre_df.iloc[0, : -1],
            'type': 'pie',
            'name': company_genre_df.index[0],
            'domain': {'x': [0, .48],
                       'y': [0, .49]},
            'hoverinfo':'label+percent+name',
            'textinfo':'none'
        },
        {
            'labels': genre_list,
            'values': company_genre_df.iloc[1, : -1],
            'type': 'pie',
            'name':  company_genre_df.index[1],
            'domain': {'x': [.52, 1],
                       'y': [0, .49]},
            'hoverinfo':'label+percent+name',
            'textinfo':'none'

        },
        {
            'labels': genre_list,
            'values': company_genre_df.iloc[2, : -1],
            'type': 'pie',
            'name':  company_genre_df.index[2],
            'domain': {'x': [0, .48],
                       'y': [.51, 1]},
            'hoverinfo':'label+percent+name',
            'textinfo':'none'
        },
        {
            'labels': genre_list,
            'values': company_genre_df.iloc[3, : -1],
            'type': 'pie',
            'name': company_genre_df.index[3],
            'domain': {'x': [.52, 1],
                       'y': [.51, 1]},
            'hoverinfo':'label+percent+name',
            'textinfo':'none'
        }
    ],
    'layout': {'title': 'four companies preferences of genres',
               'showlegend': True}
}

plotly.offline.plot(fig, filename = 'four_companies_genre.html')




# ### popularity through out year 


pop_year_dict = {'name': [], 'year': [], 'company': [], 'pop': []}

for i in range(df.shape[0]):
    name = df['original_title'].iloc[i]
    year = df['release_year'].iloc[i]
    companies = df['production_company'].iloc[i]
    pop = df['popularity'].iloc[i]
    
    for j in range(len(companies)):
        pop_year_dict['name'].append(name)
        pop_year_dict['year'].append(year)
        pop_year_dict['pop'].append(pop)
        pop_year_dict['company'].append(companies[j])
        
pop_year_df = pd.DataFrame(pop_year_dict)



# create the dataframe with year, production company name and yearly averge movie popularity as columns
four_companies = ['Warner Bros.', 'Universal Pictures', 'Paramount Pictures', 'Twentieth Century Fox Film Corporation']
df_list = []

for i in range(len(four_companies)):
  df = pop_year_df[pop_year_df['company'].isin([four_companies[i]])]
  df = df.groupby('year').mean().reset_index().rename(columns = {'pop': four_companies[i].replace(' ', '_') + '_pop'})
  df_list.append(df)


for df in df_list:
    df.set_index(['year'], inplace = True)

pop_df = pd.concat(df_list, axis = 1) # join='inner'
# pop_df.reset_index(inplace = True)
pop_df.head()


# line chart - trend in yearly average movie popularity for four companies 
data = []

for i in range(len(top_companies[:4])):
    trace = go.Scatter( x = pop_df.index.values,
                        y = pop_df.iloc[:, i],
                        name = pop_df.columns[i],                   
                        mode = 'lines+markers')
    data.append(trace)

layout = dict(title = 'major production companies and their yearly average popularity',
              xaxis = dict(title = 'year'),
              yaxis = dict(title = 'average popularity'),
              width = 1000,
              height = 600,
              margin = dict(l = 40, r = 10, b = 100, t = 100, pad = 4),
             annotations = [dict(x = 1960, y = 36.826309, xref = 'x', yref = 'y',
                               text = 'Psycho', showarrow = True, arrowhead = 2,
                               ax = 0, ay = -40),
                            dict(x = 1972, y = 41.109264, xref = 'x', yref = 'y',
                               text = 'The Godfather', showarrow = True, arrowhead = 2,
                               ax = 0, ay = -40),
                            dict(x = 1982, y = 29.069632, xref = 'x', yref = 'y',
                               text = 'Blade Runner', showarrow = True, arrowhead = 2,
                               ax = 0, ay = -40),
                            dict(x = 1999, y = 19.9939424, xref = 'x', yref = 'y',
                               text = 'Fight Club', showarrow = True, arrowhead = 2,
                               ax = 0, ay = -40),
                           dict(x = 2009, y = 38.1531945, xref = 'x', yref = 'y',
                               text = 'Avatar', showarrow = True, arrowhead = 2,
                               ax = 0, ay = -40),
                           dict(x = 2015, y = 58.37523253846154, xref = 'x', yref = 'y',
                               text = 'Minions', showarrow = True, arrowhead = 2,
                               ax = 0, ay = -40),
                           dict(x = 2017, y = 63.34606228571429, xref = 'x', yref = 'y',
                               text = 'Wonder Woman', showarrow = True, arrowhead = 2,
                               ax = 0, ay = -40)
                           ])

fig = dict(data = data, layout = layout)
plotly.offline.plot(fig, filename = 'four_companies_popularity.html')



def return_pop_movie_given_year(year):
    '''
    return the most popular movie name and 
    the average popularity score of movies produced by the company with the most popular movie in a given year
    '''
    y = pop_year_df[pop_year_df['year'] == year]
    y = y[y['company'].isin(top_companies[: 4])]
    movie_name = y.loc[np.argmax(y['pop'])]['name']
    pop_company = y.loc[np.argmax(y['pop'])]['company']
    pop_company_avg_socre = np.mean(y[y['company'] == pop_company]['pop'])

    return movie_name, pop_company_avg_socre



year_given = ['1960', '1972', '1982', '1999', '2009', '2015', '2017']

for i in range(len(year_given)):
    n, p = return_pop_movie_given_year(year_given[i])
    print (n, year_given[i], p)
    

