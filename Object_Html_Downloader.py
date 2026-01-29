import os
import re
import time
from urllib.parse import urljoin

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from bs4 import BeautifulSoup
import logging
import requests
#from GUI import sidewindow
import progress
logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)


class HTML_Downloader(QObject):
    #Deals with logging the Messages and updating the progress using the pyqt strings module.
    log_message=pyqtSignal(str)
    progress_updated=pyqtSignal(int)
    finished=pyqtSignal()
    pause=pyqtSignal(int)
    def __init__(self,path,urls,parent=None):
        #Session helps download the url.
        self.session=requests.session()
        self.session.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"})
        self.ispaused=False
        #Checks that the latest version of an image is downloaded.
        self.latestpattern=re.compile(r"/latest(?:\/|\?cb).*$")
        super().__init__(parent)
        #Gets the files (Tracking progress)
        files = os.listdir(path)
        #Finds the name of the file in the future and checks if that file is already downloaded. Also seperates that from the images.
        self.name = lambda x: '/'.join(x.strip().split('/')[4::])
        self.downloadlist = [url for url in urls if (self.name(url) + ".html" not in files)]
        self.imglist = [i for i in files if not (".html" in i)]
        self.i = 1
        self.path=path
        self.paused=False
        #Why am I using two sessions?
        self.video=requests.session()
        self.video.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"})

    def paused(self):
        self.ispaused=True

    def resumed(self):
        self.ispaused=False

    def video_downloader(self,video,path):
        src=video.get('src')
        if video.has_attr('data-src'):
            src=video.get('data-src')
        name=src.split("/")[-3]
        if bool(self.latestpattern.search(src)):
            src=self.latestpattern.split(src)[0]+"/latest/"
        vid=self.video.get(src,stream=True)
        vid.raise_for_status()
        file=f"{path}{name}"
        self.log_message.emit(f"Downloading {name}")
        with open(file,"wb") as vidfile:
            for chunk in vid.iter_content(chunk_size=2048*4):
                vidfile.write(chunk)



    def image_downloader(self,image,path):
        img_url = image.get("src")
        if img_url == None or img_url.startswith("data:image"):
            img_url = image.get("data-src")
        if bool(self.latestpattern.search(img_url)):
            img_url=self.latestpattern.split(img_url)[0]+"/latest/"
        img = self.session.get(f"{img_url}")
        if img.status_code == 200:
            name=image.get('data-image-key')
            self.log_message.emit(f"Downloading {name}")
            #downloader.log(f"Downloading {image.get('data-image-key')}")
            file = f"{path}{name}"
            with open(file, "wb") as imagefile:
                imagefile.write(img.content)
            self.imglist.append(name)

    @pyqtSlot()
    def HTML_Download(self):
        #Checks the downloadlist used
        print(self.downloadlist)
        for url in self.downloadlist:
            try:
                #downloader.updatebar(i)
                #Get's the name of the url and requests the page.
                while self.ispaused:
                    time.sleep(0)
                urlname=self.name(url)
                if "/" in urlname:
                    urlname=urlname.replace('/','-')
                while self.ispaused:
                    time.sleep(0)

                html = self.session.get(url).text
                soup = BeautifulSoup(html, "html.parser")
                #downloader.updateprog(f"Downloading {url}")
                #When successful it starts to download.
                self.log_message.emit(f"Downloading {url}")

                #Downloading all images after validating that the image hasn't be downloaded yet
                for img in soup.find_all('img'):
                    if img.has_attr('data-image-key') and (img.get('data-image-key') not in self.imglist):
                        self.image_downloader(img,self.path)

                #Function to download video. Yet to test.
                for video in soup.find_all('video'):
                    video.findChild('a')
                    self.video_downloader(video,self.path)


                #Downloads the file
                with open(f"{self.path}{urlname}.html","w",encoding="utf-8") as htmlfile:
                    htmlfile.write(soup.prettify())
                #Updates progress
                self.progress_updated.emit(self.i)
                self.i+=1

            except Exception as e:
                logging.warning(e)
        self.session.close()
        self.finished.emit()
        #downloader.close()
