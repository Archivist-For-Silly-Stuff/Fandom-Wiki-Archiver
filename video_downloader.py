import logging
# Allows us to delete any copies of html
import os
# Helps to join source url's with reference url's
import os.path
import time
from time import sleep
from urllib.parse import urljoin, urlencode
# For downloading files
import requests
# Regex pattern creation
import re
import yt_dlp as yt
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QWaitCondition
# Parsing the HTML
from bs4 import BeautifulSoup
import faulthandler

class Videos:
    def __init__(self,videos,path):
        self.videos=videos
        self.path=path
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"}
        self.ydl_opts = {
            'format': 'best',
            'merge_output_format': 'mp4',
            'outtmpl': '%(title)s.%(ext)s',
            'verbose':True,
            'noplaylist': True,
            "paths":{"home":path}
        }
    def downloader(self):
        with requests.Session() as session:
            session.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"})
            driver = webdriver.Chrome()
            for video in self.videos:
                html=requests.get(video)
                soup=BeautifulSoup(html.text,"html.parser")
                a=soup.find_all("a",{ "href":True, "class":re.compile("video")})
                vids=soup.find_all("video",{"src":True})
                files=list(map(lambda x:video+'?'+urlencode({"file":x.split(':')[-1]}),[i["href"] for i in a]))
                print(files)
                if files:
                    for file in files:
                        #chrome_options = Options()
                        driver.get(file)
                        time.sleep(10)
                        html = driver.page_source
                        iframesoup=BeautifulSoup(html,"html.parser")
                        print(iframesoup.prettify())
                        ytp=iframesoup.find("iframe",{"src":re.compile("youtube|youtu.be")})
                        src=ytp["src"].split('/')
                        watch=urlencode({"v":src[-1]})
                        src='/'.join(src[:3])+'/watch?'+watch
                        with yt.YoutubeDL(self.ydl_opts) as downloader:
                            downloader.download(src)
                if vids:
                    for vid in vids:
                        h=vid["src"]
                        a=vid.find("a",{"href":True})
                        print(self.path+a["href"].strip().split(":")[-1])
                        with open(self.path+a["href"].strip().split(":")[-1],"wb") as fp:
                            res=requests.get(h)
                            fp.write(res.content)

            driver.quit()



if __name__=="main":
    x=Videos(["https://weegeepedia.fandom.com/wiki/Elmo"],"C:\\personal stuff\\repos\\Fandom-Wiki-Archiver\\venv\\testvideos\\")
    #x.downloader()