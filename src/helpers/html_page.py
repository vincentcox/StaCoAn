from yattag import Doc
from yattag import indent
import datetime
class Htmlpage:
    htmlpages = dict()

    def __init__(self, projectname = None):
        if projectname is None: # Used for just an empty html page with the same style and template
            self.doc, self.tag, self.text = Doc().tagtext()
            self.this_is_a_log_html_page = True
        else:
            Htmlpage.htmlpages[projectname] = self
            self.doc, self.tag, self.text = Doc().tagtext()

    def header(self, page):
        with self.tag('head'):
            with self.tag('script', type="text/javascript", src="html/jquery.min.js"):
                self.text("")
            with self.tag('link', rel="stylesheet", type="text/css",
                          href="html/font-awesome.min.css"):
                self.text("")
            if page =="lootbox":
                with self.tag('script', type="text/javascript", src="html/lootbox.js"):
                    self.text("")
                with self.tag('script', type="text/javascript", src="html/FileSaver.min.js"):
                    self.text("")
                with self.tag('script', type="text/javascript", src="html/jszip.min.js"):
                    self.text("")

            if page =="tree":
                with self.tag('link', rel="stylesheet", type="text/css",
                              href="html/ui.fancytree.min.css"):
                    self.text("")
                with self.tag('script', type="text/javascript", src="html/jquery.fancytree-all-deps.min.js"):
                    self.text("")
                with self.tag('script', type="text/javascript", src="html/jquery.fancytree.glyph.js"):
                    self.text("")
                with self.tag('script', type="text/javascript", src="html/jquery.fancytree.persist.js"):
                    self.text("")
                with self.tag('script', type="text/javascript", src="html/report.js"):
                    self.text("")
            with self.tag('link', rel="stylesheet", type="text/css", href="html/prism.css"):
                self.text("")
            with self.tag('link', rel="stylesheet", type="text/css", href="html/report.css"):
                self.text("")
            with self.tag('link', rel="stylesheet", type="text/css", href="html/fontawesome/fontawesome-all.min.css"):
                self.text("")
            with self.tag('link',("media", "screen,projection"), rel="stylesheet", type="text/css", href="html/materialise/css/materialize.min.css"):
                self.text("")
            with self.tag('meta',("name", "viewport"), ("content","width=device-width, initial-scale=1.0")):
                self.text("")
            with self.tag('meta', ("charset", "UTF-8")):
                self.text("")
    def navigation(self):
        # Omit navigation if it's the log-file
        self.doc.asis("""
        <ul id="slide-out" class="side-nav">
             <h5>Settings</h5>
             <div class="divider"></div>
             <div class="switch" id="matchless_files">
                Remove matchless files:
                <label>
                  Off
                  <input type="checkbox">
                  <span class="lever"></span>
                  On
                </label>
            </div>
            <script>
                $(function() {
                    if (localStorage.getItem('matchless_files') === "true"){
                    removeUnimportantFiles();
                    $('#matchless_files').find("input[type=checkbox]").prop('checked', true);
                    }
                });
                $("#matchless_files").find("input[type=checkbox]").on("change",function() {
                    var status = $(this).prop('checked');
                    if (status==true){
                        removeUnimportantFiles();
                        localStorage.setItem('matchless_files', true); 
                    }else{
                         Materialize.toast('Refresh page to take effect.', 4000);
                         localStorage.setItem('matchless_files', false); 
                    }
                     console.log(status);
                });
            </script>
            Expand tree: <a id="expand_tree" class="waves-effect waves-light btn" style="background-color: #30363A !important;height: 24px;line-height: 24px;padding: 0 0.5rem;">Expand</a>
            <script>
                $( "#expand_tree" ).click(function() {
                  $("#tree").fancytree("getTree").visit(function(node){
                    node.setExpanded();
                  });
                });
            </script>
        </ul>
        """)
        self.doc.asis("""
            <nav>
                <div class="nav-wrapper" style="background-color: #30363A !important;">
                  <a href="start.html" class="brand-logo center" style="position:relative;"><img style="height:100%;" src="html/logo.png"></a>
                  <ul id="nav-mobile" class="right hide-on-med-and-down">

                            """)
        self.doc.asis("""
                <li><a href="start.html">Treeview</a></li>
                <li><a href="lootbox.html">Lootbox</a></li>
                <li><a href="log.html">Logs</a></li>
        """)

        self.doc.asis("""        
                    <li><a href="#" data-activates="slide-out" id="button-collapse" class="button"><i class="material-icons">settings</i></a></li>
                        <script>
                        $(function() {
                            // Initialize collapse button
                            $("#button-collapse").sideNav();
                            // Initialize collapsible (uncomment the line below if you use the dropdown variation)
                            //$('.collapsible').collapsible();
                        });
                        </script>
                    </ul>
                </div>
            </nav>
        """)

    def lootbox(self):
        self.doc.asis("""
        <br>
    <a class="waves-effect waves-light btn tooltipped center-align" id ="downloadPage" data-position="bottom" data-tooltip="Because the zip-file is javascript generated, it might display a security warning." data-delay="0" style="background-color: #30363A !important; display: block;margin-left: auto;margin-right: auto;width: 40%;">Download Report</a>
    <br>
    <script>
        $('#downloadPage').click(function() {
        downloadPage();
        });
    </script>
        <div id="lootbox"></div>""")

    def footer(self):
        with self.tag('script', ("data-manual"), type="text/javascript", src="html/prism.js"):
            self.text("")

        with self.tag('script', type="text/javascript", src="html/materialise/js/materialize.min.js"):
            self.text("")

        # Footer content
        with self.tag("footer", ("style", "background-color: #30363A !important;"), klass="page-footer"):
            with self.tag("div", klass="container"):
                with self.tag("div", klass="row"):
                    with self.tag("div", klass="col l6 s12"):
                        with self.tag("h5", klass="white-text"):
                            self.text("StaCoAn")
                        with self.tag("p", klass="grey-text text-lighten-4"):
                            self.text("If you like this project, feel free to give this a star on Github.")
                            self.text("If you don't and would like to see other features, feel free to make a feature request.")
                    with self.tag("div", klass="col l4 offset-l2 s12"):
                        with self.tag("h5", klass="white-text"):
                            self.text("links")
                        with self.tag("ul"):
                            with self.tag("li"):
                                with self.tag("a", href="https://github.com/vincentcox/StaCoAn", klass="grey-text text-lighten-3"):
                                    self.text("StaCoAn Github page")
                            with self.tag("li"):
                                with self.tag("a", href="https://github.com/vincentcox/StaCoAn/blob/master/LICENSE", klass="grey-text text-lighten-3"):
                                    self.text("License")
            with self.tag("div", klass="footer-copyright"):
                with self.tag("div", klass="container"):
                    now = datetime.datetime.now()
                    self.text("Report generated at "+str(now.hour)+":"+str(now.minute)+":"+str(now.second)+" "+str(now.day)+"/"+str(now.month)+"/"+str(now.year)+"")
        # End of Footer content
        with self.tag('script', type="text/javascript", src="html/looty.js"):
            self.text("")

    def gethtml(self):
        #return indent(self.doc.getvalue(), indent_text=2)
        return self.doc.getvalue()
