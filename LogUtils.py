#!/usr/bin/env python
# coding:utf-8
"""
:Author: Sonia Karkar -- karkar@in2p3.fr

:What: Tools for logging from various methods or modules
        and to various destinations (console, files, qt window...)

"""
# from __future__ import unicode_literals
import logging
from logging import handlers
import sys
import os
from PyQt4 import QtCore, QtGui
if __name__ == "__main__":
    logname = os.path.basename(__file__)[:-3]
else:
    logname = __name__
if len(logname) > 20:
    logname = logname[:9] + "--" + logname[-9:]

orange = QtGui.QColor(255, 140, 0)


class QtHandler(logging.Handler):

    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        record = self.format(record)
        if record:
            XStream.stdout().write('%s\n' % record)


def addQtHandler(logger):
    # Make the logger also print in the qt window
    qthandler = QtHandler()
    logformat = logging.Formatter("%(asctime)s - %(name)-20s -"
                                  + "%(levelname)-5s - %(message)s")
    qthandler.setFormatter(logformat)
    logger.addHandler(qthandler)


def configure_my_logger(logger, filename, qt=False):
    logger.setLevel(logging.INFO)
    # define format
    logformat = logging.Formatter("%(asctime)s - %(name)-20s -"
                                  + "%(levelname)-5s - %(message)s")
    # print messages to terminal
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logformat)
    logger.addHandler(ch)
    # also print messages to file
    fh = handlers.RotatingFileHandler(
        filename, maxBytes=(1048576 * 5), backupCount=7)
    fh.setFormatter(logformat)
    logger.addHandler(fh)
    if qt:
        addQtHandler(logger)


def MyLog(logname, qt=False, logdir=""):
    if len(logdir) > 0:
        LOGFILE = logdir + logname + ".log"
    else:
        LOGFILE = logname + ".log"
    log = logging.getLogger(logname)
    configure_my_logger(log, LOGFILE, qt)
    return log


def CloseAll(log):
    for hdlr in list(log.handlers):
        log.removeHandler(hdlr)
        hdlr.close()


class XStream(QtCore.QObject):
    _stdout = None
    _stderr = None
    messageWritten = QtCore.pyqtSignal(str)

    def flush(self):
        pass

    def fileno(self):
        return -1

    def write(self, msg):
        if (not self.signalsBlocked()):
            # self.messageWritten.emit(unicode(msg))
            self.messageWritten.emit(msg)

    @staticmethod
    def stdout():
        if (not XStream._stdout):
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout

    @staticmethod
    def stderr():
        if (not XStream._stderr):
            XStream._stderr = XStream()
            sys.stderr = XStream._stderr
        return XStream._stderr


class LogWin(QtGui.QTextEdit):

    def __init__(self, myqtapp):
        super(LogWin, self).__init__()
        self.myqtapp = myqtapp
        self._console = QtGui.QTextBrowser(self)
        self.move(self.myqtapp.desktop().availableGeometry(1).topLeft())
        self.resize(700, 500)
        self.setWindowTitle("Info")
        self._console.resize(700, 500)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self._console)
        XStream.stdout().messageWritten.connect(self._console.insertPlainText)
        XStream.stderr().messageWritten.connect(self._console.insertPlainText)
        self.show()


if __name__ == '__main__':

    log = MyLog(logname, qt = True, logdir = os.getenv("HOME")+"/log/")
    log.info("log created")
    app = QtGui.QApplication(sys.argv)
    logwin = LogWin(app)
    log.debug('debug message')
    log.info('info message')
    log.warning('warning message')
    log.error('error message')
    print 'Old school hand made print message'
    sys.exit(app.exec_())
