# !/usr/bin/env python
# coding:utf-8
"""
:Author: Sonia Karkar -- karkar@in2p3.fr


:What: This hosts the main structure for the FEB prod test GUI.

        It mainly consists of creating a main window containing a tab widget
        then a loop over a testList to add test-specific widget to the
        main window.

        Each test is expected to come with its set of two widgets:
        a TestWidget and ShowResult widgets.

        The TestWidget shall contain the GUI that will run the given
        test. It is made available only once the previous tests in the list are
        done.

        The ShowResult widget shall be called once the test is finished to
        run the analysis and present the main result of the test. It will be
        available while the user is running the following tests.


"""
import sys
import os
import traceback
from LogUtils import MyLog
if __name__ == "__main__":
    logname = os.path.basename(__file__)[:-3]
else:
    logname = __name__
    if len(logname) > 20:
        logname = logname[:9] + "--" + logname[-9:]
# Create a logger with file, console and qt widget printing
logdir = os.getenv("HOME") + "/log/"
if not (os.path.isdir(logdir)):
    os.mkdir(logdir)
log = MyLog(logname, qt=True, logdir=logdir)
import logging
# default logging level is INFO uncomment below for DEBUG
# log.setLevel(logging.DEBUG)
from errors import Type1Error, HandlingType1Error
from errors import Type2Error, HandlingType2Error
from PyQt4 import QtGui, QtCore
import numpy as np
import configargparse
# from PyQt4.QtCore import pyqtSlot, SIGNAL
import TestsWidgets
import ShowResult
from qtUtils import Worker, centerOnScreen
from qtUtils import wait_signal
from GuiMainElements import MainWindow, addTestRestart
from GuiMainElements import getTestListwin


def StopTest(MainWin, itest):
    """Stops the current test in an orderly maner."""
    log.info("Stop test {}".format(itest))
    # clean connexions to instruments and close files
    MainWin.tabs.widget(itest).TestWidget.SafeExit()
    # terminate the running thread
    if MainWin.NonBlockingRunTest.isRunning():
        try:
            # MainWin.NonBlockingRunTest.quit()
            MainWin.NonBlockingRunTest.terminate()
            MainWin.NonBlockingRunTest.wait()
        except Exception as e:
            traceback.print_exc()
            raise e
    # hide stop button
    MainWin.tabs.widget(itest).StopThisTestBtn.setVisible(False)
    log.debug("try removing TestWidget")
    log.debug("MainWin.tabs.widget(itest).TestWidget {}".format(
        MainWin.tabs.widget(itest).TestWidget))
    try:
        MainWin.tabs.widget(itest).layout.removeWidget(
            MainWin.tabs.widget(itest).TestWidget)
        MainWin.tabs.widget(itest).TestWidget.deleteLater()
        # MainWin.tabs.widget(itest).TestWidget = None
        QtGui.QApplication.processEvents()
    except:
        log.error("couldnt remove TestWidget")
    log.debug("adding restart button")
    addTestRestart(MainWin.tabs.widget(itest))
    MainWin.tabs.widget(itest).RestartThisTestBtn.setEnabled(True)
    MainWin.tabs.widget(itest).RestartThisTestBtn.clicked.connect(
        lambda: RestartTest(MainWin, itest))
    log.debug("MainWin.tabs.widget(itest).RestartThisTestBtn {}".format(
        MainWin.tabs.widget(itest).RestartThisTestBtn))
    QtGui.QApplication.processEvents()


def RestartTest(MainWin, itest):
    """Restarts from the begining the current test."""
    SetUpGUITest(MainWin, itest)
    RunTest(MainWin, itest)


