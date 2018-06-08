#!/bin/python
import codecs
import hashlib
import os
import sys
import webbrowser
import configparser
import argparse
import threading
import json
import multiprocessing
from threading import Thread
from multiprocessing import Process
from time import time


from helpers.logger import Logger
from helpers.project import Project
from helpers.report_html import Report_html
from helpers.searchwords import SearchLists
from helpers.server import ServerWrapper


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
    parser.add_argument('--disable-server', action='store_true', required=False,
                        help='Do not run the server to drag and drop files to be analysed')

    log_group = parser.add_mutually_exclusive_group(required=False)
    log_group.add_argument('--log-all', action='store_true', help='Log all errors, warnings and info messages (default)')
    log_group.add_argument('--log-errors', action='store_true', help='Log only errors')
    log_group.add_argument('--log-warnings', action='store_true', help='Log only errors and warning messages')


    # Check if the right parameters are set
    args = parser.parse_args()
    if args.disable_server and args.project is None:
        parser.error("--disable-server requires the input file (application file) specified with -p")
    if args.project:
        args.disable_server == True


    # return aur args, usage: args.argname
    return args

# Note that this server(args) function CANNOT be placed in the server.py file. It calls "program()", which cannot be
# called from the server.py file
def server(args, server_disabled, DRAG_DROP_SERVER_PORT):
    # Windows multithreading is different on Linux and windows (fork <-> new instance without parent context and args)
    child=False
    if os.name == 'nt':
        if os.path.exists(".temp_thread_file"):
            with open(".temp_thread_file") as f:
                content = f.readlines()
            # you may also want to remove whitespace characters like `\n` at the end of each line
            content = [x.strip() for x in content]
            args.project = [content[0]]
            args.disable_server = content[1]
            args.log_warnings = content[2]
            args.disable_browser = content[3]
            child = True
            os.remove(".temp_thread_file")
    else:
        if os.path.exists(".temp_thread_file"):
            child = True
            os.remove(".temp_thread_file")

    if (not(server_disabled or args.disable_server) or ((not len(sys.argv) > 1))) and (not child):
        # This is a "bridge" between the stacoan program and the server. It communicates via this pipe (queue)
        def serverlistener(in_q):
            while True:
                # Get some data
                data = in_q.get()
                if data == "KILLSERVERCOMMAND":
                    t1.isAlive = False
                    download_thread.isAlive = False
                    Logger("Server reports killed", Logger.INFO)
                    Logger("Exiting program! Bye. ", Logger.INFO)
                    exit(0)

                # Process the data
                args = argparse.Namespace(project=[data], disable_server=False, log_warnings=False, log_errors=False, disable_browser=True)
                # On windows: write arguments to file, spawn process, read arguments from file, delete.
                if os.name == 'nt':
                    with open('.temp_thread_file', 'a') as the_file:
                        the_file.write(data+"\n")
                        the_file.write("False\n") # disable_server
                        the_file.write("False\n")  # log_warnings
                        the_file.write("True\n")
                else:
                    with open('.temp_thread_file', 'a') as the_file:
                        the_file.write("filling")

                p = Process(target=program, args=(args,))
                p.start()

        # Create report server instance
        reportserver = ServerWrapper.create_reportserver()
        download_thread = threading.Thread(target=reportserver.serve_forever)
        download_thread.daemon = True
        download_thread.start()

        # Create the shared queue and launch both threads
        t1 = Thread(target=serverlistener, args=(ServerWrapper.dragdropserver.q,))
        t1.daemon = True
        t1.start()
        dragdropserver = ServerWrapper.create_drag_drop_server()
        drag_drop_server_thread = threading.Thread(target=dragdropserver.serve_forever)
        drag_drop_server_thread.daemon = True
        drag_drop_server_thread.start()

        if (not args.disable_browser) and not (args.disable_server or server_disabled):
            # Open the webbrowser to the generated start page.
            report_folder_start = "http:///127.0.0.1:" + str(DRAG_DROP_SERVER_PORT)
            webbrowser.open(report_folder_start)

        # Keep waiting until q is gone.
        ServerWrapper.dragdropserver.q.join()
        drag_drop_server_thread.join()
        return() # Not needed because it will be killed eventually.

def program(args):
    # Script cannot be called outside script directory. It contains a lot of os.getcwd().
    if not os.path.dirname(os.path.abspath(__file__)) == os.getcwd():
        Logger("Script cannot be called outside directory", Logger.ERROR)


    # Keep track of execution time
    start_time = time()

    # Read information from config file
    # Todo edit dockerfile with new path for report
    # ToDo create a settings class that parses the ini file with set and get functions

    config = configparser.ConfigParser()
    config.read("config.ini")
    server_disabled = config.getboolean("ProgramConfig", 'server_disabled')
    DRAG_DROP_SERVER_PORT = json.loads(config.get("Server", 'drag_drop_server_port'))

    # Update log level
    if not (args.log_warnings or args.log_errors):
        loglevel = 3
    else:
        loglevel = 1 if args.log_errors else 2
    config.set('ProgramConfig', 'loglevel', str(loglevel))
    with open("config.ini", "w+") as configfile:
        config.write(configfile)

    # Import the searchwords lists
    # Searchwords.searchwords_import(Searchwords())
    SearchLists()


    # Server(args) checks if the server should be run and handles the spawning of the server and control of it
    if not args.project:
        server(args, server_disabled, DRAG_DROP_SERVER_PORT)

    # For each project (read .ipa or .apk file), run the scripts.
    all_project_paths = args.project

    if not all_project_paths:
        sys.exit(0)
    for project_path in all_project_paths:
        try:
            Project.projects[project_path] = Project(project_path)
        except:
            sys.exit(0)

        report_folder = os.path.join(Project.projects[project_path].name, config.get("ProgramConfig", 'report_folder'))
        report_folder_start = os.path.join(os.getcwd(), report_folder, "start.html")

        Logger("Decompiling app...")
        Project.projects[project_path].app_prepper()
        Logger("Decompiling done.")
        Logger("Searching trough files")
        Project.projects[project_path].searchcontroller()
        Logger("Searching done.")
        Logger("start generating report")

        # ToDo: Generate the tree-view + Source code view for each SOURCE file
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
        with open(words_overview_html_report_file, 'w', encoding="utf-8") as f:
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
        if (not args.disable_browser) or (args.disable_server or server_disabled):
            Logger("Now automatically opening the HTML report.")
            # Open the webbrowser to the generated start page.
            if sys.platform == "darwin":  # check if on OSX
                # strip off http:///
                report_folder_start = str(report_folder_start).strip("http:///")
                report_folder_start = "file:///" + report_folder_start
            webbrowser.open(report_folder_start)
    # Exit program
    sys.exit()

if __name__ == "__main__":
    if os.path.exists(".temp_thread_file"):
        os.remove(".temp_thread_file")
    multiprocessing.freeze_support()
    if os.environ.get('DEBUG') is not None:
        program(parse_args())
        exit(0)
    try:
        program(parse_args())
    except Exception as e:
        Logger("ERROR: Unknown error: %s." % str(e), Logger.ERROR)
