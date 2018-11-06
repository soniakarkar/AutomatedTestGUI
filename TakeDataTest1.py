# !/usr/bin/env python
# coding:utf-8
"""
:Author: Sonia Karkar -- karkar@in2p3.fr

:What: Test1 in action

"""
import argparse
from TestUtils import MyObject as MyObject
import os
import sys
import logging
from LogUtils import MyLog
if __name__ == "__main__":
    logname = os.path.basename(__file__)[:-3]
else:
    logname = __name__
if len(logname) > 20:
    logname = logname[:9] + "--" + logname[-9:]
log = MyLog(logname, qt=True, logdir=os.getenv("HOME") + "/log/")
# log.setLevel(logging.DEBUG)


def main(ObjectTested):
    prepareForTest1(ObjectTested)
    mainTest1Loop(ObjectTested)
    dataDir = cleanAfterTest1(ObjectTested)
    return dataDir


def prepareForTest1(ObjectTested):
    pass


def mainTest1Loop(ObjectTested):
    pass


def cleanAfterTest1(ObjectTested):
    """clean After Test1"""
    dataDir = "."
    return dataDir


MyObject.TakeDataTest1 = main
MyObject.cleanAfterTest1 = cleanAfterTest1
MyObject.prepareForTest1 = prepareForTest1
MyObject.mainTest1Loop = mainTest1Loop

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--config-file",
                        default='./config/default.cfg',
                        dest="CONFIGFILE", metavar="CONFIGFILE",
                        help="provide a configuration file",
                        required=True)
    parser.add_argument("-i", "--object-id", default='DXX',
                        dest="ObjectTestedid", metavar="ObjectTestedid",
                        help="provide a MyObject id.",
                        required=True)
    args = parser.parse_args()
    CONFIGFILE = args.CONFIGFILE
    ObjectTestedid = args.ObjectTestedid
    MyObject = MyObject(ObjectTestedid)
    try:
        main(MyObject)
    except(Exception) as err:
        mymsg = ("During 'main' of " + logname + " : {}".format(err.args[0]))
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
        sys.exit(1)
