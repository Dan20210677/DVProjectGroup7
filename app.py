import dash
from dash import dcc
from dash import html
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
from skimage import io

# https://htmlcheatsheet.com/css/

######################################################Data##############################################################

covid = pd.read_csv('assets/covid19.csv')
covid = covid.drop('Unnamed: 0', axis=1)
covid = covid.drop('index', axis=1)
covid = covid.drop('population', axis=1)
covid = covid.fillna(0)

l = covid['deaths_new']
new_l = []
for i in l:
    if isinstance(i, str):
        if '+-' in i:
            new_l.append(i[2:])
        else:
            new_l.append(i[1:])
    else:
        new_l.append(i)

covid['deaths_new'] = new_l
covid.loc[covid['deaths_new'] == '', 'deaths_new'] = 0
covid.deaths_new = covid.deaths_new.astype(int)
covid.day = pd.to_datetime(covid.day)
covid['month'] = covid['day'].dt.strftime('%Y-%m')
covidmonthsum = covid.groupby(['month','country']).sum()[['cases_new','deaths_new']]
covidmonthmax = covid.groupby(['month','country']).max()[['cases_recovered','cases_1M_pop','cases_total',
                                           'deaths_1M_pop','deaths_total','tests_1M_pop','tests_total']]
covidmonth = pd.concat([covidmonthsum, covidmonthmax], axis=1)
covidmonth['month'] = covidmonth.index.to_frame()['month']
covidmonth['country'] = covidmonth.index.to_frame()['country']
covidmonth = covidmonth.reset_index(drop=True)

vacinas2 = pd.read_csv('assets/country_vaccinations.csv')
vacinas2['1M_pop_vaccinations'] = vacinas2['total_vaccinations_per_hundred']*10000
covid2 = covid.groupby(['country']).max()[['cases_total','deaths_total','cases_1M_pop','deaths_1M_pop']]
vacinas3 = vacinas2.groupby(['country']).max()[['total_vaccinations','1M_pop_vaccinations']]
covid2['country'] = covid2.index.to_frame()['country']
covid2 = covid2.reset_index(drop=True)
vacinas3['country'] = vacinas3.index.to_frame()['country']
vacinas3 = vacinas3.reset_index(drop=True)

######################################################Interactive Components############################################

months = sorted(list(set(covidmonth['month'])))

cases_deaths = [{'label': 'Number of Cases', 'value': 'cases'},
           {'label': 'Number of Deaths', 'value': 'deaths'}]

Cnew_total_1M = [{'label': 'New Cases', 'value': 'new'}, #for cases
           {'label': 'Total Cases', 'value': 'total'},
           {'label': 'Cases by 1M Population', 'value': '1M_pop'}]

Dnew_total_1M = [{'label': 'New Deaths', 'value': 'new'},  #for deaths
           {'label': 'Total Deaths', 'value': 'total'},
           {'label': 'Deaths by 1M Population', 'value': '1M_pop'}]

total_1M = [{'label': 'Total', 'value': 'total'},
           {'label': 'By 1M Population', 'value': '1M_pop'}]

world_continents = [{'label': 'World', 'value': 'world'},
           {'label': 'Europe', 'value': 'europe'},
           {'label': 'Asia', 'value': 'asia'},
           {'label': 'Africa', 'value': 'africa'},
           {'label': 'North America', 'value': 'north america'},
           {'label': 'South America', 'value': 'south america'}]


graph_oneOrMany = [{'label': 'Separar ', 'value': 'separar'},
           {'label': 'juntar', 'value': 'juntar'}]

countries = [{'label': i, 'value': i} for i in list(set(covid.country))]

##################################################APP###################################################################

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY]) 

server = app.server

