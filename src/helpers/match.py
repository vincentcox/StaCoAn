class Match:
    all_global_matches = list()
    def __init__(self, matchword, importance, comment):
        self.matchword = matchword
        self.importance = importance
        self.comment = comment
        self.regex = False


class MatchSource(Match):
    def __init__(self, matchword, line, lines_in_file, importance, total_count_lines, owasp_item, comment):
        Match.__init__(self, matchword, importance, comment)
        self.line = line
        self.owasp_item = owasp_item
        self.lines_in_file = lines_in_file
        self.total_count_lines = total_count_lines
        Src_Match.all_global_matches.append(self)


class MatchDatabase(Match):
    def __init__(self, matchword, line, table, value, importance, comment):
        Match.__init__(self, matchword, importance, comment)
        self.table = table
        self.line = line
        self.value = value
        Db_Match.all_global_matches.append(self)



class Src_Match:
    all_global_matches = list()

    def __init__(self, matchword, line, lines_in_file, importance):
        self.matchword = matchword
        self.line = line
        self.lines_in_file = lines_in_file
        self.importance = importance
        Src_Match.all_global_matches.append(self)


class Db_Match:
    all_global_matches = list()

    def __init__(self, matchword, line, key, value, importance):
        self.matchword = matchword
        self.line = line
        self.key = key
        self.value = value
        self.importance = importance
        Db_Match.all_global_matches.append(self)