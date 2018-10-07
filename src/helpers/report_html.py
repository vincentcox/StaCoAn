import base64
import codecs
import errno
import hashlib
import json
import os
import re
import sqlite3

import configparser

from helpers.html_page import Htmlpage
from helpers.logger import Logger
from helpers.project import Project
from helpers.searchwords import SearchLists


class Report_html(Htmlpage):
    # Read out the configuration file for the necessary parameters
    config = configparser.ConfigParser()
    config.read("config.ini")
    non_regex_indicator = config.get("ProgramConfig", 'non_regex_indicator')
    code_offset = config.getint("ProgramConfig", 'code_offset')

    def __recursion_files(self, jsfile, folder, relative_path_array):
        # Recursion is used to iterate trough the files and folders.
        for item in os.listdir(folder):
            filename = item
            item = os.path.join(folder, item)
            # exclude the looty.js and lootbox.js
            # if looty.js is included you end up with a 100 gig file
            # if lootbox.js is included, you end up with double results
            #  |-> you will get the expected results + the localstorage results.
            #  |-> by excluding this file, you ommit the localstorage results.
            if not filename in ["looty.js", "lootbox.js"]:
                if os.path.isfile(item):  # if current item is not a folder
                    itemdata = ""
                    with open(item, 'rb') as f:
                        itemdata = f.read()
                    # The contens of the file needs to be encoded into base64.
                    itemdata = str(base64.b64encode(itemdata).decode('utf-8'))
                    # Creating a file entry in the looty.js file
                    jsfile += os.path.basename(
                        folder) + ".file(\"" + filename + "\", \"" + itemdata + "\", {base64: true});" + "\n"
                else:  # if current item is a folder
                    # Creating a folder entry in the looty.js file
                    jsfile += "var " + filename + " = " + os.path.basename(
                        folder) + ".folder('" + filename + "');" + "\n"
                    # relative_path_array keeps track how deep we are in the folder-architecture
                    # in the zip-file.
                    relative_path_array.append(os.path.basename(folder))
                    # For every folder we need to do all previous steps (recursion)
                    jsfile += self.__recursion_files("", item, relative_path_array) + "\n"
        return jsfile

    def make_loot_report_content(self):
        # Building the zip architecture when a user wants to download the report.
        # Keep in mind that the "lootpage" is build by content from the html5 localstorage.
        # Therefore, if you just CTRL+S the page it will work for your computer. But the moment
        # you use it in a different browser or computer, the page will be empty because
        # the localstorage doesn't contain the loot.
        #
        # Using https://stuk.github.io/jszip/ to assemble the zip and make it download.
        jsfile = "function downloadPage(){"
        jsfile += "var zip = new JSZip();"  +"\n"
        jsfile += "var html = zip.folder('html');"
        jsfile += "var myHTMLDoc = document.documentElement.innerHTML;"
        jsfile += "zip.file('report.html', btoa(myHTMLDoc), {base64: true});"

        # file and folder entries in the zip architecture
        jsfile += self.__recursion_files("", os.path.join(os.getcwd(), "report", "html"), ["html"])

        jsfile += """
            zip.generateAsync({type:"blob"})
                .then(function(content) {
                    // see FileSaver.js
                    saveAs(content, "example.zip");
                });

        }
        """
        # We need to write the content to a an empty file, so first removing it.
        path = os.path.join(os.getcwd(), "report", "html", "looty.js")
        try:
            os.remove(path)
        except:
            pass # if file is already deleted, it's fine
        with open(path, 'a') as the_file:
            the_file.write(jsfile)

    def get_source_code_from_file(self, file_path, project):
        if file_path in Project.projects[project.name].db_files:
            with self.tag("div", klass="chip col"):
                with self.tag("i", klass="material-icons"):
                    self.text("attach_file")
                with self.tag('a', ('href', "html/view_source.html?file=" + file_path),
                              ("target", "_blank")):
                    self.text(file_path.split(os.getcwd())[1])
            file = Project.projects[project.name].db_files[file_path]
            for match in file.db_matches:
                with self.tag("div", klass="col s12"):
                    with self.tag("div", klass="card"):
                        with self.tag("div", klass="valign-wrapper"):
                            # rating color
                            with self.tag("i",
                                          klass="material-icons medium grade-" + str(
                                              next((ListItem.importance for ListItem in
                                                    SearchLists.all_lists["DB_WORDS"].ListCollection if
                                                    ListItem.searchword == match.matchword), None))):

                                self.text("report")
                            with self.tag('h5'):
                                if not match.regex:
                                    self.text(match.matchword)
                                    # print(match.matchword)
                                else:
                                    self.text("regex: " + match.matchword)
                        # If comment of match is not empty, place the issue description
                        if not match.comment == "":
                            with self.tag("ul", klass="collapsible"):
                                with self.tag("li"):
                                    with self.tag("div", klass="collapsible-header"):
                                        with self.tag("i", klass="material-icons"):
                                            self.text("info")
                                        self.text("Issue Description")
                                    with self.tag("div", klass="collapsible-body"):
                                        with self.tag("span"):
                                            self.text(match.comment)
                        with self.tag("div", klass="card-content"):
                            self.text("table: \""+str(match.table)+"\" : "+ str(match.value))
            with self.tag('div', klass="row"):
                with self.tag("div", klass="col s12"):
                    with self.tag("div", klass="card"):
                        with self.tag("div", klass="card-content"):
                            with self.tag("h5"):
                                self.text("Table viewer:")
                            file_lines_matches = ""
                            try:
                                con = sqlite3.connect(file_path)
                                cursor = con.cursor()
                                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                                tables = cursor.fetchall()
                                for tbl in tables:
                                    with self.tag('div', klass="row"):
                                        with self.tag("div", klass="col s12"):
                                            with self.tag("div", klass="card"):
                                                with self.tag("div", klass="card-content", style="overflow: scroll;"):
                                                    with self.tag("span", klass="card-title"):
                                                        self.text(tbl[0])
                                                    cursor.execute("SELECT * FROM " + tbl[0] + ";")
                                                    names = list(map(lambda x: x[0], cursor.description))
                                                    rows = cursor.fetchall()
                                                    with self.tag("table", klass="striped highlight"):
                                                        with self.tag("thead"):
                                                            with self.tag("tr"):
                                                                for name in names:
                                                                    with self.tag("th"):
                                                                        self.text(str(name))
                                                        matches = dict()
                                                        for match in file.db_matches:
                                                            matches[match.matchword] = match.importance
                                                        with self.tag("tbody"):
                                                            for row in rows:
                                                                with self.tag("tr"):
                                                                    for item in row:
                                                                        if str(item) in matches:
                                                                            with self.tag("td", klass="grade-" + str(matches[item])):
                                                                                self.text(str(item))
                                                                        else:
                                                                            with self.tag("td"):
                                                                                self.text(str(item))
                            except:
                                pass

                            with self.tag('pre',('data-src', os.path.basename(file_path)), ('data-line', file_lines_matches ), klass='code line-numbers'):
                                try:
                                    with codecs.open(file_path, "r", 'utf-8', errors='ignore') as file:
                                        lines_in_file = file.read().splitlines()
                                        with self.tag('code'):
                                            i = 0
                                            for line in lines_in_file:
                                                self.text(line)
                                                self.doc.nl()
                                except:
                                    Logger("could not open file '%s'." % file_path, Logger.WARNING)

        elif file_path in Project.projects[project.name].src_files:
            file = Project.projects[project.name].src_files[file_path]
            if not file.src_matches:
                self.doc.asis("""
                <script>
                $( document ).ready(function() {
                    Materialize.toast('No matches found in this file', 9000)
                });
                </script>
                """)
                # print(file.name)
                # It is oke now, but you can place a message "no matches found" at the file.
            with self.tag("div", klass="chip col"):
                with self.tag("i", klass="material-icons"):
                    self.text("attach_file")
                with self.tag('a', ('href', "html/view_source.html?file=" + file.file_path),
                              ("target", "_blank")):
                    self.text(file.file_path.split(os.getcwd())[1])
            # had to get rid of duplicates, might make this cleaner in the future.
            local_tracking_list = dict()
            for word in file.unique_words:
                local_tracking_list[word] = int(0)
            for grouped_word, group in file.grouped_matches.items():
                for match in group:
                    if local_tracking_list[match.matchword] > 0:
                        continue  # skip duplicate
                    local_tracking_list[match.matchword] = +1
                    with self.tag("div", klass="col s12"):
                        with self.tag("div", klass="card"):
                            with self.tag("div", klass="valign-wrapper"):
                                # rating color
                                with self.tag("i",
                                              klass="material-icons medium grade-" + str(
                                                  next((ListItem.importance for ListItem in
                                                        SearchLists.all_lists["SRC_WORDS"].ListCollection if
                                                        ListItem.searchword == match.matchword), None))):
                                    self.text("report")
                                with self.tag('h5'):
                                    if not match.regex:

                                        self.text(match.matchword)
                                    else:
                                        self.text("regex: " + match.matchword)
                            # If comment of match is not empty, place the issue description
                            if not match.comment == "":
                                with self.tag("ul", klass="collapsible"):
                                    with self.tag("li"):
                                        with self.tag("div", klass="collapsible-header"):
                                            with self.tag("i", klass="material-icons"):
                                                self.text("info")
                                            self.text("Issue Description")
                                        with self.tag("div", klass="collapsible-body"):
                                            with self.tag("span"):
                                                self.text(match.comment)
                            # Place owasp icon
                            if match.owasp_item:
                                with self.tag("ul", klass="collapsible"):
                                    with self.tag("li"):
                                        with self.tag("div", klass="collapsible-header"):
                                            with self.tag("img", ('data-position', 'top'),
                                                          ('data-tooltip', 'OWASP item'),
                                                          src="html/owasp_logo.png", height="20em", style="margin-right: 1rem;margin-left: 5px;", klass="tooltipped"):
                                                pass
                                            self.text(" OWASP Item")
                                        with self.tag("div", klass="collapsible-body"):
                                            with self.tag("span"):
                                                self.text("For more information, have a look at: https://www.owasp.org/index.php/OWASP_Mobile_Security_Testing_Guide")


                            with self.tag("div", klass="card-tabs"):
                                with self.tag("ul", klass="tabs tabs-fixed-width", style="background-color: #30363A !important;"):
                                    for group_matchword, matchobjects_list in file.grouped_matches.items():
                                        temp_counter = 0
                                        if not match.matchword == group_matchword:
                                            continue
                                        for matchobject in matchobjects_list:
                                            with self.tag("li", klass="tab"):
                                                if temp_counter > 0:
                                                    with self.tag('a', style="color: #d82c2b;",
                                                                  href="#" + os.path.basename(
                                                                      file.name).replace(".", "_") + str(
                                                                      matchobject.line) + ''.join(
                                                                      filter(str.isalpha, match.matchword))[
                                                                                          :4]):
                                                        self.text("line " + str(matchobject.line))
                                                else:
                                                    with self.tag('a', style="color: #d82c2b;",
                                                                  href="#" + os.path.basename(
                                                                      file.name).replace(".", "_") + str(
                                                                      matchobject.line) + ''.join(
                                                                      filter(str.isalpha, match.matchword))[:4],
                                                                  klass="active"):
                                                        self.text("line " + str(matchobject.line))
                                            temp_counter += 1

                            with self.tag("div", klass="card-content"):
                                for group_matchword, matchobjects_list in file.grouped_matches.items():
                                    if not match.matchword == group_matchword:
                                        continue
                                    for matchobject in matchobjects_list:
                                        with self.tag("div",
                                                      id=os.path.basename(file.name).replace(".", "_") + str(
                                                          matchobject.line) + ''.join(
                                                          filter(str.isalpha, match.matchword))[:4]):
                                            self.text("Code @ line " + str(matchobject.line))
                                            start_line = max(matchobject.line - Report_html.code_offset, 1)
                                            with self.tag('pre', ('data-start', start_line),
                                                          ('data-line', matchobject.line),
                                                          ('data-src', os.path.basename(file.file_path)),
                                                          klass='code line-numbers'):
                                                with self.tag('code'):
                                                    for code in matchobject.lines_in_file:
                                                        fullcode = code + "\n"
                                                        self.text(fullcode)
                                            # Lootbox
                                            # To do: clean up


                                            string = file.file_path + "|||line: " + str(matchobject.line) + " : " + matchobject.matchword +"|||"+str(matchobject.importance)+"|||"+str(matchobject.matchword)+"|||"+str(matchobject.line)+"|||"+str(start_line)

                                            key = "loot_" + str(base64.b64encode(bytes(string, "utf-8")).decode('utf-8'))
                                            key = key.rstrip('=')
                                            codefile = ""
                                            for code in matchobject.lines_in_file:
                                                codefile = codefile + code + "\n"
                                            fullcode = str(base64.b64encode(bytes(codefile, "utf-8")).decode('utf-8'))
                                            self.doc.asis("<a class=\"waves-effect waves-light btn\" style='background-color: #30363A;' id=\"")
                                            self.doc.asis(key)
                                            self.doc.asis("\">Add to lootbox</a><script>"
                                                          "if (localStorage.getItem('"+key+"')){"
                                                                                           "$('#"+key+"').addClass('disabled');"
                                                                                           "}"
                                                          ""
                                                          "$( \"#")
                                            self.doc.asis(key)
                                            self.doc.asis("""" ).click(function() {
                                            $(this).addClass('disabled');
                                            localStorage.setItem('""")
                                            self.doc.asis(str(key))
                                            self.doc.asis("""' , """)
                                            self.doc.asis("'"+fullcode+"');")
                                            self.doc.asis("""  
                                            });
                                            </script>
                                            """)

                                            # End of lootbox

            with self.tag('div', klass="row"):
                with self.tag("div", klass="col s12"):
                    with self.tag("div", klass="card"):
                        with self.tag("div", klass="card-content"):
                            with self.tag("h5"):
                                self.text("Source code")
                            file_lines_matches = ""
                            for group_matchword, matchobjects_list in file.grouped_matches.items():
                                for matchobject in matchobjects_list:
                                    file_lines_matches = file_lines_matches + str(matchobject.line) + ","
                            with self.tag('pre',('data-src', os.path.basename(file_path)), ('data-line', file_lines_matches ), klass='code line-numbers'):
                                try:
                                    with codecs.open(file_path, "r", 'utf-8', errors='ignore') as file:
                                        lines_in_file = file.read().splitlines()
                                    with self.tag('code'):
                                        i = 0
                                        for line in lines_in_file:
                                            self.text(line)
                                            self.doc.nl()
                                except:
                                    Logger("could not open file '%s'." % file_path, Logger.WARNING)



    def findings_overview(self, project):
        with self.tag('div', klass=project.name + "_div"):
            with self.tag('h1', klass=project.name + "_title center-align"):
                self.text("Project: " + project.name)
            # print for each file the findings
            for file in project.src_files.values():
                if not file.src_matches:
                    continue
                with self.tag('div', klass="row"):
                    with self.tag("div", klass="chip col s10 offset-s1"):
                        with self.tag("i", klass="material-icons"):
                            self.text("attach_file")
                        with self.tag('a', ('href', "html/view_source.html?file=" + file.file_path),
                                      ("target", "_blank")):
                            self.text(file.file_path.split(os.getcwd())[1])
                    # had to get rid of duplicates, might make this cleaner in the future.
                    local_tracking_list = dict()
                    for word in file.unique_words:
                        local_tracking_list[word] = int(0)
                    for grouped_word, group in file.grouped_matches.items():
                        for match in group:
                            if local_tracking_list[match.matchword] > 0:
                                continue  # skip duplicate
                            local_tracking_list[match.matchword] = +1
                            with self.tag("div", klass="col s10 offset-s1"):
                                with self.tag("div", klass="card"):
                                    with self.tag("div", klass="valign-wrapper"):
                                        # rating color
                                        with self.tag("i",
                                                      klass="material-icons mediumgrade-" + str(
                                              Searchwords.all_searchwords[match.matchword])):
                                            self.text("beenhere")
                                        with self.tag('h5'):
                                            if not match.regex:
                                                self.text(match.matchword)
                                                # print(match.matchword)
                                            else:
                                                self.text("regex: " + match.matchword)
                                    with self.tag("div", klass="card-tabs"):
                                        with self.tag("ul", klass="tabs tabs-fixed-width cyan lighten-5"):
                                            for group_matchword, matchobjects_list in file.grouped_matches.items():
                                                temp_counter = 0
                                                if not match.matchword == group_matchword:
                                                    continue
                                                for matchobject in matchobjects_list:
                                                    with self.tag("li", klass="tab"):
                                                        if temp_counter > 0:
                                                            with self.tag('a',
                                                                          href="#" + os.path.basename(
                                                                              file.name).replace(".", "_") + str(
                                                                              matchobject.line) + ''.join(
                                                                              filter(str.isalpha, match.matchword))[
                                                                                                  :4]):
                                                                self.text("line " + str(matchobject.line))
                                                        else:
                                                            with self.tag('a',
                                                                          href="#" + os.path.basename(
                                                                              file.name).replace(".", "_") + str(
                                                                              matchobject.line) + ''.join(
                                                                              filter(str.isalpha, match.matchword))[:4],
                                                                          klass="active"):
                                                                self.text("line " + str(matchobject.line))
                                                    temp_counter += 1

                                    with self.tag("div", klass="card-content"):
                                        for group_matchword, matchobjects_list in file.grouped_matches.items():
                                            temp_counter = 0
                                            if not match.matchword == group_matchword:
                                                continue
                                            for matchobject in matchobjects_list:
                                                with self.tag("div",
                                                              id=os.path.basename(file.name).replace(".", "_") + str(
                                                                      matchobject.line) + ''.join(
                                                                      filter(str.isalpha, match.matchword))[:4]):
                                                    self.text("Code @ line " + str(matchobject.line))
                                                    fullcode = ""
                                                    start_line = max(matchobject.line - Report_html.code_offset, 1)
                                                    if matchobject.line < 3:
                                                        highlight_line = matchobject.line - start_line + 1
                                                    else:
                                                        highlight_line = matchobject.line - 1
                                                    with self.tag('pre', ('data-start', start_line),
                                                                  ('data-line', matchobject.line),
                                                                  ('data-src', os.path.basename(file.file_path)),
                                                                  klass='code line-numbers'):
                                                        with self.tag('code'):
                                                            #### This is a bugfix, newlines are removed in the beginning and end of the code. for now this placeholder to append
                                                            if matchobject.lines_in_file[0] == "":
                                                                matchobject.lines_in_file[
                                                                    0] = "<<<<empty line, will be fixed in futher release of stacoan>>>"
                                                            for code in matchobject.lines_in_file:
                                                                fullcode = code + "\n"
                                                                self.text(fullcode)

    def html_wordlist(self, project):
        with self.tag('div', klass=os.path.basename(project.workfolder) + "_div"):
            # print for each file the finding
            # maybe place this in project def
            frequency_words = project.frequency_word_list()
            # ----
            with self.tag("div", klass="row"):
                with self.tag("div", klass="col s12 offset"):
                    with self.tag("div", klass="card"):
                        with self.tag("div", klass="card-content"):
                            with self.tag("h5"):
                                self.text("Top findings:")
                            for word, freq in frequency_words.items():
                                with self.tag("div", klass="chip"):
                                    with self.tag("i",
                                                  klass="material-icons grade-"+str(
                                                  next((ListItem.importance for ListItem in
                                                        SearchLists.all_lists["ALL_WORDS"].ListCollection if
                                                        ListItem.searchword == word), None))):
                                        self.text("beenhere")
                                    self.text(word + " : " + freq)
                                # get src_files with frequency
                                with self.tag("ul", klass="collection"):
                                    for f, file in project.all_files.items():
                                        for match in file.all_matches:
                                            if word == match.matchword:
                                                with self.tag("li", klass="collection-item"):
                                                    with self.tag("i", klass="fa fa-"+file.fa_icon):
                                                        self.text("")
                                                    with self.tag('a', (
                                                            'href',
                                                            hashlib.md5(file.file_path.encode('utf-8')).hexdigest()+'.html?' + "&line=" + str(
                                                                match.line)),
                                                                  ("target", "_self")):
                                                        self.text(file.name)

                                self.doc.stag('br')

    class Tree_builder:
        # This class builds the tree view based on fancyTree.
        # More information: https://github.com/mar10/fancytree
        def return_tree_object(self):
            return self.path_hierarchy(self.project.workfolder)

        def hierarchy_line_object(self, path, match):
            # This is the line object in the tree hierarchy
            hierarchy = {
                'folder': False,
                'key': os.path.join(os.path.split(path)[0], os.path.basename(path)),
                'title': "line: " + str(match.line) + " : " + match.matchword,
                'path': path,
                'icon': "fa fa-long-arrow-alt-right fa-lg grade-" + str(match.importance),
                'line': match.line
            }
            return hierarchy

        def path_hierarchy(self, path):
            matches = list()
            for file_path, file in self.project.all_files.items():
                if path in file_path:
                    for match in file.all_matches:
                        matches.append(match)
            # The hierarchy structure will be the building block for each Folder/File
            # Note that we use for both the file and folder: Folder: True
            # This is because the line-number is the final leaf in the tree.
            # To make it work with fancyTree we have to consider a file as Folder=True
            hierarchy = {
                'folder': True,
                'key': os.path.split(path)[0] + os.path.basename(path),
                'title': os.path.basename(path),
                'path': path,
                'icon': "fa fa-folder fa-lg",
            }

            try:
                def dirpaths(path):
                    dirpaths = list()

                    # for path_from_dir_list in os.listdir(path):
                    if not len(path.encode('unicode_escape').decode()) > 255: # filepath too long
                        for path_from_dir_list in os.listdir(path):
                            if path_from_dir_list.endswith(tuple(Project.allowed_file_extensions)) or os.path.isdir(os.path.join(path,path_from_dir_list)):
                                dirpaths.append(path_from_dir_list)
                    return dirpaths
                hierarchy['children'] = [
                    self.path_hierarchy(os.path.join(path, contents))
                    for contents in dirpaths(path)
                ]
                # Get the max match importance for the bottom-up structure.
                # A folder containing a file with critical matches should be colored red.
                # The coloring happens with grade-NUMBER, where the number is the
                # match importance (criticality of the finding).

                highest_importance = 0
                for file in self.project.all_files:
                    if path in file:
                        for match in matches:
                            if int(highest_importance) < int(match.importance):
                                highest_importance = match.importance
                hierarchy['icon'] = "fa fa-folder fa-lg grade-" + str(highest_importance)

            except OSError as e:
                if e.errno != errno.ENOTDIR:
                    raise
                hierarchy['folder'] = False
                if e.filename in self.project.all_files:
                    for match in self.project.all_files[e.filename].all_matches:
                        hierarchy['children'] = [
                            self.hierarchy_line_object(path, match)
                            for match in self.project.all_files[e.filename].all_matches
                        ]
                # Get the max match importance for the bottom-up structure.
                # A folder containing a file with critical matches should be colored red.
                # The coloring happens with grade-NUMBER, where the number is the
                # match importance (criticality of the finding).
                highest_importance = 0
                for file in self.project.all_files:
                    if path in file:
                        for match in matches:
                            if int(highest_importance) < int(match.importance):
                                highest_importance = match.importance
                hierarchy['icon'] = "fa fa-"+self.project.all_files[e.filename].fa_icon+" fa-lg grade-" + str(highest_importance)
                # We set this parameter "is_file"=True, because we want to trigger only a click at the
                # lines (end leaves in the tree). This is because a file is here not the end leaf of the tree.
                hierarchy['is_file'] = True
                if self.current_file == path:
                    hierarchy['selected'] = True
                    hierarchy['focussed'] = True
                    hierarchy['active'] = True
                hierarchy['url'] = hashlib.md5(path.encode('utf-8')).hexdigest()+'.html'
            return hierarchy

        def __init__(self, project, file):
            self.project = project
            self.current_file = file

        def tree_js_file(project):
            tree_js_file_content=""
            tree_js_file_content+="""
                  $("#tree").fancytree({
                  source: ["""
            tree_js_file_content+=json.dumps(project.tree_object, indent=2, sort_keys=True)  # speed improvement of 0.5s per created file
            # self.doc.asis(json.dumps(Report_html.Tree_builder(project, FILE).return_tree_object(), indent=2, sort_keys=True))
            tree_js_file_content+="""
                  ],
                  extensions: ["glyph", "persist"],
                  persist: {
                    // Available options with their default:
                    cookieDelimiter: "~",    // character used to join key strings
                    cookiePrefix: undefined, // 'fancytree-<treeId>-' by default
                    cookie: { // settings passed to jquery.cookie plugin
                      raw: false,
                      expires: "",
                      path: "",
                      domain: "",
                      secure: false
                    },
                    expandLazy: false, // true: recursively expand and load lazy nodes
                    expandOpts: undefined, // optional `opts` argument passed to setExpanded()
                    overrideSource: true,  // true: cookie takes precedence over `source` data attributes.
                    store: "auto",     // 'cookie': use cookie, 'local': use localStore, 'session': use sessionStore
                    types: "active expanded focus selected"  // which status types to store: active expanded focus selected
                  },
                      icon: function(event, data){
                        // (Optional dynamic icon definition...)
                      },
                      glyph: {
                        // The preset defines defaults for all supported icon types.
                        // It also defines a common class name that is prepended (in this case 'fa ')
                        preset: "awesome4",
                        map: {
                          // Override distinct default icons here
                          folder: "fa-folder",
                          folderOpen: "fa-folder-open"
                        }
                      },
                        activeVisible: true, // Make sure, active nodes are visible (expanded)
                        aria: true, // Enable WAI-ARIA support
                        autoActivate: true, // Automatically activate a node when it is focused using keyboard
                        autoCollapse: false, // Automatically collapse all siblings, when a node is expanded
                        autoScroll: false, // Automatically scroll nodes into visible area
                        clickFolderMode: 3, // 1:activate, 2:expand, 3:activate and expand, 4:activate (dblclick expands)
                        checkbox: false, // Show checkboxes
                        debugLevel: 2, // 0:quiet, 1:normal, 2:debug
                        disabled: false, // Disable control
                        focusOnSelect: true, // Set focus when node is checked by a mouse click
                        escapeTitles: false, // Escape `node.title` content for display
                        generateIds: false, // Generate id attributes like <span id='fancytree-id-KEY'>
                        idPrefix: "ft_", // Used to generate node idÂ´s like <span id='fancytree-id-<key>'>
                        icon: true, // Display node icons
                        keyboard: true, // Support keyboard navigation
                        keyPathSeparator: "/", // Used by node.getKeyPath() and tree.loadKeyPath()
                        minExpandLevel: 1, // 1: root node is not collapsible
                        quicksearch: false, // Navigate to next node by typing the first letters
                        rtl: false, // Enable RTL (right-to-left) mode
                        selectMode: 1, // 1:single, 2:multi, 3:multi-hier
                        tabindex: "0", // Whole tree behaves as one single control
                        titlesTabbable: false, // Node titles can receive keyboard focus
                        tooltip: false // Use title as tooltip (also a callback could be specified)
                    });
                    $( document ).ready(function() {
                        var loot_files = JSON.parse(localStorage.getItem("loot_files"));
                    });
    
    
                    $(document).dblclick(function(event) {
                    try {
                          var node = $.ui.fancytree.getNode(event),
                          // Only for click and dblclick events:
                          // 'title' | 'prefix' | 'expander' | 'checkbox' | 'icon'
                          tt = $.ui.fancytree.getEventTargetType(event);
                          if (node.data.is_file){
                          console.log(node.key);
                          console.log(node.data.url);
                          window.location.href = node.data.url;      
                          }
                    }
                    catch(err) {
    
                    }
                });
                $("#lootbox").on("click", ".close", function(){ 
                var current_file = $(this).parent().text().slice(0, -5);
                var loot_files = JSON.parse(localStorage.getItem("loot_files"));
                var i = 0;
                loot_files.forEach(function(entry) {
                    console.log(entry);
                    console.log(i);
                    if (current_file === String(entry)) 
                    {
                        if (String(i) === String(0)){
                        loot_files = loot_files.splice(i, 1);
                        i = i -1;
                        }else{
    
                        }
                        localStorage.setItem("loot_files", JSON.stringify(loot_files));
                    }
                    i += 1;  
                });
    
                ;});
                
                """
            return tree_js_file_content




    def tree_view(self, project, FILE):
        # This class builds the HTML page for the Treeview.
        with self.tag('div', klass=os.path.basename(project.workfolder) + "_div"):
            with self.tag('h1', klass=os.path.basename(project.workfolder) + "_title center-align"):
                self.text("Project: " + os.path.basename(project.name))
            with self.tag("div", klass="row"):
                with self.tag("div", id="tree", klass="col s12 m12 l3"):
                    self.text("")
                with self.tag("div", id="codeview", klass="col s12 m12 l9"):
                    if FILE != "":
                        self.get_source_code_from_file(
                            FILE,
                            project)
                    else:
                        #this is the startpage of the project
                        self.html_wordlist(project)
            self.doc.asis("""
            <script src="tree_js_content.js"></script>
            """)
