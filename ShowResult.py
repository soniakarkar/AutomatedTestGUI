# !/usr/bin/env python
# coding:utf-8
"""
:Author: Sonia Karkar -- karkar@in2p3.fr

:What:

"""
# from __future__ import unicode_literals
from PyQt4 import QtGui, QtCore
# from PyQt4.QtCore import pyqtSlot
import os
from errors import Type1Error, Type2Error
import numpy as np
from TestUtils import PrepareTests, ParseQRCode
import TestsWidgets
import analyseTest1
from qtUtils import Worker, ImageViewer, WidgetTimer
from TestStucture import RunTest
from argparse import Namespace
from LogUtils import MyLog
if __name__ == "__main__":
    logname = os.path.basename(__file__)[:-3]
else:
    logname = __name__
if len(logname) > 20:
    logname = logname[:9] + "--" + logname[-9:]
log = MyLog(logname, qt=True, logdir=os.getenv("HOME") + "/log/")
import logging
# log.setLevel(logging.DEBUG)
icon_ok_file = "./icon_ok.png"
icon_failed_file = "./icon_failed.png"


def CreateResultlabel(widget):
    resultLabel = QtGui.QTextEdit(widget)
    resultLabel.setReadOnly(True)
    log.debug("resultLabel {}".format(resultLabel))
    grid = QtGui.QGridLayout()
    log.debug("grid {}".format(grid))
    grid.addWidget(resultLabel, 0, 1)
    widget.setLayout(grid)
    return resultLabel, grid


def PrintResult(ResultLabel, MainWin, printresult, itest):
    log.debug("printresult {}".format(printresult))
    ResultLabel.insertPlainText(printresult)
    if((MainWin.ObjectTested is not None)
       and (MainWin.ObjectTested.results[itest])):
        log.debug("MainWin.ObjectTested.results[itest] {}".format(
            MainWin.ObjectTested.results[itest]))
        ResultLabel.setStyleSheet(
            "background-color: green;padding: 5px; border-radius: 20px")
        # MainWin.tabs.tabBar().MySetTabIcon(itest, icon_ok_file)
        MainWin.tabs.tabBar().MySetTabColor(itest,
                                            QtGui.QColor(QtCore.Qt.darkGreen))
    else:
        log.debug("bad result")
        ResultLabel.setStyleSheet(
            "background-color: red; padding: 5px; border-radius: 20px")
        # MainWin.tabs.tabBar().MySetTabIcon(itest, icon_failed_file)
        MainWin.tabs.tabBar().MySetTabColor(itest,
                                            QtGui.QColor(QtCore.Qt.red))
    # sb = ResultLabel.verticalScrollBar()
    # sb.setValue(sb.maximum())


