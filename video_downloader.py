import logging
# Allows us to delete any copies of html
import os
# Helps to join source url's with reference url's
import os.path
import time
import undetected_chromedriver as uc
from time import sleep
from urllib.parse import urljoin, urlencode
# For downloading files
import requests
# Regex pattern creation
import re
import yt_dlp as yt
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import curl_cffi
#from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QWaitCondition
# Parsing the HTML
from bs4 import BeautifulSoup
import faulthandler
from fake_useragent import UserAgent

class Videos:
    def __init__(self,videos,path):
        self.videos=videos
        self.ua=UserAgent(browsers=["chrome"],os=["Windows"],platforms=["desktop"])
        self.path=path
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"}
        self.ydl_opts = {
            'format': 'best',
            'merge_output_format': 'mp4',
            'outtmpl': '%(title)s.%(ext)s',
            'verbose':True,
            'noplaylist': True,
            "paths":{"home":path},
            "":r"C:\Users\raksh\.deno\bin\deno.exe",
            "sleep_interval":5,
            "max_sleep_interval":10
        }
        self.chops=uc.ChromeOptions()
        self.chops.add_argument('--window-size=1920,1080')
        #self.chops.add_argument('--headless')


    def downloader(self):
        driver=uc.Chrome(options=self.chops,version_main=146)
        with curl_cffi.Session(impersonate="chrome") as ses:
            for video in self.videos:
                html=ses.get(video)
                #breakpoint()
                soup=BeautifulSoup(html.text,"html.parser")
                a=soup.find_all("a",{ "href":True , "class":re.compile("video")})
                vids=soup.find_all("video",{"src":True})
                #print(a)
                    #if a:
                        #ht=ses.get(a[0]["href"])
                        #soup=BeautifulSoup(ht.content,"html.parser")
                        #print(soup.prettify())
                files=list(map(lambda x:video+'?'+urlencode({"file":x.split(':')[-1]}),[i["href"] for i in a]))
                print(files)
                if files:
                    videofile=[]
                    for file in files:
                        #chrome_options = Options()
                            #f=ses.get(file)
                        #breakpoint()
                        print(file)
                        driver.get(file)
                        time.sleep(5)
                        ytp=""
                        while not ytp:
                            html = driver.page_source
                            iframesoup=BeautifulSoup(html,"html.parser")
                            ytp=iframesoup.find("iframe",{"src":re.compile(r"(?:youtube|youtu\.be)")})
                            time.sleep(3)
                        #print(ytp,file)

                        src=ytp["src"].split('/')
                        watch=urlencode({"v":src[-1]})
                        src='/'.join(src[:3])+'/watch?'+watch
                        videofile.append(src)
                        #print(src)
                    with yt.YoutubeDL(self.ydl_opts) as downloader:
                        downloader.download(videofile)
                if vids:
                    for vid in vids:
                        h=vid["src"]
                        a=vid.find("a",{"href":True})
                        print(self.path+a["href"].strip().split(":")[-1])
                        with open(self.path+a["href"].strip().split(":")[-1],"wb") as fp:
                            res=requests.get(h)
                            fp.write(res.content)

            driver.quit()



if __name__=="__main__":
    x=Videos(["https://weegeepedia.fandom.com/wiki/Elmo","https://venturebrothers.fandom.com/wiki/Venture_Brothers_Wiki"],"C:\\personal stuff\\repos\\Fandom-Wiki-Archiver\\venv\\testvideos\\")
    x.downloader()