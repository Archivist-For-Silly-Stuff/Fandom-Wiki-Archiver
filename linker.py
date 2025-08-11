import os
from bs4 import BeautifulSoup
import requests
import logging
import shutil

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)
class linker:
    def __init__(self,path,domain):
        self.path=path
        self.domain=domain
        self.csslist=[]
        self.css_downloads=[]
        self.css_count=0
        self.phplist=[]


    def css(self,soup):
        b = soup.find_all("link", rel=lambda value: value and "stylesheet" in value)
        for z in b:
            if (z['href'] not in self.phplist) and z not in self.css_downloads:
                try:
                    css = requests.get("https://" + self.domain + "/" + z['href'])
                    self.csslist.append(f"css_{self.css_count}.css")
                    self.phplist.append(z["href"])
                    self.css_downloads.append(z)
                    with open(f"{self.path}css_{self.css_count}.css", "w", encoding="utf-8") as cfp:
                        cfp.write(css.text)

                    z["href"] = f"css_{self.css_count}.css"
                    self.css_count += 1
                except Exception as e:
                    logging.info(e)
            else:
                z["href"]=self.csslist[self.phplist.index(z["href"])]

        with open(f"{self.path}css.txt","w") as f:
            f.writelines(list(map(lambda x,y:x+" : "+y+"\n",self.phplist,self.csslist)))
        return soup

    def image(self,soup):
        a = [image for image in soup.find_all("img") if image.has_attr("data-image-key")]
        for img in a:
            try:
                img["src"] = img["data-image-key"]
            except Exception as e:
                logging.info(f"{e}")
        return soup
    def link(self):
        list=os.listdir(self.path)
        valid_list=[el for el in list if ".html" in el and not(el.startswith("edited_")) and ("edited_"+el not in list)]
        for x in valid_list:
            logging.info(f"Linking {x}")
            with open(self.path+x,"r",encoding="utf-8") as fp:
                soup=BeautifulSoup(fp,"html.parser")
                soup=self.css(soup)
                soup=self.image(soup)
                with open(self.path+"edited_"+x,"w",encoding="utf-8") as fp2:
                    fp2.write(soup.prettify())




