#!/usr/bin/env python
# coding:utf-8
"""
:Author: Sonia Karkar -- karkar@in2p3.fr

:What:

"""
# from __future__ import unicode_literals
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtGui import QPainter, QLinearGradient, QWidget,  QBrush
from PyQt4.QtCore import Qt, QRectF
import sys
from PyQt4.QtCore import pyqtRemoveInputHook
import pdb
from LogUtils import MyLog, XStream
import subprocess
import re
import os
# from errors import MissingInstrumentsError, MissingXmlFileError
# from errors import MissingSignalError, MissingDrawerError
from contextlib import contextmanager
if __name__ == "__main__":
    logname = os.path.basename(__file__)[:-3]
else:
    logname = __name__
if len(logname) > 20:
    logname = logname[:9] + "--" + logname[-9:]
# Create a logger with file and console printing
log = MyLog(logname, qt=True, logdir=os.getenv("HOME") + "/log/")
# default logging level is INFO uncomment below for DEBUG
import logging
# log.setLevel(logging.DEBUG)
orange = QtGui.QColor(255, 140, 0)


def pyqt_set_trace():
    '''Set a tracepoint in the Python debugger that works with Qt'''
    pyqtRemoveInputHook()
    # set up the debugger
    debugger = pdb.Pdb()
    debugger.reset()
    # custom next to get outside of function scope
    debugger.do_next(None)  # run the next command
    # frame where the user invoked `pyqt_set_trace()`
    users_frame = sys._getframe().f_back
    debugger.interaction(users_frame, None)


def centerMainWin(win):
    frameGm = win.frameGeometry()
    screen = QtGui.QApplication.desktop().screenNumber(
        QtGui.QApplication.desktop().cursor().pos())
    centerPoint = QtGui.QApplication.desktop().screenGeometry(screen).center()
    frameGm.moveCenter(centerPoint)
    win.move(frameGm.topLeft())


class BlinkingQPaintDevice(QtGui.QPaintDevice):

    def __init__(self):
        QtGui.QPaintDevice.__init__(self)

    def getBackColor(self):
        return self.palette().color(QtGui.QPalette.Background)

    def setBackColor(self, color):
        pal = self.palette()
        pal.setColor(QtGui.QPalette.Background, color)
        self.setPalette(pal)

    backColor = QtCore.pyqtProperty(
        QtGui.QColor, getBackColor, setBackColor)

    def startBlink(self,
                   color1=QtGui.QColor(188, 16, 16),
                   color2=QtGui.QColor(229, 131, 2)):
        self.color_anim = QtCore.QPropertyAnimation(self, 'backColor')
        self.color_anim.setStartValue(color1)
        self.color_anim.setKeyValueAt(0.99, color2)
        self.color_anim.setEndValue(color1)
        self.color_anim.setDuration(500)
        self.color_anim.setLoopCount(-1)
        self.color_anim.start()


class BlinkingInputDialog(BlinkingQPaintDevice, QtGui.QInputDialog):

    backColor = QtCore.pyqtProperty(QtGui.QColor,
                                    BlinkingQPaintDevice.getBackColor,
                                    BlinkingQPaintDevice.setBackColor)

    def __init__(self):
        super(BlinkingInputDialog, self).__init__()


class BlinkingWidget(BlinkingQPaintDevice, QtGui.QWidget):

    backColor = QtCore.pyqtProperty(QtGui.QColor,
                                    BlinkingQPaintDevice.getBackColor,
                                    BlinkingQPaintDevice.setBackColor)

    def __init__(self):
        super(BlinkingWidget, self).__init__()


