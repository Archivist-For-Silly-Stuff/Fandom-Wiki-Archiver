import os
import pathlib
import re
import glob
import bs4
import time
import curl_cffi.requests
from curl_cffi.requests import AsyncSession
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from bs4 import BeautifulSoup
import asyncio
import traceback
import aiofiles
from crawlgui import csvfiles
"""I am met with a simple problem.
We are using the image-data-key to find the name of an image. This image name can be like:
SANS
and
sans
However the files being saved evaluate SANS==sans because they're rendered in lower letters
So, for finding the file names I have been using this convention where I append the progress bar wheel to find if they are repeated.
I could use a dict to maintain this same format, yes.
duplicates={
image.lower():[data-image-key list]
}
name translation:
name=image+duplicates[image.lower()].index(image)
for (key,item) in self.images:
    if key not in duplicates:
        duplicates[key.lower()]=item
    else:
        
        
images:dict[str|list[tag,bool]]
images:dict(name:[<tag object>,Linked])
"""


class asyncdownloader(QObject):
    log_message = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal()
    newrange = pyqtSignal(int)
    sendcsv=pyqtSignal(csvfiles)

    def __init__(self, path, urls, domain, parent=None):
        super().__init__(parent)
        #Gets the files (Tracking progress)
        self.path = pathlib.Path(path)
        self.files = os.listdir(self.path)
        self.resources = {file for file in self.files if ".html" not in file}
        self.csvfile:csvfiles = urls
        self.urlslist:list[dict] = self.csvfile.getsites()
        self.allowed_domain=domain
        self.filepointer=open(self.path.joinpath("error.log"),"w",encoding="utf-8")

        #self.downloadlist={url:val for (url,val) in urls.items() if not(val["Downloaded"]) and (val["name"] not in self.files)} #and (val["name"] not in self.files)
        """#Finds the name of the file in the future and checks if that file is already downloaded. Also seperates that from the images.
        self.name = lambda x: '-'.join(x.strip().split('/')[4::])
        self.downloadlist = [url for url in urls if (self.cleaningstring(self.name(url)) + ".html" not in self.files)]"""
        #self.imglist = {i for i in self.files if not (".html" in i)}
        #self.newfilter=re.compile(r"|".join(self.imglist))

        self.i = 1
        #self.path=path
        self.paused = False

        #self.imglist = {i for i in self.files if not (".html" in i)}

        self.pause_event = asyncio.Event()
        self.pause_event.set()

        #self.alock = asyncio.Lock()
        self.count=0
        self.retries = []

        self.unlinkedmedia:list[dict[str,str]]=self.csvfile.getmedia()
        print(self.unlinkedmedia)
        self.unique_tags={}
        self.headers:dict={}

    def aufilter(self, au: bs4.Tag):
        a = au.find("a", {"href": True})
        name = a["href"].strip().split(":")[-1]
        return name

    def pause(self, arg=None):
        self.pause_event.clear()
        self.log_message.emit("Downloads paused")

    def resume(self, arg=None):
        self.pause_event.set()
        self.log_message.emit("Downloads resumed")

    def cleaningstring(self, urlname: str) -> str:
        urlname = urlname.replace('/', '-')
        urlname = urlname.replace('.', '_')
        urlname = urlname.replace(':', ' ')
        return urlname


    async def main(self):
        """ This is the main function. It times how long it takes and runs it all in one session."""
        start = time.time()
        sem = asyncio.BoundedSemaphore(25)

        async def sem_download(semurl: dict[str, str], semsession: curl_cffi.requests.Session):
            async with sem:
                await self.download(semurl, semsession)
        async def sem_media(semurl: dict[str, str], semsession: curl_cffi.requests.Session):
            async with sem:
                await self.media(semurl, semsession)

        """async def imgdownload(imgurl: list, imsession: curl_cffi.requests.Session,ogurl:str):
            async with sem:
                await self.imgdownload(imgurl, imsession,ogurl)

        async def audownload(auurl: str, ausession: curl_cffi.requests.Session,auog:str):
            async with sem:
                await self.audiodownload(auurl, ausession,auog)
        async def videodownload(vidurl: str, vidsession: curl_cffi.requests.Session,vidog:str):
            async with sem:
                await self.videodownload(vidurl, vidsession,vidog)
"""
        try:
            async with AsyncSession(impersonate="firefox", max_clients=5) as session:
                tasks = []
                for url in self.urlslist:
                    await self.pause_event.wait()
                    tasks.append(asyncio.create_task(sem_download(url, session)))

                for media in self.unlinkedmedia:
                    await self.pause_event.wait()
                    tasks.append(sem_media(media,session))

                if tasks:
                    await asyncio.gather(*tasks)
            """while self.retries:
                async with AsyncSession(impersonate="chrome", max_clients=5) as session:
                    tasks = []
                    # breakpoint()
                    for url in self.retries:
                        await self.pause_event.wait()
                        tasks.append(asyncio.create_task(sem_download(url, session)))
                    if tasks:
                        await asyncio.gather(*tasks)"""

            end = time.time()
            print(end - start)

            #TODO:MAKE IT WORK
            """if self.downvid:
                x=Videos(self.downvid,self.path)
                x.downloader()"""

        except Exception as e:
            self.log_message.emit(str(e))
        finally:
            self.csvfile.save_media(self.path.joinpath(f"csv_{self.allowed_domain.split(".")[0]}_media.csv"))
            self.csvfile.save_urls(self.path.joinpath(f"csv_{self.allowed_domain.split(".")[0]}.csv"))
            self.filepointer.close()
            self.finished.emit()
            self.sendcsv.emit(self.csvfile)


    async def download(self, url: dict[str,str], session: curl_cffi.requests.Session):
        """This is the main download operation which runs every single url.
        It takes the url and the session as parameters and using it, it gets
        all the images, videos if there are any and then downloads them all
        From there it finally downloads the page in full"""
        await self.pause_event.wait()
        urlname = url["name"]
        #TODO:Deal with files that technically have the same name (different caps) - (not )Done
        #if urlname.lower()+".html" in self.files:
        #   urlname+=str(self.i)
        #print(urlname)
        for turn in range(3):
            try:
                res:curl_cffi.requests.Response = await session.get(url['site'])
                if res.status_code == 200:
                    html = res.content
                    soup = BeautifulSoup(html, 'html.parser')
                    """                    for img in soup.find_all("img",{"data-image-key":True}):
                        name=img['data-image-key']
                        if name not in self.unique_image_list:
                            self.unique_image_list.update(name)
                            modname=name
                            if name.lower() in self.images:
                                modname=self.nameimg.search(name)
                                if not modname:
                                    modname=f"{name}({self.count}).webp"
                                else:
                                    modname=modname.group(1)+f"({self.count})."+modname.group(2)
                                self.count+=1
                            if modname not in self.resources:
                                src=img.get('src')
                                self.images[name]=[src
                                                   if src and not(src.startswith("data:image"))
                                                   else img.get('data-src')
                                                    ,False,modname]
                    #self.images.update(self.unique_tags)

                    aulist:dict[str,list] = {self.aufilter(au): [au["src"], False]
                              for au in soup.find_all("audio", {"src": True})}
                    self.audio.update(aulist)
                    videos = {self.aufilter(video):[video["src"],False]
                              for video in soup.find_all("video", {"src": True})}
                    self.downvid.update(videos)"""
                    async with aiofiles.open(self.path.joinpath(urlname), "w", encoding="utf-8") as htmlfile:
                        await htmlfile.write(soup.prettify())
                    # Updates progress
                    self.log_message.emit(f"Finished downloading {urlname}")
                    self.progress_updated.emit(self.i)
                    self.i += 1
                    self.csvfile.update_url_download(urlname)
                    for row in self.urlslist:
                        if urlname == row["name"]:
                            row["downloaded"] = "True"
                            #print(row)
                            break
                    break
                else:
                    retry = res.headers.get("Retry-After")
                    if retry:
                        self.log_message.emit(f"Too many requests. Waiting {retry}")
                        await asyncio.sleep(int(retry))
                        continue
                    res.raise_for_status()
            except Exception as e:
                #self.log_message.emit(str(e))
                print(f"Error downloading {urlname}: {str(e)}\n{traceback.format_exc()}",file=self.filepointer,)
                self.log_message.emit(f"Failed to download {urlname}. Will try again")
                self.log_message.emit("Continue?")
                self.pause()
        self.i += 1
        self.progress_updated.emit(self.i)

    async def media(self, media:dict[str,str],session:curl_cffi.requests.Session):
        await self.pause_event.wait()
        name=media["name"]
        src=media["source"]
        file=self.path.joinpath(name)
        if os.path.isfile(file):
            self.csvfile.update_media(name)
            self.i += 1
            self.progress_updated.emit(self.i)
            return
        for retry in range(3):
            try:
                res=await session.get(src)
                if res.status_code==200:
                    data=res.content
                    with open(file,"wb") as f:
                        f.write(data)
                    self.resources.add(name)
                    self.csvfile.update_media(name)
                    for row in self.unlinkedmedia:
                        if row["name"]==name:
                            row["downloaded"]="TRUE"
                            break
                    self.log_message.emit(f"Finished downloading {name}")
                    break
                else:
                    retry = res.headers.get("Retry-After")
                    if retry:
                        self.log_message.emit(f"Too many requests. Waiting {retry}")
                        await asyncio.sleep(int(retry))
                        continue
                    if res.status_code==404:
                        self.log_message.emit(f"{src}")
                    res.raise_for_status()
            except Exception as e:
                self.log_message.emit(f"Error downloading {name}")

                print(f"Error downloading {name}: {str(e)}\n{traceback.format_exc()}\n Trying again",file=self.filepointer)
                #self.log_message.emit("Continue?")
                #self.pause()
                #self.log_message.emit(f"Failed to download {src}")
        self.i += 1
        self.progress_updated.emit(self.i)


    async def imgdownload(self, image:list, session, ogurl:str):
        """This is for downloading images.
        It takes the path of the file, the image element and the async session as inputs
        It gets the source and if theres a data-src, it gets that as well.
        From there it makes it the latest edition to return it to the normal scale.
        Finally it gets the image and saves it in the path as it's name which it gets
        from the data-image-key"""
        await self.pause_event.wait()
        img_url = image[0]
        if self.latestpattern.search(img_url):
            img_url = self.latestpattern.split(img_url)[0] + "/latest/"
        img:curl_cffi.requests.Response = await session.get(img_url)
        for retry in range(3):
            try:
                if img.status_code == 200:
                    name = image[2]
                    file=self.path.joinpath(name)
                    """if name.lower() in self.resources:
                        name+=str(self.i)"""  #TODO:Deal with duplicates
                    if os.path.isfile(file):
                        return
                    data = img.content

                    with open(file, "wb") as imagefile:
                        imagefile.write(data)
                        imagefile.flush()
                    self.log_message.emit(f"downloaded {name}")
                    self.images[ogurl][1] = True
                    self.resources.add(name)
                    break
                else:
                    retry=img.headers.get("Retry-After")
                    if retry:
                        self.log_message.emit(f"Too many requests. Waiting {retry}")
                        await asyncio.sleep(int(retry))
                        continue
                    img.raise_for_status()
            except Exception as e:
                self.log_message.emit(str(e))
                print(f"Error downloading {img_url}: {str(e)}\n{traceback.format_exc()}")
                self.log_message.emit("Continue? Press resume to unpause")
                self.pause()
                #await self.pause_event.wait()
        self.i += 1
        self.progress_updated.emit(self.i)

    async def audiodownload(self, audio:str, session:curl_cffi.requests.Session,ogurl:str):
        """Downloads any audio files present on the site"""
        await self.pause_event.wait()
        au_url = audio
        if bool(self.latestpattern.search(au_url)):
            au_url = self.latestpattern.split(au_url)[0] + "/latest/"
        name = ogurl
        au:curl_cffi.requests.Response = await session.get(au_url)
        for retry in range(3):
            try:
                if au.status_code == 200:
                    data = au.content
                    file = self.path.joinpath(name)
                    with open(file, "wb") as aufile:
                        aufile.write(data)
                    self.log_message.emit(f"downloaded {name}")
                    self.resources.add(name)
                    break
                else:
                    retry = au.headers.get("Retry-After")
                    if retry:
                        self.log_message.emit(f"Too many requests. Waiting {retry}")
                        await asyncio.sleep(int(retry))
                        continue
                    au.raise_for_status()
            except Exception as e:
                self.log_message.emit(str(e))
                print(f"Error downloading {au_url}: {str(e)}\n{traceback.format_exc()}. Trying again")
                self.log_message.emit("Continue?")
                self.pause()
        self.i += 1
        self.progress_updated.emit(self.i)

    async def videodownload(self, video:str, session:curl_cffi.requests.Session,ogurl:str):
        """Downloads any audio files present on the site"""
        await self.pause_event.wait()
        au_url = video
        if bool(self.latestpattern.search(au_url)):
            au_url = self.latestpattern.split(au_url)[0] + "/latest/"
        name = ogurl
        au:curl_cffi.requests.Response = await session.get(au_url)
        for retry in range(3):
            try:
                if au.status_code == 200:
                    data = au.content
                    file = self.path.joinpath(name)
                    with open(file, "wb") as vidfile:
                        vidfile.write(data)
                    self.log_message.emit(f"downloaded {name}")
                    self.resources.add(name)
                    break
                else:
                    retry = au.headers.get("Retry-After")
                    if retry:
                        self.log_message.emit(f"Too many requests. Waiting {retry}")
                        await asyncio.sleep(int(retry))
                        continue
                    au.raise_for_status()
            except Exception as e:
                self.log_message.emit(str(e))
                print(f"Error downloading {au_url}: {str(e)}\n{traceback.format_exc()}. Trying again")
                self.log_message.emit("Continue?")
                self.pause()
        self.i += 1
        self.progress_updated.emit(self.i)


    async def embedded_video(self, ses, file):
        await self.pause_event.wait()
        down = await ses.get(file)
        soup = BeautifulSoup(down.text, "lxml")
        iframe = soup.find("iframe", {"src": re.compile(rf"^https://youtube.come/.*$")})
        if iframe:
            you = iframe.get("src")
            output_template = os.path.join(self.path, '%(title)s.%(ext)s')
            process = await asyncio.create_subprocess_exec(
                'yt-dlp',
                '--no-playlist',
                '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                '-o', output_template,
                "--cookies",
                you,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for the download to finish
            stdout, stderr = await process.communicate()

    async def collect(self, ses, soup):
        vid = soup.find_all("video", {"src": True})
        self.vidlist.extend([video["src"] for video in vid])
