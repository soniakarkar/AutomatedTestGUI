# !/usr/bin/env python
# coding:utf-8
"""
:Author: Sonia Karkar -- karkar@in2p3.fr

:What: Afew ancillary class and functions for the Testbench to run

"""
import pandas as pd
from __builtin__ import str
import os
from LogUtils import MyLog
if __name__ == "__main__":
    logname = os.path.basename(__file__)[:-3]
else:
    logname = __name__
if len(logname) > 20:
    logname = logname[:9] + "--" + logname[-9:]
log = MyLog(logname, qt=True, logdir=os.getenv("HOME") + "/log/")
# import logging
# log.setLevel(logging.DEBUG)


def ParseQRCode(QRCode, currentVersion=4):
    """Checks that the QRcode is in the form ObjectTestedid/ObjectTestedversion
    with ObjectTestedid on 4 digits and ObjectTestedversion = 4
    and returns theses values
    """
    newObjectTestedid = None
    newObjectTestedversion = None
    infolist = QRCode.split("/")
    log.debug("infolist {}".format(infolist))
    if len(infolist) == 2:
        # extract values
        newObjectTestedid = str(infolist[0])
        log.debug("newObjectTestedid {}".format(newObjectTestedid))
        newObjectTestedversion = str(infolist[1])
        log.debug("newObjectTestedversion {}".format(newObjectTestedversion))
        # check values
        febidok = (len(newObjectTestedid) == 4)
        log.debug("febidok {}".format(febidok))
        febversionok = (newObjectTestedversion == str(currentVersion))
        log.debug("febversionok {}".format(febversionok))
        pbm = not(febidok and febversionok)
    else:
        pbm = True
    if pbm:
        newObjectTestedid = None
        newObjectTestedversion = None
    return newObjectTestedid, newObjectTestedversion


def PrepareTests(Objectid):
    theObjectTested = MyObject(Objectid)
    return theObjectTested


class MyObject:
    '''
    class used to manage tests and upload of result to db via pandas dataframe

    '''

    def __init__(self, Objectid, location='here', version='5', status='new'):
        self.id = Objectid
        self.version = version
        self.location = location
        self.status = status
        # default dataframe for the feb entry in the list of FEBs
        self.listentry = pd.DataFrame({'SerialNB': [self.id],
                                       'version': [self.version],
                                       'Location': [self.location],
                                       'Status': [self.status],
                                       'LastModif': [pd.Timestamp.now()]},
                                      columns=['SerialNB',
                                               'version',
                                               'Location',
                                               'Status',
                                               'LastModif'])
        # default test and  config dataframes
        self.Tests = pd.DataFrame({'SerialNB': [self.id],
                                   'LastModif': [pd.Timestamp.now()]},
                                  columns=['SerialNB',
                                           'LastModif'])
        self.Config = pd.DataFrame({'SerialNB': [self.id],
                                    'LastModif': [pd.Timestamp.now()]},
                                   columns=['SerialNB',
                                            'LastModif'])

    def __repr__(self):
        toprint = "Serial number :" + str(self.id) + "\n"
        toprint = toprint + "Test data :" + "\n" + str(self.Tests) + "\n"
        toprint = toprint + "Config data :" + "\n" + str(self.Config)
        return toprint
