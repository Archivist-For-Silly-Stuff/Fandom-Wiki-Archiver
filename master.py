import requests
from PyQt5.QtCore import pyqtSignal


class masterscraping:
    log_message = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal()
    def __init__(self,dirpath,listourl=[]):
        self.session=requests.session()
        self.path=dirpath
        self.urls=listourl