def SetUpGUITest(MainWin, itest):
    """Populates the main window with a new tab for a given test"""
    log.debug("Prepare GUI for test {} ".format(itest))
    log.debug("MainWin.widgStart[itest] {}".format(MainWin.widgStart[itest]))
    if MainWin.widgStart[itest] > 0:
        log.debug("try removing restart button")
        log.debug("MainWin.tabs.widget(itest).RestartThisTestBtn {}".format(
            MainWin.tabs.widget(itest).RestartThisTestBtn))
        try:
            MainWin.tabs.widget(itest).layout.removeWidget(
                MainWin.tabs.widget(itest).RestartThisTestBtn)
            MainWin.tabs.widget(itest).RestartThisTestBtn.deleteLater()
            # MainWin.tabs.widget(itest).RestartThisTestBtn = None
            QtGui.QApplication.processEvents()
        except:
            log.error("couldnt remove RestartButton")
        # get stop button back visible
        MainWin.tabs.widget(itest).StopThisTestBtn.setVisible(True)

    # At this point we want to allow user to stop/terminate the thread
    # so we enable that button and connect it to the appropriate function
    MainWin.tabs.widget(itest).StopThisTestBtn.setEnabled(True)
    MainWin.tabs.widget(itest).StopThisTestBtn.setDefault(False)
    MainWin.tabs.widget(
        itest).StopThisTestBtn.clicked.connect(lambda: StopTest(MainWin, itest))

    # TestWidget = QtGui.QLabel(MainWin.testsList[itest])
    TestWidget = getattr(TestsWidgets, MainWin.testsList[itest])(MainWin)
    log.debug("TestWidget {}".format(TestWidget))
    MainWin.tabs.widget(itest).layout.addWidget(TestWidget, 1, 0)
    log.debug("TestWidget added to tab layout")
    MainWin.tabs.widget(itest).TestWidget = TestWidget
    log.debug("TestWidget added to MainWin instance")
    log.debug("MainWin.tabs.widget(itest).TestWidget{}".format(
        MainWin.tabs.widget(itest).TestWidget))
    QtGui.QApplication.processEvents()
    MainWin.widgStart[itest] = MainWin.widgStart[itest] + 1


def ShowTestResult(MainWin, itest):
    """
    In the main window, replaces the test widget
    by its corresponding showresult widget.
    """
    log.info("show result for test {}".format(itest))
    log.debug("MainWin {}".format(MainWin))
    if MainWin.ObjectTested is not None:
        log.debug("MainWin.ObjectTested.listentry {}".format(
            MainWin.ObjectTested.listentry))
    # first get rid of the original widget
    MainWin.tabs.widget(itest).layout.removeWidget(
        MainWin.tabs.widget(itest).TestWidget)
    MainWin.tabs.widget(itest).TestWidget.deleteLater()
    # MainWin.tabs.widget(itest).TestWidget = None
    # also get rid of the stop button
    MainWin.tabs.widget(itest).layout.removeWidget(
        MainWin.tabs.widget(itest).StopThisTestBtn)
    MainWin.tabs.widget(itest).StopThisTestBtn.deleteLater()
    # MainWin.tabs.widget(itest).StopThisTestBtn = None
    QtGui.QApplication.processEvents()
    # now replace with the widget of result
    ResultWigdet = getattr(ShowResult, MainWin.testsList[itest])(MainWin)
    log.debug("ResultWigdet {}".format(ResultWigdet))
    MainWin.tabs.widget(itest).layout.addWidget(ResultWigdet)
    log.debug("Result Widget added to tab layout")
    MainWin.tabs.widget(itest).ResultWigdet = ResultWigdet
    log.debug("ResultWigdet added to MainWin instance")
    log.debug("MainWin.tabs.widget(itest).ResultWigdet{}".format(
        MainWin.tabs.widget(itest).ResultWigdet))
    # will do the data analysis as a thread to keep the GUI responsive
    MainWin.NonBlockingRunAnalysis = Worker(
        MainWin.tabs.widget(itest).ResultWigdet.Run, ())
    # catch exceptions occuring there
    MainWin.NonBlockingRunAnalysis.myexception.connect(receiveException)
    # prepare what will be done next
    if (itest < len(MainWin.testsList) - 1) and (not MainWin.StopAfterShow):
        MainWin.NonBlockingRunAnalysis.finished.connect(
            lambda: ShowAndMoveNext(MainWin,
                                    itest + 1))
    else:
        MainWin.NonBlockingRunAnalysis.finished.connect(lambda:
                                                        lastAnalysisFinished(
                                                            MainWin))
    # effectively start the analysis
    MainWin.NonBlockingRunAnalysis.start()
    # QtGui.QApplication.processEvents()


