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
        #deal_with_the_exception()
        #print("there's somthing wrong!\n")
        return 0

def clean_center_word(subject_):
    subject_replace = ''
    for i in subject_:
        if i.isalnum():
            subject_replace += i
        elif i == ' ':
            subject_replace += '_'
        else:
            subject_replace = subject_replace +'\\' +i
    return subject_replace

key = ['http://dbpedia.org/ontology/','http://dbpedia.org/resource/','http://dbpedia.org/property/']
value_type_skip = ['typed-literal'] #多为时间数字等；这两者都对于度计算时，没有意义;但实际上他们可以提供非常丰富的语料信息，【本质问题感觉是没有考虑边属性】

class get_by_degree:
    '''
    1. 去除不合格前缀网址及wiki
    2. 去除不合格类型
    3. 对于一个点，二者之间可能有多种关系，要将关系合并后再将边放入graph
    '''
    def __init__(self,center_word = None, escape = True,num = 10,res_format = 'json'):
        self.center_word = center_word #the recent center word
        self.escape = escape #whether to escape thr key
        self.query = "" # for sql
        self.top_k = num  #nums to show the entities
        self.format = res_format #reutrn format
        
    def _get_query(self,center_word,is_for_expand):
        if not is_for_expand: 
            self.query =[ 
                f'''
                prefix dbo:<http://dbpedia.org/ontology/> 
                prefix dbr:<http://dbpedia.org/resource/> 
                SELECT ?property ?value 
                Where {{ 
                dbr:{self.center_word} ?property  ?value 
                }}
                '''
                ,
                f'''
                prefix dbo:<http://dbpedia.org/ontology/> 
                prefix dbr:<http://dbpedia.org/resource/> 
                SELECT  ?value ?property
                Where {{ 
                 ?value ?property dbr:{self.center_word}
                }}
                '''
            ]
                
        else:
            center_word = clean_center_word(center_word)
            self.query = [f'''
        prefix dbo:<http://dbpedia.org/ontology/> 
        prefix dbr:<http://dbpedia.org/resource/> 
        SELECT COUNT(?label ) as ?num  
        Where{{ 
        dbr:{center_word} ?label ?value
        }}
        '''
           ,
            f'''
        prefix dbo:<http://dbpedia.org/ontology/> 
        prefix dbr:<http://dbpedia.org/resource/> 
        SELECT COUNT(?label ) as ?num  
        Where{{ 
        ?value ?label  dbr:{center_word}
        }}
        ''']
        
    def _clean_data(self,data):
        '''
        can use filter to speed up the process
        '''
        w = []
        for i in data["results"]["bindings"]:
            if i['property']['value'].startswith(key[0]) or i['property']['value'].startswith(key[1]) or i['property']['value'].startswith(key[2]):
                if i['value']['type'] in value_type_skip:
                    continue
                if i['value']['type'] == 'uri':
                    v = i['value']['value'].split('/')[-1]
                elif  i['value']['type'] == 'literal' and i['value']['xml:lang'] == "en" and i['value']['value']!= "": #注意有为空的情况
                    v = i['value']['value']
                else:
                    continue
                l = i['property']['value'].split('/')[-1]
                if l.startswith('wiki'): #escape wiki in dbo
                    continue
                if len(w)>0 and v in w: #yhe entity has been recorded
                    continue
                else:
                    if v == self.center_word:
                        print(i)
                        continue
                    w.append(v)

                
        return w
    
    def _get_the_relationship(self,subject_,object_):
        relationship = None
        subject_ = clean_center_word(subject_)
        object_ = clean_center_word(object_)
        

        query = f'''
                prefix dbo:<http://dbpedia.org/ontology/> 
                prefix dbr:<http://dbpedia.org/resource/> 
                SELECT ?property
                Where {{ 
                dbr:{subject_} ?property  dbr:{object_} 
                }}
                '''
        
        data = get_data(query,self.format)
        if data == 0: #they don't have realtionship from this direction
            return None
        for i in data["results"]["bindings"]:
            l = i['property']['value'].split('/')[-1]#查看过其返回类型都是uri
            if l.startswith('wiki'): #dbo中也有wiki
                continue
            if relationship == None:
                relationship = l
            else:
                relationship =relationship+ '/'+ l
        
        return relationship 
    
    def _get_data(self):
        print("=== run the get data process ===== ")
        self._get_query(self.center_word,False)
        data = get_data(self.query[0],self.format) # 作主语
        if data == 0:
            print(data)
            w = [] 
        else:
            print(len(data))
            print(f'[!] as the subject: num  = {len(data["results"]["bindings"])}')
        #print(len(data))
            if self.escape:
                w = self._clean_data(data)
            else:
                w = data["results"]["bindings"]
            print(f'[!] as the subject after cleanning: num  = {len(w)}')
        
        data = get_data(self.query[1],self.format) # 作宾语
        if data == 0:
            print(f'[!] as the object: num  = {data}')
            w_ = []
                
        else:
            print(f'[!] as the object: num  = {len(data["results"]["bindings"])}')
            if self.escape:
                w_ = self._clean_data(data)
            else:
                w_ = data["results"]["bingdings"]
            print(f'[!] as the object after cleanning: num  = {len(w_)}')
        
        w = w + w_
        w = list(set(w))
        
        # call _get_the_top10_by_degree()
        w = self._get_the_topk_by_degree(w,self.top_k)
    
        
        edges,nodes=self._get_nodes_edges(w)

        return edges,nodes
    
    def _get_the_topk_by_degree(self,words,top_k=10):
        
        w = []
        total_degree = 0
        for i in tqdm(range(len(words))):
            self._get_query(words[i],True)
            res = get_data(self.query[0],self.format)#as object, outdegree
            if res != 0:
                num =int(res["results"]["bindings"][0]["num"]["value"])
            else:
                num = 0
                
            res = get_data(self.query[1],self.format)#as subject,in_degree
            if res != 0:
                num +=int(res["results"]["bindings"][0]["num"]["value"])
            else:
                num += 0
            total_degree += num
            w.append({'value':words[i],'degree':num})
        
        
        
        
        print('degree\n',sorted(w,key=lambda k:k['degree'],reverse=True))
        print('total_degree\n',total_degree)

        w = sorted(w,key=lambda k:k['degree'],reverse=True)[:top_k]
        

        return w
    
    def _get_nodes_edges(self,words):
        
        edges = []
        nodes = []
        nodes.append((self.center_word,{'value':self.center_word.replace('_',' ')})) #避免显示的困扰
        for w in words:
            nodes.append((w['value'],{'value':w['value'].replace('_',' ')}))#避免显示的困扰
            
            relationship = self._get_the_relationship(subject_=self.center_word,object_=w['value'])
            if relationship != None:
                edges.append((self.center_word,w['value'],{'property':relationship}))#center-> entity
            else:    
                relationship_ =self._get_the_relationship(subject_=w['value'],object_=self.center_word) 
                if relationship_ != None:
                    edges.append((w['value'],self.center_word,{'property':relationship_}))#entity->center
                else:# relationship == None and relationship_ == None:
                    #print(f'[!] all none :{self.center_word} {w["value"]}')
                    continue
        
            
        return edges,nodes
    

    
    def _change_center_word(self,center_word):
        center_word = clean_center_word(center_word)
        self.center_word = center_word
        print(self.center_word)