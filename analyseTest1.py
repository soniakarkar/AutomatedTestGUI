#!/usr/bin/env python
# coding:utf-8
'''
:Author: Sonia Karkar -- karkar@in2p3.fr

:Usage: analysePattern.py [options]

:Options:
  ``-h``, ``--help``            show this help message and exit
  ``-f CONFIGFILE``, ``--config-file=CONFIGFILE``
                        provide a configuration file. Using 'none' by default.
  ``-i febid``, ``--feb-id=febid``
                        provide a feb id. Using 'DXX' by default.
  ``-d Test1datadir``, ``--pattern-data=Test1datadir``
                        provide a Test1datadir Using 'Test1' by default.

'''
# from __future__ import unicode_literals
import subprocess
import os
import sys
import matplotlib.pyplot as plt
import random
from time import sleep
from TestUtils import MyObject
from optparse import OptionParser
from ConfigParser import ConfigParser
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


def main(ObjectTested, dataDir):
    log.info("starting Test1 analysis")

    reportfile = dataDir + "/" + logname + "_report.txt"
    Test1fh = logging.FileHandler(reportfile)
    logformat = logging.Formatter(" %(message)s")
    Test1fh.setFormatter(logformat)
    log.addHandler(Test1fh)
    log.info("starting analysis loop")
    log.debug("%s", ObjectTested.Tests)
    # pretend to be doing some clever analysis and it's a long task
    for col in ["Parameter{}".format(i) for i in range(15)]:
        ObjectTested.Tests[col] = random.randint(-10, 10)
        sleep(0.2)
        log.debug(" %s, %s", col, ObjectTested.Tests[col].values)
    for col in ["Sigma{}".format(i) for i in range(15)]:
        ObjectTested.Tests[col] = random.random() * 2
        log.debug(" %s, %s", col, ObjectTested.Tests[col].values)
        sleep(0.2)
    plt.errorbar(x=range(15),
                 y=[ObjectTested.Tests[x]
                     for x in ObjectTested.Tests.columns
                     if "Parameter" in x],
                 yerr=[ObjectTested.Tests[x]
                       for x in ObjectTested.Tests.columns
                       if "Sigma" in x])
    try:
        os.makedirs(dataDir + "/plots")
    except OSError as err:
        if err.errno != 17:
            raise
    plt.savefig(dataDir + "/plots/parametersanalysis1.png")
    plt.close("all")
    Test1TestOK = True
    if Test1TestOK:
        log.info("all results are ok")
    else:
        log.warning("analysis has shown some pbms in the test data")
    log.removeHandler(Test1fh)
    return dataDir, Test1TestOK


MyObject.analyseTest1 = main

if __name__ == "__main__":
    helpmsg = """%prog [options]
    Use '-h' to get the help message
    """
    # Parse options
    parser = OptionParser(usage=helpmsg)
    parser.add_option("-f", "--config-file",
                      default=None,
                      dest="CONFIGFILE",
                      metavar="CONFIGFILE",
                      help=("provide a configuration file."
                            + " Using '%default' by default.")
                      )
    parser.add_option("-i", "--feb-id", default='DXX',
                      dest="febid", metavar="febid",
                      help="provide a feb id. Using '%default' by default.")
    parser.add_option("-d", "--NF-data", default='Test1',
                      dest="Test1datadir", metavar="Test1datadir",
                      help=("provide a Test1datadir "
                            + " Using '%default' by default.")
                      )
    (opt, args) = parser.parse_args()
    CONFIGFILE = opt.CONFIGFILE
    febid = opt.febid
    Test1datadir = opt.Test1datadir + "/"

    feb = FEB(febid)
    configfile = Test1datadir + "/Test1.cfg"
    if CONFIGFILE is not None:
        subprocess.call(['cp', CONFIGFILE, configfile])
    config = ConfigParser()
    config.read(configfile)
    #         config.set(section, option, value)
    config.set("Directories", "DataDir", Test1datadir)
    config.set("Directories", "OutDir", Test1datadir + "/plots")
    for section in config.sections():
        if len(config.options(section)) == 0:
            config.remove_section(section)
    config.write(open(configfile, "w"))
    try:
        main(feb, configfile)
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