def lastAnalysisFinished(MainWin):
    """Create a summary of all tests performed"""
    log.info("Last analysis finished")
    totalduration = MainWin.MainTimer.stop()
    log.info("Total Test duration {}".format(totalduration))
    MainWin.tabs.setCurrentIndex(len(MainWin.testsList))
    MainWin.tabs.widget(len(MainWin.testsList)).layout.removeWidget(
        MainWin.tabs.widget(len(MainWin.testsList)).StopThisTestBtn)
    MainWin.tabs.widget(len(MainWin.testsList)).StopThisTestBtn.deleteLater()

    MainWin.tabs.widget(len(MainWin.testsList)).layout.addWidget(
        QtGui.QLabel("Test Name"), 1, 0)
    MainWin.tabs.widget(len(MainWin.testsList)).layout.addWidget(
        QtGui.QLabel("Test Duration"), 1, 1)
    MainWin.tabs.widget(len(MainWin.testsList)).layout.addWidget(
        QtGui.QLabel("Analysis Duration"), 1, 2)
    MainWin.tabs.widget(len(MainWin.testsList)).layout.addWidget(
        QtGui.QLabel("Test result"), 1, 3)

    for itest, test in enumerate(MainWin.testsList):
        MainWin.tabs.widget(len(MainWin.testsList)).layout.addWidget(
            QtGui.QLabel(test), 2 + itest, 0)
        MainWin.tabs.widget(len(MainWin.testsList)).layout.addWidget(
            QtGui.QLabel(MainWin.TestTimers[itest]), 2 + itest, 1)
        MainWin.tabs.widget(len(MainWin.testsList)).layout.addWidget(
            QtGui.QLabel(MainWin.ResultTimers[itest]), 2 + itest, 2)
        ResultLabel = QtGui.QLabel()
        if(MainWin.ObjectTested is None) or (not MainWin.ObjectTested.results[itest]):
            ResultLabel.setStyleSheet("background-color: red;"
                                      + "padding: 2px;border-radius: 5px")
            ResultLabel.setText("Problem")
        else:
            ResultLabel.setStyleSheet("background-color: green;"
                                      + "padding: 2px;border-radius: 5px")
            ResultLabel.setText("OK")

        MainWin.tabs.widget(len(MainWin.testsList)).layout.addWidget(
            ResultLabel, 2 + itest, 3)

    qbtn = QtGui.QPushButton('Quit', MainWin)
    qbtn.clicked.connect(sys.exit)
    qbtn.setStyleSheet(
        "background-color: orange; padding: 2px;border-radius: 5px")
    #    + "border-radius: 2px")
    MainWin.tabs.widget(len(MainWin.testsList)).layout.addWidget(
        qbtn, 2 + len(MainWin.testsList), 1, 1, 2)

    MainWin.tabs.tabBar().MySetTabColor(len(MainWin.testsList),
                                        QtGui.QColor('blue'))
    MainWin.setTabsEnable(len(MainWin.testsList), MainWin.testsList)
    QtGui.QApplication.processEvents()
    log.info("{}".format(MainWin.testsList))
    log.info("Summary Tests durations {}".format(MainWin.TestTimers))
    log.info("Summary analysis durations {}".format(MainWin.ResultTimers))


