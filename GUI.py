from network import Graphx

"""
We are using urljoin to help in joining together and autocorrecting the link from which 
we need to get all the pages of a wiki
"""
from urllib.parse import urljoin
"""
PyQt is used for the GUI because of its many widgets
"""
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QMessageBox, QFileDialog,
                             QDialog, QCheckBox)

import sys

from qasync import asyncSlot
import qasync
"""This helps download everything asynchronously"""
import downloader_async

"""This helps import the crawler which shall collect all the links"""
from crawlgui import crawler
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSlot, QThread, QTimer
from pyvis.network import Network
import re
"""This helps link everything"""
import linker
import os
import asyncio

"""This is for the progress bar"""
from progress import progress






class mainwindow(QMainWindow, QDialog):
    """This creates a main window from where the different functions may get called
    It has two textfields to find the wiki and to specify the path and a submit button
    to archive the wiki."""
    def __init__(self):
        QMainWindow.__init__(self)
        super(mainwindow, self).__init__()
        #sets title and makes sure that the window still takes a response

        self.paused = False
        self.setWindowTitle("Archiver")
        self.setGeometry(1000, 500, 600, 600)

        self.folderbutton = QPushButton('Open Folder', self)

        self.submitbutton = QPushButton("Submit", self)

        self.pausebutton = QPushButton("Pause", self)

        self.resumebutton = QPushButton("Resume", self)

        self.label = QLabel("Archive", self)

        self.labelurl = QLabel("URL", self)
        self.url = QLineEdit(self)

        self.labelpath = QLabel("Path", self)
        self.path = QLineEdit(self)

        self.graphdis=QLabel("Graph",self)
        self.checkbox=QCheckBox(self)

        self.error = QMessageBox()
        self.error.setIcon(QMessageBox.Critical)

        self.errorpath = QMessageBox()
        self.errorpath.setIcon(QMessageBox.Critical)

        self.errorpath = QMessageBox()
        self.errorpath.setIcon(QMessageBox.Critical)

        self.errorurl = QMessageBox()
        self.errorurl.setIcon(QMessageBox.Critical)

        self.flag = True

        self.initUI()

    def initUI(self):

        #Title
        self.flagnet=False

        self.label.setFont(QFont("Times New Roman", 30))
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
        self.labelurl.setFont(QFont("Times New Roman", 20))
        self.label.setGeometry(0, 0, 600, 100)
        self.labelurl.setGeometry(50, 150, 100, 100)
        self.url.setGeometry(150, 170, 400, 50)
        self.label.setAlignment(Qt.AlignCenter)
        self.labelurl.setAlignment(Qt.AlignCenter)

        #Path row

        self.path.setPlaceholderText("Enter Path")
        self.path.setStyleSheet("font-size:20px;"
                                "font-family:arial;")
        self.labelpath.setFont(QFont("Times New Roman", 20))
        self.labelpath.setGeometry(50, 250, 100, 100)
        self.path.setGeometry(150, 270, 255, 50)
        self.labelpath.setAlignment(Qt.AlignCenter)

        #button row

        self.submitbutton.setGeometry(450, 370, 75, 50)
        self.submitbutton.clicked.connect(self.submit)

        self.pausebutton.setGeometry(450, 450, 75, 50)
        self.pausebutton.setEnabled(False)

        self.resumebutton.setGeometry(350, 450, 75, 50)
        self.resumebutton.setEnabled(False)

        self.folderbutton.setGeometry(400, 270, 150, 50)
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


        self.graphdis.setGeometry(75,390,100,50)
        self.graphdis.setFont(QFont("Times New Roman",12))
        self.checkbox.setEnabled(True)
        self.checkbox.setGeometry(100,450,30,30)
        self.checkbox.stateChanged.connect(self.checkf)


    def checkf(self,f):
        """This helps check if we should make a network"""
        if f:
            self.flagnet=True
        else:
            self.flagnet=False


    def folder(self):
        """This is the function which helps to get the folder and set the Text in the path text box"""
        folder = QFileDialog.getExistingDirectory(self, "Open Directory", "c:\\")
        if folder:
            self.path.setText(folder)


    def collector(self,url):
        """This helps in collecting all the link
        It runs the crawler object in a thread which helps to take everything
        from the file site map to be used to download the whole wiki.
        This is more efficient than crawling like usual and a map of the whole wiki may be made at the end either way via the
        Network function"""
        self.crawl_thread = QThread()
        self.progress_bar1 = progress(2, "Crawler")
        self.domain = url.split('/')[2]
        self.f = crawler(self.domain, self.dirpath, [url])
        self.f.moveToThread(self.crawl_thread)

        self.crawl_thread.started.connect(lambda: QTimer.singleShot(0, self.f.downloadbar))
        self.progress_bar1.show()
        self.f.log.connect(self.progress_bar1.log)
        self.f.prog.connect(self.progress_bar1.setprogress)
        self.f.sendurl.connect(self.urls)
        self.f.finish.connect(self.crawl_thread.exit)
        self.f.finish.connect(self.progress_bar1.close)
        self.pausebutton.clicked.connect(self.f.paused, type=Qt.DirectConnection)
        self.resumebutton.clicked.connect(self.f.resumed, type=Qt.DirectConnection)
        self.pausebutton.setEnabled(True)
        self.resumebutton.setEnabled(True)

        self.crawl_thread.start()

    @asyncSlot(list)
    async def urls(self, urls):
        """Thsi helps to download all the url's. This is done so asynchronously allowing
        everything to be downloaded in a decent time."""
        self.downloading_urls = urls
        self.progress_bar2 = progress(len(urls), "Downloading")
        self.downloader = downloader_async.asyncdownloader(self.dirpath, urls)
        self.progress_bar2.show()
        try:
            self.pausebutton.clicked.disconnect()
            self.resumebutton.clicked.disconnect()
        except:
            pass

        self.pausebutton.clicked.connect(self.downloader.pause)
        self.resumebutton.clicked.connect(self.downloader.resume)

        asyncio.create_task(self.downloader.main())


        self.downloader.log_message.connect(self.progress_bar2.log)
        self.downloader.progress_updated.connect(self.progress_bar2.setprogress)


        self.downloader.finished.connect(self.linking)
        self.downloader.finished.connect(self.progress_bar2.close)


    def linking(self):
        """We then link the html files with all the resources downloaded and the other files as well."""
        self.link_thread = QThread()
        self.progress_bar3 = progress(len(self.downloading_urls), "Linking")
        self.link = linker.linker(self.dirpath, self.domain)
        self.link.moveToThread(self.link_thread)
        #This is a singleshot timer That makes the program only work once when this function is called.
        self.link_thread.started.connect(lambda: QTimer.singleShot(0, self.link.link))
        self.progress_bar3.show()

        self.link.log.connect(self.progress_bar3.log)
        self.link.prog.connect(self.progress_bar3.setprogress)
        self.link.finished.connect(self.link_thread.exit)

        try:
            self.pausebutton.clicked.disconnect()
            self.resumebutton.clicked.disconnect()
        except:
            pass

        self.pausebutton.clicked.connect(self.link.paused,type=Qt.DirectConnection)
        self.resumebutton.clicked.connect(self.link.resumed,type=Qt.DirectConnection)

        self.link.finished.connect(self.cleanup)
        self.link.finished.connect(self.progress_bar3.close)



        self.link_thread.start()

    @pyqtSlot()
    def cleanup(self):
        """This re-enables anything that is required to be re-enabled and disables anything to be disabled"""

        self.flag = True
        self.submitbutton.setEnabled(True)
        if self.flagnet:
            print("h")
            self.net()
        self.pausebutton.setEnabled(False)
        self.resumebutton.setEnabled(False)

    def net(self):

        self.Net_Thread=QThread()
        self.graphs=Graphx(self.downloading_urls,self.dirpath)
        self.graphs.moveToThread(self.Net_Thread)
        self.Net_Thread.started.connect(self.graphs.add_edges)
        self.graphs.dqsig.connect(self.endproc)


        self.Net_Thread.start()

    @pyqtSlot(object)
    def endproc(self,G):

        output_path = os.path.join(self.dirpath, 'network_map.html')
        nt = Network('1000px', '1000px', bgcolor='#222222', font_color='white')
        nt.from_nx(G)
        nt.toggle_physics(True)
        nt.write_html(output_path)
        import webbrowser
        webbrowser.open(output_path)

    def submit(self):
        url = str(self.url.text())
        path = str(self.path.text())
        patternscrap = re.compile(
            r"^https:\/\/"
            r"[a-zA-Z0-9\-]+\.fandom\.com\/"
            r"wiki\/Local_Sitemap"
            r"(?:\?namefrom=[^#]+"
            r"|)$",
            re.IGNORECASE
        )
        wikscrap=re.compile(
            r"^https:\/\/"
            r"[a-zA-Z0-9\-]+\.fandom\.com\/"
            r"wiki\/.*$",
            re.IGNORECASE
        )
        f1 = os.path.isdir(path)
        f2 = bool(patternscrap.match(url))
        f3=bool(wikscrap.match(url))
        if (not (url or path) and self.flag) or (not (f1) and (not (f2) and not f3)):
            self.error.exec_()
        elif self.flag and f1 and f3:
            if not f2:
                url=urljoin(url,"/wiki/Local_Sitemap")
            self.flag = False
            self.submitbutton.setEnabled(False)
            path = rf"{path}"
            if path[-1] != "/":
                path += "/"
            self.dirpath = path
            self.collector(url)




        elif not (f1) and self.flag:
            self.errorpath.exec_()

        elif not (f2) and self.flag:
            print("F")
            print(not (f2))
            self.errorurl.exec_()


def main():
    app = QApplication(sys.argv)
    loop=qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = mainwindow()
    window.show()
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
