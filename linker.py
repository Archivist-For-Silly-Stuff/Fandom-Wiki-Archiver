import os
from bs4 import BeautifulSoup
import requests
import logging

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)
class linker:
    #Takes the path where all the html is saved and domain of the url
    def __init__(self,path,domain):
        self.path=path
        self.domain=domain
        self.csslist=[]
        self.css_downloads=[]
        self.phplist=[]
        self.scriptlist=[]
        self.jslist=[]
    #Downloads and links css
    def css(self,soup):
        b = soup.find_all("link", rel=lambda value: value and "stylesheet" in value)
        for z in b:
            if (z['href'] not in self.phplist) and z not in self.css_downloads:
                try:
                    css = requests.get("https://" + self.domain + "/" + z['href'])
                    self.csslist.append(f"css_{len(self.css_downloads)}.css")
                    self.phplist.append(z["href"])
                    self.css_downloads.append(z)
                    with open(f"{self.path}css_{len(self.css_downloads)}.css", "w", encoding="utf-8") as cfp:
                        cfp.write(css.text)

                    z["href"] = f"css_{len(self.css_downloads)}.css"
                except Exception as e:
                    logging.info(e)
            else:
                z["href"]=self.csslist[self.phplist.index(z["href"])]
        with open(f"{self.path}css.txt","w") as f:
            f.writelines(list(map(lambda x,y:x+" : "+y+"\n",self.phplist,self.csslist)))
        return soup
    #Links images using the data-image-key
    def image(self,soup):
        a = [image for image in soup.find_all("img") if image.has_attr("data-image-key")]
        for img in a:
            try:
                img["src"] = img["data-image-key"]
            except Exception as e:
                logging.info(f"{e}")
        return soup
    #Removes js tracking scripts and  any suspicious iframes
    def remove_trackers(self,soup):
        c=[script for script in soup.find_all("script")]+[script for script in soup.find_all("iframe")]
        for script in c:
            try:
                if script:
                    script.decompose()
            except Exception as e:
                logging.info(e)
        return soup



    def link(self):
        #Helps continue from where you left off
        list=os.listdir(self.path)
        valid_list=[el for el in list if ".html" in el and not(el.startswith("edited_")) and ("edited_"+el not in list)]
        for x in valid_list:
            logging.info(f"Linking {x}")
            with open(self.path+x,"r",encoding="utf-8") as fp:
                soup=BeautifulSoup(fp,"html.parser")
                soup=self.css(soup)
                soup=self.image(soup)
                soup=self.remove_trackers(soup)
                with open(self.path+"edited_"+x,"w",encoding="utf-8") as fp2:
                    fp2.write(soup.prettify())