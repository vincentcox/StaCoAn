import os
import sys
from collections import OrderedDict
from operator import itemgetter

import configparser

from helpers.logger import Logger


class Searchwords:
    all_searchwords = OrderedDict()
    # 'src_search_words': Contains all searchwords for source, config files like .java, .xml, .html, .js,...
    owasp_search_words = OrderedDict()
    src_search_words = OrderedDict()
    # 'db_search_words': Contains all searchwords for database files
    db_search_words = OrderedDict()
    # 'exclusion_list.txt': Contains all searchwords which should be excluded in a certain folder
    exclusion_list = []

    # Each Searchwords-list needs to be imported.
    # 'filename' will be the location of the list which needs to be imported.
    # 'search_words' will be linked to: 'src_search_words' or 'db_search_words'
    def searchwords_for_type(self, filename, search_words):
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
                    search_words[line.split('|||')[0]] = int(line.split('|||')[1])
                else:
                    # Default criticality = 20
                    search_words[line.split('|||')[0]] = 20
                line_index = line_index + 1
        except IOError:
            Logger("Format is not readable or file is missing: %s." % filename, Logger.ERROR)
            sys.exit()
        # Sort search words.
        search_words = OrderedDict(sorted(search_words.items(), key=itemgetter(1)))
        self.all_searchwords.update(search_words)

    def exclusion_list_reader(self, filename):
        try:
            with open(filename, "r") as file:
                lines_in_file = file.read().splitlines()
        except IOError:
            Logger("could not open file '%s'." % filename, Logger.ERROR)
            return list()
        line_index = 1
        try:
            for line in lines_in_file:
                dir_list_with_quotes = str(line.split('|||')[1]).split(',')
                dir_list_without_quotes = []
                for item in dir_list_with_quotes:
                    dir_list_without_quotes.append(item.strip("\""))
                self.exclusion_list.append([line.split('|||')[0],  os.path.join(*dir_list_without_quotes)])
                line_index = line_index + 1
        except IOError:
            Logger("Format is not readable or file is missing: %s." % filename, Logger.ERROR)
            sys.exit()
        #self.exclusion_list.append(search_words)

    def searchwords_import(self):
        config = configparser.ConfigParser()
        config.read("config.ini")
        # How to extend with other filetypes:
        # TYPE_filename = os.path.join(config.get("ProgramConfig", 'config_folder'),
        #                            config.get("ProgramConfig", 'TYPE_search_words'))

        src_filename = os.path.join(config.get("ProgramConfig", 'config_folder'),
                                    config.get("ProgramConfig", 'src_search_words'))
        owasp_filename = os.path.join(config.get("ProgramConfig", 'config_folder'),
                                    config.get("ProgramConfig", 'owasp_search_words'))
        db_filename = os.path.join(config.get("ProgramConfig", 'config_folder'),
                                   config.get("ProgramConfig", 'db_search_words'))
        exclusion_filename = os.path.join(config.get("ProgramConfig", 'config_folder'),
                                   config.get("ProgramConfig", 'exclusion_filename'))
        search_list = dict()
        exclusion_list = dict()
        search_list[src_filename] = Searchwords.src_search_words
        search_list[owasp_filename] = Searchwords.owasp_search_words
        search_list[db_filename] = Searchwords.db_search_words
        exclusion_list[exclusion_filename] = Searchwords.exclusion_list
        # How to extend (Cont.d)
        # search_list[TYPE_filename] = Searchwords.TYPE_search_words
        for filename, search_words in search_list.items():
            self.searchwords_for_type(filename, search_words)
        for filename, search_words in exclusion_list.items():
            self.exclusion_list_reader(filename)

        # add owasp list to source code list:
        Searchwords.src_search_words.update(Searchwords.owasp_search_words)