def centerOnScreen(widget):
    '''centerOnScreen()
    Centers the window on the screen.'''
    mainwin = QtGui.QDesktopWidget()
    # mainwin = QtGui.QApplication.desktop()
    log.debug("widget bieng centered on screen {}".format(widget))
    log.debug("mainwin {}".format(mainwin))
    resolution = mainwin.screenGeometry(widget)
    log.debug("resolution {}".format(resolution))
    log.debug("mainwin.isVirtualDesktop() {}".format(
        mainwin.isVirtualDesktop()))
    log.debug("mainwin.primaryScreen() {}".format(mainwin.primaryScreen()))
    log.debug("mainwin.numScreens() {}".format(mainwin.numScreens()))
    log.debug("mainwin.screenCount() {}".format(mainwin.screenCount()))
    log.debug("mainwin.screenNumber() {}".format(mainwin.screenNumber()))
    if not mainwin.isVirtualDesktop():
        W = resolution.width()
        log.debug("W {}".format(W))
        screenW = W / mainwin.screenCount()
        log.debug("screenW {}".format(screenW))
        widgetw = widget.frameSize().width()
        log.debug("widgetw {}".format(widgetw))
        # this sends all windows to the next scren
        # x = ((1 + mainwin.screenNumber()) * screenW) + (screenW - widgetw) /
        # 2
        x = (mainwin.screenNumber() * screenW) + (screenW - widgetw) / 2
        y = ((resolution.height() / 2) - (widget.frameSize().height() / 2))
    else:
        x = (resolution.width() / 2) - (widget.frameSize().width() / 2)
        y = (resolution.height() / 2) - (widget.frameSize().height() / 2)
    log.debug("x {} , y {} ".format(x, y))
    widget.move(x, y)

# def centerOnScreen(widget):
#     fg = widget.frameGeometry()
#     cp = QtGui.QDesktopWidget().availableGeometry().center()
#     fg.moveCenter(cp)
#     widget.move(fg.topLeft())


# class MyRoundWidget(QtGui.QWidget):
#
#     def __init__(self, master=None):
#         super(MyRoundWidget, self).__init__(master)
#         self.setStyleSheet('border: 1px dark gray; border-radius: 20px')
    # 'border: 2px solid black; border-radius: 10px;')
    # self.setWindowFlags(Qt.FramelessWindowHint)
    # self.setWindowTitle("QLinearGradient Vertical Gradient ")
    # self.setAttribute(Qt.WA_TranslucentBackground)
    # def paintEvent(self, ev):
    #     painter = QPainter(self)
    #     # painter.begin(self)
    #     # gradient = QLinearGradient(
    #     #     QRectF(self.rect()).topLeft(), QRectF(self.rect()).bottomLeft())
    #     # gradient.setColorAt(0.0, Qt.black)
    #     # gradient.setColorAt(0.4, Qt.gray)
    #     # gradient.setColorAt(0.7, Qt.black)
    #     # painter.setBrush(gradient)
    #     painter.setBrush(QBrush(Qt.transparent))
    #     painter.drawRoundedRect(self.rect(), 20.0, 20.0)
    #     # painter.end()


