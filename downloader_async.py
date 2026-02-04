import os
import re
from yarl import URL
import time
from urllib.parse import urljoin
from curl_cffi.requests import AsyncSession
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from bs4 import BeautifulSoup
import logging
import requests
import asyncio
import aiohttp

from video_downloader import Videos



class asyncdownloader(QObject):
    log_message = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal()
    def __init__(self,path,urls,parent=None):
        #Checks that the latest version of an image is downloaded.
        self.latestpattern=re.compile(r"/latest(?:\/|\?cb).*$")
        super().__init__(parent)
        #Gets the files (Tracking progress)
        files = os.listdir(path)
        #Finds the name of the file in the future and checks if that file is already downloaded. Also seperates that from the images.
        self.name = lambda x: '-'.join(x.strip().split('/')[4::])
        self.downloadlist = [url for url in urls if (self.cleaningstring(self.name(url)) + ".html" not in files)]
        self.imglist = [i for i in files if not (".html" in i)]
        self.i = 1
        self.path=path
        self.paused=False
        self.imgfilter=lambda img:(img.get('data-image-key') not in self.imglist)
        self.pause_event=asyncio.Event()
        self.pause_event.set()
        self.downvid=[]
        self.nameimg = re.compile(r"\.(?:(jpg|jpeg|png|gif|svg))$", re.IGNORECASE)

    def pause(self,arg=None):
        self.pause_event.clear()
        self.log_message.emit("Downloads paused")

    def resume(self,arg=None):
        self.pause_event.set()
        self.log_message.emit("Downloads resumed")

    def cleaningstring(self,urlname):
        urlname = urlname.replace('/', '-')
        urlname = urlname.replace('.', ' ')
        urlname = urlname.replace(':', ' ')
        return urlname

    async def audiodownload(self,path,audio,session):
        """"""
        await self.pause_event.wait()
        au_url = audio["src"]

        if bool(self.latestpattern.search(au_url)):
            au_url = self.latestpattern.split(au_url)[0] + "/latest/"
        a=audio.find("a",{"href":True})
        name=a["href"].strip().split(":")[-1]
        au=await session.get(au_url)
        try:
            if au. status_code == 200:
                data=au.content
                file = f"{path}{name}"
                with open(file, "wb") as aufile:
                    aufile.write(data)
                self.log_message.emit(f"downloaded {name}")
                self.imglist.append(name)
        except Exception as e:
            self.log_message.emit(str(e))
            print(str(e))
            self.i += 1
            self.progress_updated.emit(self.i)
            self.log_message.emit("Continue?")
                #self.pause()

    async def imgdownload(self,path,image,session):
        """This is for downloading images.
        It takes the path of the file, the image element and the async session as inputs
        It gets the source and if theres a data-src, it gets that as well.
        From there it makes it the latest edition to return it to the normal scale.
        Finally it gets the image and saves it in the path as it's name which it gets
        from the data-image-key"""
        await self.pause_event.wait()
        img_url = image.get("src")
        if img_url == None or img_url.startswith("data:image"):
            img_url = image.get("data-src")

        if bool(self.latestpattern.search(img_url)):
            img_url = self.latestpattern.split(img_url)[0] + "/latest/"
        img=await session.get(img_url)
        try:
            if img.status_code == 200:
                name = image.get('data-image-key')
                if not(bool(self.nameimg.search(name))):
                    name+=".webp"
                data=img.content
                file = f"{path}{name}"
                with open(file, "wb") as imagefile:
                    imagefile.write(data)
                self.log_message.emit(f"downloaded {name}")
                self.imglist.append(name)
        except Exception as e:
            self.log_message.emit(str(e))
            print(str(e))
            self.i += 1
            self.progress_updated.emit(self.i)
            self.log_message.emit("Continue?")
                #self.pause()


    async def download(self,url,session):
        """This is the main download operation which runs every single url.
        It takes the url and the session as parameters and using it, it gets
        all the images, videos if there are any and then downloads them all
        From there it finally downloads the page in full"""
        await self.pause_event.wait()
        try:
            res=await session.get(url)
            if (res.status_code==200):
                urlname = self.name(url)
                urlname = urlname.replace('/', '-')
                if "." in urlname:
                    urlname=urlname.replace('.','_')
                urlname=urlname.replace(':','_')

                html=res.content
                soup=BeautifulSoup(html,'html.parser')
                tasks=[self.imgdownload(self.path,img,session) for img in soup.find_all('img',{"data-image-key":True}) if self.imgfilter(img)]
                tasks2=[]
                for x in soup.find_all("audio",{"src":True}):
                    a=x.find("a",{"href":True})
                    name=a["href"].strip().split(":")[-1]
                    if name not in self.imglist:
                        tasks2.append(self.audiodownload(self.path,x,session))
                tasks=tasks+tasks2
                if tasks:
                    await asyncio.gather(*tasks)
                videos= [i for i in soup.find_all('a',{"src":True,"class":re.compile("video")})]+[c for c in soup.find_all("video",{"src":True})]
                if videos:
                    self.downvid.append(url)
                    #videos=[self.videodownload(session,vid) for vid in videos]
                    #await asyncio.gather(*videos)
                with open(f"{self.path}{urlname}.html", "w", encoding="utf-8") as htmlfile:
                    htmlfile.write(soup.prettify())
                # Updates progress
                self.log_message.emit(f"Finished downloading {urlname}")
                self.progress_updated.emit(self.i)
                self.i += 1
            else:
                res.raise_for_status()
        except Exception as e:
            self.log_message.emit(str(e))
            print(str(e))
            self.i+=1
            self.progress_updated.emit(self.i)
            self.log_message.emit("Continue?")
            #self.pause()

    async def main(self):
        """ This is the main function. It times how long it takes and runs it all in one session."""
        start=time.time()
        sem=asyncio.BoundedSemaphore(9)
        resolver = aiohttp.AsyncResolver(nameservers=["8.8.8.8", "8.8.4.4"])
        connector = aiohttp.TCPConnector(resolver=resolver)
        async def sem_download(url,session):
            async with sem:
                await self.download(url,session)

        async with AsyncSession(impersonate="firefox" ,max_clients=15,trust_env=True) as session:
            tasks=[]
            session.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"})
            for url in self.downloadlist:
                await self.pause_event.wait()
                tasks.append(asyncio.create_task(sem_download(url,session)))
            await asyncio.gather(*tasks)
        end=time.time()
        print(end-start)
        print(self.downvid)
        if self.downvid:
            x=Videos(self.downvid,self.path)
            x.downloader()
        self.finished.emit()