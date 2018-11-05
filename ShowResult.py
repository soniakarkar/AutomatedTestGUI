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
from errors import MissingInstrumentsError, MissingSignalError, BoardPowerError
import subprocess
from ConfigParser import ConfigParser
import numpy as np
import ToolBox
import analysePattern
import analyseL0PedScan
import analyseStartCheck
import analyseNF
import analyseOneFreeCell
import analyseCheckFEBandTrigBoard
import analyseL0L1PulseSizeScan
import TestsWidgets
from qtUtils import Worker, ImageViewer, WidgetTimer
from TakeDataCheckChipStart import prepareForStartCheck, StartCheckPedestal
from TakeDataCheckChipStart import mainStartCheckLoop, cleanAfterStartCheck
from TestStucture import RunTest
from SlowControlUtils import CreateDataFolders
from errors import MissingInstrumentsError, BadFEBIdError
import PrepareTests
from AnalysisParameters import currentFEBVersion
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


def CheckFebCode(FEBCode):
    newfebid = None
    newfebversion = None
    infolist = FEBCode.split("/")
    log.debug("infolist {}".format(infolist))
    if len(infolist) == 3:
        newfebid = str(infolist[2])
        log.debug("newfebid {}".format(newfebid))
        newfebversion = str(infolist[1])
        log.debug("newfebversion {}".format(newfebversion))
        newpbs = str(infolist[0])
        log.debug("newpbs {}".format(newpbs))
        pbsok = (newpbs == '1.2') or (newpbs == '7.3N.1.2')
        log.debug("pbsok {}".format(pbsok))
        febidok = (len(newfebid) == 4)
        log.debug("febidok {}".format(febidok))
        febversionok = (newfebversion == str(currentFEBVersion))
        log.debug("febversionok {}".format(febversionok))
        pbm = not(pbsok and febidok and febversionok)
    else:
        pbm = True
    if pbm:
        newfebid = None
        newfebversion = None
    return newfebid, newfebversion


def PrintResult(ResultLabel, MainWin, printresult, itest):
    log.debug("printresult {}".format(printresult))
    ResultLabel.insertPlainText(printresult)
    if(MainWin.feb is not None) and (MainWin.feb.results[itest]):
        log.debug("MainWin.feb.results[itest] {}".format(
            MainWin.feb.results[itest]))
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


