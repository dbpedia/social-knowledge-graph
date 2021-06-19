from SPARQLWrapper import SPARQLWrapper
import networkx as nx

def get_data(query,res_format):
    sparql = SPARQLWrapper("https://dbpedia.org/sparql/")
    sparql.setQuery(query)
    sparql.setReturnFormat(res_format)
    try:
        ret = sparql.query().convert()
    except:
        print("there's somthing wrong!\n")
    

key = ['http://dbpedia.org/ontology/','http://dbpedia.org/resource/','http://dbpedia.org/property/']
value_type_skip = ['literal'] #这种情况下多为描述

class get_by_degree:
    def __init__(self,center_word = None, escape = True,num = 10,res_format = 'json'):
        self.center_word = center_word #最近的中心词
        self.escape = escape #是否判断key和跳过value_type_skip
        self.graph = nx.DiGraph() #存放图
        self.query = "" #得到查询语句
        self.top_k = num  #最终结果展示的个数
        self.format = res_format #查询语句返回的形式
        
    def _get_query(self,center_word,is_for_expand):
        if !is_for_expand: #is_for_expand == False
            self.query = f'''
                prefix dbo:<http://dbpedia.org/ontology/> 
                prefix dbr:<http://dbpedia.org/resource/> 
                SELECT ?property ?value 
                Where {{ 
                dbr:{self.center_word} ?property  ?value 
                }}
                '''
        else:
            self.query = f'''
        prefix dbo:<http://dbpedia.org/ontology/> 
        prefix dbr:<http://dbpedia.org/resource/> 
        SELECT COUNT(?label ) as ?num  
        Where{{ 
        dbr:{center_word} ?label ?value
        }}
        '''
        
    def _clen_data(self):
        #这里不用 fliter而用遍历是因为返回值都为uri，还是要遍历取出string方便画图
        #只保留以key开头的边
        #且去除节点为value_type_skip的值的节点
        #最终保留在w中
        '''
        形式：
        {
        'label':'deathPlace',
        'value': 'Cambridge'
        }
        '''
        w = []
        for i in data["results"]["bindings"]:
            if i['property']['value'].startswith(key[0]) or i['property']['value'].startswith(key[1]):
                if i['value']['type'] in value_type_skip:
                    continue
                if i['value']['type'] == 'uri':
                    v = i['value']['value'].split('/')[-1]
                else:
                    v = i['value']['value']
                l = i['property']['value'].split('/')[-1]#查看过其返回类型都是uri
                w.append({'property':l,'value':v})
            else:
                continue
        return w
    
    def _get_data(self):
        _get_query(self.center_word,False)
        data = get_data(self.query,self.format)
        if self.escape:
            w = _clen_data()
        else:
            w = data["results"]["bindings"] #？感觉这个else没有写对，就算不跳过，也应该从uri中获得strig
        # call _get_the_top10_by_degree()
        w = _get_the_topk_by_degree(words,self.top_k)
        #undo add the res to self.graph
    
    def _get_the_topk_by_degree(self,words，top_k=10):
        #?在度的计算中是否需要进行 clean_data
        # ？是否要讲原center排除，避免出现有向环状的情况，即死循环
        
        #不进行clean_data的版本
        for i in range(len(words)):#对每一个结果查询其周围的度
            _get_query(words[i]['value'],True)
            num =int(get_data(self.query,self.format)["results"]["bindings"]["num"]["value"])
            words[i]['degree'] = num
        
        #进行clean_data在查询中做 filter，不要再遍历循环 
        #undo
        
        
        words = sorted(words,key=lambda w:w['degree'],reverse=True)[:top_k]
        return words
    def _add_to_graph(self,words):
        #由于添加点和边的时候都要添加属性，因此要分别添加，不能通过添边来间接添点
        #networkx的好处，重复添加结点会忽略
        edges = []
        nodes = []
        nodes.append((self.center_word,{'value':self.center_word}))
        for w in words:
            nodes.append((w['value'],{'value'}:w['value']))
            edges.append((self.center_word,w['value'],{'property':w['property']}))
        self.graph.add_nodes_from(nodes)
        self.graph.add_edges_from(edges)
        
        
        
        
        
