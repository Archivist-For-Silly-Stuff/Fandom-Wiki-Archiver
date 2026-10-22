import os
import pathlib
import re
import traceback
from csv import DictWriter
from sys import orig_argv
from urllib.parse import urljoin, urlsplit
from crawlgui import csvfiles
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QWaitCondition
from bs4 import BeautifulSoup
import requests
import logging
import csv
import cssbeautifier
import typing
import progress
import curl_cffi
from urllib.parse import urlparse
logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)

#from GUI import sidewindow


class linker(QObject):
    log=pyqtSignal(str)
    prog=pyqtSignal(int)
    finished=pyqtSignal()
    pause=pyqtSignal(int)
    sendcsv=pyqtSignal(csvfiles)
    #Takes the path where all the html is saved and domain of the url
    def __init__(self,parent=None):
        """"""
        QObject.__init__(self,parent)

        self.trackers=re.compile(r"(googletag|quantserve|scorecard|beacon|metrics|silversurfer|search-insight)")
        self.latestpattern=re.compile(r"\?cb.*\&")
        self.staticfull=re.compile(r"^((https\:)?\/\/static\..+\.net\/([^\/]+)\/)"
                                   r"((images\/)|([^\/]+\/))?" 
                                   r"((([^\/]+)\/){2})"
                                   r"([^\/]+)" #file name
                                   r"(|((\/revision\/latest\/).*|\/.*))$")
        self.findimg=lambda url:self.staticfull.match(url).group(10)

        self.wiki:str=""
        self.fandom:bool=0
        self.miraheze:bool=0
        self.ispaused:bool=False

        self.session: curl_cffi.Session|None =None

        self.csslist:list=[]
        self.css_downloads:list=[]
        self.phplist:list=[]

        self.rows:list=[]
        self.headers:list[str]=['css','php']
        self.cssdict: dict = dict()

        self.urlfragmentremove=lambda url:(urlsplit(url)
                                           ._replace(fragment="")
                                           .geturl())

        self.mutex:QMutex=QMutex()
        self.pausecon:QWaitCondition=QWaitCondition()

        self.domain:str=""
        self.path:pathlib.Path=pathlib.Path()

        self.base:str="https://{}/"
        self.sanitise = None
        self.absolute = None

        self.csvurl:csvfiles|None=None
        self.links:list[dict] =[]
        self.sites:dict={}
        self.media:dict={}

        self.i = 0


    def prep_l(self,path:pathlib.Path,domain:str,csvurls:csvfiles):
        self.csslist:list=[]
        self.css_downloads:list=[]
        self.phplist:list=[]

        self.rows:list=[]
        self.cssdict: dict = dict()

        self.wiki=domain.split(".")[1]
        self.fandom:bool=self.wiki=="fandom"
        self.miraheze:bool=self.wiki=="miraheze"

        self.session= curl_cffi.Session(impersonate="firefox")

        self.domain=domain
        self.base:str=f"https://{self.domain}/"
        self.absolute=lambda url:urljoin(self.base,url)
        self.sanitise=lambda url:self.urlfragmentremove(self.absolute(url))

        self.csvurl:csvfiles=csvurls
        self.links:list[dict] = self.csvurl.getdownloadedsites()
        self.sites:dict={row["site"]:row["name"] for row in self.links}
        self.media:dict={row["original name"]:row["name"] for row in self.csvurl.mediacsv}

        self.path=pathlib.Path(path)

        try:
            with open(self.path.joinpath("css.csv"),"r",encoding='utf-8') as fp:
                reader=csv.DictReader(fp)
                for row in reader:
                    self.csslist.append(row['css'])
                    self.phplist.append(row['php'])
                    self.rows.append({'css':row['css'], 'pfp':row['php']})

        except FileNotFoundError as e:
            with open(self.path.joinpath("css.csv"),"w",encoding='utf-8') as fp:
                reader=csv.DictWriter(fp,fieldnames=self.headers)
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

    @pyqtSlot()
    def main(self):

        #Helps continue from where you left off
        #lists=os.listdir(self.path)
        self.i=1
        for x in self.links:
            self.link(x)
        self.csvurl.save_urls(self.path.joinpath(f"csv_{self.domain.split('.')[0]}.csv"))
        self.session.close()
        self.finished.emit()

    @pyqtSlot()
    def link(self,x:dict):
        try:
            self.check_pause()

            name = x["name"]
            self.log.emit(f"Linking {name}")
            self.prog.emit(self.i)
            pathname = self.path.joinpath(name)
            # breakpoint()
            with open(pathname, "r", encoding="utf-8") as fp:
                soup = BeautifulSoup(fp, "html.parser")

                soup = self.image(soup)
                soup = self.css(soup)
                soup = self.fixlinks(soup)
                soup = self.remove_trackers(soup)

            with open(pathname, "w", encoding="utf-8") as fp2:
                fp2.write(soup.prettify())

            self.csvurl.update_url_link(name)

            self.i += 1
        except Exception as e:
            print(f"{str(e)}\n\n{traceback.format_exc()}")

    """@pyqtSlot()
    def link(self):
        #Helps continue from where you left off
        #lists=os.listdir(self.path)
        self.i=1

        for x in self.links:
            try:
                self.check_pause()

                name=x["name"]
                self.log.emit(f"Linking {name}")
                self.prog.emit(self.i)
                pathname=self.path.joinpath(name)
                #breakpoint()
                with open(pathname,"r",encoding="utf-8") as fp:
                    soup=BeautifulSoup(fp,"html.parser")

                    soup=self.image(soup)
                    soup=self.css(soup)
                    soup=self.fixlinks(soup)
                    soup=self.remove_trackers(soup)

                with open(pathname,"w",encoding="utf-8") as fp2:
                    fp2.write(soup.prettify())
                    self.csvurl.update_url_link(x["name"])


                self.i+=1
            except Exception as e:
                print(f"{str(e)}\n\n{traceback.format_exc()}")

        self.session.close()
        self.finished.emit()"""

    def image(self,soup:BeautifulSoup)->BeautifulSoup:
        if self.fandom:
            a = ({image for image
                  in soup.find_all("img", {"data-image-key":True,"src":True})
                 if image['data-image-key']!=image['src']}
                 |{image for image
                   in soup.find_all("img", {"data-image-key":True,"data-src":True})
                   if image['data-image-key']!=image['data-src']})

            if a:
                for img in list(a):
                    try:
                        img["src"] = img["data-image-key"]
                        if img.has_attr('data-src'):
                            img['data-src']=img["data-image-key"]
                            img["loading"]="eager"
                            if "lazyload" in img["class"]:
                                img["class"].remove("lazyload")
                    except Exception as e:
                        self.log.emit(str(e))
                        logging.info(f"{e}")
                #self.side.login(e)
        elif self.miraheze:
            a = ({image for image
                  in soup.find_all("img", {"src": True})
                  if self.staticfull.search(image['src'])}
                 | {image for image
                    in soup.find_all("img", { "data-src": True})
                    if self.staticfull.search(image['data-src'])})
            print(a)

            if a:
                for img in list(a):
                    try:
                        if img.has_attr("data-src"):
                            src=img.get("data-src")
                            print(src)
                        elif img.has_attr("src"):
                            src=img.get("src")
                            print(src)
                        if not(src.startswith("https:")):
                            src="https:"+src
                        name=self.findimg(src)
                        print(name)
                        img["src"] = name
                        if img.has_attr('data-src'):
                            img['data-src'] = name

                            img["loading"] = "eager"
                            if "lazyload" in img["class"]:
                                img["class"].remove("lazyload")
                        if img.has_attr("srcset"):
                            img["srcset"]=name
                    except Exception as e:
                        self.log.emit(str(e))
                        logging.info(f"{e}")
                        breakpoint()
                # self.side.login(e)

        a=soup.find_all("audio",{"src":True})+soup.find_all("video",{"src":True})
        if a:
            for media in a:

                aref=media.find("a",{"href":re.compile(r"./wiki/File:.+$")})
                if aref:
                    name=aref.get("href").strip().split(":")[-1]
                    aref["href"]=self.media[name]
                    media["loading"]="eager"
                    media["src"]=self.media[name]



        return soup

    #Downloads and links css
    def css(self,soup:BeautifulSoup)->BeautifulSoup:

        b = soup.find_all("link", {"rel":"stylesheet","href":True})

        for z in b:
            if (z['href'] not in self.phplist) and (z['href'] not in self.csslist):
                try:
                    css = self.session.get(self.absolute(z['href']))
                    css_count=len(self.phplist)
                    csname=f"css_{css_count}.css"
                    self.csslist.append(csname)
                    self.phplist.append(z["href"])
                    #self.css_downloads.append(z)

                    cssfile = open(self.path.joinpath("css.csv"), "w", encoding="utf-8")
                    writer = DictWriter(cssfile, fieldnames=self.headers)
                    writer.writeheader()
                    self.rows.append({'css':csname,'php':z["href"]})
                    writer.writerows(self.rows)

                    with open(self.path.joinpath(csname), "w", encoding="utf-8") as cfp:
                        cfp.write(css.text)
                    cssfile.close()

                    z["href"] = csname
                except Exception as e:
                    self.log.emit(str(e))
                    logging.info(str(e))
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

    def redirect_check(self,url):
        headers=self.session.head(url,allow_redirects=True)
        return headers.url

    def findurlname(self,url):
        if url in self.sites:
            return self.sites[url]
        return url

    def fixlinks(self,html:BeautifulSoup)->BeautifulSoup:
        a=html.find_all("a",{"href":re.compile(r"^\/wiki\/(?!((Special\:)|(Category\:)|(File\:))).*$"),"title":True})
        for i in a:
            self.check_pause()
            url=i["href"]
            if "#" in url:
                url=self.sanitise(url)
            else:
                url=self.absolute(url)
            if url not in self.sites:
                url=self.redirect_check(url)
            i["href"]=self.findurlname(url)
        b=html.find_all("a",{"href":re.compile(r"^\/wiki\/File:.*$")})
        for i in b:
            self.check_pause()
            i["href"]=i["href"].split(':')[-1]
        c=html.find_all("a",{"href":self.staticfull})
        for link in c:
            link["href"]=self.findimg(link["href"])
        #AREN'T THEY THE SAME FUDGING METHOD????
        """a=html.find_all("video",{"src":True})+html.find_all("audio",{"src":True})
        for x in a:
            e=x.find("a",{"href":True})
            name=e["href"].strip().split(":")[-1]
            e["href"]=name
            x["src"]=name
        a = html.find_all("a", {"href": True, "class": re.compile("video")})
        for i in a:
            i["href"]=i["href"].strip().split(":")[-1]"""
        return html



    def php(self):
        link = urljoin(self.base,
                       "/load.php?cb=20201211140723&lang=en&modules=startup&only=scripts&raw=1&skin=fandomdesktop")
        res = self.session.get(link)
        with open(f"{self.path}js_0.js","w",encoding="utf-8") as fp:
            fp.write(res.text)




    #Removes js tracking scripts and  any suspicious iframes
    def remove_trackers(self,soup:BeautifulSoup)->BeautifulSoup:
        self.check_pause()
        scripts=[script.decompose() for script in soup.find_all("script")]
        print(soup.find_all("script"))
        c1=[script.decompose() for script in soup.find_all("iframe",{"height":re.compile(r"^[01]$"),"width":re.compile(r"^[01]$")})]
        c1=map(lambda x:x.decompose(),c1)
        for link in soup.find_all("link", {"as": "script", "rel": "preload", "href": re.compile(r"seg\.ad\.gt")}):   #<link as="script" href="https://seg.ad.gt/api/v1/s/158" nonce="" rel="preload"/>
            link.decompose()
        med = soup.find("div", {"id": "featured-video__player-container"})
        if med:
            med.decompose()

        """        script=soup.find("script",{"src":re.compile(r"^(\/load.php\?).*$")})
        if script:
            script["src"]="js_0.js"""
        return soup

    def cleaningstring(self,urlname:str)->str:
        urlname = urlname.replace('/', '-')
        urlname = urlname.replace('.', '_')
        urlname = urlname.replace(':', ' ')
        return urlname

