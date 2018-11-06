# !/usr/bin/env python
# coding:utf-8
"""
:Author: Sonia Karkar -- karkar@in2p3.fr

:What: Widgets for the tests to be used in TestStucture

"""
from PyQt4 import QtGui, QtCore
import ShowResult
import ressources
from qtUtils import WidgetTimer, centerOnScreen, BlinkingInputDialog
# import analyseL0PedScan
import os
import subprocess
import TakeDataTest1
from TestStucture import ShowTestResult
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


def CreateWidgetLabel(widget):
    """
    * This function takes a widget and adds to it a QGridLayout.
    * Then it adds a QLabel as a first element to that layout.
    * The QLabel text is set to the name of the widget class.
    * It returns the QLabel and the QGridLayout

    """
    instructionLabel = QtGui.QLabel(widget)
    log.debug("instructionLabel {}".format(instructionLabel))
    instructionLabel.setText(
        "This is the test " + str(type(widget).__name__))
    instructionLabel.setStyleSheet('padding: 5px; border-radius: 20px')
    grid = QtGui.QGridLayout()
    log.debug("grid {}".format(grid))
    grid.addWidget(instructionLabel, 0, 1)
    widget.setLayout(grid)
    return instructionLabel, grid


class Test0(QtGui.QWidget):
    """
    Widget used by TestStucture.py as part of the MainWindow.
    The Run() method of this widget ask the user to enter some input
    that will be used.
    As an exemple, this input could be the serial number of the item under test
    read from a QR code
    """
    done = QtCore.pyqtSignal()
    QRCode = QtCore.pyqtSignal(QtCore.QString)

    def __init__(self, parent):
        super(Test0, self).__init__(parent)
        log.debug("creating widget " + str(type(self).__name__))
        log.debug("parent {}".format(parent))
        self.myWin = parent
        self.itest = self.myWin.testsList.index("Test0")
        log.debug("self.myWin {}".format(self.myWin))
        self.done.connect(lambda: ShowTestResult(parent, self.itest))
        log.debug("just connected self.done {}".format(self.done))
        self.initUI()

    def initUI(self):
        log.debug("initUI Widget" + str(type(self).__name__))
        self.instructionLabel, self.Gridlayout = CreateWidgetLabel(self)
        self.timer = WidgetTimer("in " + logname + str(type(self).__name__))
        self.Gridlayout.addWidget(self.timer)
        self.imageLabel = QtGui.QLabel()
        self.imageLabel.setPixmap(QtGui.QPixmap(":/images/ScanFeb.jpg"))

        self.dialog = BlinkingInputDialog()
        self.dialog.startBlink(color1=QtGui.QColor(188, 16, 16),
                               color2=QtGui.QColor(229, 131, 2))
        self.dialog.setWindowTitle(str(type(self).__name__))
        centerOnScreen(self.dialog)
        self.dialog.setLabelText("Please enter some input")
        self.dialog.setOkButtonText("Use this input")

        layout = self.dialog.layout()
        layout.addWidget(self.imageLabel)

        self.dialog.accepted.connect(self.mybuttonClicked)

    def Run(self):
        try:
            self.timer.start()
            self.dialog.exec_()
            log.debug("{} is ready ".format(self))
            log.info("waiting for Feb to be scanned")
        except Exception as err:
            mymsg = ("{}".format(err.args[0]))
            log.error(mymsg)
            self.SafeExit()
            raise

    def mybuttonClicked(self):
        log.debug("in buttonClicked self.done {}".format(self.done))
        self.QRCodefield = str(self.dialog.textValue())
        log.debug("self.QRCodefield {}".format(self.QRCodefield))

        duration = self.timer.stop()
        log.debug("this test took {} ".format(duration))
        self.myWin.TestTimers[self.itest] = duration
        self.done.emit()

    def giveObjectTestedNumber(self):
        """uses the qt signal/slot mechanism to communicate across threads"""
        self.QRCode.emit(QtCore.QString(self.QRCodefield))

    def SafeExit(self):
        """Does whatever needs to be done with the testbench to exit safely
        an exemple is to turn off the power supply
        and disconnect from all instruments"""
        pass


class Test1(QtGui.QWidget):

    done = QtCore.pyqtSignal()
    datadir = QtCore.pyqtSignal(QtCore.QString)

    def __init__(self, parent):
        super(Test1, self).__init__(parent)
        log.debug("creating widget " + str(type(self).__name__))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        # link with the next operation: result of this test
        self.done.connect(lambda: ShowTestResult(parent, self.itest))
        log.debug("self.datadir {}".format(self.datadir))
        self.initUI()

    def initUI(self):
        log.debug("initUI Widget" + str(type(self).__name__))
        self.instructionLabel, self.layout = CreateWidgetLabel(self)
        self.timer = WidgetTimer("in " + logname + str(type(self).__name__))
        self.layout.addWidget(self.timer)

    def Run(self):
        try:
            self.timer.start()
            log.debug("should be doing test " + str(type(self).__name__))
            log.info(str(type(self).__name__) + " Test starting")
            # Prevent stopping the test while connecting to instruments
            self.myWin.tabs.widget(
                self.itest).StopThisTestBtn.setEnabled(False)
            self.myWin.ObjectTested.prepareForTest1()
            # allow stopping while in main loop
            self.myWin.tabs.widget(self.itest).StopThisTestBtn.setEnabled(True)
            self.myWin.ObjectTested.mainTest1Loop()
            # prevent stopping while cleaning connections
            self.myWin.tabs.widget(
                self.itest).StopThisTestBtn.setEnabled(False)
            self.Test1datadir = self.myWin.ObjectTested.cleanAfterTest1()
            log.info("Test1 Data in {} ".format(self.Test1datadir))
            duration = self.timer.stop()
            log.debug("this test took {} ".format(duration))
            self.myWin.TestTimers[self.itest] = duration
            self.done.emit()
        except Exception as err:
            mymsg = ("{}".format(err.args[0]))
            log.error(mymsg)
            self.SafeExit()
            raise

    def giveDatadir(self):
        self.datadir.emit(QtCore.QString(self.Test1datadir))

    def SafeExit(self):
        pass


