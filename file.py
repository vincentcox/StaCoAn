import configparser
import os
import re
import sqlite3

from logger import Logger
from match import MatchDatabase, MatchSource
from searchwords import Searchwords


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
                for matchword in Searchwords.db_search_words:
                    if matchword in str(row):
                        importance = Searchwords.db_search_words[matchword]
                        db_match = MatchDatabase(matchword, line, str(table_name), str(row), importance)
                        self.db_matches.append(db_match)
                        self.all_matches.append(db_match)
        self.orden_matches()

    def find_matches_in_src_file(self, CODE_OFFSET, QUERY_IMPORTANCE):
        try:
            with open(self.file_path, "r", encoding="utf8", errors='ignore') as file:
                lines_in_file = file.read().splitlines()
        except IOError as e:
            Logger("could not open file '%s'. Error:" %(self.file_path, e.strerror), Logger.WARNING)
            return list()
        line_index = 1
        for line in lines_in_file:
            for query in Searchwords.src_search_words.keys():
                if int(Searchwords.src_search_words[query]) > QUERY_IMPORTANCE:
                    if re.match(File.non_regex_indicator, query):
                        if query.lower() in line.lower():
                            upper_range = min(line_index + CODE_OFFSET, len(lines_in_file)+1)
                            lower_range = max(line_index - CODE_OFFSET-1, 1)
                            src_match = MatchSource(query, line_index, lines_in_file[lower_range:upper_range],
                                                    Searchwords.src_search_words[query], len(lines_in_file))
                            self.all_matches.append(src_match)
                            self.src_matches.append(src_match)

                    else:
                        if re.search(query, line.lower(), re.IGNORECASE):
                            upper_range = min(line_index + CODE_OFFSET, len(lines_in_file)+1)
                            lower_range = max(line_index - CODE_OFFSET-1, 1)
                            src_match = MatchSource(query, line_index, lines_in_file[lower_range:upper_range],
                                                    Searchwords.src_search_words[query], len(lines_in_file))
                            self.all_matches.append(src_match)
                            self.src_matches.append(src_match)
            line_index = line_index + 1
        self.orden_matches()

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

