import os
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import logging
import requests
#from GUI import sidewindow
import progress
logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)



def image_downloader(image,path):
    global imglist, downloader
    if image.has_attr("data-image-key"):
        img_url = image.get("src")
        if img_url == None or img_url.startswith("data:image"):
            img_url = image.get("data-src")
        img = requests.get(f"{img_url}")
        if img.status_code == 200 and (img_url not in imglist):
            logging.info(f"Downloading {image.get('data-image-key')}")
            downloader.log(f"Downloading {image.get('data-image-key')}")
            file = f"{path}{image.get('data-image-key')}"
            with open(file, "wb") as imagefile:
                imagefile.write(img.content)
            imglist.append(img_url)


def HTML_Download(urls, path):
    global imglist, downloader
    files=os.listdir(path)
    named=lambda y:y.strip().split('/')[-1]
    downloadlist=[named(url) for url in urls if (named(url)+".html" not in files)]
    imglist=[i for i in files if not(".html" in i)]
    filelist=[i for i in files if (".html" in i)]
    downloadlist=list(set(downloadlist)-set(filelist))
    urlnames=lambda x:urljoin(x,urls[0])
    downloadlist=list(map(urlnames,downloadlist))
    print(downloadlist)
    downloader=progress.progress(len(downloadlist),"Downloader")
    i=1
    for url in downloadlist:
        try:
            downloader.setprogress(i)
            name=named(url)
            html = requests.get(url).text
            soup = BeautifulSoup(html, "html.parser")
            downloader.updateprog(f"Downloading {url}")
            logging.info(f"Downloading {url}")
            for image in soup.find_all("img"):
                image_downloader(image,path)
            with open(f"{path}{name}.html","w",encoding="utf-8") as htmlfile:
                htmlfile.write(soup.prettify())
            i+=1

        except Exception as e:
                logging.warning(e)
    downloader.close()
