#!/bin/python
import codecs
import hashlib
import os
import sys
import webbrowser
import configparser
import argparse
from time import time

from helpers.logger import Logger
from helpers.project import Project
from helpers.report_html import Report_html
from helpers.searchwords import Searchwords


def parse_args():
    # Description
    argument_width_in_help = 30
    parser = argparse.ArgumentParser(description='StaCoAn is a crossplatform tool '
                'which aids developers, bugbounty hunters and ethical hackers performing static '
                'code analysis on mobile applications.',
                formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=argument_width_in_help))

    # Arguments: see https://docs.python.org/3/library/argparse.html
    parser.add_argument('-p', metavar="PATH", dest='project', required=False, nargs='+',
                        help='Relative path to the project')
    parser.add_argument('--disable-browser', action='store_true', required=False,
                        help='Do not automatically open the HTML report in a browser')

    log_group = parser.add_mutually_exclusive_group(required=False)
    log_group.add_argument('--log-all', action='store_true', help='Log all errors, warnings and info messages (default)')
    log_group.add_argument('--log-errors', action='store_true', help='Log only errors')
    log_group.add_argument('--log-warnings', action='store_true', help='Log only errors and warning messages')

    # return aur args, usage: args.argname
    return parser.parse_args()

def program(args):
    # Script cannot be called outside script directory. It contains a lot of os.getcwd().
    if not os.path.dirname(os.path.abspath(__file__)) == os.getcwd():
        Logger("Script cannot be called outside directory", Logger.ERROR)

    # Keep track of execution time
    start_time = time()

    # Read information from config file
    # ToDo create a settings class that parses the ini file with set and get functions
    config = configparser.ConfigParser()
    config.read("config.ini")
    report_folder = config.get("ProgramConfig", 'report_folder')
    report_folder_start = os.path.join(os.getcwd(), report_folder, "start.html")
    development = config.getint("Development", 'development')
    server_enabled = config.getboolean("ProgramConfig", 'SERVER_ENABLED')

    # Update log level
    if not (args.log_warnings or args.log_errors):
        loglevel = 3
    else:
        loglevel = 1 if args.log_errors else 2
    config.set('ProgramConfig', 'loglevel', str(loglevel))
    with open("config.ini", "w+") as configfile:
        config.write(configfile)

    # Import the searchwords lists
    Searchwords.searchwords_import(Searchwords())

    # For each project (read .ipa or .apk file), run the scripts.
    all_project_paths = args.project
    for project_path in all_project_paths:
        Project.projects[project_path] = Project(project_path)
        Logger("Decompiling app...")
        Project.projects[project_path].app_prepper()
        Logger("Decompiling done.")
        Logger("Searching trough files")
        Project.projects[project_path].searchcontroller()
        Logger("Searching done.")
        Logger("start generating report")

    # To Do: Generate the tree-view + Source code view for each SOURCE file
    all_files = dict()
    all_files.update(Project.projects[project_path].db_files)
    all_files.update(Project.projects[project_path].src_files)
    amount_files = len(all_files)
    for i, file in enumerate(all_files):
        Logger("progress: "+str(format((i/amount_files)*100, '.2f'))+"%", rewriteLine=True)
        hash_object = hashlib.md5(file.encode('utf-8'))
        file_report_file = os.path.join(report_folder, hash_object.hexdigest()+'.html')
        overview_html = Report_html(Project.projects[project_path])
        overview_html.header("tree")
        overview_html.navigation()
        overview_html.tree_view(Project.projects[project_path], file)
        overview_html.footer()
        f = codecs.open(file_report_file, 'w', encoding='utf8')
        f.write(overview_html.gethtml())
        # with open(file_report_file, 'w') as f:
        #     print(overview_html.gethtml(), file=f)
    Logger("progress: 100%  ")

    # Generate the startpage
    file_report_file = os.path.join(report_folder, 'start.html')
    overview_html = Report_html(Project.projects[project_path])
    overview_html.header("tree")
    overview_html.navigation()
    overview_html.tree_view(Project.projects[project_path], "")
    overview_html.footer()
    f = codecs.open(file_report_file, 'w', encoding='utf8')
    f.write(overview_html.gethtml())
    # with open(file_report_file, 'w') as f:
    #     print(overview_html.gethtml(), file=f)

    # Generate words overview html file
    words_overview_html_report_file = os.path.join(report_folder, "wordlist_overview.html")
    words_overview_html = Report_html(Project.projects[project_path])
    words_overview_html.header("words_overview")
    words_overview_html.navigation()
    words_overview_html.html_wordlist(Project.projects[project_path])
    words_overview_html.footer()
    with open(words_overview_html_report_file, 'w') as f:
        print(words_overview_html.gethtml(), file=f)

    # Generate lootbox
    lootbox_html_report_file = os.path.join(report_folder, "lootbox.html")
    lootbox_html_report = Report_html(Project.projects[project_path])
    lootbox_html_report.header("lootbox")
    lootbox_html_report.navigation()
    lootbox_html_report.lootbox()
    lootbox_html_report.footer()
    f = codecs.open(lootbox_html_report_file, 'w', encoding='utf8')
    f.write(lootbox_html_report.gethtml())
    # with open(lootbox_html_report_file, 'w') as f:
    #     print(lootbox_html_report.gethtml(), file=f)

    # Generate the treeview
    tree_js_file_path = os.path.join(report_folder, "tree_js_content.js")
    f = codecs.open(tree_js_file_path, 'w', encoding='utf8')
    f.write(Report_html.Tree_builder.tree_js_file(Project.projects[project_path]))
    # with open(tree_js_file_path, 'w') as f:
    #     print(Report_html.Tree_builder.tree_js_file(Project.projects[project_path]), file=f)

    # Generate looty.js file, for the zip creation process at the lootbox page
    Report_html().make_loot_report_content()

    # Write all log-events to logfile
    Logger.dump()

    # Log some end results
    if loglevel == 3:
        print("\n--------------------\n")
    Logger("Static code analyzer completed succesfully in %fs." % (time() - start_time))
    Logger("HTML report is available at: %s" % report_folder_start)
    if not args.disable_browser:
        Logger("Now automatically opening the HTML report.")

        # Open the webbrowser to the generated start page.
        if sys.platform == "darwin":  # check if on OSX
            report_folder_start = "file:///" + report_folder_start
        webbrowser.open(report_folder_start)

    # Exit program
    sys.exit()

if __name__ == "__main__":
    if os.environ.get('DEBUG') is not None:
        program(parse_args())
        exit(0)
    try:
        program(parse_args())
    except Exception as e:
        Logger("ERROR: Unknown error: %s." % str(e), Logger.ERROR)
