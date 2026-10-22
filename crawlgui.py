import datetime
import logging
# Allows us to delete any copies of html
import os
# Helps to join source url's with reference url's
import os.path
import pathlib
import csv
from csv import DictReader
from time import sleep
from typing import AnyStr
from urllib.parse import urljoin

import bs4
import curl_cffi
# For downloading files
# Regex pattern creation
import re
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QWaitCondition
# Parsing the HTML
from bs4 import BeautifulSoup

import faulthandler
faulthandler.enable()
# Configure logging
logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)
# Graphs
import traceback
"""Takes the list of all media in a wiki and all sites as parameters.
        They are a list of dictionary objects (each dict is a record).
        For sites, the fields are
        site
        name
        linked
        downloaded
        for media the fields are:
        original name
        name
        source
        downloaded"""

class csvfiles:
    def __init__(self,media:list[dict],sites:list[dict]):

        self.mediacsv=media
        self.sitescsv=sites
    def getmedia(self)->list[dict]:
        return [row for row in self.mediacsv if row["downloaded"].lower()=="false"]

    def getsites(self)->list[dict]:
        return [row for row in self.sitescsv if row["downloaded"].lower()=="false"]

    def getdownloadedsites(self)->list[dict]:
        return [row for row in self.sitescsv if row["linked"].lower()=="false" and row["downloaded"].lower()=="true"]

    def update_url_download(self,urlname)->None:
        for row in range(len(self.sitescsv)):
            if urlname == self.sitescsv[row]["name"]:
                self.sitescsv[row]["downloaded"] = "TRUE"
                # print(row)
                break

    def update_url_link(self,urlname:str)->None:
        for row in range(len(self.sitescsv)):
            if urlname == self.sitescsv[row]["name"]:
                self.sitescsv[row]["linked"] = "TRUE"
                # print(row)
                break

    def update_media(self,media:str)->None:
        for row in range(len(self.mediacsv)):
            if media == self.mediacsv[row]["name"]:
                self.mediacsv[row]["downloaded"] = "TRUE"
                # print(row)
                break

    def save_media(self, path:pathlib.Path)->None:
        with open(path,"w",encoding="utf-8") as fp:
            writer=csv.DictWriter(fp,fieldnames=["original name","source","name","downloaded"],lineterminator="\n")
            writer.writeheader()
            writer.writerows(self.mediacsv)

    def save_urls(self, path:pathlib.Path)->None:
        with open(path,"w",encoding="utf-8") as fp:
            writer=csv.DictWriter(fp,fieldnames=["site","name","linked","downloaded"],lineterminator="\n")
            writer.writeheader()
            writer.writerows(self.sitescsv)

    def save(self,path:pathlib.Path)->None:
        self.save_media(path)
        self.save_urls(path)

    def getlen(self)->int:
        return len(self.sitescsv)

    def getlenmedia(self)->int:
        return len(self.mediacsv)

    def __len__(self)->dict[str,int]:
        return {
            "sites":len(self.sitescsv),
            "media":len(self.mediacsv)
        }


