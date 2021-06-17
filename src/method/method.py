from SPARQLWrapper import SPARQLWrapper

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
        self.graph = {} #以三元式的形式存放图 头 边 尾
        self.query = "" #得到查询语句
        self.num = num  #最终结果展示的个数
        self.format = res_format #查询语句返回的形式
        
    def _get_query(self):
        self.query = f '''
        prefix dbo:<http://dbpedia.org/ontology/> 
        prefix dbr:<http://dbpedia.org/resource/> 
        SELECT ?property ?value 
        Where { 
        dbr:{self.center_word} ?property  ?value 
        }
        '''
    def _clen_data(self):
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
        _get_query()
        data = get_data(self.query,self.format)
        if self.escape:
            w = _clen_data()
        else:
            w = data["results"]["bindings"]
        #undo call _get_the_top10_by_degree()
        #undo add the res to self.graph
    
    def _get_the_top10_by_degree():
        pass
        
        
        
        
