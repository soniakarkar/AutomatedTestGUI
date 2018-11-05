#!/usr/bin/env python
# coding:utf-8
"""
:Author: Sonia Karkar -- karkar@in2p3.fr

:What:

"""
# from __future__ import unicode_literals
from qtUtils import centerOnScreen, wait_signal
from PyQt4 import QtGui, QtCore
import os
import ressources
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


class Type1Error(IOError):
    """
    Raised when type 1 error happens
    """

    def __init__(self, Type1Information, msg=None):
        if msg is None:
            # Set some default useful error message
            msg = "Info retrieved: {}".format(Type1Information)
        super(Type1Error, self).__init__(msg)
        self.Type1Information = Type1Information


def HandlingType1Error(catchedException):
    log.debug("handling exception : type 1 error")
    dialog = QtGui.QMessageBox()
    dialog.setIcon(QtGui.QMessageBox.Warning)
    dialog.setText("{}".format(catchedException.args[0]) +
                   "\n Please check this "
                   + "\n and start again")
    dialog.DoneButton = dialog.addButton(QtCore.QString("Done"),
                                         QtGui.QMessageBox.AcceptRole)
    centerOnScreen(dialog)
    with wait_signal(dialog.DoneButton.clicked, timeout=300000):
        dialog.show()


class Type2Error(IOError):
    """
    Raised when type 2 error happens
    """

    def __init__(self, Type2Information, msg=None):
        if msg is None:
            # Set some default useful error message
            msg = "Missing Instruments: {}".format(Type2Information)
        super(Type2Error, self).__init__(msg)
        self.Type2Information = Type2Information


def HandlingType2Error(catchedException):
    log.debug("handling exception : type2 error")
    dialog = QtGui.QMessageBox()
    dialog.setIcon(QtGui.QMessageBox.Warning)
    dialog.setText("{}".format(catchedException.args[0]) +
                   "\n Please check  that"
                   + "\n and start again")
    dialog.DoneButton = dialog.addButton(QtCore.QString("Done"),
                                         QtGui.QMessageBox.AcceptRole)
    centerOnScreen(dialog)
    with wait_signal(dialog.DoneButton.clicked, timeout=300000):
        dialog.show()


def TestAllErrors():
    myapp = QtGui.QApplication([])
    instruer = Type1Error(['a', 'b', 'c'])
    HandlingType1Error(instruer)
