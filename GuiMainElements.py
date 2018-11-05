#!/usr/bin/env python
# coding:utf-8
"""
:Author: Sonia Karkar -- karkar@in2p3.fr

:What:

"""
# from __future__ import unicode_literals
from PyQt4 import QtGui
from PyQt4 import QtCore
import ressources
import sys
from qtUtils import FingerTabBarWidget, WidgetTimer,  centerOnScreen
import os
from LogUtils import MyLog
from qtUtils import LogWidget
if __name__ == "__main__":
    logname = os.path.basename(__file__)[:-3]
else:
    logname = __name__
if len(logname) > 20:
    logname = logname[:9] + "--" + logname[-9:]

sidePanelWidth = 200
sidePanelHeight = 50

# Create a logger with file and console printing
log = MyLog(logname, qt=True, logdir=os.getenv("HOME") + "/log/")
# default logging level is INFO uncomment below for DEBUG
import logging
# log.setLevel(logging.DEBUG)
mycolors = 'plum skyblue lightgreen tomato orange yellow   '.split()


def CreateMainTabWidget(parent, testsList):
    tabs = QtGui.QTabWidget(parent=parent)
    tabs.setTabBar(FingerTabBarWidget(
        width=sidePanelWidth, height=sidePanelHeight))
    for i, d in enumerate(testsList + ["Summary"]):
        widget = QtGui.QWidget()
        tabs.addTab(widget, d)
        layout = QtGui.QGridLayout()
        tabs.widget(i).setLayout(layout)
        tabs.widget(i).layout = layout
        addTestStop(tabs.widget(i))
        addTestTitle(tabs.widget(i), i, d)
        tabs.tabBar().MySetTabColor(i, QtGui.QColor('skyblue'))
    tabs.setTabPosition(QtGui.QTabWidget.West)
    return tabs


def addTestTitle(tab, i, d):
    title = QtGui.QLabel("tab {} , test {}".format(i, d))
    title.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)
    title.setStyleSheet(
        "background-color: blue; padding: 2px;border-radius: 10px")
    tab.layout.addWidget(title, 0, 0)


def addTestStop(tab):
    StopThisTestBtn = QtGui.QPushButton("Stop this test")
    tab.layout.addWidget(StopThisTestBtn, 1, 1)
    StopThisTestBtn.setStyleSheet(
        "background-color: orange;padding: 2px; border-radius: 5px")
    StopThisTestBtn.setMaximumWidth(100)
    StopThisTestBtn.setEnabled(False)
    StopThisTestBtn.setDefault(False)
    tab.StopThisTestBtn = StopThisTestBtn


def addTestRestart(tab):
    RestartThisTestBtn = QtGui.QPushButton("Restart this test from begining")
    tab.layout.addWidget(RestartThisTestBtn, 1, 0)
    RestartThisTestBtn.setStyleSheet(
        "background-color: green; padding: 2px;border-radius: 5px")
    RestartThisTestBtn.setEnabled(False)
    RestartThisTestBtn.setDefault(False)
    tab.RestartThisTestBtn = RestartThisTestBtn


