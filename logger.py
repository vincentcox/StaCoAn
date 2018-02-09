from html_page import Htmlpage
import configparser
import os
import sys

# This class uses a singleton. http://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html


class Logger:
    log_html_document = Htmlpage()

    class __Logger:
        config = configparser.ConfigParser()
        config.read("config.ini")
        loglevel = config.get("ProgramConfig", 'loglevel')
        logpath = os.path.join(config.get("ProgramConfig", 'report_folder'),
                               config.get("ProgramConfig", 'log_file'))
        logmodule = []

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

        def log(self, message, level):
            def make_log_entry(message, color):
                with Logger.log_html_document.tag("div", klass="row"):
                    with Logger.log_html_document.tag("div", klass="col s10 offset-s1"):
                        with Logger.log_html_document.tag("div", klass="card"):
                            with Logger.log_html_document.tag("div", klass="card-content " + color):
                                Logger.log_html_document.text(message)

            if int(level) == 1 and int(self.loglevel) >= 1:
                # Level 1 is error
                print(message)
                make_log_entry(message, "red")
                sys.exit()
            elif int(level) == 2 and int(self.loglevel) >= 2:
                # Level 2 is warning
                make_log_entry(message, "amber")
            elif int(level) == 3 and int(self.loglevel) >= 3:
                # Level 3 is informational
                make_log_entry(message, "light-blue")

    instance = None

    def __init__(self, message, level):
        if not Logger.instance:
            Logger.instance = Logger.__Logger(message, level)
        else:
            Logger.instance.log(message, level)

    def dump():
        # passing the dump command to the singleton
        Logger.instance.dump()

