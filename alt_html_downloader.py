import os
from bs4 import BeautifulSoup
import logging
import requests
#from GUI import sidewindow

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)



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
            imglist.append(img_url)


def HTML_Download(list,path):
    global imglist
    imglist=[i for i in os.listdir(path) if not(".html" in i)]
    filelist=[i for i in os.listdir(path) if (".html" in i)]
    for url in list:
        if url not in filelist:
            try:
                url = url.strip()
                if not(url.startswith(("https://", "http://"))) or ('Local_Sitemap' in url):
                    continue
                name = url.split("/")[-1]
                files=os.listdir(path)
                if (name+".html" in files):
                    continue
                elif (name+".html" not in files):
                    html = requests.get(url).text
                    soup = BeautifulSoup(html, "html.parser")
                    logging.info(f"Downloading {url}")
                    for image in soup.find_all("img"):
                        image_downloader(image,path)
                    with open(f"{path}{name}.html","w",encoding="utf-8") as htmlfile:
                        htmlfile.write(soup.prettify())
            except Exception as e:
                    logging.info(e)
