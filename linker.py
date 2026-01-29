import os
import re
from csv import DictReader, DictWriter
from pydoc import ispath
from urllib.parse import urljoin

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QWaitCondition
from bs4 import BeautifulSoup
import requests
import logging
import csv


import progress
logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)

#from GUI import sidewindow


class linker(QObject):
    log=pyqtSignal(str)
    prog=pyqtSignal(int)
    finished=pyqtSignal()
    pause=pyqtSignal(int)
    #Takes the path where all the html is saved and domain of the url
    def __init__(self,path,domain,parent=None):
        """"""
        QObject.__init__(self,parent)
        self.trackers=re.compile(r"(googletag|quantserve|scorecard|beacon|metrics|silversurfer|search-insight)")
        self.ispaused=False
        self.latestpattern=re.compile(r"\?cb.*\&")
        self.session=requests.session()
        #"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0"
        #self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0"})
        self.session.auth=('user','pass')
        self.path=path[0:len(path)-1]+'/'
        self.domain=domain
        self.csslist=[]
        self.css_downloads=[]
        self.phplist=[]
        self.jssrc=[]
        self.jscounter=[]
        self.headers=['css','cssdownload','php']
        self.rows=[]
        self.js=[]
        self.linkedlist=[]
        self.named=lambda y: '-'.join(y.strip().split('/')[4::])
        self.ref=lambda y: '-'.join(y.strip().split('/')[2::])
        self.jsheaders=['jssrc','jscounter']
        self.mutex=QMutex()
        self.pausecon=QWaitCondition()
        with open(self.path+"url.csv",encoding='utf-8') as fp:
            reader=csv.DictReader(fp)
            for row in reader:
                self.linkedlist.append({'URL':row['URL'],'Linked':row['Linked']})

        try:
            with open(self.path+"css.csv","r",encoding='utf-8') as fp:
                reader=csv.DictReader(fp)
                for row in reader:
                    self.csslist.append(row['css'])
                    self.css_downloads.append(row['cssdownload'])
                    self.phplist.append(row['php'])
                    self.rows.append({'css':row['css'], 'cssdownload':row['cssdownload'], 'pfp':row['php']})

        except FileNotFoundError as e:
            with open(self.path+"css.csv","w",encoding='utf-8') as fp:
                reader=csv.DictWriter(fp,fieldnames=self.headers)
                reader.writeheader()

        try:
            with open(self.path+"js.csv","r",encoding='utf-8') as fp:
                reader=csv.DictReader(fp)
                for row in reader:
                    self.jssrc.append(row['jssrc'])
                    self.jscounter.append(row['jscounter'])

        except FileNotFoundError as e:
            with open(self.path+"js.csv","w",encoding='utf-8') as fp:
                reader=csv.DictWriter(fp,fieldnames=self.jsheaders)
                reader.writeheader()


    def paused(self,arg=None):
        self.mutex.lock()
        self.ispaused=True
        self.mutex.unlock()
        self.log.emit("Paused")

    def resumed(self,arg=None):
        self.mutex.lock()
        self.ispaused=False
        self.pausecon.wakeAll()
        self.mutex.unlock()

    def check_pause(self):
        self.mutex.lock()
        while self.ispaused:
            self.pausecon.wait(self.mutex)
        self.mutex.unlock()

    #Downloads and links css
    def css(self,soup):
        b = soup.find_all("link", {"rel":"stylesheet","href":True})
        for z in b:
            if ((z['href'] not in self.phplist) and (z['href'] not in self.csslist)) and z not in self.css_downloads:
                try:
                    css = requests.get("https://"+self.domain+z['href'])
                    css_count=len(self.css_downloads)
                    self.csslist.append(f"css_{css_count}.css")
                    self.phplist.append(z["href"])
                    self.css_downloads.append(z)

                    cssfile = open(self.path+"css.csv", "a", encoding="utf-8")
                    writer = DictWriter(cssfile, fieldnames=self.headers)
                    writer.writerow({'css':f"css_{css_count}.css",'php':z["href"],'cssdownload':z})

                    with open(f"{self.path}css_{css_count}.css", "w", encoding="utf-8") as cfp:
                        cfp.write(css.text)
                    cssfile.close()

                    z["href"] = f"css_{css_count}.css"
                except Exception as e:
                    logging.info(e)
                    #self.side.login(e)
            else:
                """The csslist is basically the list of downloaded cssfiles. This makes sure that the href is not in that list
                This is honestly redundant"""
                if z['href'] not in self.csslist:
                    z["href"]=self.csslist[self.phplist.index(z["href"])]
        #This is a leftover from the previous method used.
        """with open(f"{self.path}css.txt","w",encoding='utf-8') as f:
            f.writelines(list(map(lambda x,y:x+" : "+y+"\n",self.phplist,self.csslist)))"""
        return soup
    #Links images using the data-image-key
    def image(self,soup):
        a = [image for image in soup.find_all("img", {"data-image-key":True,"src":True}) if image['data-image-key']!=image['src']]
        if a:
            """
            This is unlikely to be needed since everything in the list has by default a src and a data-src is already being checked for.
            a1=[img for img in a if img.has_attr('src') and img['data-image-key']!=img['src']]
            a2=[img for img in a if img.has_attr('data-src') and img['data-image-key']!=img['data-src']]
            a=a1+a2"""
            for img in a:
                try:
                    if img.has_attr('data-src'):
                        img['data-src']=img["data-image-key"]
                        img["src"]=img["data-image-key"]
                        img["loading"]="eager"
                        img["class"]="mw-file-element"
                    elif img.has_attr('src'):
                        img["src"] = img["data-image-key"]
                except Exception as e:
                    logging.info(f"{e}")
                #self.side.login(e)
        return soup

    def fixlinks(self,html):
        a=html.find_all("a",{"href":re.compile(r"^\/wiki\/(?!((Special:)|Category:)).*$"),"title":True})
        for i in a:
            self.check_pause()
            i["href"]=self.cleaningstring(self.ref(i["href"]))+".html"
        a=html.find_all("video",{"src":True})+html.find_all("audio",{"src":True})
        for x in a:
            e=x.find("a",{"href":True})
            name=e["href"].strip().split(":")[-1]
            e["href"]=name
            x["src"]=name
        a = html.find_all("a", {"href": True, "class": re.compile("video")})
        for i in a:
            i["href"]=i["href"].strip().split(":")[-1]
        return html



    def php(self):
        link = urljoin(f"https://{self.domain}/",
                       "/load.php?cb=20201211140723&lang=en&modules=startup&only=scripts&raw=1&skin=fandomdesktop")
        res = self.session.get(link)
        with open(f"{self.path}js_0.js","w",encoding="utf-8") as fp:
            fp.write(res.text)




    #Removes js tracking scripts and  any suspicious iframes
    def remove_trackers(self,soup):
        c1=[script for script in soup.find_all("iframe",{"height":re.compile(r"^[01]$"),"width":re.compile(r"^[01]$")})]
        c2=soup.find_all("script",{"src":re.compile(r"^(?!(\/load.php\?)).+$")})
        c=c1+c2
        c=map(lambda x:x.decompose(),c)
        c=[i.decompose() for i in soup.find_all("script",{"src":False}) if bool(self.trackers.search(i.text))]
        script=soup.find("script",{"src":re.compile(r"^(\/load.php\?).*$")})
        self.check_pause()
        if script:
            script["src"]="js_0.js"
        return soup

    def cleaningstring(self,urlname):
        urlname = urlname.replace('/', '-')
        if "." in urlname:
            urlname = urlname.replace('.', '_')
        urlname = urlname.replace(':', '_')
        return urlname
    @pyqtSlot()
    def link(self):
        #Helps continue from where you left off
        lists=os.listdir(self.path)
        valid_list=[]
        for row in self.linkedlist:
            self.check_pause()
            if row['Linked']=="False":
                valid_list.append(row['URL'])
        self.i=1
        if valid_list:
            for x in valid_list:
                self.check_pause()
                name=self.cleaningstring(self.named(x))
                self.log.emit(f"Linking {name}")
                self.prog.emit(self.i)
                with open(self.path+name+'.html',"r",encoding="utf-8") as fp:
                    soup=BeautifulSoup(fp,"html.parser")
                    soup=self.image(soup)
                    soup=self.css(soup)
                    soup=self.fixlinks(soup)
                    soup=self.remove_trackers(soup)
                with open(self.path+name+'.html',"w",encoding="utf-8") as fp2:
                    fp2.write(soup.prettify())
                    urls=open(self.path+"url.csv","w",encoding='utf-8')
                    update=csv.DictWriter(urls,fieldnames=['URL','Linked'])
                    for row in self.linkedlist:
                        if row['URL']==x:
                            row['Linked']=True
                            break
                    update.writeheader()
                    update.writerows(self.linkedlist)
                self.i+=1
        self.session.close()
        self.finished.emit()
