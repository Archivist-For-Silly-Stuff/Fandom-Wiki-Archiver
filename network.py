import os
import random
import networkx as nx
from PyQt5.QtCore import QObject, pyqtSignal
from bs4 import BeautifulSoup
import re
import pyvis


class Graphx(QObject):
    dqsig=pyqtSignal(object)
    finished=pyqtSignal()

    def __init__(self,path,parent=None):
        QObject.__init__(self,parent)
        self.G=pyvis.network.Network('1000px', "100%", bgcolor='#222222', font_color='white')
        self.G.barnes_hut()
        self.path=path
        self.names=[i for i in os.listdir(self.path) if ".html" in i]
        if "network_map.html" in self.names:
            self.names.remove("network_map.html")
        self.w=[]
        self.size=[]
        self.label=[]
        self.edges=[]
        self.cats=[]


    def random_color_generator(self):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        return (r, g, b)

    def research(self,filename):
        with open(self.path+filename,"r",encoding="utf-8") as fp:
            soup=BeautifulSoup(fp,"lxml")
            x = soup.find('table',{"class":re.compile(r"mw-collapsible")})
            if x:
                x.decompose()
            pages=soup.find_all("a",{"href":re.compile(r"^.*\.html$")})
            #self.w.append((len(pages))/(len(self.names)))
            cat=soup.find("a",{"href":re.compile(r"^\/wiki\/Category:.+$")})
            if cat:
                self.cats.append(cat["href"].split(":")[-1])
            else:
                self.cats.append("Uncategorized")

            self.size.append(len(pages)+1)
            self.label.append(filename)
            self.edges=self.edges+[(filename,x) for x in [i["href"] for i in pages] if x in self.names]


    def add_edges(self):
        for i in self.names:
            self.research(i)
            #self.G[i]['title']=i
        self.colors={i:self.random_color_generator() for i in (list(set(self.cats)))}
        print(self.cats)
        self.cats=['#%02x%02x%02x' % self.colors[i] for i in self.cats]
        self.G.add_nodes(self.names,label=self.label,value=self.size,color=self.cats)
        self.G.add_edges(self.edges)

        self.dqsig.emit(self.G)
        self.finished.emit()