app.layout = html.Div([
    html.Div([
        html.H1('COVID-19 Data Dashboard'),
    ], className='header grid'),
    
    html.Div([
        html.Div([
            html.Div([
                html.Div([
                    dbc.RadioItems(
                        id="cases_deaths",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-dark btn-lg",
                        labelCheckedClassName="active",
                        options=cases_deaths,
                        value='cases'
                    ),
                ]),
            ], className='colsFixed'),


            html.Div([
                html.Div([
                    dbc.RadioItems(
                        id="new_total_1M",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-dark btn-lg",
                        labelCheckedClassName="active",
                        options=Cnew_total_1M,
                        value='new'
                    ),
                ]),
            ], className='colsFixed'),
        ], className='fixed'),
        
        html.Div([

            dbc.Row([
                dbc.Col(
                    html.H2('COVID-19 Hotspots by Months'),

                ),
                dbc.Col(
                    html.Div([
                        dcc.Dropdown(
                            id='world_continents',
                            options=world_continents,
                            value='world'
                        ),
                    ], className='scope'), width={"size": 3},
                ),
            ]),

            dcc.Graph(
                id='map'
            ),

            dcc.Slider(
                id='slider',
                min=0,
                max=len(months) - 1,
                marks={months.index(i): i for i in months},
                value=0,
                step=1
            )
        ], className='map statistics'),


        html.Div([
            html.H2('Country Comparer'),
            html.P('Compare countries with each other. Change the axis and graphs to see the differences'),
            html.Div([
                dcc.Dropdown(
                    id='country1',
                    options=countries,
                    value='Portugal',
                    multi=False
                ),

                dcc.Dropdown(
                    id='country2',
                    options=countries,
                    value=None,
                    multi=False
                ),

                dcc.Dropdown(
                    id='country3',
                    options=countries,
                    value=None,
                    multi=False
                ),

                dcc.Dropdown(
                    id='country4',
                    options=countries,
                    value=None,
                    multi=False
                ),

                dcc.Dropdown(
                    id='country5',
                    options=countries,
                    value=None,
                    multi=False
                )
            ], className ='countries'),

            dcc.Graph(
                id='comparison'
            ),

            html.Div([
                html.Div([
                    dbc.Button("Join Graphs", id="graph_oneOrMany", outline=True, color="info", n_clicks=0)
                ]),
                

                html.Div([
                    dbc.Button("Split Axis", id="splixAxisY", outline=True, color="info", n_clicks=0, disabled=False)
                ]),

            ], className ='splitAxis'),

        ], className='comparison statistics'),
    ], className='bigDiv'),

    html.Div([
        html.Div([
            html.H2('Top 10 Countries'),
            html.P('Top countries in which category in the period recorded'),
            dbc.RadioItems(
                id="total_1M",
                className="btn-group",
                inputClassName="btn-check",
                labelClassName="btn btn-outline-info",
                labelCheckedClassName="active",
                options=total_1M,
                value='total'
            ),
            
            dcc.Graph(
                id='vacina'
            ),
                
        ], className='vacinas statistics'),


        html.Div([
            dbc.Row([
                html.Img(src=app.get_asset_url('covid.png'), alt="Covid-19 ilustrades figure")
            ], className='img'),

            dbc.Row([
                html.H4('Dash made by:'),
                html.H6('Group 7'),
                html.P('Carolina Sá, m20210693'),
                html.P('Diogo Nobre, m20210677'),
                html.P('Mariana Romão, m20210688'),
                html.P('Mário Negas, m20210596'),

            ], className='madeBy')
        ]),
    ], className='cols'),


        

], className='dashboard')

######################################################Callbacks#########################################################