class Worker(QtCore.QThread):
    myexception = QtCore.pyqtSignal(Exception)

    def __init__(self, func, args):
        super(Worker, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        log.debug("starting function in worker{}".format(self.func))
        try:
            self.func(*self.args)
        # except MissingInstrumentsError as err:
        # mymsg = ("MissingInstrumentsError While running {}: {}".format(
        #     self.func.__name__ , err.args[0]))
        #     log.error(mymsg, exc_info=True)
        #     log.debug("type(err) {}".format(type(err)))
        #     log.debug("err.args {}".format(err.args))
        #     self.myexception.emit(err)
        except Exception as err:
            mymsg = ("Exception While running {}: {}".format(
                self.func.__name__, err.args[0]))
            log.error(mymsg, exc_info=True)
            log.debug("type(err) {}".format(type(err)))
            log.debug("err.args {}".format(err.args))
            self.myexception.emit(err)


# Updated so a PyQT4 Designer TabWidget can be promoted to a FingerTabWidget
class FingerTabBarWidget(QtGui.QTabBar):

    def __init__(self, parent=None, *args, **kwargs):
        self.tabSize = QtCore.QSize(kwargs.pop(
            'width', 300), kwargs.pop('height', 50))
        QtGui.QTabBar.__init__(self, parent, *args, **kwargs)
        # TODO fins a way to expand the list when addTab is called
        Maxtab = 100
        self.tabColors = [None] * Maxtab
        self.tabIcon = [None] * Maxtab

    def paintEvent(self, event):
        painter = QtGui.QStylePainter(self)
        option = QtGui.QStyleOptionTab()
        for index in range(self.count()):
            self.initStyleOption(option, index)
            tabRect = self.tabRect(index)
            tabRect.moveLeft(10)
            if self.tabColors[index] is not None:
                option.palette.setColor(
                    QtGui.QPalette.Window, QtGui.QColor(self.tabColors[index]))
            painter.drawControl(QtGui.QStyle.CE_TabBarTabShape, option)
            # if self.tabIcon[index] is not None:
            #     iconRect = self.tabRect(index)
            # painter.drawImage(iconRect, QtGui.QImage(self.tabIcon[index]))
            painter.drawText(tabRect, QtCore.Qt.AlignVCenter |
                             QtCore.Qt.TextDontClip,
                             self.tabText(index))

        painter.end()

    def MySetTabColor(self, index, color):
        self.tabColors[index] = color

    # def MySetTabIcon(self, index, iconfile):
    #     self.tabIcon[index] = iconfile

    def tabSizeHint(self, index):
        return self.tabSize

# Shamelessly stolen from this thread:
#   http://www.riverbankcomputing.com/pipermail/pyqt/2005-December/011724.html


class FingerTabWidget(QtGui.QTabWidget):
    """A QTabWidget equivalent which uses our FingerTabBarWidget"""

    def __init__(self, parent, *args):
        QtGui.QTabWidget.__init__(self, parent, *args)
        self.setTabBar(FingerTabBarWidget(self))


# setTabTextColor(index, color)


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [atoi(c) for c in re.split('(\d+)', text)]


class LogWidget(QtGui.QWidget):

    def __init__(self, parent, width, height):
        super(LogWidget, self).__init__(parent)
        self._console = QtGui.QTextEdit(parent)
        self._console.setReadOnly(True)
        self._console.resize(width, height)
        # self._console.setStyleSheet(
        #     'border: 1px solid black; border-radius: 20px;')
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self._console)
        self.setLayout(layout)
        XStream.stdout().messageWritten.connect(self.handletext)
        XStream.stderr().messageWritten.connect(self.handletext)

    def handletext(self, text):
        self._console.setTextColor(QtCore.Qt.blue)
        if ("ERROR" in text) or ("Error" in text) or ("error" in text):
            self._console.setTextColor(QtCore.Qt.red)
        if "DEBUG" in text:
            self._console.setTextColor(QtCore.Qt.black)
        if "WARNING" in text:
            self._console.setTextColor(orange)
        self._console.insertPlainText(text)
        self._console.moveCursor(QtGui.QTextCursor.End)
        self._console.ensureCursorVisible()
        self._console.setTextColor(QtCore.Qt.black)


class ImageViewer(QtGui.QScrollArea):

    def __init__(self, size):
        super(ImageViewer, self).__init__()
        self._imagesInList = []
        self._count = -1
        self.scaleFactor = 0.0
        self.imageLabel = QtGui.QLabel()
        self.imageLabel.setBackgroundRole(QtGui.QPalette.Base)
        self.imageLabel.setSizePolicy(QtGui.QSizePolicy.Ignored,
                                      QtGui.QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.setBackgroundRole(QtGui.QPalette.Dark)
        self.setWidget(self.imageLabel)

        self.createActions()
        self.createMenus()
        self.showNextAct.setEnabled(True)
        self.showPreviousAct.setEnabled(True)

        self.setMinimumSize(size)
        self.resize(size)
        self.move(QtCore.QPoint(0, 0))

    def setDirectory(self, directory):
        log.debug("directory {}".format(directory))
        log.info("Image directory is {}".format(directory))
        self.directory = directory
        imgLst = subprocess.check_output(
            ["ls", directory]).split("\n")
        imgLst.remove('')
        imgLst.sort(key=natural_keys)
        log.debug("imgLst {}".format(imgLst))
        self._imagesInList = imgLst
        self._count = -1
        self.nextImage()
        self.fitToWindowAct.setChecked(True)
        self.fitToWindow()

    def open(self, fileName):
        fileName = os.path.join(self.directory, fileName)
        if fileName:
            log.debug("fileName {}".format(fileName))
            image = QtGui.QImage(fileName)
            log.debug("image {}".format(image))
            if image.isNull():
                QtGui.QMessageBox.information(self, "Image Viewer",
                                              "Cannot load %s ." % fileName)
                return

            self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(image))
            self.scaleFactor = 1.0

            self.fitToWindowAct.setEnabled(True)
            self.updateActions()

            if not self.fitToWindowAct.isChecked():
                self.imageLabel.adjustSize()

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()

        self.updateActions()

    def nextImage(self):
        """ switch to next image
        """
        if self._imagesInList:
            self._count += 1
            if self._count == len(self._imagesInList):
                self._count = 0
            log.debug("self._imagesInList[self._count] {}".format(
                self._imagesInList[self._count]))
            self.open(
                self._imagesInList[self._count])

    def previousImage(self):
        """ switch to previous image
        """
        if self._imagesInList:
            self._count -= 1
            if self._count == -1:
                self._count = len(self._imagesInList) - 1
            self.open(
                self._imagesInList[self._count])

    def createActions(self):
        self.showNextAct = QtGui.QAction("Next image", self,
                                         shortcut="Ctrl+N", enabled=False,
                                         triggered=self.nextImage)
        self.showPreviousAct = QtGui.QAction("Previous image", self,
                                             shortcut="Ctrl+P", enabled=False,
                                             triggered=self.previousImage)

        self.zoomInAct = QtGui.QAction("Zoom &In (25%)", self,
                                       shortcut="Ctrl++", enabled=False,
                                       triggered=self.zoomIn)

        self.zoomOutAct = QtGui.QAction("Zoom &Out (25%)", self,
                                        shortcut="Ctrl+-", enabled=False,
                                        triggered=self.zoomOut)

        self.normalSizeAct = QtGui.QAction("&Normal Size", self,
                                           shortcut="Ctrl+S", enabled=False,
                                           triggered=self.normalSize)

        self.fitToWindowAct = QtGui.QAction("&Fit to Window", self,
                                            enabled=False, checkable=True,
                                            shortcut="Ctrl+F",
                                            triggered=self.fitToWindow)

    def createMenus(self):

        self.viewMenu = QtGui.QMenu("&View", self)
        self.viewMenu.addAction(self.showNextAct)
        self.viewMenu.addAction(self.showPreviousAct)
        self.viewMenu.addAction(self.showPreviousAct)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)
        self.myQMenuBar = QtGui.QMenuBar(self)
        self.myQMenuBar.addMenu(self.viewMenu)

    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(
            self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))


