
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QMessageBox, QFileDialog,
                             QDialog, QWidget, QVBoxLayout, QProgressBar)
import sys

import Object_Html_Downloader
import crawl
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QThread, QTimer
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
import re
import linker
import os

from Object_Html_Downloader import HTML_Downloader
from progress import progress






class mainwindow(QMainWindow, QDialog):
    def __init__(self):
        QMainWindow.__init__(self)
        super(mainwindow,self).__init__()
        #sets title


        self.setWindowTitle("Archiver")
        self.setGeometry(1000,500,600,600)

        self.folderbutton=QPushButton('Open Folder',self)

        self.submitbutton=QPushButton("Submit",self)

        self.label=QLabel("Archive",self)

        self.labelurl=QLabel("URL",self)
        self.url=QLineEdit(self)

        self.labelpath=QLabel("Path",self)
        self.path=QLineEdit(self)

        self.error=QMessageBox()
        self.error.setIcon(QMessageBox.Critical)

        self.errorpath = QMessageBox()
        self.errorpath.setIcon(QMessageBox.Critical)

        self.errorpath = QMessageBox()
        self.errorpath.setIcon(QMessageBox.Critical)

        self.errorurl = QMessageBox()
        self.errorurl.setIcon(QMessageBox.Critical)

        self.flag=True

        self.initUI()
    def initUI(self):

        #Title

        self.label.setFont(QFont("Times New Roman",30))
        self.label.setStyleSheet("background-color:red;"
                            "text-align:center;"
                            "font-weight:bold;"
                            "font-style:italic;"
                            "border-width:5px;"
                            "border-color:black;"
                            "border-style:solid;"
                    )

        #Url row

        self.url.setPlaceholderText("Enter Url")
        self.url.setStyleSheet("font-size:20px;"
                          "font-family:arial;")
        self.labelurl.setFont(QFont("Times New Roman",20))
        self.label.setGeometry(0,0,600,100)
        self.labelurl.setGeometry(50,150,100,100)
        self.url.setGeometry(150,170,400,50)
        self.label.setAlignment(Qt.AlignCenter)
        self.labelurl.setAlignment(Qt.AlignCenter)

        #Path row

        self.path.setPlaceholderText("Enter Path")
        self.path.setStyleSheet("font-size:20px;"
                          "font-family:arial;")
        self.labelpath.setFont(QFont("Times New Roman",20))
        self.labelpath.setGeometry(50,250,100,100)
        self.path.setGeometry(150,270,255,50)
        self.labelpath.setAlignment(Qt.AlignCenter)

        #button row

        self.submitbutton.setGeometry(450,370,75,50)
        self.submitbutton.clicked.connect(self.submit)

        self.folderbutton.setGeometry(400,270,150,50)
        self.folderbutton.clicked.connect(self.folder)

        self.error.setText("Data Missing")
        self.error.setInformativeText("You haven't entered the information correctly, try again")
        self.error.setWindowTitle('Data Missing')

        self.errorpath.setText("Invalid Path")
        self.errorpath.setInformativeText("The path you've specified doesn't exist!")
        self.errorpath.setWindowTitle('Path error')

        self.errorurl.setText("Invalid URL")
        self.errorurl.setInformativeText("Enter a Local Sitemap url!")
        self.errorurl.setWindowTitle('Path error')

    def folder(self):
        folder=QFileDialog.getExistingDirectory(self,"Open Directory","c:\\")
        if folder:
            self.path.setText(folder)


    def urls(self,urls):
        self.downloading_urls=urls
        self.download_thread=QThread()
        self.progress_bar2=progress(len(urls),"Downloading")
        self.downloader=Object_Html_Downloader.HTML_Downloader(self.dirpath,urls)

        self.downloader.moveToThread(self.download_thread)
        self.download_thread.started.connect(lambda: QTimer.singleShot(0,self.downloader.HTML_Download))
        self.progress_bar2.show()

        self.downloader.log_message.connect(self.progress_bar2.log)
        self.downloader.progress_updated.connect(self.progress_bar2.setprogress)


        self.downloader.finished.connect(self.download_thread.exit)
        self.downloader.finished.connect(self.linking)


        self.download_thread.start()

    def linking(self):
        self.link_thread=QThread()
        self.progress_bar3=progress(len(self.downloading_urls),"Linking")
        self.link=linker.linker(self.dirpath,self.domain)
        self.link.moveToThread(self.link_thread)
        self.link_thread.started.connect(lambda: QTimer.singleShot(0,self.link.link))
        self.progress_bar3.show()

        self.link.log.connect(self.progress_bar3.log)
        self.link.prog.connect(self.progress_bar3.setprogress)
        self.link.finished.connect(self.link_thread.exit)

        self.link_thread.start()

        self.flag=True
        self.submitbutton.setEnabled(True)


    def submit(self):
        url=str(self.url.text())
        path=str(self.path.text())
        patternscrap = re.compile(
            r"^https:\/\/"
            r"[a-zA-Z0-9\-]+\.fandom\.com\/"
            r"wiki\/Local_Sitemap"
            r"(?:\?namefrom=[^#]+"
            r"|)$",
            re.IGNORECASE
        )
        f1=os.path.isdir(path)
        f2=bool(patternscrap.match(url))
        if (not(url or path) and self.flag) or (not(f1) and not(f2)):
            self.error.exec_()
        elif self.flag and f1 and f2:
            self.flag=False
            self.submitbutton.setEnabled(False)
            path=rf"{path}"
            if path[-1]!="\\":
                path+="\\"
            self.dirpath=path
            self.crawl_thread=QThread()

            self.progress_bar1=progress(2,"Crawler")
            self.domain=url.split('/')[2]
            self.f=crawl.crawler(self.domain, path,[url])
            self.f.moveToThread(self.crawl_thread)

            self.crawl_thread.started.connect(lambda: QTimer.singleShot(0,self.f.downloadbar))
            self.progress_bar1.show()
            self.f.log.connect(self.progress_bar1.log)
            self.f.prog.connect(self.progress_bar1.setprogress)
            self.f.sendurl.connect(self.urls)
            self.f.finish.connect(self.crawl_thread.exit)
            self.f.finish.connect(self.progress_bar1.close)
            self.crawl_thread.start()


        elif not(f1) and self.flag:
            self.errorpath.exec_()

        elif not(f2) and self.flag:
            print("F")
            print(not(f2))
            self.errorurl.exec_()






def main():
    app = QApplication(sys.argv)
    window = mainwindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
