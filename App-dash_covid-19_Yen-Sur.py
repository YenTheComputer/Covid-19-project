import pandas as pd # version 1.0.1
import plotly # (version 4.5.1)
import plotly.express as px  
import plotly.graph_objects as go
import json # 2.0.9
import numpy as np #2.0.9
import plotly.io as pio
pio.renderers.default = 'browser'

import dash  # 1.8.0
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_table #4.6.0
import urllib.request #3.6
from urllib.request import urlretrieve as ret 
import datetime

app = dash.Dash(__name__)

# ------------------------------------------------------------------------------
################################### Chargement des fichiers à jour #####################################""
config_file = pd.read_csv('config_dash.csv')
today = datetime.datetime.now()
day = today.strftime("%Y-%m-%d")
if config_file.loc[0,'Date'] != day :
    try:
        url2 = "https://www.data.gouv.fr/fr/datasets/r/6fadff46-9efd-4c53-942a-54aca783c30c"
        ret(url2, 'data_france_hp.csv')
        df_fr_dpt_0 = pd.read_csv('data_france_hp.csv',  sep = ';')

        config_file.loc[0,'Date'] = day
        config_file.to_csv('config_dash.csv', index = False)
        print('la date a changé')

    except:
        pass
else :
    df_fr_dpt_0 = pd.read_csv('data_france_hp.csv',  sep = ';')
    print('la date est inchangée')

try :       
    url1 = "https://raw.githubusercontent.com/OxCGRT/covid-policy-tracker/master/data/OxCGRT_latest.csv"
    df = pd.read_csv(url1)
except :
    df = pd.read_csv('OxCGRT_latest0.csv')
print('Veuillez patienter svp...')
################################### Transformation des données ###########################################
#### Données mondiales
df['Date'] = pd.to_datetime(df['Date'], format = '%Y%m%d')

##### Création d'une nouvelle colonne référençant les nouveaus décès de la journée
df['NewDeaths'] = np.nan

for i in range(0, len(df)) :
    try :
        df.loc[i,'NewDeaths'] = df.loc[i+1,'ConfirmedDeaths'] - df.loc[i,'ConfirmedDeaths']
    except :
        pass
df_france = df[df['CountryName'] == 'France']
df_france = df_france.reset_index()

ligne_fr = len(df_france) -3
df_late = df[df['Date'] == df_france.loc[ligne_fr,'Date']]
df_late = df_late.reset_index()

df_pays = df[df['Date']== '2020-02-02']
df_pays = df_pays.reset_index()


######## geojson des département
france_dpt = json.load(open("departements.geojson", "r"))

######## transformation des données
id_dpt_map = {}
for feature in france_dpt['features'] :
    feature['id'] = feature['properties']['code']
    id_dpt_map[feature['properties']['nom']] = feature['id']

df_dpt = pd.DataFrame(id_dpt_map.items(), columns=['Nom du département', 'dep'])
df_fr_dpt = pd.merge(df_fr_dpt_0, df_dpt, on='dep', how='left')

df_fr_ain01 = df_fr_dpt[df_fr_dpt['dep'] == '01']
df_fr_ain01 = df_fr_ain01.reset_index()



# ------------------------------------------------------------------------------
###################################################### App layout
app.layout = html.Div([

    html.H1("Covid-19 dashboard", style={'text-align': 'center'}),
    html.Br(),
    html.H2("World map representing daily new cases of Covid-19"),
    dcc.Dropdown(id="slct_year",
                 options=[
                     {"label": i.date(), "value": i}
                     for i in df_france['Date']
                     ],
                 multi=False,
                 value='2020-03-26',
                 style={'width': "40%"}
                 ),
    
    html.Div(id='datatable_world', children=[]),


    html.Div(id='output_container', children=[]),

    dcc.Graph(id='my_covid_map', figure={}, style= {"height" : 700}),
    dcc.Graph(id = 'bar-chart',figure = {}, style = {"height" : 300}),

    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
    html.H1("Search for a specific data", style={'text-align': 'center'}),
    dcc.Dropdown(id="slct_country",
                 options=[
                     {"label": i, "value": i}
                     for i in df_pays['CountryName']
                     ],
                 multi=False,
                 value='France',
                 style={'width': "40%"}
                 ),

    html.Div(id='output_container2', children=[]),

    dcc.Dropdown(id="slct_date",
                options=[
                    {"label": i.date(), "value": i}
                    for i in df_france['Date']
                    ],
                multi=False,
                value=df_late.loc[1,'Date'],
                style={'width': "40%"}
                ),


    html.Div(id='output_container3', children=[]),

    html.Div(id='datatable', children=[]),

    html.Br(),
    html.Br(),

    html.H1("World overview data", style={'text-align': 'center'}),

    html.Div([
        dash_table.DataTable(
            id = 'top-table',
            data = df_late.to_dict('records'),
            columns = [
                {"name" : "CountryName", "id" : "CountryName"},
                {"name" : "RegionName" , "id" : "RegionName"},
                {"name" : "Date", "id" : "Date"},
                {"name" : "ConfirmedCases", "id" : "ConfirmedCases"},
                {"name" : "ConfirmedDeaths" , "id" : "ConfirmedDeaths"},
                {"name" : "NewDeaths", "id" : "NewDeaths"}
            ],
            filter_action = "native",
            page_action = "native",
            page_current=0,
            page_size = 10,
            sort_action = "native",
            sort_mode = "single"
            )
        ]),
    html.Br(),
    html.Br(),
######################################################## FRANCE ###################################################
    html.H1("Hospital overview France data", style={'text-align': 'center'}),


    dcc.Dropdown(id="slct_date_fr_dpt",
                 options=[
                     {"label": i, "value": i}
                     for i in df_fr_ain01['jour']
                     ],
                 multi=False,
                 value=df_fr_ain01.iloc[-1,2],
                 style={'width': "40%"}
                 ),

    html.Div(id='output_container4', children=[]),

    dcc.Graph(id='my_fr_map_dc_hopital', figure={}, style= {"height" : 700}),
    dcc.Graph(id='my_fr_map_hosp_hopital', figure={}, style= {"height" : 700}),
    dcc.Graph(id='my_fr_map_rea_hopital', figure={}, style= {"height" : 700}),
    dcc.Graph(id='my_fr_map_rad_hopital', figure={}, style= {"height" : 700})

])



