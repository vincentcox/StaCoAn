import cgi
import configparser
import http.server
import json
import mimetypes
import os
import posixpath
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
import socketserver

from io import BytesIO
from queue import Queue
from threading import Thread
from helpers.logger import Logger


class ServerWrapper:
    # Read information from config file
    config = configparser.ConfigParser()
    config.read("config.ini")
    apptypes = json.loads(config.get("ProgramConfig", 'apptypes'))
    REPORT_SERVER_PORT = json.loads(config.get("Server", 'report_server_port'))
    DRAG_DROP_SERVER_PORT = json.loads(config.get("Server", 'drag_drop_server_port'))

    def create_reportserver():
        Logger("serving report server at port: " + str(ServerWrapper.REPORT_SERVER_PORT), Logger.INFO)
        return socketserver.TCPServer(("", ServerWrapper.REPORT_SERVER_PORT), RequestHandlerClass=ServerWrapper.reportserver)

    def create_drag_drop_server():
        Logger("serving dragdrop server at port: " + str(ServerWrapper.DRAG_DROP_SERVER_PORT), Logger.INFO)
        return socketserver.TCPServer(("", ServerWrapper.DRAG_DROP_SERVER_PORT), RequestHandlerClass=ServerWrapper.dragdropserver)

    class reportserver(http.server.SimpleHTTPRequestHandler):
        def log_request(self, code='-', size='-'):
            if not any(s in str(self.requestline) for s in
                       ('lootbox.html', '.ico', 'robots.txt', '.js', '.css', 'start.html', '.woff2', '.png', '.jpg')):
                Logger(self.requestline + " " + str(code) + " " + str(size), Logger.INFO)

        def log_error(self, format, *args):
            if not any(s in str(self.requestline) for s in
                       ('lootbox.html', 'robots.txt')):
                Logger(("%s - - [%s] %s\n" %
                        (self.address_string(),
                         self.log_date_time_string(),
                         format % args)), Logger.WARNING)

        def log_message(self, format, *args):
            Logger(("%s - - [%s] %s\n" %
                    (self.address_string(),
                     self.log_date_time_string(),
                     format % args)), Logger.INFO)

    class dragdropserver(http.server.BaseHTTPRequestHandler):
        # The Queue communicates with the stacoan.py file. It's a communication pipe.
        q = Queue()

        def log_request(self, code='-', size='-'):
            if not any(s in str(self.requestline) for s in
                       ('lootbox.html', '.ico', 'robots.txt', '.js', '.css', 'start.html', '.woff2', '.png', '.jpg')):
                Logger(self.requestline+ " " + str(code) + " " + str(size), Logger.INFO)

        def log_error(self, format, *args):
            if not any(s in str(self.requestline) for s in
                       ('lootbox.html', 'robots.txt')):
                Logger(("%s - - [%s] %s - %s\n" %
                        (self.address_string(),
                         self.log_date_time_string(),
                         format % args, str(self.requestline))), Logger.WARNING)

        def log_message(self, format, *args):
            Logger(("%s - - [%s] %s\n" %
                             (self.address_string(),
                              self.log_date_time_string(),
                              format % args)), Logger.INFO)
        def do_GET(self):
            """Serve a GET request."""
            f = self.send_head()
            if f:
                self.copyfile(f, self.wfile)
                f.close()

        def do_POST(self):
            """Serve a POST request."""
            if re.findall(r'KILLSERVERCOMMAND', self.requestline):
                ServerWrapper.dragdropserver.q.put("KILLSERVERCOMMAND")
                Logger("Server upload killed", Logger.INFO)
                self.send_response(200)
                exit(0)
                return True, "Exit"
            r, info = self.deal_post_data()
            Logger((str(r) + str(info) + "by: " + str(self.client_address)), Logger.INFO)
            f = BytesIO()
            f.write(b'<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
            f.write(b"<html>\n<title>Upload Result Page</title>\n")
            f.write(b"<body>\n<h2>Upload Result Page</h2>\n")
            f.write(b"<hr>\n")
            if r:
                f.write(b"<strong>Success:</strong>")
            else:
                f.write(b"<strong>Failed:</strong>")
            f.write(info.encode())
            f.write(("<br><a href=\"%s\">back</a>" % self.headers['referer']).encode())
            length = f.tell()
            f.seek(0)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-Length", str(length))
            self.end_headers()
            if f:
                self.copyfile(f, self.wfile)
                f.close()

        def deal_post_data(self):




            content_type = self.headers['content-type']
            if not content_type:
                return (False, "Content-Type header doesn't contain boundary")
            boundary = content_type.split("=")[1].encode()
            remainbytes = int(self.headers['content-length'])
            line = self.rfile.readline()
            remainbytes -= len(line)
            if not boundary in line:
                return (False, "Content NOT begin with boundary")
            for line in self.rfile:
                remainbytes -= len(line)
                fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*\S.*)"', line.decode())
                if fn:
                    break
            if not fn:
                return (False, "Can't find out file name...")

            # check filetype serverside:
            if not (str(fn[0]).endswith(tuple(ServerWrapper.apptypes))):
                self.send_error(408, "Filetype not allowed")
                return (False, "Filetype not allowed.")
            path = self.translate_path(self.path)

            # fn holds an array of files, have to make a for all loop
            fn = os.path.join(path, fn[0])
            line = self.rfile.readline()
            remainbytes -= len(line)
            line = self.rfile.readline()
            remainbytes -= len(line)
            try:
                out = open(fn, 'wb')
            except IOError:
                return (False, "Can't create file to write, do you have permission to write?")

            preline = self.rfile.readline()
            remainbytes -= len(preline)
            while remainbytes > 0:
                line = self.rfile.readline()
                remainbytes -= len(line)
                if boundary in line:
                    preline = preline[0:-1]
                    if preline.endswith(b'\r'):
                        preline = preline[0:-1]
                    out.write(preline)
                    out.close()
                    # Start stacoan instance (program), by using the queue
                    ServerWrapper.dragdropserver.q.put(fn)
                    return True, "File '%s' upload success!" % fn

                else:
                    out.write(preline)
                    preline = line
            return False, "Unexpected End of data."

        def send_head(self):
            """Common code for GET and HEAD commands.

            This sends the response code and MIME headers.

            Return value is either a file object (which has to be copied
            to the outputfile by the caller unless the command was HEAD,
            and must be closed by the caller under all circumstances), or
            None, in which case the caller has nothing further to do.

            """
            path = self.translate_path(self.path)
            f = None
            if os.path.isdir(path):
                if not self.path.endswith('/'):
                    # redirect browser - doing basically what apache does
                    self.send_response(301)
                    self.send_header("Location", self.path + "/")
                    self.end_headers()
                    return None
                for index in "index.html", "index.htm":
                    index = os.path.join(path, index)
                    if os.path.exists(index):
                        path = index
                        break
                else:
                    return self.list_directory(path)
            ctype = self.guess_type(path)
            try:
                # Always read in binary mode. Opening files in text mode may cause
                # newline translations, making the actual size of the content
                # transmitted *less* than the content-length!
                f = open(path, 'rb')
            except IOError:
                self.send_error(404, "File not found")
                return None
            self.send_response(200)
            self.send_header("Content-type", ctype)
            fs = os.fstat(f.fileno())
            self.send_header("Content-Length", str(fs[6]))
            self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()
            return f

        def list_directory(self, path):
            """Helper to produce a directory listing (absent index.html).

            Return value is either a file object, or None (indicating an
            error).  In either case, the headers are sent, making the
            interface the same as for send_head().

            """
            try:
                list = os.listdir(path)
            except os.error:
                self.send_error(404, "No permission to list directory")
                return None
            list.sort(key=lambda a: a.lower())
            f = BytesIO()

            # ToDo make resources local (now files are loaded externally)
            f.write(b"""
            <head>
                <meta charset="utf-8">
                <title>Drag and Drop File Uploading</title>
                <meta name="viewport" content="width=device-width,initial-scale=1" />
                <link rel="stylesheet" href="//fonts.googleapis.com/css?family=Roboto:300,300italic,400" />
                <script type="text/javascript" src="report/html/jquery.min.js"></script>
                <style>
                        body
                        {
                            font-family: Roboto, sans-serif;
                            color: #0f3c4b;
                            background-color: #e5edf1;
                            padding: 5rem 1.25rem; /* 80 20 */
                        }
                        .container
                        {
                            width: 100%;
                            max-width: 680px; /* 800 */
                            text-align: center;
                            margin: 0 auto;
                        }
                            .container h1
                            {
                                font-size: 42px;
                                font-weight: 300;
                                color: #0f3c4b;
                                margin-bottom: 40px;
                            }
                            .container h1 a:hover,
                            .container h1 a:focus
                            {
                                color: #39bfd3;
                            }
            
                            .container nav
                            {
                                margin-bottom: 40px;
                            }
                                .container nav a
                                {
                                    border-bottom: 2px solid #c8dadf;
                                    display: inline-block;
                                    padding: 4px 8px;
                                    margin: 0 5px;
                                }
                                .container nav a.is-selected
                                {
                                    font-weight: 700;
                                    color: #39bfd3;
                                    border-bottom-color: currentColor;
                                }
                                .container nav a:not( .is-selected ):hover,
                                .container nav a:not( .is-selected ):focus
                                {
                                    border-bottom-color: #0f3c4b;
                                }
            
                            .container footer
                            {
                                color: #92b0b3;
                                margin-top: 40px;
                            }
                                .container footer p + p
                                {
                                    margin-top: 1em;
                                }
                                .container footer a:hover,
                                .container footer a:focus
                                {
                                    color: #39bfd3;
                                }
            
                            .box
                            {
                                font-size: 1.25rem; /* 20 */
                                background-color: #c8dadf;
                                position: relative;
                                padding: 100px 20px;
                            }
                            .box.has-advanced-upload
                            {
                                outline: 2px dashed #92b0b3;
                                outline-offset: -10px;
            
                                -webkit-transition: outline-offset .15s ease-in-out, background-color .15s linear;
                                transition: outline-offset .15s ease-in-out, background-color .15s linear;
                            }
                            .box.is-dragover
                            {
                                outline-offset: -20px;
                                outline-color: #c8dadf;
                                background-color: #fff;
                            }
                                .box__dragndrop,
                                .box__icon
                                {
                                    display: none;
                                }
                                .box.has-advanced-upload .box__dragndrop
                                {
                                    display: inline;
                                }
                                .box.has-advanced-upload .box__icon
                                {
                                    width: 100%;
                                    height: 80px;
                                    fill: #92b0b3;
                                    display: block;
                                    margin-bottom: 40px;
                                }
            
                                .box.is-uploading .box__input,
                                .box.is-success .box__input,
                                .box.is-error .box__input
                                {
                                    visibility: hidden;
                                }
            
                                .box__uploading,
                                .box__success,
                                .box__error
                                {
                                    display: none;
                                }
                                .box.is-uploading .box__uploading,
                                .box.is-success .box__success,
                                .box.is-error .box__error
                                {
                                    display: block;
                                    position: absolute;
                                    top: 50%;
                                    right: 0;
                                    left: 0;
            
                                    -webkit-transform: translateY( -50% );
                                    transform: translateY( -50% );
                                }
                                .box__uploading
                                {
                                    font-style: italic;
                                }
                                .box__success
                                {
                                    -webkit-animation: appear-from-inside .25s ease-in-out;
                                    animation: appear-from-inside .25s ease-in-out;
                                }
                                    @-webkit-keyframes appear-from-inside
                                    {
                                        from	{ -webkit-transform: translateY( -50% ) scale( 0 ); }
                                        75%		{ -webkit-transform: translateY( -50% ) scale( 1.1 ); }
                                        to		{ -webkit-transform: translateY( -50% ) scale( 1 ); }
                                    }
                                    @keyframes appear-from-inside
                                    {
                                        from	{ transform: translateY( -50% ) scale( 0 ); }
                                        75%		{ transform: translateY( -50% ) scale( 1.1 ); }
                                        to		{ transform: translateY( -50% ) scale( 1 ); }
                                    }
            
                                .box__restart
                                {
                                    font-weight: 700;
                                }
                                .box__restart:focus,
                                .box__restart:hover
                                {
                                    color: #39bfd3;
                                }
            
                                .js .box__file
                                {
                                    width: 0.1px;
                                    height: 0.1px;
                                    opacity: 0;
                                    overflow: hidden;
                                    position: absolute;
                                    z-index: -1;
                                }
                                .js .box__file + label
                                {
                                    max-width: 80%;
                                    text-overflow: ellipsis;
                                    white-space: nowrap;
                                    cursor: pointer;
                                    display: inline-block;
                                    overflow: hidden;
                                }
                                .js .box__file + label:hover strong,
                                .box__file:focus + label strong,
                                .box__file.has-focus + label strong
                                {
                                    color: #39bfd3;
                                }
                                .js .box__file:focus + label,
                                .js .box__file.has-focus + label
                                {
                                    outline: 1px dotted #000;
                                    outline: -webkit-focus-ring-color auto 5px;
                                }
                                    .js .box__file + label *
                                    {
                                        /* pointer-events: none; */ /* in case of FastClick lib use */
                                    }
            
                                .no-js .box__file + label
                                {
                                    display: none;
                                }
            
                                .no-js .box__button
                                {
                                    display: block;
                                }
                                .box__button
                                {
                                    font-weight: 700;
                                    color: #e5edf1;
                                    background-color: #39bfd3;
                                    display: none;
                                    padding: 8px 16px;
                                    margin: 40px auto 0;
                                }
                                    .box__button:hover,
                                    .box__button:focus
                                    {
                                        background-color: #0f3c4b;
                                    }
                                    
                                    
                                    .killserverbutton {
                                        -moz-box-shadow:inset 0px 39px 0px -24px #e67a73;
                                        -webkit-box-shadow:inset 0px 39px 0px -24px #e67a73;
                                        box-shadow:inset 0px 39px 0px -24px #e67a73;
                                        background-color:#e4685d;
                                        -moz-border-radius:4px;
                                        -webkit-border-radius:4px;
                                        border-radius:4px;
                                        border:1px solid #ffffff;
                                        display:inline-block;
                                        cursor:pointer;
                                        color:#ffffff;
                                        font-family:Arial;
                                        font-size:15px;
                                        padding:6px 15px;
                                        text-decoration:none;
                                        text-shadow:0px 1px 0px #b23e35;
                                    }
                                    .killserverbutton:hover {
                                        background-color:#eb675e;
                                    }
                                    .killserverbutton:active {
                                        position:relative;
                                        top:1px;
                                    }

            
                </style>
            
                <!-- remove this if you use Modernizr -->
                <script>(function(e,t,n){var r=e.querySelectorAll("html")[0];r.className=r.className.replace(/(^|\s)no-js(\s|$)/,"$1js$2")})(document,window,0);</script>
            
            </head>
            
            <body>
            
            
            <center>    
            <form id="killserverform" action="/KILLSERVERCOMMAND" target="" method="POST">
              <input type="text" name="KILLSERVERCOMMAND" value="Mickey" hidden>
              <input type="submit" value="KILL SERVER" class="killserverbutton">
            </form>
            
            <script>
            $('#killserverform').submit(function() {
                alert("Server will shut down! Bye!");
                return true; // return false to cancel form action
            });
            </script>
            </center>
            
            
            
            
            <div class="container" role="main">
            
            
                <form action="/" ENCTYPE="multipart/form-data" method="post" novalidate class="box">
            
                    
                    <div class="box__input">
                        <svg class="box__icon" xmlns="http://www.w3.org/2000/svg" width="50" height="43" viewBox="0 0 50 43"><path d="M48.4 26.5c-.9 0-1.7.7-1.7 1.7v11.6h-43.3v-11.6c0-.9-.7-1.7-1.7-1.7s-1.7.7-1.7 1.7v13.2c0 .9.7 1.7 1.7 1.7h46.7c.9 0 1.7-.7 1.7-1.7v-13.2c0-1-.7-1.7-1.7-1.7zm-24.5 6.1c.3.3.8.5 1.2.5.4 0 .9-.2 1.2-.5l10-11.6c.7-.7.7-1.7 0-2.4s-1.7-.7-2.4 0l-7.1 8.3v-25.3c0-.9-.7-1.7-1.7-1.7s-1.7.7-1.7 1.7v25.3l-7.1-8.3c-.7-.7-1.7-.7-2.4 0s-.7 1.7 0 2.4l10 11.6z"/></svg>
			""")

            f.write(b"""<input type="file" name="file" id="file" class="box__file" data-multiple-caption="{count} files selected" multiple accept=\"""")
            for apptype in ServerWrapper.apptypes:
               f.write(bytes(str(apptype)+", ", 'utf-8'))

            f.write(b"""\" />""")
            f.write(b"""
                        <label for="file" id="nameup"><strong>Choose a file</strong><span class="box__dragndrop"> or drag it here</span>.</label>
                        <button type="submit" class="box__button">Upload</button>
                    </div>
                    <div class="box__uploading">Uploading&hellip;</div>
                    <div class="box__success">Done! <a href="/" class="box__restart2" id="done_link" onclick="javascript:event.target.port=""")
            f.write(bytearray(str(ServerWrapper.REPORT_SERVER_PORT), 'utf8'))
            f.write(b"""" role="button" target="_blank">Open report!</a></div>
                    <div class="box__error">Error! <span></span>. <a href="/?" class="box__restart" role="button">Try again!</a></div>
                </form>
            </div>
            <script>
                'use strict';
                ;( function ( document, window, index )
                {
                    // feature detection for drag&drop upload
                    var isAdvancedUpload = function()
                        {
                            var div = document.createElement( 'div' );
                            return ( ( 'draggable' in div ) || ( 'ondragstart' in div && 'ondrop' in div ) ) && 'FormData' in window && 'FileReader' in window;
                        }();
                    // applying the effect for every form
                    var forms = document.querySelectorAll( '.box' );
                    Array.prototype.forEach.call( forms, function( form )
                    {
                        var input		 = form.querySelector( 'input[type="file"]' ),
                            label		 = form.querySelector( 'label' ),
                            errorMsg	 = form.querySelector( '.box__error span' ),
                            restart		 = form.querySelectorAll( '.box__restart' ),
                            droppedFiles = false,
                            showFiles	 = function( files )
                            {
                                label.textContent = files.length > 1 ? ( input.getAttribute( 'data-multiple-caption' ) || '' ).replace( '{count}', files.length ) : files[ 0 ].name;
                            },
                            triggerFormSubmit = function()
                            {
                                var event = document.createEvent( 'HTMLEvents' );
                                event.initEvent( 'submit', true, false );
                                form.dispatchEvent( event );
                            };
            
                        // letting the server side to know we are going to make an Ajax request
                        var ajaxFlag = document.createElement( 'input' );
                        ajaxFlag.setAttribute( 'type', 'hidden' );
                        ajaxFlag.setAttribute( 'name', 'ajax' );
                        ajaxFlag.setAttribute( 'value', 1 );
                        form.appendChild( ajaxFlag );
            
                        // automatically submit the form on file select
                        input.addEventListener( 'change', function( e )
                        {
                            showFiles( e.target.files );
                            triggerFormSubmit();
                        });
            
                        // drag&drop files if the feature is available
                        if( isAdvancedUpload )
                        {
                            form.classList.add( 'has-advanced-upload' ); // letting the CSS part to know drag&drop is supported by the browser
                            [ 'drag', 'dragstart', 'dragend', 'dragover', 'dragenter', 'dragleave', 'drop' ].forEach( function( event )
                            {
                                form.addEventListener( event, function( e )
                                {
                                    // preventing the unwanted behaviours
                                    e.preventDefault();
                                    e.stopPropagation();
                                });
                            });
                            [ 'dragover', 'dragenter' ].forEach( function( event )
                            {
                                form.addEventListener( event, function()
                                {
                                    form.classList.add( 'is-dragover' );
                                });
                            });
                            [ 'dragleave', 'dragend', 'drop' ].forEach( function( event )
                            {
                                form.addEventListener( event, function()
                                {
                                    form.classList.remove( 'is-dragover' );
                                });
                            });
                            form.addEventListener( 'drop', function( e )
                            {
                                droppedFiles = e.dataTransfer.files; // the files that were dropped
                                showFiles( droppedFiles );
                                triggerFormSubmit();
                                                });
                        }
                        // if the form was submitted
                        form.addEventListener( 'submit', function( e )
                        {
                            // preventing the duplicate submissions if the current one is in progress
                            if( form.classList.contains( 'is-uploading' ) ) return false;
            
                            form.classList.add( 'is-uploading' );
                            form.classList.remove( 'is-error' );
            
                            if( isAdvancedUpload ) // ajax file upload for modern browsers
                            {
                                e.preventDefault();
            
                                // gathering the form data
                                var ajaxData = new FormData( form );
                                if( droppedFiles )
                                {
                                    Array.prototype.forEach.call( droppedFiles, function( file )
                                    {
                                        ajaxData.append( input.getAttribute( 'name' ), file );
                                        document.getElementById("done_link").setAttribute("href", file.name.replace(/\./g, "_")+"/report/start.html");
                                    });
                                }
                                
            
                                // ajax request
                                var ajax = new XMLHttpRequest();
                                ajax.open( form.getAttribute( 'method' ), form.getAttribute( 'action' ), true );
            
                                ajax.onload = function()
                                {
                                    form.classList.remove( 'is-uploading' );
                                    if( ajax.status == 408 )
                                    {
                                        alert( 'Filetype is not allowed');
                                    }
                                    else if( ajax.status >= 200 && ajax.status < 400 )
                                    {
                                        var data = ajax.responseText;
                                        console.log(data)
                                        form.classList.add( data.includes("Success:") == true ? 'is-success' : 'is-error' );
                                        if( !data.includes("Success:") ) errorMsg.textContent = data.error;
                                        if (data.includes("Success:") ) document.getElementById("done_link").setAttribute("href", nameup.innerHTML.replace(/\./g, "_")+"/report/start.html");
                                    }
                                    else alert( 'Error. Please, contact the webmaster!' );
                                };
            
                                ajax.onerror = function()
                                {
                                    form.classList.remove( 'is-uploading' );
                                    alert( 'Error. Please, try again! Filetype is probably not supported.' );
                                };
                                ajax.send( ajaxData );
                            }
                            else // fallback Ajax solution upload for older browsers
                            {
                                alert(1);
                                var iframeName	= 'uploadiframe' + new Date().getTime(),
                                    iframe		= document.createElement( 'iframe' );
            
                                    $iframe		= $( '<iframe name="' + iframeName + '" style="display: none;"></iframe>' );
            
                                iframe.setAttribute( 'name', iframeName );
                                iframe.style.display = 'none';
            
                                document.body.appendChild( iframe );
                                form.setAttribute( 'target', iframeName );
                                iframe.addEventListener( 'load', function()
                                {
                                    var data = JSON.parse( iframe.contentDocument.body.innerHTML );
                                    form.classList.remove( 'is-uploading' )
                                    form.classList.add( data.success == true ? 'is-success' : 'is-error' )
                                    form.removeAttribute( 'target' );
                                    if( !data.success ) errorMsg.textContent = data.error;
                                    iframe.parentNode.removeChild( iframe );
                                });
                            }
                        });
            
            
                        // restart the form if has a state of error/success
                        Array.prototype.forEach.call( restart, function( entry )
                        {
                            entry.addEventListener( 'click', function( e )
                            {
                                e.preventDefault();
                                form.classList.remove( 'is-error', 'is-success' );
                                input.click();
                            });
                        });
            
                        // Firefox focus bug fix for file input
                        input.addEventListener( 'focus', function(){ input.classList.add( 'has-focus' ); });
                        input.addEventListener( 'blur', function(){ input.classList.remove( 'has-focus' ); });
                    });
                }( document, window, 0 ));
            </script>
            </body>
            </html>
            """)

            # f.write(b"<form ENCTYPE=\"multipart/form-data\" method=\"post\">")
            # f.write(b"<input name=\"file\" type=\"file\"/>")
            # f.write(b"<input type=\"submit\" value=\"upload\"/></form>\n")

            length = f.tell()
            f.seek(0)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-Length", str(length))
            self.end_headers()
            return f

        def translate_path(self, path):
            """Translate a /-separated PATH to the local filename syntax.

            Components that mean special things to the local file system
            (e.g. drive or directory names) are ignored.  (XXX They should
            probably be diagnosed.)

            """
            # abandon query parameters
            path = path.split('?', 1)[0]
            path = path.split('#', 1)[0]
            path = posixpath.normpath(urllib.parse.unquote(path))
            words = path.split('/')
            words = [_f for _f in words if _f]
            path = os.getcwd()
            for word in words:
                drive, word = os.path.splitdrive(word)
                head, word = os.path.split(word)
                if word in (os.curdir, os.pardir): continue
                path = os.path.join(path, word)
            return path

        def copyfile(self, source, outputfile):
            """Copy all data between two file objects.

            The SOURCE argument is a file object open for reading
            (or anything with a read() method) and the DESTINATION
            argument is a file object open for writing (or
            anything with a write() method).

            The only reason for overriding this would be to change
            the block size or perhaps to replace newlines by CRLF
            -- note however that this the default server uses this
            to copy binary data as well.

            """
            shutil.copyfileobj(source, outputfile)

        def guess_type(self, path):
            """Guess the type of a file.

            Argument is a PATH (a filename).

            Return value is a string of the form type/subtype,
            usable for a MIME Content-type header.

            The default implementation looks the file's extension
            up in the table self.extensions_map, using application/octet-stream
            as a default; however it would be permissible (if
            slow) to look inside the data to make a better guess.

            """

            base, ext = posixpath.splitext(path)
            if ext in self.extensions_map:
                return self.extensions_map[ext]
            ext = ext.lower()
            if ext in self.extensions_map:
                return self.extensions_map[ext]
            else:
                return self.extensions_map['']

        if not mimetypes.inited:
            mimetypes.init()  # try to read system mime.types
        extensions_map = mimetypes.types_map.copy()
        extensions_map.update({
            '': 'application/octet-stream',  # Default
            '.py': 'text/plain',
            '.c': 'text/plain',
            '.h': 'text/plain',
        })



    def startserver(HandlerClass=dragdropserver,
             ServerClass=http.server.HTTPServer):

        # Code to supress the welcoming message from the server. Yes, its a lot of code, but no other way...
        from contextlib import contextmanager
        import sys, os

        @contextmanager
        def suppress_stdout():
            with open(os.devnull, "w") as devnull:
                old_stdout = sys.stdout
                sys.stdout = devnull
                try:
                    yield
                finally:
                    sys.stdout = old_stdout
        with suppress_stdout():
            print("You cannot see this")

            # Start the server
        http.server.test(HandlerClass, ServerClass)