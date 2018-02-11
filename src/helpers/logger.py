import os
import sys
import inspect
from time import localtime, strftime

import configparser

from helpers.html_page import Htmlpage


# This class uses a singleton. http://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html


class Logger:
    log_html_document = Htmlpage()
    ERROR = 1
    WARNING = 2
    INFO = 3

    class __Logger:
        config = configparser.ConfigParser()

        currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        parentdir = os.path.dirname(currentdir)
        configfile = os.path.join(parentdir, "config.ini")
        config.read(configfile)

        loglevel = config.get("ProgramConfig", 'loglevel')
        logpath = os.path.join(config.get("ProgramConfig", 'report_folder'),
                               config.get("ProgramConfig", 'log_file'))
        logmodule = list()

        def dump(self):
            Logger.log_html_document.footer()
            with open(self.logpath, 'w') as f:
                print(Logger.log_html_document.gethtml(), file=f)

        def __init__(self, message, level):
            # First call of the logger, so it builds the title of the log-page
            Logger.log_html_document.header("log")
            Logger.log_html_document.navigation()
            with Logger.log_html_document.tag("h1", klass="center-align"):
                Logger.log_html_document.text("Log-file")
            self.logmodule.append(self)
            self.log(message, level)

        @staticmethod
        def timeString():
            return strftime("%H:%M:%S", localtime())

        def __make_log_entry(self, message, color):
            with Logger.log_html_document.tag("div", klass="row"):
                with Logger.log_html_document.tag("div", klass="col s10 offset-s1"):
                    with Logger.log_html_document.tag("div", klass="card"):
                        with Logger.log_html_document.tag("div", klass="card-content " + color):
                            Logger.log_html_document.text("%s: %s" % (self.timeString, message))

        @staticmethod
        def cPrint(message, level):
            if level == 1:
                tag = "[ERROR]"
            elif level == 2:
                tag = "[WARNING]"
            else:
                tag = "[INFO]"
            print("%s %s" % (tag, message))

        def log(self, message, level=3):
            self.cPrint(message, level)
            if int(level) == 1 and int(self.loglevel) >= 1:
                self.__make_log_entry(message, "red")
                sys.exit(1)
            elif int(level) == 2 and int(self.loglevel) >= 2:
                self.__make_log_entry(message, "amber")
            elif int(level) == 3 and int(self.loglevel) >= 3:
                self.__make_log_entry(message, "light-blue")

    instance = None

    def __init__(self, message, level=3):
        if not Logger.instance:
            Logger.instance = Logger.__Logger(message, level)
        else:
            Logger.instance.log(message, level)

    def dump():
        # passing the dump command to the singleton
        Logger.instance.dump()

