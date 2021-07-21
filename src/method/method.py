from SPARQLWrapper import SPARQLWrapper
import networkx as nx
import spacy
import numpy as np
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
        print("there's somthing wrong!\n")
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
        
    def _clean_data(self,data,as_subject=True):
        #这里不用 fliter而用遍历是因为返回值都为uri，还是要遍历取出string方便画图
        #只保留以key开头的边
        #且去除节点为value_type_skip的值的节点
        #最终保留在w中
        '''
        形式：
        [,,,]
        只保存节点，边的属性可以在查出top_10后再添加
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
                l = i['property']['value'].split('/')[-1]#查看过其返回类型都是uri
                if l.startswith('wiki'): #dbo中也有wiki
                    continue
                if len(w)>0 and v in w: #若此时节点已经记录了
                    continue
                else:
                    if v == self.center_word:
                        print(i)
                        continue
                    w.append(v)

                
        return w
    
    def _get_the_relationship(self,subject_,object_):
        'here relationship is string'
        relationship = None
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
                w = data["results"]["bindings"] #？感觉这个else没有写对，就算不跳过，也应该从uri中获得strig
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
                w_ = data["results"]["bingdings"]#？感觉这个else没有写对，就算不跳过，也应该从uri中获得strig
            print(f'[!] as the object after cleanning: num  = {len(w_)}')
        
        w = w + w_
        w = list(set(w)) #去重
        
        # call _get_the_top10_by_degree()
        w = self._get_the_topk_by_degree(w,self.top_k)
        print("the top 10:")
        print(w) #show the top-10 degree words
        
        #call add the res to self.graph
        self._add_to_graph(w)
        return w
    
    def _get_the_topk_by_degree(self,words,top_k=10):
        #?在度的计算中是否需要进行 clean_data
        # ？是否要讲原center排除，避免出现有向环状的情况，即死循环
        
        #不进行clean_data的版本
        w = []
        for i in tqdm(range(len(words))):#对每一个结果查询其周围的度,出度（作主语）和入度（作宾语）
            self._get_query(words[i],True)
            res = get_data(self.query[0],self.format)#作主语
            if res != 0:
                num =int(res["results"]["bindings"][0]["num"]["value"])
            else:
                num = 0
                
            res = get_data(self.query[1],self.format)#作宾语
            if res != 0:
                num +=int(res["results"]["bindings"][0]["num"]["value"])
            else:
                num += 0
            w.append({'value':words[i],'degree':num})
        
        
        #进行clean_data在查询中做 filter，不要再遍历循环 
        #undo
        

        w = sorted(w,key=lambda k:k['degree'],reverse=True)[:top_k]
        
        
#         for r in rdf:
#             relationship = _get_the_relationship(subject_=self.center_word,object_=r)
#             res.append("subject":self.center_word,"property":relationship,"object":r)
#             relationship = _get_the_relationship(subject_=r,object_=self.center_word) #采用手工交换
#             res.append("subject":r,"property":relationship,"object":self.center_word)
        
        return w
    
    def _add_to_graph(self,words):
        #由于添加点和边的时候都要添加属性，因此要分别添加，不能通过添边来间接添点
        #networkx的好处，重复添加结点会忽略
        edges = []
        nodes = []
        nodes.append((self.center_word,{'value':self.center_word}))
        for w in words:
            nodes.append((w['value'],{'value':w['value']}))
            
            relationship = self._get_the_relationship(subject_=self.center_word,object_=w['value'])
            if relationship != None:
                edges.append((self.center_word,w['value'],{'property':relationship}))#center-> entity
            else:    
                relationship_ =self._get_the_relationship(subject_=w['value'],object_=self.center_word) 
                if relationship_ != None:
                    edges.append((w['value'],self.center_word,{'property':relationship_}))#entity->center
                else:# relationship == None and relationship_ == None:
                    print(f'[!] all none :{self.center_word} {w["value"]}')
                    continue
            print(edges[-1])
            
        self.graph.add_nodes_from(nodes)
        self.graph.add_edges_from(edges)
    
    def _get_graph(self):
        self._get_data()
        return self.graph
        
        
        
        
        
class consider_relationship_and_entity:
    '''
    同时考虑关系和节点
    '''
    def __init__(self,center_word = None,escape = True,num=10,res_format = 'json',weight_degree  =0.5,weight_relationship = 0.5):
        self.center_word = center_word
        self.escape = escape #是否判断key和跳过value_type_skip
        self.query = "" #得到查询语句
        self.top_k = num  #最终结果展示的个数
        self.format = res_format #查询语句返回的形式
        self.nlp = spacy.load("en_core_web_md")
    
    def _new_centerword(self,center_word):
        self.center_word  =center_word
    
    def _get_centerword(self,center_word):
        return self.center_word
    
    def _get_query(self,center_word,is_for_expand):
        if not is_for_expand: #is_for_expand == False
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
    
    def _clean_data(self,data,as_subject=True):
        #这里不用 fliter而用遍历是因为返回值都为uri，还是要遍历取出string方便画图
        #只保留以key开头的边
        #且去除节点为value_type_skip的值的节点
        #最终保留在w中
        '''
        形式：
        [,,,]
        只保存节点，边的属性可以在查出top_10后再添加
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
                l = i['property']['value'].split('/')[-1]#查看过其返回类型都是uri
                if l.startswith('wiki'): #dbo中也有wiki
                    continue
                if len(w)>0 and v in w: #若此时节点已经记录了
                    continue
                else:
                    if v == self.center_word:
                        print(i)
                        continue
                    w.append(v)

                
        return w
    
    def _get_the_relationship(self,subject_,object_):
        'here return relationship as turple'
        relationships = []
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
            else:
                relationships.append(l)
        
        return relationships
    
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
                w = data["results"]["bindings"] #？感觉这个else没有写对，就算不跳过，也应该从uri中获得strig
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
                w_ = data["results"]["bingdings"]#？感觉这个else没有写对，就算不跳过，也应该从uri中获得strig
            print(f'[!] as the object after cleanning: num  = {len(w_)}')
        
        w = w + w_
        w = list(set(w)) #去重
        
        # call _get_the_top10_by_degree()
        w = self._get_the_topk_by_RD(w,self.top_k)
        print("the top 10:")
        print(w) #show the top-10 degree words
        
        
        return w 
    
    def _get_the_norm_degree(self,words):
        w = []
        total_num = 0 #用于做度的归一化
        for i in tqdm(range(len(words))):#对每一个结果查询其周围的度,出度（作主语）和入度（作宾语）
            self._get_query(words[i],True)
            res = get_data(self.query[0],self.format)#作主语
            if res != 0:
                num =int(res["results"]["bindings"][0]["num"]["value"])
            else:
                num = 0
                
            res = get_data(self.query[1],self.format)#作宾语
            if res != 0:
                num +=int(res["results"]["bindings"][0]["num"]["value"])
            else:
                num += 0
            total_num += num
            w.append({'value':words[i],'degree':num})
        
        
        #进行clean_data在查询中做 filter，不要再遍历循环 
        #undo
        
        #得到按度进行排列的
        w = sorted(w,key=lambda k:k['degree'],reverse=True)
        #把度进行归一化
        w = [{'value':i['value'],'norm_degree':i['degree']/total_num} for i in w]
        return w
    
    def _get_the_norm_relationship(self,w):
        #获得关系
        nodes = []
        relationship_matrix = []
        for i in w:
            node = i['value']
            relationship =self._get_the_relationship(subject_=self.center_word,object_=node)
            i['direction'] = 'out'
            if relationship == None:
                relationship = self._get_the_relationship(subject_=node,object_=self.center_word)
                i['direction'] = 'in'
            
            if relationship == None:
                print('relationship == None',"  ",i)
                continue
            i['num_relationship'] = len(relationship)
            nodes.append(i)
            relationship_matrix += relationship
        
        relationship_vector = [self.nlp(r).vector for r in relationship_matrix] #不确定是不是这样堆叠起来
        trans_relationship_vector = np.transpose(relationship_vector)
        similarity = np.dot(relationship_vector,trans_relationship_vector) 
        norm = np.linalg.norm(similarity) #此时按行求norm
        similarity_norm = similarity / norm #得到【0~1】的相似度
        
        return similarity_norm,nodes
        
        
        
        
        
    
    def _get_the_topk_by_RD(self,words,top_k = 10):
        
        w = self._get_the_norm_degree(words) 
        norm_similarity,w = self._get_the_norm_relationship(w)
        #??注意当同一个entity有多个relationship时如何处理,【目前方法是直接相加】
        '''
        w =[
        {
        'direction':
        'value':
        'num_relationship':
        'norm_degree':
        }
        .....
        ]
        
        '''
        num_total =  np.size(norm_similarity,axis=1) #得到列数，即一行有多少
        sum_norm_similarity = np.sun(norm_similarity,axis = 1) #按行求和
        for i in w:
            sim_score = 0
            for _ in range(i['num_realtionship']):
                sim_score = sim_score + (num_total-sum_norm_similarity[0])/num_total
                sum_norm_similarity = sum_norm_similarity[1:]
            i['sim_score'] = sim_score
            i['score'] = self.weight_degree*i['norm_degree'] + self.weight_relationship *i['sim_score']
        
        w = sorted(w,key=lambda k:k['score'],reverse = True)[:10]
        return w
        
                
        
        
        
        
        
        
        
        
        
            
            
        
        
        
        
    