from degree import get_by_degree
import plotly.graph_objs as go
import networkx as nx

class data_for_vis:
    def __init__(self,method,center_word = 'James_Clerk_Maxwell'):
        self.following_node_di ={}
        self.following_edges_di = {}
        self.followers_node_di = {}
        self.followers_edges_di ={}
        if method == 'degree':
            self.method = get_by_degree(center_word=center_word) #默认为Maxwell，当改变时，重新默认
        self.nodes = set()
        self.cy_edges = []
        self.cy_nodes = []
  
    def change_the_center_word(self,center_word):
        self.method = get_by_degree() #提交submit，则原图清空
        self.method._change_center_word(center_word)
        self.center_word = center_word
  
    def get_the_begein_center(self):
        cy_source = {"data": {"id": self.center_word, "label": self.center_word}}
        cy_source['classes'] = "genesis"
        return [cy_source] # default_elements
    
  
    def get_follower(self):
        data = self.method._get_data()
    
    # # 此处假设了所有节点都是由中心点向外扩展
        source = self.center_word
        followers_nodes = []
        followers_edges = []
        for each in data:
            target = each['value']
            cy_edge = {'data': {'id': source+target, 'source': source, 'target': target}}
            cy_target = {"data": {"id": target, "label": target}}
            # cy_source = {"data": {"id": source, "label": source}}

            followers_nodes.append(cy_target)
            followers_edges.append(cy_edge)
        return followers_nodes,followers_edges




    def click_nodes(self,word): #一次点击之后，不清空，只是改变中心之后，重新画图
        self.method._change_center_word(word)
        return self.get_graph()

        
    def get_graph(self,old_edges=[],old_nodes =[]):
        edges,nodes = self.method._get_data()
        # 融合后为图上要展示的边和点
        edges += old_edges
        nodes += old_nodes
        # 生成图
        G = nx.DiGraph()
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)
        # 添加位置属性
        pos = nx.layout.circular_layout(G)
        for node in G.nodes:
            G.nodes[node]['pos'] = list(pos[node]) 

        traceRecode = []  # contains edge_trace, node_trace, middle_node_trace
        ###
        for edge in G.edges:
            x0, y0 = G.nodes[edge[0]]['pos']
            x1, y1 = G.nodes[edge[1]]['pos']
            trace = go.Scatter(x=tuple([x0, x1, None]), y=tuple([y0, y1, None]),
                                mode='lines',
                                line=dict(width=1),
                                line_shape='spline',
                                opacity=1
                                )
            traceRecode.append(trace)
        ###
        node_trace = go.Scatter(x=[], y=[], hovertext=[], text=[], mode='markers+text', textposition="bottom center",
                                hoverinfo="text", marker={'size': 50, 'color': 'LightSkyBlue'})
        for node in G.nodes():
            x, y = G.nodes[node]['pos']
            print('value',str(G.nodes[node]['value']),'x',x,'y',y)
            hovertext = "Name: " + str(G.nodes[node]['value']) + "<br>" 
            text = str(G.nodes[node]['value'])
            node_trace['x'] += tuple([x])
            node_trace['y'] += tuple([y])
            node_trace['hovertext'] += tuple([hovertext])
            node_trace['text'] += tuple([text])
        traceRecode.append(node_trace)
        ####
        middle_hover_trace = go.Scatter(x=[], y=[], hovertext=[], mode='markers', hoverinfo="text",
                                        marker={'size': 20, 'color': 'LightSkyBlue'},
                                        opacity=0)


        for edge in G.edges:
            x0, y0 = G.nodes[edge[0]]['pos']
            x1, y1 = G.nodes[edge[1]]['pos']
            # hovertext = "From: " + str(G.nodes[edge[0]]['value']) + "<br>" + "To: " + str(
            #     G.nodes[edge[1]]['value']) + "<br>" + "property: " + str(G.edges[edge]['property'])
            hovertext = "property: " + str(G.edges[edge]['property'])
            middle_hover_trace['x'] += tuple([(x0 + x1) / 2])
            middle_hover_trace['y'] += tuple([(y0 + y1) / 2])
            middle_hover_trace['hovertext'] += tuple([hovertext])

        traceRecode.append(middle_hover_trace)
        ###
        figure = {
        "data": traceRecode,
        "layout": go.Layout(title='Visualization for the ego graphs', showlegend=False, hovermode='closest',
                            margin={'b': 40, 'l': 40, 'r': 40, 't': 40},
                            xaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                            yaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                            height=600,
                            clickmode='event+select',
                            annotations=[
                                dict(
                                    ax=(G.nodes[edge[0]]['pos'][0] + G.nodes[edge[1]]['pos'][0]) / 2,
                                    ay=(G.nodes[edge[0]]['pos'][1] + G.nodes[edge[1]]['pos'][1]) / 2, 
                                    axref='x', ayref='y',
                                    x=(G.nodes[edge[1]]['pos'][0] * 3 + G.nodes[edge[0]]['pos'][0]) / 4,
                                    y=(G.nodes[edge[1]]['pos'][1] * 3 + G.nodes[edge[0]]['pos'][1]) / 4, 
                                    xref='x', yref='y',
                                    showarrow=True,
                                    arrowhead=3,
                                    arrowsize=4,
                                    arrowwidth=1,
                                    opacity=1
                                ) for edge in G.edges]
                            )}
        return figure,edges,nodes



