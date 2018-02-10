import ntpath
import os
import subprocess
import zipfile
import json
import sys

from logger import Logger
from file import File
from searchwords import Searchwords
import configparser
from collections import OrderedDict


PATH = os.getcwd()


class Project:
    config = configparser.ConfigParser()
    config.read("config.ini")
    apptypes = json.loads(config.get("ProgramConfig", 'apptypes'))
    src_filetypes = json.loads(config.get("ProgramConfig", 'src_filetypes'))
    db_filetypes = json.loads(config.get("ProgramConfig", 'db_filetypes'))
    query_importance = config.getint("ProgramConfig", 'query_importance')
    code_offset = config.getint("ProgramConfig", 'code_offset')
    limit_top_findings= config.getint("ProgramConfig", 'limit_top_findings')
    development = config.getint("Development", 'development')
    allowed_file_extensions = list()
    allowed_file_extensions = src_filetypes + db_filetypes
    projects = dict()
    tree_object = dict()

    def __init__(self, application_file):
        self.name = os.path.basename(application_file).replace(".", "_")
        self.application_file = application_file
        self.src_files = dict()
        self.db_files = dict()
        self.all_files = dict()
        self.src_filetypes = self.src_filetypes
        self.query_importance = self.query_importance
        Project.projects[self.name] = self

    def searchcontroller(self):
        # controller to search for each file in project
        for root, directories, filenames in os.walk(self.workfolder):
            for filename in filenames:
                full_file_name = os.path.join(root, filename)
                if (full_file_name.lower().endswith(tuple(self.src_filetypes))):
                    self.src_files[full_file_name] = File(full_file_name)
                    self.src_files[full_file_name].find_matches_in_src_file(self.code_offset, self.query_importance)
                elif (full_file_name.lower().endswith(tuple(Project.db_filetypes))):
                    self.db_files[full_file_name] = File(full_file_name)
                    self.db_files[full_file_name].find_matches_in_db_file()
        self.all_files.update(self.db_files)
        self.all_files.update(self.src_files)
        from report_html import Report_html
        treeview = Report_html.Tree_builder(self, "")
        self.tree_object = treeview.return_tree_object()

    def get_file(self, file_path):
        return self.src_files[file_path]

    def frequency_word_list(self):
        frequency_words = OrderedDict()
        # Get frequency of each word
        for f, file in self.all_files.items():
            for group_word, group in file.grouped_matches.items():
                for match in group:
                    frequency_words[match.matchword] = 0
        for f, file in self.all_files.items():
            for match in file.all_matches:
                frequency_words[match.matchword] = str(int(frequency_words[match.matchword]) + 1)

        # Sort OrderedDict according to importance of the searchwords
        frequency_words = OrderedDict(sorted(frequency_words.items(), key=lambda t: int(Searchwords.all_searchwords[t[0]]), reverse=True))
        # Limit to top 10
        limited_frequency_words = OrderedDict()
        i = 0
        for word, freq in frequency_words.items():
            if (self.limit_top_findings <= i):
                break
            i += 1
            limited_frequency_words[word] = freq
        # Return
        return limited_frequency_words

    def app_prepper(self):
        if not self.application_file.lower().endswith(tuple(self.apptypes)):
            Logger("No mobile app detected, exiting! Hgnnnhh", 1)
            sys.exit()
        if not os.path.exists(os.path.join(PATH,  ntpath.basename(self.application_file))):
            os.makedirs(os.path.join(PATH,  ntpath.basename(self.application_file)))
        if Project.development == 1:
            self.workfolder = os.path.join(PATH, os.path.splitext(os.path.basename(self.application_file))[0])
        else:
            zip_ref = zipfile.ZipFile(self.application_file, 'r')
            new_folder = os.path.join(PATH, os.path.splitext(os.path.basename(self.application_file))[0])
            # Unpacking the .apk or .ipa file (it is just a ZIP archive)
            zip_ref.extractall(new_folder)
            zip_ref.close()
            self.workfolder = new_folder
            # For Android: decompile with JADX
            if self.application_file.lower().endswith("apk"):
                jadx_folder = os.path.join(new_folder, "jadx_source_code")
                Logger(jadx_folder)
                if not os.path.exists(jadx_folder):
                    os.makedirs(jadx_folder)
                if not os.access(os.path.join(os.getcwd(), "jadx", "bin", "jadx"), os.X_OK) and not os.name == 'nt':
                    Logger( "jadx is not executable. Run \"chmod +x jadx/bin/jadx\"", 1)
                # if i.startswith("'") and i.endswith("'"):
                if (self.application_file.startswith("'") and self.application_file.endswith("'") ) or (self.application_file.startswith("\"") and self.application_file.endswith("\"") ):
                    self.application_file = "\"" + self.application_file + "\""
                cmd = "\""+os.path.join(os.getcwd(), "jadx", "bin", "jadx") + '\" -d \"' +jadx_folder + "\" " + self.application_file
                Logger(cmd)
                jadx_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
                output_jadx = "--------- JADX OUTPUT BELOW --------- \n "
                for line in jadx_process.stdout:
                    output_jadx += str(line)
                Logger(str(output_jadx))
                jadx_process.wait()
                Logger("jadx return code: "+str(jadx_process.returncode))
            # TO DO: ipa decompiling tool
            elif self.application_file.lower().endswith("ipa"):
                Logger(".ipa files not implemented yet.", 1)
                sys.exit()

