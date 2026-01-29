import os

import networkx as nx
import requests
from PyQt5.QtCore import QObject, pyqtSignal
from bs4 import BeautifulSoup
import re
import csv
import matplotlib.pyplot as plt
class Graphx(QObject):
    dqsig=pyqtSignal(object)
    finished=pyqtSignal()

    def __init__(self,v,path,parent=None):
        QObject.__init__(self,parent)
        self.G=nx.DiGraph()
        self.v=v #will be removed later
        self.path=path
        self.names=[i for i in os.listdir(self.path) if ".html" in i]
        self.G.add_nodes_from(self.names)


    def add_edges(self):
        for i in self.names:
            #self.G[i]['title']=i
            with open("{}{}".format(self.path,i),"r",encoding="utf-8") as res:
                soup=BeautifulSoup(res.read(),"html.parser")
                a=soup.find_all("a",{"title":True,"href":re.compile(r"^.*\.html$")})
                y=[x["href"] for x in a]
                self.G.add_edges_from([(i,x) for x in y])
        self.dqsig.emit(self.G)
        self.finished.emit()