def receiveException(catchedException):
    """Catches all exceptions.
     For known expection, runs the appropriate handling code
     For unknow exception, reraises it
     """
    log.debug("catchedException {}".format(catchedException))
    log.debug("type(catchedException) {}".format(type(catchedException)))
    log.debug("catchedException.args {}".format(catchedException.args))
    log.error("Received Exception : {}".format(catchedException))
    if type(catchedException)is Type1Error:
        log.debug("exception is : missing instru")
        HandlingType1Error(catchedException)
    elif type(catchedException)is Type2Error:
        log.debug("exception is:  missing xml")
        HandlingType2Error(catchedException)
    else:
        raise


def ShowAndMoveNext(MainWin, itest):
    """Transitions from the end of a test analysis to the next test.
    Keeps the result to screen 2 seconds before starting the next test
    """
    # get a chance to look at the result before switching to next step
    timer = QtCore.QTimer(MainWin)
    timer.setSingleShot(True)
    log.debug("after timer will start test {} itest {}".format(
        MainWin.testsList[itest], itest))
    waitmsec = 2000
    if not MainWin.StopAfterShow:
        # before any hardware intervention turn off power supply
        if (
            # (MainWin.testsList[itest] is "ConnectSignal")
                # or
                (MainWin.testsList[itest] is'ConnectHVPA')
                or (MainWin.testsList[itest] is'DisConnectHVPA')):
            MainWin.PS.AllOFF()
        timer.timeout.connect(lambda: RunTest(MainWin, itest))
        log.info("Will move to next test in {} seconds".format(waitmsec / 1000))
    else:
        timer.timeout.connect(lambda: lastAnalysisFinished(MainWin))
    log.debug("timer {}".format(timer))
    timer.start(waitmsec)
    log.debug("timer started")


def RunTest(MainWin, itest):
    """Starts the test in a separeted thread via a worker."""
    # get ready for the test
    log.debug("getting ready for test {}".format(MainWin.testsList[itest]))
    MainWin.tabs.setCurrentIndex(itest)
    MainWin.tabs.widget(itest).TestWidget.setFocus()
    MainWin.tabs.tabBar().MySetTabColor(itest, QtGui.QColor('blue'))
    MainWin.setTabsEnable(itest, MainWin.testsList)
    QtGui.QApplication.processEvents()
    # start the test as a thread to keep the GUI responsive
    MainWin.NonBlockingRunTest = Worker(
        MainWin.tabs.widget(itest).TestWidget.Run, ())
    MainWin.NonBlockingRunTest.myexception.connect(receiveException)
    # now effectively start to run the tests
    MainWin.NonBlockingRunTest.start()


# def getTestListGUI():
#     ListWin = getTestListwin()
#     ListWin.show()
    # newList = ListWin.MyList
    # return newList


def main(mainargs, testsList):
    """Initialisation of the autotest.

    * Processes the CLI options.
    * Creates the main window.
    * Populates the main window with a widget for each test from the testsList.
    * Starts the process by running the first test.

    """
    log.info("Log info testing messsage")
    log.warning('Log warning testing message')
    log.error("Log error testing message")
    log.debug("Log debug testing messsage")
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_X11InitThreads)
    # app = QtGui.QApplication(sys.argv)
    app = MyApp(sys.argv)
    sys.excepthook = my_excepthook

    Maindatadir = mainargs.datadir
    if mainargs.expertMode:
        ListWin = getTestListwin()
        centerOnScreen(ListWin)
        with wait_signal(ListWin.done, timeout=60000):
            ListWin.show()
        testsList = ListWin.MyList
        ListWin.close()
        if Maindatadir is not None:
            defaultdatadir = Maindatadir
        else:
            defaultdatadir = "/home/nectar/2017/V5"
        dialog = QtGui.QFileDialog()
        Maindatadir = dialog.getExistingDirectory(
            None,
            "Select a folder to store data",
            defaultdatadir,
            QtGui.QFileDialog.ShowDirsOnly)
        centerOnScreen(dialog)
    log.debug("testsList {}".format(testsList))
    log.debug("Maindatadir {}".format(Maindatadir))
    # ntests = len(testsList)
    # Check current working directory.
    retval = os.getcwd()
    log.info("Current working directory {}".format(retval))
    # Now change the directory
    os.chdir(Maindatadir)
    # Check current working directory.
    retval = os.getcwd()
    log.info("Directory changed successfully {}".format(retval))
    TheMainWindow = MainWindow(testsList)
    TheMainWindow.show()
    TheMainWindow.widgStart = np.zeros((len(testsList)))
    TheMainWindow.TestTimers = [""] * len(testsList)
    TheMainWindow.ResultTimers = [""] * len(testsList)
    TheMainWindow.testsList = testsList
    TheMainWindow.StopAfterShow = False
    TheMainWindow.mainargs = mainargs
    TheMainWindow.MainTimer.start()
    # put in GUI all the tests widgets
    for itest, testname in enumerate(testsList):
        log.debug("setting up GUI for test number {},{}".format(itest,
                                                                testname))
        SetUpGUITest(TheMainWindow, itest)
    # run the first test to start the chain , next will follow
    try:
        RunTest(TheMainWindow, 0)
        sys.exit(app.exec_())
        # app.exec_()
    except(Exception) as err:
        raise Exception("executing qtapp in main" + err.messsage)
        sys.exit()


