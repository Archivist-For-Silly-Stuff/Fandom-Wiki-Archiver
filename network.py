import os
import random
from collections import Counter

import networkx as nx
from PyQt5.QtCore import QObject, pyqtSignal
from bs4 import BeautifulSoup
import re
import pyvis


class Graphx(QObject):
    dqsig=pyqtSignal(object)
    finished=pyqtSignal()
    log=pyqtSignal(str)
    prog=pyqtSignal(int)
    res=pyqtSignal(int)
    def __init__(self,path,parent=None):
        QObject.__init__(self,parent)
        self.catcount:dict|Counter =None
        self.G=pyvis.network.Network('1000px', "100%", bgcolor='#222222', font_color='white')
        self.G.barnes_hut()
        self.path=path
        self.names=[i for i in os.listdir(self.path) if ".html" in i]
        breakpoint()
        if "network_map.html" in self.names:
            self.names.remove("network_map.html")
        self.w=[]
        self.size={}
        self.label=[]
        self.edges=[]
        self.cats=[]
        self.categories:dict={}
        self.colors:dict[str,str]={}
        self.count=0


    def random_color_generator(self):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        return (r, g, b)

    def research(self,filename):
        with open(self.path.joinpath(filename),"r",encoding="utf-8") as fp:
            soup=BeautifulSoup(fp,"lxml")
            x = soup.find('table',{"class":re.compile(r"mw-collapsible")})
            if x:
                x.decompose()
            pages=soup.find_all("a",{"href":re.compile(r"^.*\.html$")})
            #self.w.append((len(pages))/(len(self.names)))
            cat=soup.find_all("a",{"href":re.compile(r"^\/wiki\/Category:.+$")})
            if cat:
                self.categories[filename]=[link["href"].split(":")[-1] for link in cat]
                #self.cats.append(cat["href"].split(":")[-1])
            else:
                self.categories[filename]=["Uncategorized"]

            self.size[filename]=len(pages)+1
            self.label.append(filename)
            self.edges=self.edges+[(filename,x) for x in [i["href"] for i in pages] if x in self.names]

    def catcheck(self,file):
        minval=0
        category=""
        for cat in self.categories[file]:
            if self.catcount[cat]>minval:
                minval=self.catcount[cat]
                category=cat
        return (category,minval)

    def add_edges(self):
        tot=len(self.names)
        self.prog.emit(self.count)
        for i in self.names:
            self.research(i)
            self.log.emit(f"Researched {i}")
            self.count+=1
            self.prog.emit(self.count)
            #self.G[i]['title']=i
        catlist=[]
        for (file,item) in self.categories.items():
            for cat in item:
                catlist.append(cat)
        self.catcount=Counter(catlist)
        self.colors={i:'#%02x%02x%02x' % self.random_color_generator() for i in (self.catcount.keys())}
        print(self.catcount)
        self.catcount=dict(self.catcount)
        print(self.catcount)
        normcat={}
        self.res.emit(len(self.categories))
        self.log.emit("Adding nodes")
        breakpoint()
        for file in self.categories:
            cat,val=self.catcheck(file)
            normcat[file]=cat
            #val=val/self.size[file]
            self.G.add_node(file,label=file,value=self.size[file],color=self.colors[cat])
            self.log.emit(f"Added {file} as node")
            self.count+=1
            self.prog.emit(self.count)
        """for file in self.categories:
            cat,val=self.catcheck(file)
            val=val/self.size[file]
            self.G.add_node(file,label=file,value=self.size[file],color=self.colors[cat])"""
        edgew={}
        self.res.emit(len(self.edges))
        self.log.emit("Connecting edges")
        breakpoint()
        for edge in self.edges:
            n0=edge[0]
            n1=edge[1]
            w=int((self.size[n0]+self.size[n1])/tot)
            self.G.add_edge(n0,n1,weight=w)
            self.count+=1
            self.prog.emit(self.count)
        #self.cats=['#%02x%02x%02x' % self.colors[i] for i in self.cats]
        #self.G.add_nodes(self.names,label=self.label,value=self.size,color=self.cats)
        #self.G.add_edges(self.edges)

        self.finished.emit()
        self.dqsig.emit(self.G)