class ScanFeb(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(ScanFeb, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        self.myWin = parent
        log.debug("myWin {}".format(self.myWin))
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        testwidget = self.myWin.tabs.widget(self.itest).TestWidget
        testwidget.FEBQRCode.connect(self.receiveFEBNumber)
        testwidget.giveFEBNumber()
        log.debug("self.FEBCode {}".format(self.FEBCode))
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
            newfebid, newfebversion = CheckFebCode(self.FEBCode)
            if (newfebid is None) or (newfebversion is None):
                self.myWin.StopAfterShow = True
                self.printresult += "bad code :  {}".format(self.FEBCode)
                raise BadFEBIdError(self.FEBCode)
            log.debug("self.myWin.mainargs {}".format(self.myWin.mainargs))
            self.myWin.args = Namespace(
                febid=newfebid,
                febversion=newfebversion,
                xmlFile=self.myWin.mainargs.xmlFile,
                TakeDataExe=self.myWin.mainargs.TakeDataExe,
                OPCUAServerExe=self.myWin.mainargs.OPCUAServerExe,
                URLOPCUAServer=self.myWin.mainargs.URLOPCUAServer
                # xmlFile="/home/nectar/Desktop/defaultFEBTest.xml",
                # TakeDataExe="/opt/bin/TakeData",
                # OPCUAServerExe="/opt/bin/qNectarCamOpcUaServer",
                # URLOPCUAServer="opc.tcp://localhost.localdomain:48010"
            )
            log.debug("self.myWin.args {}".format(self.myWin.args))
            thefeb = PrepareTests.main(self.myWin.args)
            self.myWin.feb = thefeb
            self.myWin.feb.results = np.zeros(len(self.myWin.testsList), bool)
            self.myWin.feb.results[self.itest] = True
            log.info(
                "will be using this feb : \n {}".format(
                    thefeb.listentry))
            self.printresult += "{}".format(self.myWin.feb.listentry)

        except Exception as err:
            if type(err)is BadFEBIdError:
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

    def receiveFEBNumber(self, FEBNumber):
        self.FEBCode = str(FEBNumber)
        log.debug("self.FEBCode %s", self.FEBCode)

    def SafeExit(self):
        pass


class CheckInstrumentsConnexion(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(CheckInstrumentsConnexion, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        log.debug("parent {}".format(parent))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        self.PrintResultSig.connect(lambda: PrintResult(self.resultLabel,
                                                        self.myWin,
                                                        self.printresult,
                                                        self.itest))
        self.initUI()

    def initUI(self):
        log.debug("initUI ScanFeb result Widget" + str(type(self).__name__))
        self.resultLabel, self.layout = CreateResultlabel(self)
        self.timer = WidgetTimer("in " + logname + str(type(self).__name__))
        self.layout.addWidget(self.timer)

    def Run(self):
        try:
            self.timer.start()
            log.debug("self.timer {} started".format(self.timer))
            self.printresult = ""
            okinstruments = [x.__name__.replace("Check", "")
                             for x in self.myWin.tabs.widget(
                self.itest).TestWidget.instrumentsCheck[
                np.where(self.myWin.tabs.widget(
                    self.itest).TestWidget.oks)]
            ]
            if len(okinstruments) > 0:
                self.printresult += "instruments connected:\n"
                for line in okinstruments:
                    self.printresult += line + "\n"
            missinginstruments = [x.__name__.replace("Check", "")
                                  for x in self.myWin.tabs.widget(
                self.itest).TestWidget.instrumentsCheck[
                np.where(np.logical_not(self.myWin.tabs.widget(
                    self.itest).TestWidget.oks))]
            ]
            if len(missinginstruments) > 0:
                self.printresult += "instruments missing:\n"
                for line in missinginstruments:
                    self.printresult += line + "\n"
            log.debug("self.myWin.feb.results[self.itest] {}".format(
                self.myWin.feb.results[self.itest]))
            self.PrintResultSig.emit()
            duration = self.timer.stop()
            log.debug("self.timer {} stopped".format(self.timer))
            log.debug("this test took {} ".format(duration))
            self.myWin.ResultTimers[self.itest] = duration

        except Exception as err:
            log.debug("type(err) {}".format(type(err)))
            mymsg = ("{}".format(err.args[0]))
            log.error(mymsg)
            self.SafeExit()
            raise Exception(mymsg)

        if not self.myWin.feb.results[self.itest]:
            self.myWin.StopAfterShow = True
            raise MissingInstrumentsError(missinginstruments)

    def SafeExit(self):
        pass


class Pattern(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(Pattern, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        log.debug("parent {}".format(parent))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        testwidget = self.myWin.tabs.widget(self.itest).TestWidget
        testwidget.datadir.connect(self.receiveDatadir)
        testwidget.giveDatadir()
        log.debug("self.patterndatadir {}".format(self.patterndatadir))
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
            configfile = self.patterndatadir + "/Pattern.cfg"
            log.debug("configfile {}".format(configfile))
            config = ConfigParser()
            config.read(configfile)
            config.set("Directories", "DataDir", self.patterndatadir)
            config.set("Directories", "OutDir", self.patterndatadir + "/plots")
            config.write(open(configfile, "w"))
            log.info("Starting to analyse Pattern Data")
            a, Result = self.myWin.feb.analysePattern(configfile)
            Prefix = "FEB_{}_{}".format(
                self.myWin.feb.version, self.myWin.feb.id)
            reportfile = open(self.patterndatadir +
                              Prefix + "_report.txt", "r")
            self.printresult = ""
            for line in reportfile.readlines():
                self.printresult += line
            for col in ["Voltage", "Current", "Pattern", "SigmaPattern"]:
                self.printresult += "\n {} {}".format(
                    self.myWin.feb.FebTests[col].name,
                    self.myWin.feb.FebTests[col].values
                )
            # self.resultLabel.insertPlainText(printresult)
            self.myWin.feb.results[self.itest] = Result
            if not Result:
                self.myWin.StopAfterShow = True
            self.PrintResultSig.emit()
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
        self.patterndatadir = str(datadir)


# class ConnectSignal(QtGui.QWidget):
#     PrintResultSig = QtCore.pyqtSignal()
#     def __init__(self, parent):
#         super(ConnectSignal, self).__init__(parent)
#         log.debug("creating Result Widget " + str(type(self).__name__))
#         log.debug("parent {}".format(parent))
#         self.myWin = parent
#         self.itest = self.myWin.testsList.index(str(type(self).__name__))
#         self.PrintResultSig.connect(lambda: PrintResult(self.resultLabel,
#                                                 self.myWin,
#                                                 self.printresult,
#                                                 self.itest))
#         self.initUI()
#
#     def initUI(self):
#         log.debug("initUI result Widget " + str(type(self).__name__))
#         self.resultLabel, self.layout = CreateResultlabel(self)
#         self.timer = WidgetTimer("in " + logname + str(type(self).__name__))
#         self.layout.addWidget(self.timer)
#
#     def Run(self):
#         self.myWin.feb.results[self.itest] = True
#         self.printresult = "check of connection will happen later"
#         self.PrintResultSig.emit()
#
#     def SafeExit(self):
#         # disconnect from instruments and FEB
#         for instrument in [self.myWin.PS, self.myWin.lecroy, self.myWin.att]:
#             try:
#                 instrument.realClose()
#             except:
#                 log.error("couldnt clean connexion to {}".format(instrument))


class CheckConnectSignal(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(CheckConnectSignal, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        log.debug("parent {}".format(parent))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        testwidget = self.myWin.tabs.widget(self.itest).TestWidget
        testwidget.datadir.connect(self.receiveDatadir)
        testwidget.giveDatadir()
        log.debug("self.SingleStartCheckdatadir {}".format(
            self.SingleStartCheckdatadir))
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
            self.printresult = "Checking Signal Input\n"
            Prefix = "FEB_{}_{}".format(
                self.myWin.feb.version, self.myWin.feb.id)
            reportfile = open(self.SingleStartCheckdatadir +
                              Prefix + "_report.txt", "r")
            for line in reportfile.readlines():
                self.printresult += line

            self.PrintResultSig.emit()
            duration = self.timer.stop()
            log.debug("this test took {} ".format(duration))
            self.myWin.ResultTimers[self.itest] = duration
        except Exception as err:
            mymsg = ("{}".format(err.args[0]))
            log.error(mymsg)
            self.SafeExit()
            raise Exception(mymsg)
        if not self.myWin.feb.results[self.itest]:
            self.myWin.StopAfterShow = True
            raise MissingSignalError(self.SingleStartCheckdatadir)

    def receiveDatadir(self, datadir):
        self.SingleStartCheckdatadir = str(datadir)

    def SafeExit(self):
        # disconnect from instruments and FEB
        for instrument in [self.myWin.PS, self.myWin.lecroy, self.myWin.att]:
            try:
                instrument.realClose()
            except:
                log.error("couldnt clean connexion to {}".format(instrument))


class IBOF(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(IBOF, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        log.debug("parent {}".format(parent))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        testwidget = self.myWin.tabs.widget(self.itest).TestWidget
        testwidget.datadir.connect(self.receiveDatadir)
        testwidget.giveDatadir()
        log.debug("self.IBOFdatadir {}".format(
            self.IBOFdatadir))
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
            # Prefix = "FEB_{}_{}".format(
            #     self.myWin.feb.version, self.myWin.feb.id)
            self.resultLabel.insertPlainText("")
            gainfile = open(self.IBOFdatadir + "pedestals.txt", "r")
            icffile = open(self.IBOFdatadir + "IBOFs.txt", "r")
            self.printresult = ("Ibof ajusted xml is available at "
                                + self.IBOFdatadir + "\n")
            for line in icffile.readlines():
                self.printresult += line
            for line in gainfile.readlines():
                self.printresult += line
            self.PrintResultSig.emit()
            duration = self.timer.stop()
            log.debug("this test took {} ".format(duration))
            self.myWin.ResultTimers[self.itest] = duration
        except Exception as err:
            mymsg = ("{}".format(err.args[0]))
            log.error(mymsg)
            self.SafeExit()
            raise Exception(mymsg)

    def receiveDatadir(self, datadir):
        self.IBOFdatadir = str(datadir)

    def SafeExit(self):
        # disconnect from instruments and FEB
        for instrument in [self.myWin.PS, self.myWin.lecroy, self.myWin.att]:
            try:
                instrument.realClose()
            except:
                log.error("couldnt clean connexion to {}".format(instrument))


class CheckFEBandTrigBoard(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(CheckFEBandTrigBoard, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        log.debug("parent {}".format(parent))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        testwidget = self.myWin.tabs.widget(self.itest).TestWidget
        testwidget.datadir.connect(self.receiveDatadir)
        testwidget.giveDatadir()
        log.debug("self.datadir {}".format(self.datadir))
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
            self.resultLabel.insertPlainText(
                "Checking FEB and Trigger board connection\n")
            configfile = self.datadir + "/CheckFEBandTrigBoard.cfg"
            log.debug("configfile {}".format(configfile))
            config = ConfigParser()
            config.read(configfile)
            config.set("Directories", "DataDir", self.datadir)
            config.set("Directories", "OutDir", self.datadir + "/plots")
            config.write(open(configfile, "w"))
            log.info("Starting to analyse CheckFEBandTrigBoard Data")
            a, self.printresult, Result = self.myWin.feb.analyseCheckFEBandTrigBoard(
                configfile)
            self.myWin.feb.results[self.itest] = Result
            self.PrintResultSig.emit()
            duration = self.timer.stop()
            log.debug("this test took {} ".format(duration))
            self.myWin.ResultTimers[self.itest] = duration
        except Exception as err:
            mymsg = ("{}".format(err.args[0]))
            log.error(mymsg)
            self.SafeExit()
            raise Exception(mymsg)
        if not self.myWin.feb.results[self.itest]:
            self.myWin.StopAfterShow = True
            raise BoardPowerError(self.printresult)

    def SafeExit(self):
        pass

    def receiveDatadir(self, datadir):
        self.datadir = str(datadir)


class DACL(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(DACL, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        log.debug("parent {}".format(parent))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        testwidget = self.myWin.tabs.widget(self.itest).TestWidget
        testwidget.datadir.connect(self.receiveDatadir)
        testwidget.giveDatadir()
        log.debug("self.DACLdatadir {}".format(self.DACLdatadir))
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
            configfile = self.DACLdatadir + "/DACL.cfg"
            log.debug("configfile {}".format(configfile))
            config = ConfigParser()
            config.read(configfile)
            config.set("Directories", "DataDir", self.DACLdatadir)
            config.set("Directories", "OutDir", self.DACLdatadir + "/plots")
            config.write(open(configfile, "w"))
            log.info("Starting to analyse DACL Data")
            dacl = ToolBox.ToolBox(configfile=configfile)
            dacl.ProcessAllFiles()
            Prefix = "FEB_{}_{}".format(
                self.myWin.feb.version, self.myWin.feb.id)
            self.printresult = "xml file with calibrated DACL "
            self.printresult += Prefix + "/DACLCalibValues.xml \n"
            self.printresult += "has been updated with data from "
            self.printresult += self.DACLdatadir
            Result = True
            self.myWin.feb.results[self.itest] = Result
            self.PrintResultSig.emit()
            self.displayImage.setDirectory(self.DACLdatadir + "/plots")
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
        self.DACLdatadir = str(datadir)


class NF(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(NF, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        log.debug("parent {}".format(parent))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        testwidget = self.myWin.tabs.widget(self.itest).TestWidget
        testwidget.datadir.connect(self.receiveDatadir)
        testwidget.giveDatadir()
        log.debug("self.NFdatadir {}".format(self.NFdatadir))
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
            configfile = self.NFdatadir + "/NF.cfg"
            log.debug("configfile {}".format(configfile))
            config = ConfigParser()
            config.read(configfile)
            config.set("Directories", "DataDir", self.NFdatadir)
            config.set("Directories", "OutDir", self.NFdatadir + "/plots")
            config.write(open(configfile, "w"))
            log.info("Starting to plot NF Data")
            nf = ToolBox.ToolBox(configfile=configfile)
            nf.ProcessAllFiles()

            config.set("Parse", "firsttimeplot", "False")
            config.write(open(configfile, "w"))
            a, Result = self.myWin.feb.analyseNF(configfile)
            Prefix = "FEB_{}_{}".format(
                self.myWin.feb.version, self.myWin.feb.id)
            reportfile = open(self.NFdatadir +
                              Prefix + "_report.txt", "r")
            self.printresult = ""
            for line in reportfile.readlines():
                self.printresult += line
            OneCellConfigfile = Prefix + "/NF/ChargeHisto.cfg"
            subprocess.call(['cp', OneCellConfigfile, self.NFdatadir +
                             "/" + "/ChargeHisto.cfg"])
            configfilefree = self.NFdatadir + "/ChargeHisto.cfg"
            log.debug("configfilefree {}".format(configfilefree))
            configfree = ConfigParser()
            configfree.read(configfilefree)
            configfree.set("Directories", "DataDir", self.NFdatadir)
            configfree.set("Directories", "OutDir", self.NFdatadir + "/plots")
            configfree.write(open(configfilefree, "w"))
            log.info("Starting to plot 1 free cell Data")
            free = ToolBox.ToolBox(configfile=configfilefree)
            free.ProcessAllFiles()
            a2, Result2 = self.myWin.feb.analyseOneFree(configfilefree)
            reportfile2 = open(self.NFdatadir +
                               Prefix + "NF001" + "_report.txt", "r")
            for line in reportfile2.readlines():
                self.printresult += line
            self.myWin.feb.results[self.itest] = Result & Result2
            self.PrintResultSig.emit()
            self.displayImage.setDirectory(self.NFdatadir + "/plots")
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
        self.NFdatadir = str(datadir)


class L0PedScan(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(L0PedScan, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        log.debug("parent {}".format(parent))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        testwidget = self.myWin.tabs.widget(self.itest).TestWidget
        testwidget.datadir.connect(self.receiveDatadir)
        testwidget.giveDatadir()
        log.debug("self.L0PedScandatadir {}".format(self.L0PedScandatadir))
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
            configfile = self.L0PedScandatadir + "/L0PedScan.cfg"
            log.debug("configfile {}".format(configfile))
            config = ConfigParser()
            config.read(configfile)
            config.set("Directories", "DataDir", self.L0PedScandatadir)
            config.set("Directories", "OutDir",
                       self.L0PedScandatadir + "/plots")
            config.write(open(configfile, "w"))
            log.info("Starting to analyse L0PedScan Data")
            Result = self.myWin.feb.analyseL0PedScan(configfile, doplot=False)
            self.myWin.feb.results[self.itest] = Result
            Prefix = "FEB_{}_{}".format(
                self.myWin.feb.version, self.myWin.feb.id)
            self.printresult = self.L0PedScandatadir + "\n"
            log.debug("self.printresult %s", self.printresult)
            reportfile = open(self.L0PedScandatadir +
                              Prefix + "L0att00_report.txt", "r")
            log.debug("att00 report file %s", reportfile)
            for line in reportfile.readlines():
                self.printresult += line
            reportfile = open(self.L0PedScandatadir +
                              Prefix + "L0att07_report.txt", "r")
            log.debug("att07 report file %s", reportfile)
            for line in reportfile.readlines():
                self.printresult += line
            log.debug("self.printresult %s", self.printresult)
            self.PrintResultSig.emit()
            self.displayImage.setDirectory(self.L0PedScandatadir + "/plots")
            self.displayImage.update()
            duration = self.timer.stop()
            log.debug("duration of this test {}".format(duration))
            self.myWin.ResultTimers[self.itest] = duration
        except Exception as err:
            mymsg = ("{}".format(err.args[0]))
            log.error(mymsg)
            self.SafeExit()
            raise Exception(mymsg)

    def SafeExit(self):
        pass

    def receiveDatadir(self, datadir):
        self.L0PedScandatadir = str(datadir)


class StartCheck(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(StartCheck, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        log.debug("parent {}".format(parent))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        testwidget = self.myWin.tabs.widget(self.itest).TestWidget
        testwidget.datadir.connect(self.receiveDatadir)
        testwidget.giveDatadir()
        log.debug("self.StartCheckdatadir {}".format(self.StartCheckdatadir))
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
        # self.displayImage.setMinimumSize(QtCore.QSize(800, 600))
        self.layout.addWidget(self.displayImage, 1, 1)

    def receiveDatadir(self, datadir):
        self.StartCheckdatadir = str(datadir)

    def Run(self):
        try:
            self.timer.start()
            self.resultLabel.insertPlainText("")
            configfileStartCheck = (self.StartCheckdatadir
                                    + "/StartCheck.cfg")
            configStartCheck = ConfigParser()
            configStartCheck.read(configfileStartCheck)
            configStartCheck.set(
                "Directories", "DataDir", self.StartCheckdatadir)
            configStartCheck.set("Directories", "OutDir",
                                 self.StartCheckdatadir + "/plots")
            configStartCheck.set("PlotFlag",
                                 "pedestalFile",
                                 self.StartCheckdatadir + "/"
                                 + self.myWin.feb.prefix + "pedestal.h5")
            configStartCheck.write(open(configfileStartCheck, "w"))
            log.info("Starting to analyse StartCheck Data")
            StartCheck = ToolBox.ToolBox(configfile=configfileStartCheck)
            StartCheck.ProcessAllFiles()
            a, Result = self.myWin.feb.analyseStartCheck(
                configfileStartCheck)
            Prefix = "FEB_{}_{}".format(
                self.myWin.feb.version, self.myWin.feb.id)
            reportfile = open(self.StartCheckdatadir +
                              Prefix + "_report.txt", "r")
            self.printresult = self.StartCheckdatadir + "/plots" + "\n"
            for line in reportfile.readlines():
                self.printresult += line
            self.myWin.feb.results[self.itest] = Result
            self.PrintResultSig.emit()
            self.displayImage.setDirectory(self.StartCheckdatadir + "/plots")
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
        # disconnect from instruments and FEB
        for instrument in [self.PS, self.lecroy]:
            try:
                instrument.realClose()
            except:
                log.error("couldnt clean connexion to {}".format(instrument))


class ICF(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(ICF, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        log.debug("parent {}".format(parent))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        testwidget = self.myWin.tabs.widget(self.itest).TestWidget
        testwidget.datadir.connect(self.receiveDatadir)
        testwidget.giveDatadir()
        log.debug("self.ICFdatadir {}".format(self.ICFdatadir))
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
        # self.displayImage = ImageViewer(QtCore.QSize(1000, 600))
        # self.displayImage.setMinimumSize(QtCore.QSize(800, 600))
        # self.layout.addWidget(self.displayImage, 1, 1)

    def receiveDatadir(self, datadir):
        self.ICFdatadir = str(datadir)

    def Run(self):
        try:
            self.timer.start()
            self.resultLabel.insertPlainText("")
            gainfile = open(self.ICFdatadir + "gains.txt", "r")
            icffile = open(self.ICFdatadir + "icfs.txt", "r")
            self.printresult = self.ICFdatadir + "/plots" + "\n"
            for line in icffile.readlines():
                self.printresult += line
            for line in gainfile.readlines():
                self.printresult += line
            self.PrintResultSig.emit()
            # self.displayImage.setDirectory(self.ICFdatadir + "/plots")
            # self.displayImage.update()
            duration = self.timer.stop()
            log.debug("this test took {} ".format(duration))
            self.myWin.ResultTimers[self.itest] = duration
        except Exception as err:
            mymsg = ("{}".format(err.args[0]))
            log.error(mymsg)
            self.SafeExit()
            raise Exception(mymsg)

    def SafeExit(self):
        # disconnect from instruments and FEB
        for instrument in [self.PS, self.lecroy]:
            try:
                instrument.realClose()
            except:
                log.error("couldnt clean connexion to {}".format(instrument))


class ConnectHVPA(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(ConnectHVPA, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        log.debug("myWin {}".format(self.myWin))
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
            self.printresult = "Thanks for connecting the HVPA board"
            self.myWin.feb.results[self.itest] = True
            self.PrintResultSig.emit()
            duration = self.timer.stop()
            log.debug("self.timer {} stopped".format(self.timer))
            log.debug("this test took {} ".format(duration))
            self.myWin.ResultTimers[self.itest] = duration
        except Exception as err:
            mymsg = ("{}".format(err.args[0]))
            log.error(mymsg)
            self.SafeExit()
            raise Exception(mymsg)

    def SafeExit(self):
        pass


class HVPA(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(HVPA, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        log.debug("myWin {}".format(self.myWin))
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
            self.printresult = "HVPA board test"
            self.myWin.feb.results[self.itest] = True
            self.PrintResultSig.emit()
            duration = self.timer.stop()
            log.debug("self.timer {} stopped".format(self.timer))
            log.debug("this test took {} ".format(duration))
            self.myWin.ResultTimers[self.itest] = duration
        except Exception as err:
            mymsg = ("{}".format(err.args[0]))
            log.error(mymsg)
            self.SafeExit()
            raise Exception(mymsg)

    def SafeExit(self):
        pass


class Linearity(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(Linearity, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        log.debug("parent {}".format(parent))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        testwidget = self.myWin.tabs.widget(self.itest).TestWidget
        testwidget.datadir.connect(self.receiveDatadir)
        testwidget.giveDatadir()
        log.debug("self.Linearitydatadir {}".format(self.Linearitydatadir))
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
        # self.displayImage.setMinimumSize(QtCore.QSize(800, 600))
        self.layout.addWidget(self.displayImage, 1, 1)

    def receiveDatadir(self, datadir):
        self.Linearitydatadir = str(datadir)

    def Run(self):
        try:
            self.timer.start()
            self.resultLabel.insertPlainText("")
            configfileLinearity = (self.Linearitydatadir
                                   + "/Linearity1GSS.cfg")
            configLinearity = ConfigParser()
            configLinearity.read(configfileLinearity)
            configLinearity.set(
                "Directories", "DataDir", self.Linearitydatadir)
            configLinearity.set("Directories", "OutDir",
                                self.Linearitydatadir + "/plots")
            configLinearity.set("PlotFlag",
                                "pedestalFile",
                                self.Linearitydatadir + "/"
                                + self.myWin.feb.prefix + "pedestal.h5")
            configLinearity.write(open(configfileLinearity, "w"))
            log.info("Starting to analyse Linearity Data")
            Linearity = ToolBox.ToolBox(configfile=configfileLinearity)
            Linearity.ProcessAllFiles()
            # a, Result = self.myWin.feb.analyseLinearity(
            #     configfileLinearity)
            Result = True
            self.printresult = self.Linearitydatadir + "/plots"
            # Prefix = "FEB_{}_{}".format(
            #     self.myWin.feb.version, self.myWin.feb.id)
            # reportfile = open(self.Linearitydatadir +
            #                   Prefix + "_report.txt", "r")
            # for line in reportfile.readlines():
            #     self.printresult += line
            self.PrintResultSig.emit()
            self.myWin.feb.results[self.itest] = Result
            self.PrintResultSig.emit()
            self.displayImage.setDirectory(self.Linearitydatadir + "/plots")
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
        # disconnect from instruments and FEB
        for instrument in [self.PS, self.lecroy]:
            try:
                instrument.realClose()
            except:
                log.error("couldnt clean connexion to {}".format(instrument))


class L0L1PulseSizeScan(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(L0L1PulseSizeScan, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        log.debug("parent {}".format(parent))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        testwidget = self.myWin.tabs.widget(self.itest).TestWidget
        testwidget.datadir.connect(self.receiveDatadir)
        testwidget.giveDatadir()
        log.debug("self.LL0L1PulseSizeScandatadir {}".format(
            self.L0L1PulseSizeScandatadir))
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
            configfile = self.L0L1PulseSizeScandatadir + "/L0L1PulseSizeScan.cfg"
            log.debug("configfile {}".format(configfile))
            config = ConfigParser()
            config.read(configfile)
            config.set("Directories", "DataDir", self.L0L1PulseSizeScandatadir)
            config.set("Directories", "OutDir",
                       self.L0L1PulseSizeScandatadir + "/plots")
            config.write(open(configfile, "w"))
            log.info("Starting to analyse L0L1PulseSizeScan Data")
            Result = self.myWin.feb.analyseL0L1PulseSizeScan(
                configfile)
            Prefix = "FEB_{}_{}".format(
                self.myWin.feb.version, self.myWin.feb.id)
            self.printresult = self.L0L1PulseSizeScandatadir + "\n"
            log.debug("self.printresult %s", self.printresult)
            reportfile = open(self.L0L1PulseSizeScandatadir +
                              Prefix + "_report.txt", "r")
            log.debug("report file %s", reportfile)
            for line in reportfile.readlines():
                self.printresult += line
            self.myWin.feb.results[self.itest] = Result
            self.PrintResultSig.emit()
            self.displayImage.setDirectory(
                self.L0L1PulseSizeScandatadir + "/plots")
            self.displayImage.update()
            duration = self.timer.stop()
            log.debug("duration of this test {}".format(duration))
            self.myWin.ResultTimers[self.itest] = duration
        except Exception as err:
            mymsg = ("{}".format(err.args[0]))
            log.error(mymsg)
            self.SafeExit()
            raise Exception(mymsg)

    def SafeExit(self):
        pass

    def receiveDatadir(self, datadir):
        self.L0L1PulseSizeScandatadir = str(datadir)


class DisConnectHVPA(QtGui.QWidget):
    PrintResultSig = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(DisConnectHVPA, self).__init__(parent)
        log.debug("creating Result Widget " + str(type(self).__name__))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        log.debug("myWin {}".format(self.myWin))
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
            self.printresult = "Thanks for unplugging the HVPA board"
            self.myWin.feb.results[self.itest] = True
            self.PrintResultSig.emit()
            duration = self.timer.stop()
            log.debug("self.timer {} stopped".format(self.timer))
            log.debug("this test took {} ".format(duration))
            self.myWin.ResultTimers[self.itest] = duration
        except Exception as err:
            mymsg = ("{}".format(err.args[0]))
            log.error(mymsg)
            self.SafeExit()
            raise Exception(mymsg)

    def SafeExit(self):
        pass
