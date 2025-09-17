import sys
from time import sleep

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QProgressBar, QTextEdit, QMainWindow
from PyQt5.QtCore import Qt, pyqtSlot, QTimer, QObject, pyqtSignal
import logging




class progress(QMainWindow):

    def __init__(self,maxval, title="Files", parent=None):
        super().__init__(parent,Qt.Window)
        self.setWindowTitle(title)
        self.setGeometry(1000,700,500,100)
        central_widget=QWidget()
        layout=QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        self.progressbar=QProgressBar()
        self.progressbar.setRange(0,maxval)
        self.progressbar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progressbar)

        self.logop=QTextEdit()
        self.logop.setReadOnly(True)
        layout.addWidget(self.logop)

        self.setLayout(layout)


    def setprogress(self,value):
        self.progressbar.setValue(value)

    def log(self,logs):
        self.logop.append(logs)



"""def handlinglog(prog):
    handle=QtHandler()
    handle.setFormatter(logging.Formatter('%(asctime)s %(levelname)s:%(message)s'))
    handle.logs.connect(prog.log)
    logger=logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handle)
    return handle"""
if __name__=="__main__":
    app=QApplication(sys.argv)
    pro=progress(100,"e")
    sys.exit(app.exec_())
