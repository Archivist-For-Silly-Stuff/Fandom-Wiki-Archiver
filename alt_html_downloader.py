import os
from bs4 import BeautifulSoup
import logging
import requests

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)
imglist = []

def image_downloader(image,path):
    global imglist
    if image.has_attr("data-image-key"):
        img_url = image.get("src")
        if img_url == None or img_url.startswith("data:image"):
            img_url = image.get("data-src")
        img = requests.get(f"{img_url}")
        if img.status_code == 200 and (img_url not in imglist):
            logging.info(f"Downloading {image.get('data-image-key')}")
            file = f"{path}{image.get('data-image-key')}"
            with open(file, "wb") as imagefile:
                imagefile.write(img.content)
            imglist+=img_url


def HTML_Download(list,path):
    for url in list:
        try:
            url = url.strip()
            if not url.startswith(("https://", "http://")):
                continue
            name = url.split("/")[-1]
            files=os.listdir(path)
            html = requests.get(url).text
            soup = BeautifulSoup(html, "html.parser")
            if (name+".html" in files):
                continue
            elif (name+".html" not in files):
                logging.info(f"Downloading {url}")
                for image in soup.find_all("img"):
                    image_downloader(image,path)
                with open(f"{path}{name}.html","w",encoding="utf-8") as htmlfile:
                    htmlfile.write(soup.prettify())
        except Exception as e:
                logging.info(e)