@app.callback(
     [
        Output(component_id='map', component_property='figure'),
        Output(component_id='comparison', component_property='figure'),
        Output(component_id='vacina', component_property='figure'),
        Output(component_id='graph_oneOrMany', component_property='children'),
        Output(component_id='graph_oneOrMany', component_property='outline'),
        Output(component_id='splixAxisY', component_property='children'),
        Output(component_id='splixAxisY', component_property='outline'),
        Output(component_id='splixAxisY', component_property='disabled'),
        Output(component_id='new_total_1M', component_property='options')
    ],
    [
        Input(component_id='cases_deaths', component_property='value'),
        Input(component_id='new_total_1M', component_property='value'),

        Input(component_id='world_continents', component_property='value'),
        Input(component_id='slider', component_property='value'),

        Input(component_id='country1', component_property='value'),
        Input(component_id='country2', component_property='value'),
        Input(component_id='country3', component_property='value'),
        Input(component_id='country4', component_property='value'),
        Input(component_id='country5', component_property='value'),
        Input(component_id='splixAxisY', component_property='n_clicks'),
        Input(component_id='graph_oneOrMany', component_property='n_clicks'),

        Input(component_id='total_1M', component_property='value'),
        
    ]
)
def plots(cases, new, scope, month, country1, country2, country3, country4, country5, n_clicks_axisy, n_clicks, total): 
    cases_new= cases+'_'+new
    colors = ['#005f73','#52c9e1','#e9d8a6','#ee9b00','#9b2226']
    if cases == 'cases':
        new_total_1M = Cnew_total_1M
    else:
        new_total_1M = Dnew_total_1M
    ############################################ Map ##########################################################
    if (month == 0 or month == 1) and cases_new == 'deaths_1M_pop':
        img = io.imread('assets/Capture.jpg')
        fig_map = px.imshow(img)

    else:
        mapadia = covidmonth.loc[covidmonth['month'] == months[month]][['country', cases_new]]
        data_map = dict(type='choropleth',
                            locations=mapadia['country'],
                            locationmode='country names',
                            z=mapadia[cases_new],
                            text=mapadia['country'],
                            colorscale= colors
                            
                            )

        layout_map = dict(geo=dict(scope=scope,  # default
                                        #rojection=dict(type='orthographic'
                                                        #),
                                        showland=True,   # default = True
                                        landcolor='white',
                                        lakecolor='azure',
                                        showocean=True,  # default = False
                                        oceancolor='azure'
                                        ),

                                title=dict(text='Number of Covid ' + get_key(new ,new_total_1M) + ' in ' + str(months[month]),
                                            x=.5  # Title relative position according to the xaxis, range (0,1)
                                            ),
                                margin={"r":0,"t":28,"l":0,"b":0}

                                )

        fig_map = go.Figure(data=data_map, layout = layout_map)
    
    ############################################ Vacina ##########################################################
    subplot_titles = ['Cases', 'Deaths', 'Vaccines']
    if total == 'total':
        hc = 0.08
    else: 
        hc = 0.14

    sub_1 = make_subplots(rows=3, cols=1,
                          subplot_titles=subplot_titles,
                          #horizontal_spacing=hc
                          vertical_spacing= 0.1
                          )

    bar1 = covid2.sort_values('cases_' + total, ascending=False).head(10).iloc[::-1]
    trace1 = dict(type='bar',
                  y=bar1['country'],
                  x=bar1['cases_' + total],
                  name='cases_' + total,
                  text=bar1['cases_' + total],
                  textposition='auto',
                  orientation='h',
                  showlegend=False,
                  marker_color=colors[3]
                  )
    
    sub_1.add_trace(trace1, row=1, col=1)

    bar2 = covid2.sort_values('deaths_' + total, ascending=False).head(10).iloc[::-1]
    trace2 = dict(type='bar',
                  y=bar2['country'],
                  x=bar2['deaths_' + total],
                  name='deaths_' + total,
                  text=bar2['deaths_' + total],
                  textposition='auto',
                  orientation='h',
                  showlegend=False,
                  marker_color=colors[4] 
                  )
    sub_1.add_trace(trace2, row=2, col=1)

    bar3 = vacinas3.sort_values(total + '_vaccinations', ascending=False).head(10).iloc[::-1]
    trace3 = dict(type='bar',
                  y=bar3['country'],
                  x=bar3[total + '_vaccinations'].round(0),
                  name=total + '_vaccinations',
                  text=bar3[total + '_vaccinations'].round(0),
                  textposition='auto',
                  orientation='h',
                  showlegend=False,
                  marker_color=colors[1]
                  )
    sub_1.add_trace(trace3, row=3, col=1),
    sub_1.update_yaxes(showline=False, linewidth=1, linecolor='black')
    sub_1.update_xaxes(showline=False, linewidth=1, linecolor='black', gridcolor='rgb(234, 243, 228)')
    sub_1.update_layout(plot_bgcolor='rgba(0,0,0,0)'),
    sub_1.update_layout(height=800, width=600),


    ############################################ Compare Plot ##########################################################
    countries = [country1, country2, country3, country4, country5]
    toRemove=[]
    for i in countries:
        if i == None:
            toRemove.append(i)
    
    for i in toRemove:
        countries.remove(i)
    
    if n_clicks_axisy%2 != 0:
        nameAxisY = 'Split Axis'
        axisy = True
    else:
        nameAxisY = 'Match Axis'
        axisy = False

    if n_clicks%2 != 0:
        data_graph = []
        for num, i in enumerate(countries):
            covidlinha = covid.loc[covid['country'] == i][['day', cases_new]]
            covidlinha.replace(0, np.nan, inplace=True)
            mask = np.isfinite(covidlinha[cases_new])
            trace1 = dict(type='scatter',
                          x=covidlinha['day'][mask],
                          y=covidlinha[cases_new][mask],
                          name=i,
                          line_color=colors[num]
                          )
            data_graph.append(trace1)

        compare_layout = dict(xaxis=dict(title='Date'),
                          yaxis=dict(title='Number of Covid ' + get_key(new ,new_total_1M)),
                          plot_bgcolor='rgba(0,0,0,0)'
                          )

        
        compare_fig = go.Figure(data=data_graph, layout=compare_layout)
        compare_fig.update_yaxes(showline=True, linewidth=1, linecolor='black', gridcolor='rgb(234, 243, 228)')
        compare_fig.update_xaxes(showline=True, linewidth=1, linecolor='black')

        return fig_map, compare_fig, sub_1, "Split Graphs", False, nameAxisY, axisy, True, new_total_1M

    else:
        if len(countries) == 0:
            sub_compare= {}
        else:
            subplot_titles = countries
            sub_compare = make_subplots(rows=1, cols=len(countries),
                                shared_yaxes=axisy,
                                subplot_titles=subplot_titles,
                                
                                )
            data_graph = []
                    
            for num,i in enumerate(countries):
                covidlinha = covid.loc[covid['country'] == i][['day', cases_new]]
                covidlinha.replace(0, np.nan, inplace=True)
                mask = np.isfinite(covidlinha[cases_new])
                trace1 = dict(type='scatter',
                            x=covidlinha['day'][mask],
                            y=covidlinha[cases_new][mask],
                            name=i,
                            line_color=colors[num],
                            )
                
                data_graph.append(trace1)
            j = 1
            for i in data_graph:
                sub_compare.add_trace(i, row=1, col=j)
                sub_compare.update_yaxes(showline=True, linewidth=1, linecolor='black', gridcolor='rgb(234, 243, 228)')
                sub_compare.update_xaxes(showline=True, linewidth=1, linecolor='black')
                sub_compare.update_layout(plot_bgcolor='rgba(0,0,0,0)')


                j = j + 1

        
        
        return fig_map, sub_compare, sub_1, "Join Graphs", True, nameAxisY, axisy, False, new_total_1M


def get_key(val, lis):
    for idi,  i in enumerate(lis):
        for key, value in i.items():
            if val == value:
                return lis[idi].get('label')

if __name__ == '__main__':
    app.run_server(debug=True)
