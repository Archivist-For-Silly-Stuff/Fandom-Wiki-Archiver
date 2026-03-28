import os
import pathlib
import re
from csv import DictWriter
from urllib.parse import urljoin, urlsplit
from crawlgui import csvfiles
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QWaitCondition
from bs4 import BeautifulSoup
import requests
import logging
import csv
import cssbeautifier

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
    #Takes the path where all the html is saved and domain of the url
    def __init__(self,path,domain,csvurls:csvfiles,parent=None):
        """"""
        QObject.__init__(self,parent)
        self.trackers=re.compile(r"(googletag|quantserve|scorecard|beacon|metrics|silversurfer|search-insight)")
        self.latestpattern=re.compile(r"\?cb.*\&")
        self.static=re.compile(r"(https\:)?"
                               r"\/\/static\..+\.net\/"
                               r"([^\/]+)\/([^\/]+\/)?(([^\/]+)\/){2}"
                               r"([^\/]+)(\/revision\/latest\/.*)?")

        self.ispaused=False

        self.session: curl_cffi.Session = curl_cffi.Session(impersonate="chrome")

        self.path=pathlib.Path(path)
        self.domain=domain

        self.csslist=[]
        self.css_downloads=[]
        self.phplist=[]
        self.rows=[]
        self.headers=['css','php']
        self.cssdict: dict = dict()

        self.urlfragmentremove=lambda url:(urlsplit(url)
                                           ._replace(fragment="")
                                           .geturl())

        self.mutex=QMutex()
        self.pausecon=QWaitCondition()

        self.base=f"https://{self.domain}/"
        self.absolute=lambda url:urljoin(self.base,url)

        self.sanitise=lambda url:self.urlfragmentremove(self.absolute(url))

        self.csvurl=csvurls
        self.links = self.csvurl.getdownloadedsites()
        self.sites={row["site"]:row["name"] for row in self.links}
        self.media={row["original name"]:row["name"] for row in self.csvurl.mediacsv}

        self.urlpath=self.path.joinpath(f"csv_{self.domain.split(".")[0]}.csv")

        try:
            with open(self.path.joinpath("css.csv"),"r",encoding='utf-8') as fp:
                reader=csv.DictReader(fp)

                for row in reader:
                    #self.cssdict[row['css']]=row['php']
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
    def link(self):
        #Helps continue from where you left off
        #lists=os.listdir(self.path)
        self.i=1

        for x in self.links:

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

        self.session.close()
        self.finished.emit()

    def image(self,soup):
        a = ({image for image
              in soup.find_all("img", {"data-image-key":True,"src":True})
             if image['data-image-key']!=image['src']}
             |{image for image
               in soup.find_all("img", {"data-image-key":True,"data-src":True})
               if image['data-image-key']!=image['data-src']})

        if a:
            """
            This is unlikely to be needed since everything in the list has by default a src and a data-src is already being checked for.
            a1=[img for img in a if img.has_attr('src') and img['data-image-key']!=img['src']]
            a2=[img for img in a if img.has_attr('data-src') and img['data-image-key']!=img['data-src']]
            a=a1+a2"""
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
    def css(self,soup):

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

    def fixlinks(self,html):
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
        c=html.find_all("a",{"href":self.static})
        for link in c:
            link["href"]=self.static.match(link["href"]).group(6)
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
    def remove_trackers(self,soup):
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

    def cleaningstring(self,urlname):
        urlname = urlname.replace('/', '-')
        urlname = urlname.replace('.', '_')
        urlname = urlname.replace(':', ' ')
        return urlname

