import os
import sys
import inspect
from time import localtime, strftime, sleep

import configparser
from colorama import init
from colorama import Fore, Back, Style



from helpers.html_page import Htmlpage
from helpers.constants import PrintColors


# This class uses a singleton. http://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html


class Logger:
    log_html_document = Htmlpage()
    ERROR = 1
    WARNING = 2
    INFO = 3

    class __Logger:
        # Fix color output on windows
        if 'PYCHARM_HOSTED' in os.environ:
            convert = False  # in PyCharm, we should disable convert
            strip = False
        else:
            convert = None
            strip = None
        init(convert=convert, strip=strip)

        config = configparser.ConfigParser()

        currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        parentdir = os.path.dirname(currentdir)
        configfile = os.path.join(parentdir, "config.ini")
        config.read(configfile)
        logpath = os.path.join(config.get("ProgramConfig", 'report_folder'),
                               config.get("ProgramConfig", 'log_file'))
        logmodule = list()

        def dump(self):
            Logger.log_html_document.footer()
            with open(self.logpath, 'w', encoding="utf-8") as f:
                print(Logger.log_html_document.gethtml(), file=f)

        def __init__(self, message, level, rewriteLine):
            # First call of the logger, so it builds the title of the log-page
            Logger.log_html_document.header("log")
            Logger.log_html_document.navigation()
            with Logger.log_html_document.tag("h1", klass="center-align"):
                Logger.log_html_document.text("Log-file")
            self.logmodule.append(self)
            self.log(message, level, rewriteLine)

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
        def cPrint(message, level, rewriteLine):
            if level == 1:
                msg =  "%s[ERROR]" % PrintColors.ERROR
            elif level == 2:
                msg = "%s[WARNING]" % PrintColors.WARNING
            else:
                msg = "%s[INFO]%s" % (PrintColors.INFO, PrintColors.END)
            msg += " %s%s" % (message, PrintColors.END)
            if rewriteLine:
                print(msg, end='\r')
            else:
                print(msg)

        def log(self, message, level=3, rewriteLine=False):
            # read the loglevel again, needed because of the singleton design
            loglevelparser = configparser.ConfigParser()
            loglevelparser.read(self.configfile)
            loglevel = loglevelparser.get("ProgramConfig", 'loglevel')
            
            if int(level) == 1 and int(loglevel) >= 1:
                self.cPrint(message, level, rewriteLine)
                self.__make_log_entry(message, "red")
                sleep(7)
                sys.exit(1)
            elif int(level) == 2 and int(loglevel) >= 2:
                self.cPrint(message, level, rewriteLine)
                self.__make_log_entry(message, "amber")
            elif int(level) == 3 and int(loglevel) >= 3:
                self.cPrint(message, level, rewriteLine)
                self.__make_log_entry(message, "light-blue")

    instance = None

    def __init__(self, message, level=3, rewriteLine=False):
        if not Logger.instance:
            Logger.instance = Logger.__Logger(message, level, rewriteLine)
        else:
            Logger.instance.log(message, level, rewriteLine)

    def dump():
        # passing the dump command to the singleton
        Logger.instance.dump()
