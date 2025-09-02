import logging
# Allows us to delete any copies of html
import os
# Helps to join source url's with reference url's
import os.path
from urllib.parse import urljoin
# For downloading files
import requests
# Regex pattern creation
import re
# Parsing the HTML
from bs4 import BeautifulSoup
import faulthandler

faulthandler.enable()
# Linking the css, images to the HTML along with deleting any and all trackers
import linker
# Downloading the images
import alt_html_downloader

# Configure logging
logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)
import sys
# Graphs
import networkx
import csv
import time


class crawler:
    # Keeps a count of url's visited, downloaded and what domains are allowed. Besides the path to be saved too.
    # It also checks if you wanna make a graph
    def __init__(self, allowed_domain, path, urls=[], network=False):
        self.visited_urls = []
        self.urls_to_visit = urls
        self.allowed_domain = allowed_domain
        self.network = network
        self.path = path

    # Uses requests to get the url
    def download_url(self, url):
        response = requests.get(url)
        return response.text

    # Uses BeautifulSoup to find all the links in the document.
    def get_linked_url(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            path = link.get('href')
            if path and path.startswith('/'):
                path = urljoin(url, path)
                if bool(self.patternscrap.match(path)):
                    yield path

    # Adds this to the list of URL's to be visited.
    def add_url_to_visit(self, url):
        if (url not in self.visited_urls) and (url not in self.urls_to_visit):
            self.urls_to_visit.append(url)

    # Downloads the url and adds them to the url's to be visited
    def crawl(self, url):
        html = self.download_url(url)
        for href in self.get_linked_url(url, html):
            if href != None:
                if self.network:
                    self.graph.add_edge(url, href)
                self.add_url_to_visit(href)

    # The code is run
    def run(self):
        # Sets up graph if graphing is enable
        if self.network:
            self.graph = networkx.DiGraph()
        # Sets up the format of the url to be checked
        self.patternscrap = re.compile(
            rf"^https:\/\/{self.allowed_domain.split('.')[0]}\.fandom\.com\/wiki\/(?:"
            r"[A-Za-z0-9_()%\-]+"
            r"|Category:[A-Za-z0-9_()%\-]+"
            r")$",
            re.IGNORECASE
        )
        #si = GUI.sidewindow()
        # while loop so it keeps running till all URL's are visited
        while self.urls_to_visit:
            url = self.urls_to_visit.pop(0)
            if url not in self.visited_urls:
                try:
                    logging.info(f'Crawling: {url}')
                    #si.login(f'Crawling: {url}')
                    self.crawl(url)
                except Exception as e:
                    logging.exception(f'Failed to crawl: {url} because {e}')
                    #si.login(f'Failed to crawl: {url} because {e}')

                finally:
                    self.visited_urls.append(url)
        self.visited_urls = list(filter(lambda x: "Category" not in x, self.visited_urls))
        if self.network:
            networkx.draw(self.graph)
        alt_html_downloader.HTML_Download(self.visited_urls, path=self.path)

    def download(self):
        breakpoint()
        self.patternscrap = re.compile(
            rf"^https:\/\/{self.allowed_domain}\/wiki\/"
            r"[^:]+$",
            re.IGNORECASE
        )
        if not(os.path.isfile(self.path+"url.csv")):
            if "Local_Sitemap" in self.urls_to_visit[0]:
                sitemaplist=[]
                while self.urls_to_visit:
                    self.url = self.urls_to_visit.pop(0).strip()
                    sitemaplist.append(self.url)
                    html=requests.get(self.url)
                    soup=BeautifulSoup(html.text,"html.parser")
                    a=soup.find_all('a')
                    sitemap=re.compile(rf"^https:\/\/{self.allowed_domain}/wiki/Local_Sitemap(?:\?namefrom=[a-zA-Z0-9%/\-_/\\+()]+|)$",
                                       re.IGNORECASE)
                    for i in a:
                        if i.has_attr('href'):
                            href=i.get('href')
                            link=urljoin(rf"https://{self.allowed_domain}/wiki/",href)
                            if bool(sitemap.match(link)) and (link not in self.urls_to_visit) and (link not in sitemaplist):
                                self.urls_to_visit+=[link]
                                sitemaplist.append(self.url)
                            elif bool(self.patternscrap.match(link)) and ("Local_Sitemap" not in link):
                                self.visited_urls+=[link]
                breakpoint()
                if not(os.path.isfile(self.path+"url.csv")):
                    with open(self.path+"url.csv","w") as fp:
                        writer=csv.DictWriter(fp,fieldnames=['URL','Linked'])
                        writer.writeheader()
                        self.visited_urls=list(set(self.visited_urls))
                        for i in self.visited_urls:
                            writer.writerow({'URL':i,'Linked':False})
        elif os.path.isfile(self.path+"url.csv"):
            fp = open(self.path + "url.csv", "r", encoding='utf-8')
            Reader=csv.DictReader(fp)
            for row in Reader:
                self.visited_urls.append(row['URL'])
            fp.close()
        alt_html_downloader.HTML_Download(self.visited_urls,path=self.path)
        time.sleep(5)
        breakpoint()
        print(self.visited_urls)

        linking=linker.linker(path=self.path,domain=self.visited_urls[0].split('/')[2])
        linking.link()






if __name__ == "__main__":
    # Takes multiple url inputs. This feature hasn't been tested yet
    if "," in sys.argv[2]:
        l = sys.argv[2].split(",")
    else:
        l = [sys.argv[2]]
    # Corrects the path so it's more easily used by the program
    sys.argv[3] = rf"{sys.argv[3]}"
    if sys.argv[3][-1] != ('\\'):
        sys.argv[3] += "\\"
    path = sys.argv[3]
    # Crawling and downloading the data
    x = crawler(sys.argv[1], urls=l, path=sys.argv[3])
    x.run()
    # linking everything and downloading css
    y = linker.linker(sys.argv[3], sys.argv[1])
    y.link()
    # Deleting any copies
    ls = os.listdir(path)
    for i in ls:
        if not ("edited_" in i or not (".html" in i)):
            os.remove(path + i)