def my_excepthook(type, value, tback):
    """Allows to get the exceptions inside the qtApp
    to be catched and logged in a file
    """
    # log the exception here
    # log.error("type, value, tback: {}, {} , {}".format(type, value, tback))
    mymsg = ("During 'main' of " + logname + " : "
             + "{}".format(value)
             )
    for line in traceback.format_tb(tback):
        mymsg += line
    log.error(mymsg)
    thecrashlogfilename = logname + "_CRASH.log"
    log.error("aborting " + logname +
              ". See crash log : " + thecrashlogfilename)
    for hdlr in list(log.handlers):
        log.removeHandler(hdlr)
        hdlr.close()
    thecrashlog = logging.FileHandler(thecrashlogfilename)
    logformat = logging.Formatter(
        "%(asctime)s - %(name)20s - %(levelname)5s - %(message)s")
    thecrashlog.setFormatter(logformat)
    log.addHandler(thecrashlog)
    log.exception(mymsg)
    # then call the default handler
    sys.__excepthook__(type, value, tback)
    sys.exit(1)


class MyApp(QtGui.QApplication):
    """Define a qtApp with a special notify function to catch exceptions.
    """

    def notify(self, obj, event):
        isex = False
        try:
            # log.debug("in notify try")
            return QtGui.QApplication.notify(self, obj, event)
        except Exception:
            log.debug("in notify exception catcher")
            isex = True
            log.error("{}".format(traceback.format_exception(*sys.exc_info())))
            return False
        finally:
            if isex:
                self.quit()


if __name__ == '__main__':
    helpmsg = """ % prog[options]
    Use '-h' to get the help message
    """
    parser = configargparse.ArgParser(
        default_config_files=['./.cfg'])
    parser.add('-f', '--config', required=False,
               is_config_file=True, help='config file path')
    parser.add("-xml", "--xmlFile",
               default='./defaultConfigFile.xml',
               required=False,
               help="provide a xml file for configuration")
    parser.add("-d", "--datadir", required=False,
               default='.',
               help="provide a main datadir "
               + "Using '%default' by default.")
    parser.add('--skippList', nargs='+', required=False,
               help='list of tests to skip')
    parser.add("-e", "--expertMode",
               required=False,
               help="start in expert mode",
               action='store_true',
               default=False)
    mainargs = parser.parse_args()
    log.debug(mainargs)
    log.debug(mainargs.skippList)
    testsList = [
        "Test0",
        "Test1",
        # "Test2",
    ]
    if mainargs.skippList is not None:
        testsList = [x for x in testsList if x not in mainargs.skippList]
    log.debug("testsList {}".format(testsList))
    main(mainargs, testsList)
