import networkx as nx
import matplotlib.pyplot as plt

def draw_the_ego_graph(graph:nx.DiGraph()):
    node_labels = nx.get_node_attributes(graph,'value')
    edge_labels = nx.get_edge_attributes(graph, 'property')
    pos = nx.spring_layout(G) #得到position，免得边名和点名没有写在对应位置
    nx.draw(graph, pos) #画点和边
    nx.draw_networkx_labels(G, pos, labels=node_labels)#写上点名
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)#写上边名
    plt.show()
    