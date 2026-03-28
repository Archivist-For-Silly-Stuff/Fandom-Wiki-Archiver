import asyncio
import json
import os
import pathlib
import re
import pickle
from csv import DictWriter
from urllib.parse import urljoin
import cloudscraper
import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QWaitCondition
from bs4 import BeautifulSoup
import requests
import logging
import csv
import aiofiles
from curl_cffi.requests import AsyncSession


import progress
import aiocsv
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
    def __init__(self,path,domain,links:list,parent=None):
        """"""
        QObject.__init__(self,parent)
        self.trackers=re.compile(r"(googletag|quantserve|scorecard|beacon|metrics|silversurfer|search-insight)")
        self.ispaused=False
        self.latestpattern=re.compile(r"\?cb.*\&")

        #"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0"
        #self.path=path[0:len(path)-1]+'/'
        self.path=pathlib.Path(path)
        print(self.path)
        breakpoint()
        self.domain:str=domain
        self.csslist:list=[]
        self.css_downloads:list=[]
        self.phplist:list=[]
        self.headers=['css','cssdownload','php']
        #self.rows=[]
        #self.linkedlist : pd.DataFrame =links
        #self.named=lambda y: '-'.join(y.strip().split('/')[4::])
        #self.ref=lambda y: '-'.join(y.strip().split('/')[2::])
        self.i = 1
        self.asymutex=asyncio.Event()
        self.csslock=asyncio.Lock()
        """wikirestrict=f"{self.domain.split(".")[0]}"
        head,tail=wikirestrict.split("-")
        head=head.capitalize()
        tail=tail.upper()
        wikirestrict=head+"_"+tail+"_Wiki
        restrict=["User","User_Blog","Category","Special","Category"]
        restrict=map(lambda x:f"({x})",restrict)
        restrict="|".join(restrict)+":"
        print(rf"^\/wiki\/(!?(({restrict}))|(.*\?\=.*)).*$")"""
        #breakpoint()
        self.paturl=re.compile(rf"^\/wiki\/(?!(.*\:.*)|" #special/file
                                        "((.*\?.*\=.*)|" #Query
                                        "(.*\%3.*\%3.*))|" 
                                        "(.*((\#)|(\%27)).*)).*$",re.IGNORECASE)

        self.hashsub=re.compile(rf"^(https\:\/\/{self.domain}\/wiki\/.*)\#.*$")
        self.images:dict[str,list]={}





    def setupfiles(self):
        try:
            with open(self.path.joinpath("css.csv"),"r",encoding='utf-8') as fp:
                reader=csv.DictReader(fp)
                for row in reader:
                    self.csslist.append(row['css'])
                    self.css_downloads.append(row['cssdownload'])
                    self.phplist.append(row['php'])
                    #self.rows.append({'css':row['css'], 'cssdownload':row['cssdownload'], 'pfp':row['php']})
            if os.path.isfile(self.path.joinpath("images.pkl")):
                fp = open(self.path.joinpath("images.pkl"), "rb")
                self.images = pickle.load(fp)
                fp.close()
        except FileNotFoundError as e:
            with open(self.path.joinpath("css.csv"),"w",encoding='utf-8') as fp:
                reader=csv.DictWriter(fp,fieldnames=self.headers)
                reader.writeheader()



    def paused(self,arg=None):
        self.asymutex.set()
        self.log.emit("Paused")

    def resumed(self,arg=None):
        self.asymutex.clear()
        self.log.emit("Resumed")

    async def main(self):
        # print("x")
        self.setupfiles()
        self.valid_list = [link
                           for (link, val) in self.linkedlist.items()
                           if not (val["linked"])]
        """for row in self.linkedlist:
                if row['Linked'] == "False":
                valid_list.append(row['URL'])"""
        self.i = 1
        self.prog.emit(self.i)
        sem = asyncio.BoundedSemaphore(3)

        async def sem_download(url, session):
            async with sem:
                await self.link(url, session)

        try:
            async with AsyncSession(impersonate="chrome", max_clients=3) as ses:
                await self.php(ses)
                if self.valid_list:
                    tasks = [asyncio.create_task(sem_download(x, ses)) for x in self.valid_list]
                    await asyncio.gather(*tasks, return_exceptions=True)
            self.finished.emit()
        except Exception as e:
            self.log.emit(str(e))
        finally:
            print("Finally:")
            with open(self.path + "css.csv", "w", encoding="utf-8") as fp:
                writer = csv.DictWriter(fp, fieldnames=self.headers)
                writer.writeheader()
                rows = [{"css": css, "cssdownload": download, "php": php}
                        for (css, download, php) in zip(self.csslist, self.css_downloads, self.phplist)]
                print(rows)
                writer.writerows(rows)
                fp.flush()
            with open(self.path + "url.json", "w", encoding="utf-8") as jfp:
                json.dump(self.linkedlist, jfp, indent=2)
                jfp.flush()

    #Downloads and links css
    async def css(self,soup,session):
        b = soup.find_all("link", {"rel":"stylesheet","href":True})
        for z in b:
            tag=z["href"]
            if tag in self.csslist:
                continue
            if re.search(r"css_\d+\.css", tag, re.IGNORECASE):
                z["href"] = self.csslist[self.phplist.index(tag)]
                continue
            async with self.csslock:
                down = urljoin(f"https://{self.domain}", z["href"])
                self.log.emit(f"Downloading {down}")
                css_count=len(self.css_downloads)
                cssfile=f"css_{css_count}.css"

                self.csslist.append(f"css_{css_count}.css")
                self.phplist.append(tag)
                self.css_downloads.append(z)
                            #breakpoint()
                try:
                    css =await session.get(down)

                    if css.status_code==200:
                        async with aiofiles.open(self.path+cssfile, "w", encoding="utf-8") as cfp:
                            text=css.text
                            await cfp.write(text)
                    else:
                        breakpoint()
                        css.raise_for_status()

                    z["href"] = f"css_{css_count}.css"
                except Exception as e:
                    logging.info(str(e))
                                    #self.side.login(e)
                """The csslist is basically the list of downloaded cssfiles. This makes sure that the href is not in that list
                        This is honestly redundant"""

        #This is a leftover from the previous method used.
        """with open(f"{self.path}css.txt","w",encoding='utf-8') as f:
            f.writelines(list(map(lambda x,y:x+" : "+y+"\n",self.phplist,self.csslist)))"""
        return soup


    #Links images using the data-image-key
    async def image(self,soup):
        a = [image for image in soup.find_all("img", {"data-image-key":True,"src":True}) if image['data-image-key']!=image['src']]
        if a:
            """
            This is unlikely to be needed since everything in the list has by default a src and a data-src is already being checked for.
            a1=[img for img in a if img.has_attr('src') and img['data-image-key']!=img['src']]
            a2=[img for img in a if img.has_attr('data-src') and img['data-image-key']!=img['data-src']]
            a=a1+a2"""
            for img in a:
                try:
                    name=self.images[img["data-image-key"]][2]
                    img["src"] = name
                    if img.has_attr('data-src'):
                        img['data-src']=name
                        img["loading"]="eager"
                        img["class"]="mw-file-element"
                except Exception as e:
                    logging.info(f"{e}")
                #self.side.login(e)
        return soup

    async def fixlinks(self,html,ses):
        a=html.find_all("a",{"href":self.paturl,"title":True,"data-tracking-label":False})
        try:
            for i in a:
                url=urljoin(f"https://{self.domain}/",i["href"])
                #print(url)
                if self.linkedlist.get(url):
                    i["href"]=self.linkedlist[url]["name"]
                else:
                    #print(url)
                    r=await ses.head(url,allow_redirects=True)
                    url=r.url
                    if self.hashsub.search(url):
                        url=self.hashsub.sub(r"\1",url)

                    i["href"]=self.linkedlist[url]["name"]

                #(await self.cleaningstring(self.ref(i["href"])))+".html")
            b=html.find_all("a",{"href":re.compile(r"^\/wiki\/File:.*$")})
            for i in b:
                i["href"]=i["href"].split(':')[-1]
            a=html.find_all("video",{"src":True})+html.find_all("audio",{"src":True})
            for x in a:
                e=x.find("a",{"href":True})
                name=e["href"].strip().split(":")[-1]
                e["href"]=name
                x["src"]=name
            a = html.find_all("a", {"href": True, "class": re.compile("video")})
            for i in a:
                i["href"]=i["href"].strip().split(":")[-1]
        except Exception as e:
            print(str(e))
            breakpoint()
            print("Failed to link")
            self.log.emit(f"Failed to Link:{e}")
        return html



    async def php(self,session):
        link = urljoin(f"https://{self.domain}/",
                       "/load.php?cb=20201211140723&lang=en&modules=startup&only=scripts&raw=1&skin=fandomdesktop")
        res = await session.get(link)
        async with aiofiles.open(f"{self.path}js_0.js","w",encoding="utf-8") as fp:
            await fp.write(res.text)




    #Removes js tracking scripts and  any suspicious iframes
    async def remove_trackers(self,soup):
        c1=[script for script in soup.find_all("iframe",{"height":re.compile(r"^[01]$"),"width":re.compile(r"^[01]$")})]
        c2=soup.find_all("script",{"src":re.compile(r"^(?!(\/load.php\?)).+$")})
        c=c1+c2
        c=map(lambda x:x.decompose(),c)
        c=[i.decompose() for i in soup.find_all("script",{"src":False}) if bool(self.trackers.search(i.text))]
        script=soup.find("script",{"src":re.compile(r"^(\/load.php\?).*$")})
        if script:
            script["src"]="js_0.js"
        return soup

    async def cleaningstring(self,urlname):
        urlname = urlname.replace('/', '-')
        urlname = urlname.replace('.', '_')
        urlname = urlname.replace(':', ' ')
        return urlname

    async def link(self,x,session):
        #Helps continue from where you left off
        name=self.linkedlist[x]["name"]
        self.log.emit(f"Linking {name}")
        #breakpoint()
        async with aiofiles.open(f"{self.path}{name}","r",encoding="utf-8") as fp:
            con=await fp.read()
        soup:BeautifulSoup=BeautifulSoup(con,"lxml")
        soup=await self.image(soup)
        soup=await self.css(soup,session)
        soup=await self.fixlinks(soup,session)
        soup=await self.remove_trackers(soup)
        soupop=soup.prettify()
        async with aiofiles.open(f"{self.path}{name}","w",encoding="utf-8") as fp2:
            #breakpoint()
            #print(f"{self.path}{name}")
            #breakpoint()
            await fp2.write(soupop)
            await fp2.flush()
            await asyncio.get_event_loop().run_in_executor(
                None, os.fsync, fp2.fileno()
            )
        self.prog.emit(self.i)
        self.linkedlist[x]["linked"] = True

        """    
         Bye bye dumb code 
        async with aiofiles.open(self.path+"url.csv","w+",encoding='utf-8') as urls:
            update=aiocsv.AsyncDictWriter(urls,fieldnames=['URL','Linked'])
            await update.writeheader()
            for row in self.linkedlist:
                if row['URL']==x:
                    row['Linked']="True"
                    await update.writerows(self.linkedlist)
                    break"""
        self.i+=1