################################# callback world map and bar chart ###########################""
@app.callback(
    [Output(component_id='output_container', component_property='children'),
     Output(component_id='my_covid_map', component_property='figure'),
     Output(component_id='bar-chart', component_property='figure')
     ],
    [Input(component_id='slct_year', component_property='value')]
)
def update_graph(option_slctd):

    container = "The date chosen by user was: {}".format(option_slctd)

    dff = df.copy()
    dff = dff[dff['Date'] == (option_slctd)]

    # Plotly Express
    fig = px.choropleth(
        data_frame=dff,
        locationmode='country names',
        locations='CountryName',
        scope="world",
        color='NewDeaths',
        hover_data=['CountryName', 'NewDeaths'],
        color_continuous_scale=px.colors.sequential.YlOrRd,
        labels={'NewDeaths': 'New deaths at this date'},
    )

    fig2 = px.bar(
        data_frame=dff,
        x = "CountryName",
        y = "NewDeaths",
        labels={'NewDeaths' : 'New deaths at this date'}
    )

    return container, fig, fig2


################################ call back datatable ###########################""
@app.callback([
    Output(component_id='output_container2', component_property='children'),
    Output(component_id='output_container3', component_property='children'),
    Output(component_id='datatable', component_property='children')],
    [Input(component_id='slct_country', component_property='value'),
    Input(component_id='slct_date', component_property='value')
    ]
    )


def update_table(country_slctd, date_slctd) :

    container2 = "The country chosen by user was: {}".format(country_slctd)
    container3 = "The date chosen by user was: {}".format(date_slctd)

    dff2 = df.copy()
    dff2 = dff2[(dff2['CountryName'] == country_slctd) & (dff2['Date']== date_slctd)]
    
    fig3 = dash_table.DataTable(
        data = dff2.to_dict('records'),
        columns = [
            {"name" : "CountryName", "id" : "CountryName"},
            {"name" : "Date", "id" : "Date"},
            {"name" : "ConfirmedCases", "id" : "ConfirmedCases"},
            {"name" : "ConfirmedDeaths" , "id" : "ConfirmedDeaths"},
            {"name" : "NewDeaths", "id" : "NewDeaths"}
            ]
            )

    return container2, container3, fig3

############################## callback données hospitalière FR #############################
@app.callback(
    [Output(component_id='output_container4', component_property='children'),
     Output(component_id='my_fr_map_dc_hopital', component_property='figure'),
     Output(component_id='my_fr_map_hosp_hopital', component_property='figure'),
     Output(component_id='my_fr_map_rea_hopital', component_property='figure'),
     Output(component_id='my_fr_map_rad_hopital', component_property='figure')
     ],
    [Input(component_id='slct_date_fr_dpt', component_property='value')]
)
def update_graph2(option_slctd2):

    container4 = "The date chosen by user was: {}".format(option_slctd2)

    dff_fr_dpt = df_fr_dpt.copy()
    dff_fr_dpt = dff_fr_dpt[dff_fr_dpt['jour'] == option_slctd2]

    id_dpt_map = {}
    for feature in france_dpt['features'] :
        feature['id'] = feature['properties']['code']
        id_dpt_map[feature['properties']['nom']] = feature['id']

    # Plotly Express
    fig4 = px.choropleth(
        dff_fr_dpt,
        locations="dep",
        geojson=france_dpt,
        color="incid_dc",
        hover_name="Nom du département",
        title="Map representing the number of deaths at hospital",
        color_continuous_scale='YlOrRd',
        )
    fig4.update_geos(fitbounds="locations", visible=False)

    fig5 = px.choropleth(
        dff_fr_dpt,
        locations="dep",
        geojson=france_dpt,
        color="incid_hosp",
        hover_name="Nom du département",
        title="Map representing the number of hospitalisations",
        color_continuous_scale='YlOrRd',
        )
    fig5.update_geos(fitbounds="locations", visible=False)

    fig6 = px.choropleth(
        dff_fr_dpt,
        locations="dep",
        geojson=france_dpt,
        color="incid_rea",
        hover_name="Nom du département",
        title="Map representing the number of patients admitted in ICU (Intensive Care Unit)",
        color_continuous_scale='YlOrRd',
        )
    fig6.update_geos(fitbounds="locations", visible=False)

    fig7 = px.choropleth(
        dff_fr_dpt,
        locations="dep",
        geojson=france_dpt,
        color="incid_rad",
        hover_name="Nom du département",
        title="Map representing the number of patients return home after hospitalisation",
        color_continuous_scale='YlGn',
        )
    fig7.update_geos(fitbounds="locations", visible=False)


    return container4, fig4, fig5, fig6, fig7


if __name__ == '__main__':
    app.run_server(debug=True)