class crawler(QObject):
    log=pyqtSignal(str)
    prog=pyqtSignal(int)
    sendurl=pyqtSignal(csvfiles)
    finish=pyqtSignal()
    pause=pyqtSignal(bool)
    # Keeps a count of url's visited, downloaded and what domains are allowed. Besides the path to be saved too.
    # It also checks if you wanna make a graph
    def __init__(self, allowed_domain:str, path:pathlib.Path,allf:bool, urls:list=[],  parent=None):
        """
        Allowed_domain[Deprecated]:For the allowed domain here.
        path:For the path everything needs to get saved at
        urls:Every url to be saved.
        parent:dummy
        """
        print(allf)
        QObject.__init__(self,parent)
        self.allfiles:bool=allf

        self.listourl:list = []
        self.csvfile:list[dict]|DictReader[str] =[]
        self.csvmediafile:list[dict]|DictReader[str]=[]

        self.urlpath:pathlib.Path = pathlib.Path()
        self.session:curl_cffi.Session|None=None

        self.visited_urls:list=[]
        self.urls_to_visit:list[str] = urls

        self.allowed_domain:str = ""
        self.wiki:str=""
        self.fandom:bool=0
        self.miraheze:bool=0

        self.patternscrap: re.Pattern[str]|None = None

        self.ispaused:bool=False
        self.mutex:QMutex=QMutex()
        self.pausecon:QWaitCondition=QWaitCondition()


        self.nameimg:re.Pattern[AnyStr] = re.compile(r"^(.+)\.(?:(jpg|jpeg|png|gif|svg|webp|ico))$",
                             re.IGNORECASE)
        self.medianame:re.Pattern[AnyStr] = re.compile(r"^(.+)\.([^.]+)$",
                             re.IGNORECASE)
        self.latestpattern:re.Pattern[AnyStr] = re.compile(r"/latest(?:\/|\?cb).*$",
                                        re.IGNORECASE)
        self.static:re.Pattern[AnyStr] = re.compile(r"static\..+\.net",re.IGNORECASE)
        self.staticfull:re.Pattern[AnyStr] = re.compile(r"^((https\:)?\/\/static\..+\.net\/([^\/]+)\/)"
                                                        r"((images\/)|([^\/]+\/))?" 
                                                        r"((([^\/]+)\/){2})"
                                                        r"([^\/]+)" #file name
                                                        r"(|((\/revision\/latest\/).*|\/.*))$")

        self.statictime:re.Pattern[AnyStr]=re.compile(rf"^((https\:)?\/\/static\..+\.net\/([^\/]+)\/)"
                                                      rf"((images\/)|([^\/]+\/))?"
                                                      rf"((([^\/]+)\/){2})"
                                                      rf"([^\/]+)"
                                                      rf"(|((\/revision)\/((latest\/)|(\d+)).*|\/.*))$") 

        self.sitemap:re.Pattern[AnyStr]|None = None
        self.mediamap:re.Pattern[AnyStr]|None = None

        self.urls=None
        self.findimg=lambda url:self.staticfull.match(url).group(10)

        self.cleanlist:list=[]
        self.medialist:set=set()
        self.count:int=0

        self.filepath:pathlib.Path=pathlib.Path()
        self.media:dict[str,list[str]]|list=dict()

        self.resources:set=set()

        self.urlpath:pathlib.Path=pathlib.Path()
        print("F")
        self.error=open(path.joinpath("error.txt"),"w",encoding="utf-8")
        self.formattime="%H:%M, %d  %B %Y"
        self.prepc(allowed_domain,path,urls)

    def prepc(self, allowed_domain:str, path:pathlib.Path, urls:list=[]):
        self.urls_to_visit:list[str] = urls

        self.urlpath:pathlib.Path = path
        self.session=curl_cffi.Session(impersonate="firefox")

        self.allowed_domain = allowed_domain
        self.wiki=self.allowed_domain.split(".")[1].lower()
        self.fandom:bool=self.wiki=="fandom"
        self.miraheze:bool=self.wiki=="miraheze"

        self.patternscrap: re.Pattern[str] = re.compile(
            rf"^https://{self.allowed_domain}/wiki/"
            r"[^:]+$",
            re.IGNORECASE
        )

        self.sitemap:re.Pattern[AnyStr] = re.compile(rf"^https://"
                                                     rf"{self.allowed_domain}"
                                                     rf"/wiki/Special:AllPages"
                                                     rf"\??.*(from=.+)?.*$",
                                                     re.IGNORECASE)
        self.mediamap:re.Pattern[AnyStr] = re.compile(rf"^https://{self.allowed_domain}"
                                                      rf"/wiki/Special:ListFiles"
                                                      rf"(?:\?offset=.+| )$",
                                                        re.IGNORECASE)

        self.urls=lambda i:urljoin(rf"https://{self.allowed_domain}/wiki/",i['href'])

        fileregex=re.compile(r"^.+\.(?!(html)|(htm)).+$")
        self.filepath:pathlib.Path=self.urlpath.joinpath(f"csv_{self.allowed_domain.split(".")[0]}_media.csv")
        self.resources={file for file in os.listdir(self.urlpath) if bool(fileregex.match(file))}
        self.urlpath:pathlib.Path=self.urlpath.joinpath(f"csv_{self.allowed_domain.split(".")[0]}.csv")



    def cleaningstringc(self,urlname:str)->str:
        urlname='-'.join(urlname.strip().split('/')[4::])
        #urlname = urlname.replace('/', '-')
        urlname = urlname.replace('.', '_')
        urlname = urlname.replace(':', ' ')
        if urlname.lower() in self.cleanlist:
            urlname=f"{urlname}({self.count})"
            self.count+=1
            print("huh")
        self.cleanlist.append(urlname.lower())
        urlname+=".html"
        return urlname



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
        self.log.emit("Unpaused")


    def check_pause(self):
        self.mutex.lock()
        while self.ispaused:
            self.pausecon.wait(self.mutex)
        self.mutex.unlock()

    @pyqtSlot()
    def downloadbar(self):
        self.prog.emit(1)
        self.log.emit("Scraping sitemap")
        print(self.allowed_domain.split(".")[0])

        if not(os.path.isfile(self.urlpath)):
            self.collectsites()

        else:
            fp = open(self.urlpath, 'r', newline='\n', encoding="utf-8")
            self.csvfile=csv.DictReader(fp)
            self.csvfile = [row for row in self.csvfile]
            fp.close()

            if not self.csvfile:
                self.collectsites()

        if not(os.path.isfile(self.filepath)):
            self.collectfiles()

        else:
            fp = open(self.filepath, 'r', newline='\n', encoding="utf-8")
            self.csvmediafile=csv.DictReader(fp)
            self.csvmediafile = [row for row in self.csvmediafile]
            fp.close()

            if not self.csvmediafile:
                self.collectfiles()

        self.prog.emit(2)
        self.log.emit("Finished scraping sitemap")
        csvf=csvfiles(self.csvmediafile,self.csvfile)

        self.session.close()
        self.error.close()
        self.sendurl.emit(csvf)
        self.finish.emit()

    @pyqtSlot()
    def collectsites(self):
        #self.maketable()
        sitemaplist:list = [self.urls_to_visit[0]]

        while self.urls_to_visit:
            self.check_pause()
            self.url = self.urls_to_visit.pop(0).strip()
            self.log.emit(f"Collecting links from:{self.url}")
            sitemaplist.append(self.url)
            html = self.session.get(self.url)
            soup = BeautifulSoup(html.text, "html.parser")
            b=soup.find_all('a',{"href":re.compile(r"^/wiki/Special:AllPages\??.*(from=.+)?.*$")})
            a = soup.find_all('a', {"href": re.compile(r"^\/wiki\/(?!((Special:)|(Category:)|(User_blog:)|(File:))).*$"),"class":False})
            # Uses URL join to connect with the main path
            self.listourl = list(map(self.urls, a))
            blist:list=list(map(self.urls,b))
            self.urls_to_visit = list(set(self.urls_to_visit + list(filter(
                lambda x: (bool(self.sitemap.match(x)) and (x not in self.urls_to_visit) and (x not in sitemaplist)),
                blist))))
            sitemaplist = sitemaplist + self.urls_to_visit
            self.visited_urls = self.visited_urls + list(
                filter(lambda x: ((x not in sitemaplist) and (x not in self.visited_urls))
                       , self.listourl))

        self.visited_urls = list(set(self.visited_urls))
        self.csvfile:list[dict[str,str]]=[{"site":site,"name": self.cleaningstringc(site), "linked": "FALSE", "downloaded": "FALSE"} for site in self.visited_urls]
        sleep(3)
        fp=open(self.urlpath,'w',newline='\n',encoding="utf-8")
        writer=csv.DictWriter(fp,fieldnames=["site","name","linked","downloaded"],lineterminator="\n")
        writer.writeheader()
        writer.writerows(self.csvfile)
        fp.close()

    @pyqtSlot()
    def collectfiles(self):
        #self.maketable()
        #?limit=500&user=&ilshowall=1
        media:list=[urljoin(rf"https://{self.allowed_domain}/wiki/",f"/wiki/Special:ListFiles?limit=500&ilshowall={int(self.allfiles)}")]
        filelist:list = [media[0]]

        while media:
            self.check_pause()
            self.url:str = media.pop(0).strip()
            self.log.emit(f"Collecting Media from:{self.url}")
            filelist.append(self.url)
            html = self.session.get(self.url)
            soup = BeautifulSoup(html.text, "lxml")
            b=soup.find_all('a',{"href":re.compile(r"^/wiki/Special:ListFiles\??.*(offset=.+)?.*$")})
            blist = map(self.urls, b)
            try:
                """
                images=soup.find_all('img',{"src":True})
                for img in images:
                    self.mediaclean(img,"image")
                audio=soup.find_all("audio", {"src": True})
                for au in audio:
                    self.mediaclean(au,"audio")
                videos=soup.find_all("video",{"src":True})
                for vid in videos:
                    self.mediaclean(vid,"video")"""
                self.table_clean(soup.table,self.allfiles)
            except Exception as e:
                print(f"{str(e)}\n\n{traceback.format_exc()}",file=self.error)
                self.log.emit(f"{str(e)}\n\n{traceback.format_exc()}")

            media=media+ list(set(filter(lambda url:(url not in filelist)
                                                and (url not in media)
                                                and bool(self.mediamap.match(url)),blist)))
            filelist=filelist + media
        #print(self.media)
        self.csvmediafile:list[dict[str,str]]=[{"original name":key,"source":item[0],"name":item[1],"downloaded":item[2]} for (key,item) in self.media.items()]
        sleep(3)
        fp=open(self.filepath,'w',newline='\n',encoding="utf-8")
        writer=csv.DictWriter(fp,fieldnames=["original name","source","name","downloaded"],lineterminator="\n")
        writer.writeheader()
        writer.writerows(self.csvmediafile)
        fp.close()

    def table_clean(self,table:bs4.Tag,allf:bool):
        """It cleans the table row by row. Could probably get done more efficiently."""
        if allf:
            rows = [row for row in table.tbody.find_all("tr")]
            for row in rows:
                timestamp=""
                top=row.find("td",{"class":re.compile(r"col_top")}).text.strip()
                file = row.find("td", {"class": re.compile(r"col_thumb")})
                img=file.find("img")
                vid=file.find("video")
                au=file.find("audio")
                if img:
                    media=img
                elif vid:
                    media=vid
                elif au:
                    media=au
                else:
                    print(f"{file} is causing problems here!",file=self.error)
                    continue
                name=media.name if media.name!="img" else "image"
                if top.lower()=="no":
                    timestamp=row.find("td",{"class":re.compile(r"img_timestamp")}).text.strip()
                    timestamp=datetime.datetime.strptime(timestamp,self.formattime)
                    timestr:str=timestamp.strftime("_%Y_%m_%d_%H_%M_%S")
                    self.mediaclean(media,name,timestr)
                else:
                    self.mediaclean(media,name)

        else:
            images=table.find_all('img',{"src":True})
            for img in images:
                self.mediaclean(img,"image")
            media=table.find_all("video",{"src":True})+table.find_all("audio",{"src":True})
            for med in media:
                self.mediaclean(med,med.name)



    def mediaclean(self,tag:bs4.Tag,mtype:str,time:str="")->None:
        if mtype not in {"image","audio","video"}:
            raise Exception(f"Unkown media {mtype}")
        src:str=tag.get("src")
        name:str=""
        if src and src.startswith("data:image"):
            src = tag.get('data-src')
        if not(src.startswith("https:")):
            src=f"https:{src}"
        if not (bool(self.static.search(src))):
            src = urljoin(f"https://{self.allowed_domain}", src)
            name=src.split("/")[-1]
        else:
            try:
                print(f"{src}")
                if self.staticfull.search(src):
                    name=self.findimg(src)
                    src=self.staticfull.sub(r"\1\5\7\10\13",src)
                else:
                    print(src,"Needs to be downloaded. Please if you see this, send it to me!")
                    name:str=src.split("/")[-1]
            except Exception as e:
                print(f"{str(e)}\n\n{traceback.format_exc()}",file=self.error)
                print(f"\n{src}\n",file=self.error)
        if self.fandom and mtype=="image":
            namere=name
            x=tag.get('data-image-key')
            if x:
                name=x
            else:
                print(tag)
                breakpoint()
            print(name==namere)

        if name not in self.media:
            modname = name
            mname = self.nameimg.match(name)
            if mtype=="image" and not bool(mname):
                modname = f"{name}({self.count}).webp"
            if name.lower() in self.media:
                rename:str|int=self.count
                if mtype=="image":
                    mname=self.nameimg.match(modname)
                    modname = mname.group(1) + f"({rename})." + mname.group(2)
                elif mtype=="audio" or mtype=="video":
                    modname = self.medianame.match(name)
                    modname = modname.group(1) + f"({rename})." + modname.group(2)
                self.count += 1
            self.media[name] = [src,modname,"FALSE"]

        if name in self.media:
            if time:
                rename=time
                modname = name
                mname = self.nameimg.match(name)
                if mtype == "image" and not bool(mname):
                    modname = f"{name}({self.count}).webp"
                if mtype=="image":
                    mname=self.nameimg.match(modname)
                    modname = mname.group(1) + f"({rename})." + mname.group(2)
                elif mtype=="audio" or mtype=="video":
                    modname = self.medianame.match(name)
                    modname = modname.group(1) + f"({rename})." + modname.group(2)
                self.media[modname]=[src,modname,"FALSE"]




            """if self.latestpattern.search(src):
                src = self.latestpattern.split(src)[0] + "/latest/"""