class Test0(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(Test0, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        self.myWin = parent
        log.debug("myWin {}".format(self.myWin))
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        testwidget = self.myWin.tabs.widget(self.itest).TestWidget
        testwidget.QRCode.connect(self.receiveObjectTestedNumber)
        testwidget.giveObjectTestedNumber()
        log.debug("self.QRCode {}".format(self.QRCode))
        self.PrintResultSig.connect(lambda: PrintResult(self.resultLabel,
                                                        self.myWin,
                                                        self.printresult,
                                                        self.itest))
        self.initUI()

    def initUI(self):
        log.debug("initUI result Widget " + str(type(self).__name__))
        self.resultLabel, self.layout = CreateResultlabel(self)
        self.timer = WidgetTimer("in " + logname + str(type(self).__name__))
        self.layout.addWidget(self.timer)

    def Run(self):
        try:
            self.timer.start()
            log.debug("self.timer {} started".format(self.timer))
            self.printresult = ""
            newObjectTestedid, newObjectTestedversion = ParseQRCode(
                self.QRCode)
            if (newObjectTestedid is None) or (newObjectTestedversion is None):
                self.myWin.StopAfterShow = True
                self.printresult += "bad code :  {}".format(self.QRCode)
                raise Type1Error(self.QRCode)
            log.debug("self.myWin.mainargs {}".format(self.myWin.mainargs))
            self.myWin.args = Namespace(
                ObjectTestedid=newObjectTestedid,
                ObjectTestedversion=newObjectTestedversion,
                xmlFile=self.myWin.mainargs.xmlFile,
            )
            log.debug("self.myWin.args {}".format(self.myWin.args))
            theObjectTested = PrepareTests(newObjectTestedid)
            self.myWin.ObjectTested = theObjectTested
            self.myWin.ObjectTested.results = np.zeros(
                len(self.myWin.testsList), bool)
            self.myWin.ObjectTested.results[self.itest] = True
            log.info(
                "will be using this ObjectTested : \n {}".format(
                    theObjectTested.listentry))
            self.printresult += "{}".format(self.myWin.ObjectTested.listentry)

        except Exception as err:
            if type(err)is Type1Error:
                raise
            else:
                mymsg = ("{}".format(err.args[0]))
                log.error(mymsg)
                self.SafeExit()
                raise Exception(mymsg)
        finally:
            self.PrintResultSig.emit()
            duration = self.timer.stop()
            log.debug("self.timer {} stopped".format(self.timer))
            log.debug("this test took {} ".format(duration))
            self.myWin.ResultTimers[self.itest] = duration

    def receiveObjectTestedNumber(self, ObjectTestedNumber):
        self.QRCode = str(ObjectTestedNumber)
        log.debug("self.QRCode %s", self.QRCode)

    def SafeExit(self):
        pass


class Test1(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(Test1, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        log.debug("parent {}".format(parent))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        testwidget = self.myWin.tabs.widget(self.itest).TestWidget
        testwidget.datadir.connect(self.receiveDatadir)
        testwidget.giveDatadir()
        log.debug("self.Test1datadir {}".format(self.Test1datadir))
        self.PrintResultSig.connect(lambda: PrintResult(self.resultLabel,
                                                        self.myWin,
                                                        self.printresult,
                                                        self.itest))
        self.initUI()

    def initUI(self):
        log.debug("initUI result Widget " + str(type(self).__name__))
        self.resultLabel, self.layout = CreateResultlabel(self)
        self.timer = WidgetTimer("in " + logname + str(type(self).__name__))
        self.layout.addWidget(self.timer)
        self.displayImage = ImageViewer(QtCore.QSize(1000, 600))
        self.layout.addWidget(self.displayImage, 1, 1)

    def Run(self):
        try:
            self.timer.start()
            log.info("Starting to analyse Test1 Data")
            a, Result = self.myWin.ObjectTested.analyseTest1(self.Test1datadir)
            log.debug("%s, %s", a, Result)
            try:
                reportfile = open(self.Test1datadir + "/"
                                  + "analyseTest1_report.txt", "r")
            except Exception:
                log.error("couldnt open report file : %s", self.Test1datadir
                          + "/" + "analyseTest1_report.txt")
            log.debug("%s", reportfile)
            self.printresult = ""
            for line in reportfile.readlines():
                self.printresult += line

            for col in self.myWin.ObjectTested.Tests.columns:
                self.printresult += "\n {} {}".format(
                    self.myWin.ObjectTested.Tests[col].name,
                    self.myWin.ObjectTested.Tests[col].values
                )
            self.myWin.ObjectTested.results[self.itest] = Result
            if not Result:
                self.myWin.StopAfterShow = True
            self.PrintResultSig.emit()
            self.displayImage.setDirectory("plots")
            self.displayImage.update()
            duration = self.timer.stop()
            log.debug("this test took {} ".format(duration))
            self.myWin.ResultTimers[self.itest] = duration
        except Exception as err:
            mymsg = ("{}".format(err.args[0]))
            log.error(mymsg)
            self.SafeExit()
            raise Exception(mymsg)

    def SafeExit(self):
        pass

    def receiveDatadir(self, datadir):
        self.Test1datadir = str(datadir)
