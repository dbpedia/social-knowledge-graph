from SPARQLWrapper import SPARQLWrapper
import networkx as nx

from tqdm import tqdm

def get_data(query,res_format):
    sparql = SPARQLWrapper("https://dbpedia.org/sparql/")
    sparql.setQuery(query)
    sparql.setReturnFormat(res_format)
    try:
        ret = sparql.query().convert()
        return ret
    except:
        #print("there's somthing wrong!\n")
        return 0
    

key = ['http://dbpedia.org/ontology/','http://dbpedia.org/resource/','http://dbpedia.org/property/']
value_type_skip = ['typed-literal'] #多为时间数字等；这两者都对于度计算时，没有意义;但实际上他们可以提供非常丰富的语料信息，【本质问题感觉是没有考虑边属性】

class get_by_degree:
    '''
    1. 去除不合格前缀网址及wiki
    2. 去除不合格类型
    3. 对于一个点，二者之间可能有多种关系，要将关系合并后再将边放入graph
    '''
    def __init__(self,center_word = None, escape = True,num = 10,res_format = 'json'):
        self.center_word = center_word #最近的中心词
        self.escape = escape #是否判断key和跳过value_type_skip
        self.graph = nx.DiGraph() #存放图
        self.query = "" #得到查询语句
        self.top_k = num  #最终结果展示的个数
        self.format = res_format #查询语句返回的形式
        
    def _get_query(self,center_word,is_for_expand):
        if not is_for_expand: #is_for_expand == False
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
        
    def _clen_data(self,data):
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
        flag = True
        for i in data["results"]["bindings"]:
            flag =False
            if i['property']['value'].startswith(key[0]) or i['property']['value'].startswith(key[1]) or i['property']['value'].startswith(key[2]):
                if i['value']['type'] in value_type_skip:
                    continue
                if i['value']['type'] == 'uri':
                    v = i['value']['value'].split('/')[-1]
                elif if i['value']['type'] == 'literal' and i['value']['xml:lang'] == en and i['value']['value']!= "": #注意有为空的情况
                    v = i['value']['value']
                else:
                    continue
                l = i['property']['value'].split('/')[-1]#查看过其返回类型都是uri
                if l.startswith('wiki'): #dbo中也有wiki
                    continue
                    
                for j in w:
                    if j == {'property':l,'value':v}: #dbo/dbr/dbp中也有可能重复的东西
                        flag = True
                        break
                if flag:
                    continue
                w.append({'property':l,'value':v})
            else:
                continue
        return w
    
    def _get_data(self):
        self._get_query(self.center_word,False)
        data = get_data(self.query,self.format)
        print(len(data))
        if self.escape:
            w = self._clen_data(data)
        else:
            w = data["results"]["bindings"] #？感觉这个else没有写对，就算不跳过，也应该从uri中获得strig
            
        # call _get_the_top10_by_degree()
        w = self._get_the_topk_by_degree(w,self.top_k)
        print("the top 10:")
        print(w) #show the top-10 degree words
        
        #call add the res to self.graph
        self._add_to_graph(w)
    
    def _get_the_topk_by_degree(self,words,top_k=10):
        #?在度的计算中是否需要进行 clean_data
        # ？是否要讲原center排除，避免出现有向环状的情况，即死循环
        
        #不进行clean_data的版本
        for i in tqdm(range(len(words))):#对每一个结果查询其周围的度
            self._get_query(words[i]['value'],True)
            res = get_data(self.query,self.format)
            if res != 0:
                num =int(res["results"]["bindings"][0]["num"]["value"])
            else:
                num = 0
            words[i]['degree'] = num
        
        #进行clean_data在查询中做 filter，不要再遍历循环 
        #undo
        
        print('len = ' +str(len(words)))
        words = sorted(words,key=lambda w:w['degree'],reverse=True)
        
        res =  []
        total = 0
        flag = True
        for w in words: 
            flag = True
            if total == top_k: #一共就只加 10 个
                break
            total += 1
            if len(words) == 0:
                res.append({'property':w['property'],'value':w['value'],'degree':w['degree']})
            else:
                for r in res:
                    if r['value'] == w['value']: #避免一个结点对应多种关系
                        r['property'] = r['property'] +' / ' + w['property']
                        flag = False
                        total -= 1 #这种情况不算是增加结点
                        break
            if flag:
                res.append({'property':w['property'],'value':w['value'],'degree':w['degree']})
                    
        print('top_k = ' +str(top_k))
        print(' len = ' +str(len(res)))
        return res
    def _add_to_graph(self,words):
        #由于添加点和边的时候都要添加属性，因此要分别添加，不能通过添边来间接添点
        #networkx的好处，重复添加结点会忽略
        edges = []
        nodes = []
        nodes.append((self.center_word,{'value':self.center_word}))
        for w in words:
            nodes.append((w['value'],{'value':w['value']}))
            edges.append((self.center_word,w['value'],{'property':w['property']}))
        self.graph.add_nodes_from(nodes)
        self.graph.add_edges_from(edges)
    
    def _get_graph(self):
        return self.graph
        
        
        
        
        
