from linker import  linker
from crawlgui import crawler
from downloader_async import asyncdownloader
class Master(asyncdownloader,crawler,linker):
    def __init__(self, parent=None):
        asyncdownloader.__init__(self,parent)
        crawler.__init__(self,parent)
        linker.__init__(self,parent)