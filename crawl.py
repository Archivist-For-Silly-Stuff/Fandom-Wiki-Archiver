import logging
import os
from urllib.parse import urljoin
import requests
import re
from bs4 import BeautifulSoup
import linker
import alt_html_downloader
logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)
import sys
class crawler:
    def __init__(self,allowed_domain,path,urls=[]):
        self.visited_urls=[]
        self.urls_to_visit=urls
        self.allowed_domain=allowed_domain
        self.count_css=0
        self.rejection_list=[]
        self.pattern = re.compile(
            r"^https:\/\/greatbeegee\.fandom\.com\/wiki\/(?:[A-Za-z0-9_()%\-]+|File:[A-Za-z0-9_()%\-]+|Category:[A-Za-z0-9_()%\-]+)$",
            re.IGNORECASE
        )
        self.path=path

    def download_url(self,url):
        response=requests.get(url)
        return response.text
    def get_linked_url(self,url,html):
        soup=BeautifulSoup(html,'html.parser')
        for link in soup.find_all('a'):
            path=link.get('href')
            if path and path.startswith('/'):
                path=urljoin(url,path)
                yield path
            elif path and "static.wikia" in path:
                yield path

    def add_url_to_visit(self,url):

        """f=((url not in self.visited_urls) and (url not in self.urls_to_visit)
           and (self.allowed_domain in url) and not("auth.fandom.com" in url)
           and ("Special:" not in url) and ("?action:" not in url)
           and ("User:" not in url) and ("Message_Wall" not in url) and
           ("Blog:" not in url)  and ("User_blog" not in url)
           and ("/f/" not in url) and ("Talk:" not in url)
           and ("/Forum:" not in url) and ("Template:" not in url) and ("Category_talk" not in url)
           and ("MediaWiki" not in url) and ("Forum" not in url) and ("Greatbeegee_Wiki:" not in url)
           and ("Greatbeegee_Wiki_talk" not in url))"""
        """bool(self.pattern.match(url)) and"""
        if (url not in self.visited_urls) and (url not in self.urls_to_visit):
            self.urls_to_visit.append(url)

    def crawl(self,url):
        html=self.download_url(url)
        for url in self.get_linked_url(url,html):
            if url!=None and (url not in self.rejection_list):
                self.add_url_to_visit(url)
    def run(self):
        file_exts = r"(?:png|jpg|jpeg|gif|svg|webp)"
        patternscrap = re.compile(
            rf"^https:\/\/{self.allowed_domain.split('.')[0]}\.fandom\.com\/wiki\/(?:"
            r"[A-Za-z0-9_()%\-]+"
            r"|Category:[A-Za-z0-9_()%\-]+"
            r")$",
            re.IGNORECASE
        )
        patternimg = re.compile(
            rf"^https:\/\/greatbeegee\.fandom\.com\/wiki\/(?:"
            r"[A-Za-z0-9_()%\-]+"
            rf"|File:[A-Za-z0-9_()%\-]+\.(?:{file_exts})"
            r")$",
            re.IGNORECASE
        )
        patternimg_static=re.compile(rf"^https:\/\/static\.wikia\.nocookie\.net\/"
                                     rf"[a-zA-z0-9\-_]+\/images\/[a-zA-z0-9\-_\.\/\?\:\=]+$")
        while self.urls_to_visit:
            url=self.urls_to_visit.pop(0)
            if url not in self.visited_urls and (bool(patternscrap.match(url))):
                try:
                    logging.info(f'Crawling: {url}')
                    self.crawl(url)
                except Exception as e:
                    logging.exception(f'Failed to crawl: {url} because {e}')
                finally:
                    self.visited_urls.append(url)
            elif url not in self.visited_urls and (bool(patternimg.match(url))):
                self.visited_urls.append(url)
        self.visited_urls=list(filter(lambda x:"Category" not in x, self.visited_urls))
        self.visited_urls=list(map(lambda x:x+"\n",self.visited_urls))
        alt_html_downloader.HTML_Download(self.visited_urls,path=self.path)

    def download_css(self,url):
        html=requests.get(url).text
        soup=BeautifulSoup(html,"html.parser")
        path="C:\\Backups\\html\\"
        for css in soup.find_all("link", rel="stylesheet"):
            link=css.get("href")
            if "php" in link:
                php_download=requests.get("https://"+self.allowed_domain+link)
                with open(f"{path}css_{self.allowed_domain}_{self.count_css}.css","w",encoding='utf-8') as fp:
                    fp.write(php_download.text)
                self.count_css+=1


if __name__=="__main__":

    if "," in sys.argv[2]:
        l=sys.argv[2].split(",")
    else:
        l=[sys.argv[2]]
    sys.argv[3]=rf"{sys.argv[3]}"
    if sys.argv[3][-1]!=('\\'):
        sys.argv[3]+="\\"
    print(sys.argv)
    breakpoint()
    path=sys.argv[3]
    x=crawler(sys.argv[1],urls=l,path=sys.argv[3])
    x.run()
    y = linker.linker(sys.argv[3], sys.argv[1])
    y.link()
    list=os.listdir(path)
    for i in list:
        if not("edited_" in i or not(".html" in i)):
            os.remove(path+i)