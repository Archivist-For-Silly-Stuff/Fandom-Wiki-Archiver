from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QMessageBox)
import sys
import crawl
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import re
import linker
import os



"""class sidewindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.side = QMainWindow()
        self.side.setGeometry(1600, 500, 100, 200)
        self.log = QLabel("", self)
        self.log.setGeometry(0, 0, 100, 100)
        self.log.setAlignment(Qt.AlignCenter)

    def login(self, log):
        self.log.setText(log)"""

class mainwindow(QMainWindow):
    def __init__(self):
        super().__init__()
        #sets title
        self.setWindowTitle("Archiver")
        self.setGeometry(1000,500,600,600)

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
        self.path.setGeometry(150,270,400,50)
        self.labelpath.setAlignment(Qt.AlignCenter)

        #button row

        self.submitbutton.setGeometry(450,370,75,50)
        self.submitbutton.clicked.connect(self.submit)

        self.error.setText("Data Missing")
        self.error.setInformativeText("You haven't entered the information correctly, try again")
        self.error.setWindowTitle('Data Missing')

        self.errorpath.setText("Invalid Path")
        self.errorpath.setInformativeText("The path you've specified doesn't exist!")
        self.errorpath.setWindowTitle('Path error')

        self.errorurl.setText("Invalid URL")
        self.errorurl.setInformativeText("The URL you've specified doesn't exist!")
        self.errorurl.setWindowTitle('Path error')
    def submit(self):
        url=str(self.url.text())
        path=str(self.path.text())
        patternscrap = re.compile(
            rf"^https:\/\/[a-zA-Z0-9]+\.fandom\.com\/wiki\/(?:"
            r"[A-Za-z0-9_()%\-]+"
            r"|Category:[A-Za-z0-9_()%\-]+"
            r")$",
            re.IGNORECASE
        )
        f1=os.path.isdir(path)
        f2=patternscrap.match(url)
        if (not(url or path) and self.flag):
            self.error.exec_()
        elif self.flag and f1 and f2:
            self.flag=False
            path=rf"{path}"
            if path[-1]!="\\":
                path+="\\"

            f=crawl.crawler(url.split('/')[2],path,[url])
            f.download()
            self.flag=True
            """l=linker.linker(path,url.split('/')[2])
            l.link()
            ls = os.listdir(path)
            for i in ls:
                if not ("edited_" in i or not (".html" in i)):
                    os.remove(path + i)"""

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
