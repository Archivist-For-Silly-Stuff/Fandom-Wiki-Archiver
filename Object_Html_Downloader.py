import os
import re
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
    log_message=pyqtSignal(str)
    progress_updated=pyqtSignal(int)
    finished=pyqtSignal()
    def __init__(self,path,urls,parent=None):
        self.latestpattern=re.compile(r"latest(?:\/|\?cb).*$")
        super().__init__(parent)
        files = os.listdir(path)
        self.named = lambda y: y.strip().split('/')[-1]
        downloadlist = [self.named(url) for url in urls if (self.named(url) + ".html" not in files)]
        self.imglist = [i for i in files if not (".html" in i)]
        filelist = [i for i in files if (".html" in i)]
        downloadlist = list(set(downloadlist) - set(filelist))
        domain = urls[0].split("/")
        domain = '/'.join(domain[0:len(domain) - 1]) + '/'
        urlnames = lambda x: domain+x
        self.downloadlist = list(map(urlnames, downloadlist))
        self.i = 1
        self.path=path


    def image_downloader(self,image,path):
        if image.has_attr("data-image-key"):
            img_url = image.get("src")
            if img_url == None or img_url.startswith("data:image"):
                img_url = image.get("data-src")
            if self.latestpattern.match(img_url):
                img_url=self.latestpattern.split(img_url)[0]+"latest/"
            img = requests.get(f"{img_url}")
            if img.status_code == 200 and (img_url not in self.imglist):
                logging.info(f"Downloading {image.get('data-image-key')}")
                self.log_message.emit(f"Downloading {image.get('data-image-key')}")
                #downloader.log(f"Downloading {image.get('data-image-key')}")
                file = f"{path}{image.get('data-image-key')}"
                with open(file, "wb") as imagefile:
                    imagefile.write(img.content)
                self.imglist.append(img_url)

    @pyqtSlot()
    def HTML_Download(self):
        for url in self.downloadlist:
            try:
                #downloader.updatebar(i)
                name=self.named(url)
                html = requests.get(url).text
                soup = BeautifulSoup(html, "html.parser")
                #downloader.updateprog(f"Downloading {url}")
                self.log_message.emit(f"Downloading {url}")
                logging.info(f"Downloading {url}")
                for image in soup.find_all("img"):
                    self.image_downloader(image,self.path)
                with open(f"{self.path}{name}.html","w",encoding="utf-8") as htmlfile:
                    htmlfile.write(soup.prettify())
                self.progress_updated.emit(self.i)
                self.i+=1

            except Exception as e:
                logging.warning(e)
        self.finished.emit()
        #downloader.close()