class Test3(QtGui.QWidget):

    done = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(Test3, self).__init__(parent)
        log.debug("creating widget " + str(type(self).__name__))
        self.myWin = parent
        self.itest = self.myWin.testsList.index(str(type(self).__name__))
        # link with the next operation: result of this test
        self.done.connect(lambda: ShowTestResult(parent, self.itest))
        self.initUI()

    def getDiagBackColor(self):
        return self.dialog.palette().color(QtGui.QPalette.Background)

    def setDiagBackColor(self, color):
        pal = self.dialog.palette()
        pal.setColor(QtGui.QPalette.Background, color)
        self.dialog.setPalette(pal)

    def initUI(self):
        log.debug("initUI Widget" + str(type(self).__name__))
        self.instructionLabel, self.layout = CreateWidgetLabel(self)
        self.timer = WidgetTimer("in " + logname + str(type(self).__name__))
        self.layout.addWidget(self.timer, 0, 0)
        self.imageLabel2 = QtGui.QLabel()
        self.imageLabel2.setPixmap(
            QtGui.QPixmap(":/images/DisConnectSignal.png"))
        self.imageLabel2.setScaledContents(True)
        self.imageLabel2.setMaximumSize(600, 300)
        self.layout.addWidget(self.imageLabel2, 1, 0)
        self.imageLabel = QtGui.QLabel()
        self.imageLabel.setPixmap(
            QtGui.QPixmap(":/images/ConnectHVPA.png"))
        self.imageLabel.setScaledContents(True)
        self.imageLabel.setMaximumSize(600, 300)
        self.layout.addWidget(self.imageLabel, 1, 1)

        self.dialog = QtGui.QMessageBox(self)
        self.dialog.setIcon(QtGui.QMessageBox.Warning)
        self.dialog.setWindowTitle(str(type(self).__name__))
        self.dialog.setText("Please (1) disconnet the injection board \n"
                            + "then (2) connect the HVPA test board \n"
                            + " and THEN click OK to continue")
        self.dialog.setStandardButtons(QtGui.QMessageBox.Ok)

        # HVPAfilename = ":/images/ConnectHVPA.png"
        # image = QtGui.QImage(HVPAfilename)
        # self.imageLabel = QtGui.QLabel()
        # self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(image))
        # # diaglayout = QtGui.QVBoxLayout()
        # diaglayout = self.dialog.layout()
        # diaglayout.addWidget(self.imageLabel)
        # # self.dialog.setLayout(diaglayout)

        geom = self.dialog.geometry()
        geom.moveCenter(self.myWin.frameGeometry().center())
        # TODO this is what should work to center the message but fails
        # self.mydialog.move(geom.topLeft())
        # this is the closest to center i've managed to reach
        self.dialog.move(geom.center())
        # this doesnt seem to work with standard button
        # self.mydialog.setButtonText(int, QString)
        self.dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        log.debug("self.mydialog.buttonClicked {}".format(
            self.dialog.buttonClicked))
        self.dialog.buttonClicked.connect(self.Finish)
        color1 = QtGui.QColor(188, 16, 16)
        color2 = QtGui.QColor(229, 131, 2)
        self.color_anim = QtCore.QPropertyAnimation(self, 'DialogBackColor')
        self.color_anim.setStartValue(color2)
        self.color_anim.setKeyValueAt(0.3, color1)
        self.color_anim.setEndValue(color1)
        self.color_anim.setDuration(800)
        self.color_anim.setLoopCount(-1)
        self.color_anim.start()

    def Run(self):
        try:
            # before anything turn off power supply
            self.myWin.PS.AllOFF()
            self.timer.start()
            log.debug("should be doing test " + str(type(self).__name__))
            log.info(str(type(self).__name__) + " Test starting")
            # allow stopping the test
            self.myWin.tabs.widget(self.itest).StopThisTestBtn.setEnabled(True)
            self.dialog.exec_()
        except Exception as err:
            mymsg = ("{}".format(err.args[0]))
            log.error(mymsg)
            self.SafeExit()
            raise

    def Finish(self):
        duration = self.timer.stop()
        log.debug("this test took {} ".format(duration))
        self.myWin.TestTimers[self.itest] = duration
        self.done.emit()

    def SafeExit(self):
        pass

    DialogBackColor = QtCore.pyqtProperty(
        QtGui.QColor, getDiagBackColor, setDiagBackColor)
