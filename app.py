

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from method import data_for_vis







app = dash.Dash(__name__,
                external_stylesheets=['https://cdn.jsdelivr.net/npm/bootstrap@5.1.0/dist/css/bootstrap.min.css'])
server = app.server


app.layout = html.Div([
    #for store the edges and nodes
    dcc.Store(
        id = 'nodes'
    ),
    dcc.Store(
        id = 'edges'
    ),
    html.Div([
        html.Div([
            html.Div([
            html.Div([
                    dcc.Input(
                        id = 'center_word',
                        placeholder='Enter a center word you want to explore...',
                        type='text',
                        value='',
                        style={'width': '100%', 'align-content': 'center', 'padding': 10,
                                                        'border-radius': '5px', 'border': '1px solid #C0C0C0','height': '100%',}
                    )],
                   # className= 'col-lg-8',
                    style={'margin': 20}
                    )
    ,
            html.Div([
                    html.Button('Submit', id='submit_center_word', n_clicks=0,className='btn',style={'width': '100%', 'height': '100%', 'background-color': '#37474F',
                                           'color': '#FFFFFF'})],
                   # className= 'col-sm-4'
                    )
                    ],className='form-inline')
        ], className='card-body')
        
     ],
    className='card',
    style={'background-color': '#E0E0E0', 'margin': 20, 'border-radius': '10px',
    'box-shadow': '0 4px 8px 0 rgba(0, 0, 0, 0.20), 0 6px 20px 0 rgba(0, 0, 0, 0.20)'})
    ,
    html.Div([
    html.Div( children=[
        dcc.Loading(children=[
          html.Div(id = 'ego_graph') #call back to return the figure
        ]
        ,color="#119DFF", type="dot", fullscreen=False)
    ], className='card-body p-0'),

    ],className='card p-3', style={'margin': 30, 'background-color': '#263238', 'border-radius': '5px',
                                        'box-shadow': '0 4px 8px 0 rgba(0, 0, 0, 0.20),'
                                                      '0 6px 20px 0 rgba(0, 0, 0, 0.20)'})
])
 
 # ############################## CALLBACKS ####################################



@app.callback(
    [Output('ego_graph','children'),Output('edges','data'),Output('nodes','data')],
    Input('submit_center_word','n_clicks'),
    State('center_word','value')
)
def change_center_word(n_clicks,value):
    if n_clicks > 0:
        data_collection =data_for_vis(method = 'degree')
        data_collection.change_the_center_word(value)
        figure,edges,nodes = data_collection.get_graph()
        print(edges)
        
        return dcc.Graph(id = 'graph',figure = figure),edges,nodes

# for expand
@app.callback(
    [Output('graph','figure'),Output('edges','data'),Output('nodes','data')],
    Input('graph','clickData'),
    [State('edges','data'),State('nodes','data')]
)
def update_the_ego_graph(data,old_edges,old_nodes):
    
    center_word = data['points'][0]["text"]
    data_collection =data_for_vis(method = 'degree')
    data_collection.change_the_center_word(center_word)
    figure,edges,nodes = data_collection.get_graph(old_edges,old_nodes)
    return figure,edges,nodes
'''
  when click an entity
  {
    "points": [
        {
            "curveNumber": 10, 
            "pointNumber": 0, 
            "pointIndex": 0, 
            "x": 1, 
            "y": 2.7093020205643936e-9, 
            "text": "James Clerk Maxwell", 
            "hovertext": "Name: James Clerk Maxwell<br>"
        }
    ]
}
  '''


  
app.title = 'DBpedia Visualization'
app.run_server()