class WidgetTimer(QtGui.QWidget):

    def __init__(self, labeltext=""):
        super(WidgetTimer, self).__init__()
        self.timer = QtCore.QTimer(None)
        self.timer.timeout.connect(self.addOneSecond)
        self.s = 0
        self.m = 0
        self.h = 0
        self.title = "Elapsed time " + labeltext
        self.initUI()

    def initUI(self):
        self.setMinimumWidth(200)
        self.setMinimumHeight(100)
        self.lcd = QtGui.QLCDNumber(self)
        self.lcd.setStyleSheet('padding: 5px;border-radius: 10px')
        Vbox = QtGui.QVBoxLayout(self)
        log.debug("Vbox {}".format(Vbox))
        self.label = QtGui.QLabel(self.title)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet('padding: 5px; border-radius: 10px')
        Vbox.addWidget(self.label)
        Vbox.addWidget(self.lcd)
        self.setLayout(Vbox)
        self.setStyleSheet("background-color: green")

    def start(self):
        self.s = 0
        self.m = 0
        self.h = 0
        self.timer.start(1000)
        self.currentTime = "{:02d}:{:02d}:{:02d}".format(
            self.h, self.m, self.s)
        self.lcd.setDigitCount(len(self.currentTime))
        self.lcd.display(self.currentTime)

    def stop(self):
        # time.sleep(1)
        self.timer.stop()
        self.currentTime = "{:02d}:{:02d}:{:02d}".format(
            self.h, self.m, self.s)
        # return self.lcd.value()
        log.debug("stopping timer at {}".format(self.currentTime))
        return self.currentTime

    def addOneSecond(self):
        if self.s < 59:
            self.s += 1
        else:
            if self.m < 59:
                self.s = 0
                self.m += 1
            elif self.m == 59 and self.h < 24:
                self.h += 1
                self.m = 0
                self.s = 0
            else:
                self.timer.stop()

        self.currentTime = "{:02d}:{:02d}:{:02d}".format(
            self.h, self.m, self.s)
        self.lcd.setDigitCount(len(self.currentTime))
        self.lcd.display(self.currentTime)


@contextmanager
def wait_signal(signal, timeout=10000):
    """Block loop until signal emitted, or timeout (ms) elapses."""
    loop = QtCore.QEventLoop()
    signal.connect(loop.quit)

    yield

    if timeout is not None:
        QtCore.QTimer.singleShot(timeout, loop.quit)
    loop.exec_()
