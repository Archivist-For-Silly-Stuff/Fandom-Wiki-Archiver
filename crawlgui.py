import logging
# Allows us to delete any copies of html
import os
# Helps to join source url's with reference url's
import os.path
import cloudscraper
from time import sleep
from urllib.parse import urljoin
# For downloading files
import requests
# Regex pattern creation
import re

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QWaitCondition
# Parsing the HTML
from bs4 import BeautifulSoup
import faulthandler

from soupsieve import SoupSieve


faulthandler.enable()


# Configure logging
logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)
import sys
# Graphs
import csv


class crawler(QObject):
    log=pyqtSignal(str)
    prog=pyqtSignal(int)
    sendurl=pyqtSignal(list)
    finish=pyqtSignal()
    pause=pyqtSignal(bool)
    # Keeps a count of url's visited, downloaded and what domains are allowed. Besides the path to be saved too.
    # It also checks if you wanna make a graph
    def __init__(self, allowed_domain, path, urls=[], parent=None):
        QObject.__init__(self,parent)
        print("p")
        breakpoint()
        self.session = cloudscraper.create_scraper(interpreter='nodejs',
                                                   delay=2,
                                                   debug=True,
                                                   browser={
                                                       'browser': 'firefox',
                                                       'platform': 'windows',
                                                       'mobile': False
                                                   })
        print("p")
        self.visited_urls = []
        self.urls_to_visit = urls
        self.allowed_domain = allowed_domain
        self.path = path
        self.ispaused=False
        self.mutex=QMutex()
        self.pausecon=QWaitCondition()
        self.sitemap = re.compile(rf"^https:\/\/{self.allowed_domain}/wiki/Local_Sitemap(?:\?namefrom=.+| )$",
                             re.IGNORECASE)
        self.urls=lambda i:urljoin(rf"https://{self.allowed_domain}/wiki/",i['href'])

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
        self.patternscrap = re.compile(
            rf"^https:\/\/{self.allowed_domain}\/wiki\/"
            r"[^:]+$",
            re.IGNORECASE
        )
        self.prog.emit(1)

        if not(os.path.isfile(self.path+"url.csv")):
            self.collectsites()

        elif os.path.isfile(self.path+"url.csv"):
            fp = open(self.path + "url.csv", "r", encoding='utf-8')
            Reader=csv.DictReader(fp)
            self.visited_urls = [row['URL'] for row in Reader]
            if not self.visited_urls:
                fp.close()
                self.collectsites()
            else:
                fp.close()
            self.prog.emit(2)
        self.sendurl.emit(self.visited_urls)
        self.session.close()
        self.finish.emit()

    @pyqtSlot()
    def collectsites(self):
        sitemaplist = [self.urls_to_visit[0]]

        while self.urls_to_visit:
            self.check_pause()
            self.url = self.urls_to_visit.pop(0).strip()
            self.log.emit(f"Collecting links from:{self.url}")
            sitemaplist.append(self.url)
            html = self.session.get(self.url)
            soup = BeautifulSoup(html.text, "html.parser")
            print(soup.prettify())
            a = soup.find_all('a', {"href": re.compile(r"^\/wiki\/(?!((Special:)|(Category:)|(User_blog:)|(File:))).*$")})
            # Uses URL join to connect with the main path
            print(a)
            self.listourl = list(map(self.urls, a))
            self.urls_to_visit = self.urls_to_visit + list(filter(
                lambda x: (bool(self.sitemap.match(x)) and (x not in self.urls_to_visit) and (x not in sitemaplist)),
                self.listourl))
            sitemaplist = sitemaplist + self.urls_to_visit
            self.visited_urls = self.visited_urls + list(
                filter(lambda x: ((x not in sitemaplist) and (x not in self.visited_urls)), self.listourl))

        self.prog.emit(2)
        sleep(3)

        with open(self.path + "url.csv", "w") as fp:
            # self.visited_urls=list(set(self.visited_urls))
            writer = csv.DictWriter(fp, fieldnames=['URL', 'Linked'])
            writer.writeheader()
            rows = list({'URL': x, 'Linked': False} for x in self.visited_urls)

            writer.writerows(rows)





