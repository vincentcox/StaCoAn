import os
import sys
from collections import OrderedDict
import copy
from operator import itemgetter

import configparser

from helpers.logger import Logger

class ExclItem:
    def __init__(self, searchword, comment, dir):
        self.searchword = searchword
        self.comment = comment
        self.dir = dir

class SearchItem:
    def __init__(self, searchword, importance, comment, owasp):
        self.searchword = searchword
        self.importance = importance
        self.comment = comment
        self.owasp = owasp


class SearchLists:
    all_lists = dict()
    def __init__(self):
        config = configparser.ConfigParser()
        config.read("config.ini")

        src_filename = os.path.join(config.get("ProgramConfig", 'config_folder'),
                                    config.get("ProgramConfig", 'src_search_words'))
        owasp_filename = os.path.join(config.get("ProgramConfig", 'config_folder'),
                                      config.get("ProgramConfig", 'owasp_search_words'))
        db_filename = os.path.join(config.get("ProgramConfig", 'config_folder'),
                                   config.get("ProgramConfig", 'db_search_words'))
        exclusion_filename = os.path.join(config.get("ProgramConfig", 'config_folder'),
                                          config.get("ProgramConfig", 'exclusion_filename'))

        # Import all searchlists into objects in a searchlist
        self.all_lists["SRC_WORDS"] = SearchList(src_filename, "SRC_WORDS")
        self.all_lists["OWASP_WORDS"] = SearchList(owasp_filename, "OWASP_WORDS")
        self.all_lists["DB_WORDS"] = SearchList(db_filename, "DB_WORDS")
        self.all_lists["EXCL_WORDS"] = SearchList(exclusion_filename, "EXCL_WORDS")

        # Merge owasp and src
        for item in SearchLists.all_lists["OWASP_WORDS"].ListCollection:
            SearchLists.all_lists["SRC_WORDS"].ListCollection.append(item)

        # All findings
        self.all_lists["ALL_WORDS"] = copy.deepcopy(SearchLists.all_lists["SRC_WORDS"])
        for item in SearchLists.all_lists["DB_WORDS"].ListCollection:
            SearchLists.all_lists["ALL_WORDS"].ListCollection.append(item)

        # Sort again on importance
        self.all_lists["ALL_WORDS"].sortList()
        self.all_lists["SRC_WORDS"].sortList()


class SearchList:
    def __init__(self, filename, name):
        self.ListCollection = []
        if name == "EXCL_WORDS":
            self.importExclList(filename)
        else:
            self.importList(filename)
            self.sortList()


    def addSearchItem(self, searchword, importance, comment, owasp):
        item = SearchItem(searchword, importance, comment, owasp)
        self.ListCollection.append(item)
    def addExclItem(self, searchword, comment, dir):
        item = ExclItem(searchword, comment, dir)
        self.ListCollection.append(item)
    def importExclList(self, filename):
        try:
            with open(filename, "r") as file:
                lines_in_file = file.read().splitlines()
        except IOError:
            Logger("could not open file '%s'." % filename, Logger.ERROR)
            return list()
        line_index = 1
        try:
            for line in lines_in_file:

                searchword = line.split('|||')[0]
                if len(line.split('|||')) > 2:
                    comment = line.split('|||')[2]
                else:
                    comment = ""
                dir_list_with_quotes = str(line.split('|||')[1]).split(',')
                dir_list_without_quotes = []
                for item in dir_list_with_quotes:
                    dir_list_without_quotes.append(item.strip("\""))
                self.addExclItem(searchword, comment, os.path.join(*dir_list_without_quotes))
                line_index = line_index + 1
        except IOError:
            Logger("Format is not readable or file is missing: %s." % filename, Logger.ERROR)
            sys.exit()

    def importList(self, filename):
        try:
            with open(filename, "r") as file:
                lines_in_file = file.read().splitlines()
        except IOError:
            Logger("could not open file '%s'." % filename, Logger.ERROR)
            return list()
        line_index = 1
        try:
            for line in lines_in_file:
                if line.split('|||')[1]:
                    searchword = line.split('|||')[0]
                    if line.split('|||')[1]:
                        importance = int(line.split('|||')[1])
                    else:
                        importance = 20
                    if len(line.split('|||')) > 2:
                        comment = line.split('|||')[2]
                    else:
                        comment = ""
                    if "owasp_static_android.txt" in filename:
                        owasp = True
                    else:
                        owasp = False
                    self.addSearchItem(searchword, importance, comment, owasp)
                line_index = line_index + 1
        except IOError:
            Logger("Format is not readable or file is missing: %s." % filename, Logger.ERROR)
            sys.exit()
        pass

    def sortList(self):
        self.ListCollection.sort(key=lambda x: x.importance, reverse=True)