class MainWindow(QtGui.QMainWindow):

    def __init__(self, testsList):
        QtGui.QMainWindow.__init__(self)
        self.ObjectTested = None
        self.initUI(testsList)
        # sip.setdestroyonexit(False)

    def initUI(self, testsList):
        log.debug("creating main window")
        # ---------Window settings --------------------------------
        # self.setGeometry(300, 300, 280, 170)
        self.setWindowIcon(QtGui.QIcon(":/icons/qnectarcam.png"))
        if not QtGui.QDesktopWidget().isVirtualDesktop():
            screenWidth = (QtGui.QDesktopWidget().availableGeometry(
            ).width() / QtGui.QDesktopWidget().numScreens())
        else:
            screenWidth = (QtGui.QDesktopWidget().availableGeometry().width())
        screenHeight = QtGui.QDesktopWidget().availableGeometry().height()
        mainWinWidth = screenWidth * 0.98
        mainWinHeight = screenHeight * 0.98
        self.resize(mainWinWidth, mainWinHeight)
        # centerMainWin(self)
        centerOnScreen(self)
        # self.move(0, 0)
        self.setWindowTitle('FEB Prod test')
        self.show()

        # mainWidget = MyRoundWidget()
        mainWidget = QtGui.QWidget()
        self.setCentralWidget(mainWidget)
        mainlayout = QtGui.QGridLayout()
        mainlayout.setSpacing(10)
        mainWidget.setLayout(mainlayout)

        scrollWidget = QtGui.QScrollArea()
        scrollWidget.setWidget(mainWidget)
        scrollWidget.setWidgetResizable(True)
        self.setCentralWidget(scrollWidget)

        logWidth = mainWidget.frameGeometry().width() - sidePanelWidth
        logHeight = 200
        self.logwin = LogWidget(mainWidget, logWidth, logHeight)
        mainlayout.addWidget(self.logwin, 1, 0)
        log.debug("log widget added to main window")
        self.tabs = CreateMainTabWidget(
            parent=mainWidget, testsList=testsList)
        mainlayout.addWidget(self.tabs, 0, 0)
        log.debug("tab widget added to main window")
        self.MainTimer = WidgetTimer("in main window")
        self.MainTimer.setMaximumHeight(150)
        mainlayout.addWidget(self.MainTimer, 0, 1)

    def closeEvent(self, event):

        reply = QtGui.QMessageBox.question(self, 'Message',
                                           "Really quit?",
                                           QtGui.QMessageBox.Yes |
                                           QtGui.QMessageBox.No,
                                           QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            # bye = QtGui.QMessageBox()
            # bye.setText("Quiting")
            # bye.show()
            # timer = QtCore.QTimer()
            # timer.setSingleShot(True)
            # waitmsec = 2000
            # timer.timeout.connect(sys.exit)
            # timer.start(waitmsec)
            sys.exit()
        else:
            event.ignore()

    # def setFeb(self, thisFeb):
    #     self.feb = thisFeb

    def setTabsEnable(self, itest, testsList):
        for i in range(len(testsList)):
            if i <= itest:
                self.tabs.setTabEnabled(i, True)
            else:
                self.tabs.setTabEnabled(i, False)


class getTestListwin(QtGui.QWidget):

    done = QtCore.pyqtSignal()
    choicemade = False

    def __init__(self):
        super(getTestListwin, self).__init__()
        log.debug("creating Widget " + str(type(self).__name__))
        self.MyList = [
            "Pattern",
            "IBOF",
            "DACL",
            "NF",
            "L0PedScan",
            # 'ConnectSignal',
            "StartCheck",
            "ICF",
            "Linearity",
            "L0L1PulseSizeScan",
            # "ConnectHVPA",
            "HVPA",
            # "DisConnectHVPA",
        ]
        self.initUI()

    def initUI(self):
        log.debug("initUI  Widget " + str(type(self).__name__))
        vert = QtGui.QVBoxLayout()
        log.debug("vert {}".format(vert))
        self.setLayout(vert)
        myLabel = QtGui.QLabel("Choose which tests you want to run : ")
        vert.addWidget(myLabel)
        self.cb = []
        for i, test in enumerate(self.MyList):
            self.cb.append(QtGui.QCheckBox(test))
            vert.addWidget(self.cb[i])
            log.debug("self.cb[i] {}".format(self.cb[i]))
        log.debug("self.cb {}".format(self.cb))
        thebutton = QtGui.QPushButton("OK")
        log.debug("thebutton {}".format(thebutton))
        vert.addWidget(thebutton)
        thebutton.clicked.connect(self.setTestListDone)
        log.debug("vert.widgets() {}".format([vert.itemAt(i).widget()
                                              for i in range(vert.count())]))

    def setTestListDone(self):
        finalList = [
            # 'ConnectSignal',
            'ScanFeb',
            'CheckInstrumentsConnexion',
            "CheckFEBandTrigBoard"]
        finalList += [test for (i, test) in enumerate(self.MyList)
                      if self.cb[i].isChecked()]
        if "StartCheck" in finalList:
            finalList.insert(finalList.index("CheckFEBandTrigBoard") + 1,
                             'CheckConnectSignal')
        elif "ICF" in finalList:
            finalList.insert(finalList.index("CheckFEBandTrigBoard") + 1,
                             'CheckConnectSignal')
        elif "Linearity" in finalList:
            finalList.insert(finalList.index("CheckFEBandTrigBoard") + 1,
                             'CheckConnectSignal')
        elif "L0L1PulseSizeScan" in finalList:
            finalList.insert(finalList.index("CheckFEBandTrigBoard") + 1,
                             'CheckConnectSignal')
        if "HVPA" in finalList:
            finalList.insert(finalList.index("HVPA"), 'ConnectHVPA')
            finalList += ["DisConnectHVPA"]
        log.debug("finalList {}".format(finalList))
        self.MyList = finalList
        self.done.emit()
        self.choicemade = True

    def closeEvent(self, event):
        event.accept()  # let the window close
        if not self.choicemade:
            log.info("closing test choice window manually, quiting the app")
            sys.exit(1)


class PackingWindow(QtGui.QMainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.initUI()

    def initUI(self):
        log.debug("creating main window")
        # ---------Window settings --------------------------------
        # self.setGeometry(300, 300, 280, 170)
        self.setWindowIcon(QtGui.QIcon(":/icons/qnectarcam.png"))
        if not QtGui.QDesktopWidget().isVirtualDesktop():
            screenWidth = (QtGui.QDesktopWidget().availableGeometry(
            ).width() / QtGui.QDesktopWidget().numScreens())
        else:
            screenWidth = (QtGui.QDesktopWidget().availableGeometry().width())
        screenHeight = QtGui.QDesktopWidget().availableGeometry().height()
        mainWinWidth = screenWidth * 0.7
        mainWinHeight = screenHeight * 0.65
        self.resize(mainWinWidth, mainWinHeight)
        # centerMainWin(self)
        centerOnScreen(self)
        # self.move(0, 0)
        self.setWindowTitle('FEB Packing')
        self.show()

        # mainWidget = MyRoundWidget()
        mainWidget = QtGui.QWidget()
        self.setCentralWidget(mainWidget)
        mainlayout = QtGui.QGridLayout()
        mainlayout.setSpacing(10)
        mainWidget.setLayout(mainlayout)
        # make it scrollable
        scrollWidget = QtGui.QScrollArea()
        scrollWidget.setWidget(mainWidget)
        scrollWidget.setWidgetResizable(True)
        self.setCentralWidget(scrollWidget)
        # log
        logWidth = mainWidget.frameGeometry().width() - sidePanelWidth
        logHeight = 200
        self.logwin = LogWidget(mainWidget, logWidth, logHeight)
        mainlayout.addWidget(self.logwin, 1, 0)
        log.debug("log widget added to main window")
        # timer
        self.MainTimer = WidgetTimer("in main window")
        self.MainTimer.setMaximumHeight(150)
        mainlayout.addWidget(self.MainTimer, 0, 1)
        log.debug("self.MainTimer {}".format(self.MainTimer))
        # main widget showing progress
        self.progressWidg = QtGui.QWidget(parent=mainWidget)
        mainlayout.addWidget(self.progressWidg, 0, 0)
        log.debug("progressWidg widget added to main window")
        self.progressWidg.layout = QtGui.QGridLayout()
        self.progressWidg.setLayout(self.progressWidg.layout)

    def closeEvent(self, event):

        reply = QtGui.QMessageBox.question(self, 'Message',
                                           "Really quit?",
                                           QtGui.QMessageBox.Yes |
                                           QtGui.QMessageBox.No,
                                           QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            # bye = QtGui.QMessageBox()
            # bye.setText("Quiting")
            # bye.show()
            # timer = QtCore.QTimer()
            # timer.setSingleShot(True)
            # waitmsec = 2000
            # timer.timeout.connect(sys.exit)
            # timer.start(waitmsec)
            sys.exit()
        else:
            event.ignore()
