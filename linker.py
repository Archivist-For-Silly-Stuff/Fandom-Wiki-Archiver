import os
import re
from csv import DictReader, DictWriter
from idlelib.iomenu import encoding
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests
import logging
import pandas
import csv

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)

#from GUI import sidewindow


class linker:
    #Takes the path where all the html is saved and domain of the url
    def __init__(self,path,domain):
        self.path=path
        self.domain=domain
        self.csslist=[]
        self.css_downloads=[]
        self.phplist=[]
        self.jssrc=[]
        self.jscounter=[]
        self.headers=['css','cssdownload','php']
        self.rows=[]
        self.js=[]
        self.linkedlist=[]
        self.jsheaders=['jssrc','jscounter']
        with open(self.path+"url.csv",encoding='utf-8') as fp:
            reader=csv.DictReader(fp)
            for row in reader:
                self.linkedlist.append({'URL':row['URL'],'Linked':row['Linked']})
        try:
            with open(self.path+"css.csv","r",encoding='utf-8') as fp:
                reader=csv.DictReader(fp)
                for row in reader:
                    self.csslist.append(row['css'])
                    self.css_downloads.append(row['cssdownload'])
                    self.phplist.append(row['php'])
                    self.rows.append({'css':row['css'], 'cssdownload':row['cssdownload'], 'pfp':row['php']})
        except FileNotFoundError as e:
            print(e)
            with open(self.path+"css.csv","w",encoding='utf-8') as fp:
                reader=csv.DictWriter(fp,fieldnames=self.headers)
                reader.writeheader()
        try:
            with open(self.path+"js.csv","r",encoding='utf-8') as fp:
                reader=csv.DictReader(fp)
                for row in reader:
                    self.jssrc.append(row['jssrc'])
                    self.jscounter.append(row['jscounter'])
        except FileNotFoundError as e:
            print(e)
            with open(self.path+"js.csv","w",encoding='utf-8') as fp:
                reader=csv.DictWriter(fp,fieldnames=self.jsheaders)
                reader.writeheader()

    #Downloads and links css
    def css(self,soup):
        b = soup.find_all("link", rel=lambda value: value and "stylesheet" in value)
        for z in b:
            if ((z['href'] not in self.phplist) and (z['href'] not in self.csslist)) and z not in self.css_downloads:
                try:
                    css = requests.get("https://"+self.domain+z['href'])
                    css_count=len(self.css_downloads)
                    self.csslist.append(f"css_{css_count}.css")
                    self.phplist.append(z["href"])
                    self.css_downloads.append(z)
                    cssfile = open(self.path+"css.csv", "a", encoding="utf-8")
                    writer = DictWriter(cssfile, fieldnames=self.headers)
                    writer.writerow({'css':f"css_{css_count}.css",'php':z["href"],'cssdownload':z})
                    with open(f"{self.path}css_{css_count}.css", "w", encoding="utf-8") as cfp:
                        cfp.write(css.text)
                    cssfile.close()

                    z["href"] = f"css_{css_count}.css"
                except Exception as e:

                    logging.info(e)
                    #self.side.login(e)

            else:
                if z['href'] not in self.csslist:
                    z["href"]=self.csslist[self.phplist.index(z["href"])]

        with open(f"{self.path}css.txt","w",encoding='utf-8') as f:
            f.writelines(list(map(lambda x,y:x+" : "+y+"\n",self.phplist,self.csslist)))
        return soup
    #Links images using the data-image-key
    def image(self,soup):
        a = [image for image in soup.find_all("img") if image.has_attr("data-image-key") and image.has_attr('src')  and image['data-image-key']!=image['src']]
        if a:
            a1=[img for img in a if img.has_attr('src') and img['data-image-key']!=img['src']]
            a2=[img for img in a if img.has_attr('data-src') and img['data-image-key']!=img['data-src']]
            a=a1+a2
            for img in a:
                try:
                    if img.has_attr('src'):
                        img["src"] = img["data-image-key"]
                    elif img.has_attr('data-src'):
                        img['data-src']=img["data-image-key"]

                except Exception as e:
                    logging.info(f"{e}")
                #self.side.login(e)
        return soup
    #Removes js tracking scripts and  any suspicious iframes
    def remove_trackers(self,soup):
        c=[script for script in soup.find_all("script")]+[script for script in soup.find_all("iframe")]
        for script in c:
            try:
                if (script.name=="iframe") or (script.has_attr('src') and re.search(r"(googletag|quantserve|scorecard|beacon|metrics|silversurfer|search-insight)",script['src'])):
                    script.decompose()
                elif script.has_attr('src'):
                    if (script['src'] not in self.jssrc):
                        breakpoint()
                        js=requests.get("https://"+self.domain+script['src'])
                        jscount=len(self.jssrc)
                        self.jssrc.append(script['src'])
                        self.jscounter.append(f"js_{jscount}.js")
                        url=urljoin(f"https://{self.domain}",)
                        jsfile = open(self.path + "js.csv", "a", encoding="utf-8")
                        writer = DictWriter(jsfile, fieldnames=self.jsheaders)
                        writer.writerow({'jscounter': f"js_{jscount}.js", 'jssrc': script['src']})
                        with open(f"{self.path}js_{jscount}.js","wb") as jsfp:
                            jsfp.write(js.content)
                        jsfile.close()
                        script['src']=f"js_{jscount}.js"
                    else:
                        script['src']=self.jscounter[self.jssrc.index(script['src'])]
            except Exception as e:
                logging.info(e)
                #self.side.login(e)
        return soup



    def link(self):
        #Helps continue from where you left off
        list=os.listdir(self.path)
        print(list)
        valid_list=[]
        for row in self.linkedlist:
            if row['Linked']=="False":
                valid_list.append(row['URL'])
        if valid_list:
            breakpoint()
            for x in valid_list:
                logging.info(f"Linking {x.split('/')[-1]}")
                #self.side.login(f"Linking {x}")
                name=x.split('/')[-1]+".html"
                with open(self.path+name,"r",encoding="utf-8") as fp:
                    soup=BeautifulSoup(fp,"html.parser")
                    soup=self.css(soup)
                    soup=self.image(soup)
                    soup=self.remove_trackers(soup)
                with open(self.path+name,"w",encoding="utf-8") as fp2:
                    fp2.write(soup.prettify())
                    urls=open(self.path+"url.csv","w",encoding='utf-8')
                    update=csv.DictWriter(urls,fieldnames=['URL','Linked'])
                    for row in self.linkedlist:
                        if row['URL']==x:
                            row['Linked']=True
                            break
                    update.writeheader()
                    update.writerows(self.linkedlist)