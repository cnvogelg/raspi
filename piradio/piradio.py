#!/usr/bin/env python3
# piradio.py
# main program for piradio

import sys
from PyQt4 import QtCore, QtGui
from ui_piradio import Ui_MainWindow

class MyMainWindow(QtGui.QMainWindow):
  def __init__(self, *args):
    QtGui.QMainWindow.__init__(self, *args)
    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)
    self.createConnects()
    
  def createConnects(self):
    self.ui.bPlay.clicked.connect(self.doPlay)
    self.ui.bStop.clicked.connect(self.doStop)
  
  @QtCore.pyqtSlot()
  def doPlay(self):
    print("play")
    self.ui.lInfo.setText("play")
  
  @QtCore.pyqtSlot()
  def doStop(self):
    print("stop")
    self.ui.lInfo.setText("stop")

def main(argv):
  app = QtGui.QApplication(argv)
  mainwindow = MyMainWindow()
  mainwindow.show()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main(sys.argv)