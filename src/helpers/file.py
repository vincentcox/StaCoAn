import os
import re
import sqlite3

import configparser

from helpers.logger import Logger
from helpers.match import MatchDatabase, MatchSource
from helpers.searchwords import SearchLists


class File:
    config = configparser.ConfigParser()
    config.read("config.ini")
    non_regex_indicator = config.get("ProgramConfig", 'non_regex_indicator')

    def __init__(self, file_path):
        self.file_path = file_path
        self.name = os.path.basename(file_path).replace(".", "_")
        self.src_matches = list()
        self.db_matches = list()
        self.icon = "insert_drive_file" # Materialise Icon
        self.fa_icon = "file" # Font Awesome icon, used in the tree-view
        self.all_matches = list()
        self.unique_words = list()
        self.grouped_matches = dict() #contains an array of Match objects for each unique word

    def find_matches_in_db_file(self):
        # Set icon of file
        self.icon = "insert_invitation"
        self.fa_icon = "database"

        db = sqlite3.connect(self.file_path)
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table_name in tables:
            table_name = table_name[0]
            cursor = db.execute("SELECT * from %s" % table_name)
            line = 0
            for row in cursor.fetchall():
                line += 1
                for listItem in SearchLists.all_lists["DB_WORDS"].ListCollection:
                    exclude = False
                    # if re.match(File.non_regex_indicator, str(row)):
                    #     Searchwords.db_search_words[matchword].regex = True
                    if re.search(listItem.searchword, str(row), re.IGNORECASE):
                        for ExclItem in SearchLists.all_lists["EXCL_WORDS"].ListCollection:
                            if ExclItem.searchword == listItem.searchword and ExclItem.dir in self.file_path:
                                Logger("Database exclusion found: %s in file %s" % (str(ExclItem.searchword), self.file_path),
                                       Logger.INFO)
                                exclude = True
                        if exclude == False:
                            importance = listItem.importance
                            db_match = MatchDatabase(listItem.searchword, line, str(table_name), str(row), importance, listItem.comment)
                            self.db_matches.append(db_match)
                            self.all_matches.append(db_match)
        self.orden_matches()

    def find_matches_in_src_file(self, CODE_OFFSET, QUERY_IMPORTANCE):
        try:
            if len(self.file_path.encode('unicode_escape').decode()) > 255:
                Logger("Filepath is too big. Try moving the StaCoAn folder to the root of your drive, make the APK name shorter and try again. The following file will be ignored to let StaCoAn continue: '%s'" % self.file_path, Logger.WARNING)
            else:
                with open(self.file_path, "r", encoding="utf8", errors='ignore') as file:
                    lines_in_file = file.read().splitlines()
                line_index = 1
                for line in lines_in_file:
                    for listItem in SearchLists.all_lists["SRC_WORDS"].ListCollection:
                        if int(listItem.importance) > QUERY_IMPORTANCE:
                            # if re.match(File.non_regex_indicator, listItem.searchword):
                            #     Searchwords.src_search_words[query].regex = True
                            if re.search(listItem.searchword, line, re.IGNORECASE):
                                exclude = False
                                for ExclItem in SearchLists.all_lists["EXCL_WORDS"].ListCollection:
                                    if re.search(ExclItem.searchword, line, re.IGNORECASE):
                                        if (ExclItem.dir in self.file_path or (
                                                ExclItem.dir == "" or ExclItem.dir is None)):
                                            # Logger("SRC exclusion found: %s in file %s" % (str(ExclItem.searchword), self.file_path),
                                            #       Logger.INFO)
                                            exclude = True
                                if exclude == False:
                                    upper_range = min(line_index + CODE_OFFSET, len(lines_in_file) + 1)
                                    lower_range = max(line_index - CODE_OFFSET - 1, 1)
                                    src_match = MatchSource(listItem.searchword, line_index,
                                                            lines_in_file[lower_range:upper_range],
                                                            listItem.importance, len(lines_in_file), listItem.owasp,
                                                            listItem.comment)
                                    self.all_matches.append(src_match)
                                    self.src_matches.append(src_match)
                    line_index = line_index + 1
                self.orden_matches()
        except IOError as e:
            Logger("could not open file '%s'. Error:" %(self.file_path, e.strerror), Logger.WARNING)
            return list()


    def orden_matches(self):
        grouped_matches = list()
        #grouping
        for match in self.all_matches:
            if match.matchword not in self.unique_words:
                self.unique_words.append(match.matchword)
        for word in self.unique_words:
            self.grouped_matches[word] = list()
            for match in self.all_matches:
                if match.matchword == word:
                    grouped_matches.append(match)
                    self.grouped_matches[word].append(match)
        # To sort here, use this. But searchwords itself are sorted so.
        # print(self.name)
        # for matches in reversed([self.grouped_matches[i] for i in sorted(self.grouped_matches,
        #                                                                  key=Searchwords.all_searchwords.__getitem__)]):
        #     for match in matches:
        #         print(match.matchword)

        # ----
        #self.src_matches = grouped_matches
        # order them according to query importance
        # ordened_matches = OrderedDict()
        # for match in self.src_matches:
        #     ordened_matches[match.matchword] = match
        # sorting_dict = OrderedDict(sorted(ordened_matches.items(), key=itemgetter(0)))
        # temp_matches = []
        # for f, match in sorting_dict.items():
        #     temp_matches.insert(0, match)
        # self.src_matches = temp_matches

