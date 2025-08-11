import os
from bs4 import BeautifulSoup
import logging
import requests

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)

def image_downloader(image,path):
    if image.has_attr("data-image-key"):
        img_url = image.get("src")
        if img_url == None or img_url.startswith("data:image"):
            img_url = image.get("data-src")
        img = requests.get(f"{img_url}")
        if img.status_code == 200:
            logging.info(f"Downloading {img}")
            file = f"{path}{image.get('data-image-key')}"
            print(image.contents)
            with open(file, "wb") as imagefile:
                imagefile.write(img.content)


def HTML_Download(list,path):
    print(path)
    for url in list:
        try:
            url = url.strip()
            if not url.startswith(("https://", "http://")):
                continue
            name = url.split("/")[-1]
            files=os.listdir(path)
            html = requests.get(url).text
            soup = BeautifulSoup(html, "html.parser")
            if ("File:" in url) and (name not in files):
                name = name[len("File:"):]
                logging.info(f"Downloading {url}")
                for image in soup.find_all("img"):
                    if image.has_attr("data-image-key") and image.get("data-image-key") == name:
                        img_url=image.get("src")
                        if img_url==None or img_url.startswith("data:image"):
                            img_url=image.get("data-src")
                        print(img_url)
                        img = requests.get(f"{img_url}")
                        if img.status_code == 200:
                            logging.info(f"Downloading {img}")
                            file = f"{path}{image.get('data-image-key')}"
                            print(image.contents)
                            with open(file, "wb") as imagefile:
                                imagefile.write(img.content)
            elif (name in files):
                continue
            elif (name+".html" not in files):
                logging.info(f"Downloading {url}")
                for image in soup.find_all("img"):
                    image_downloader(image,path)
                with open(f"{path}{name}.html","w",encoding="utf-8") as htmlfile:
                    htmlfile.write(soup.prettify())
        except Exception as e:
                logging.info(e)
