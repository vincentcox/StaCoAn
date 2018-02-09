![StaCoAn header](https://github.com/vincentcox/StaCoAn/blob/resources/header_stacoan-01.png?raw=true)
# StaCoAn ![Issues badge](https://img.shields.io/github/issues/vincentcox/StaCoAn.svg) ![License badge](https://img.shields.io/github/license/vincentcox/StaCoAn.svg) ![status](https://img.shields.io/badge/status-alpha-red.svg)

StaCoAn is a __crossplatform__ tool which aids developers, bugbounty hunters and ethical hackers performing [static code analysis](https://en.wikipedia.org/wiki/Static_program_analysis) on mobile applications\*.

This tool will look for interesting lines in the code which can contain:
* Hardcoded credentials
* API keys
* URL's of API's
* Decryption keys
* Major coding mistakes

This tool was created with a big focus on usability and graphical guidance in the user interface.

For the impatient ones, grab the download on the [releases page](https://github.com/vincentcox/StaCoAn/releases).

<p style="font-size: 0.6em">
*: note that currently only apk files are supported, but ipa files will follow very shortly.
</p>

An example report can be found here: [example report](https://github.com/vincentcox/StaCoAn/raw/master/example-report.zip)

## Features
The concept is that you drag and drop your mobile application file (an .apk or .ipa file) on the StaCoAn application and it will generate a visual and portable report for you. You can tweak the settings and wordlists to get a customized experience.

The reports contain a handy tree viewer so you can easily browse trough your decompiled application.

![Mockup  application ](https://github.com/vincentcox/StaCoAn/blob/resources/mockup_screenshot.png?raw=true)

### Looting concept
The _Loot Function_ let you 'loot' (~bookmark) the findings which are of value for you and on the loot-page you will get an overview of your 'loot' raid.

The final report can be exported to a zip file and shared with other people.

### Wordlists
The application uses wordlists for finding interesting lines in the code.
Wordlists are in the following format:
```
API_KEY|||80||| This contains an API key reference
(https|http):\/\/.*api.*|||60||| This regex matches any URL containing 'api'
```
__Note that these wordlists also support [regex](https://www.regular-expressions.info/examples.html) entries.__

### Filetypes
Any source file will be processed. This contains '.java', '.js', '.html', '.xml',... files.

Database-files are also searched for keywords. The database also has a table viewer.

![database](https://github.com/vincentcox/StaCoAn/blob/resources/screenshot_database.png?raw=true)

### Responsive Design
The reports are made to fit on all screens.

![](https://github.com/vincentcox/StaCoAn/blob/resources/responsive.gif?raw=true)

## Limitations
This tool will have trouble with [obfuscated](https://en.wikibooks.org/wiki/Introduction_to_Software_Engineering/Tools/Obfuscation) code. If you are a developer try to compile without obfuscation turned on before running this tool. If you are on the offensive side, good luck bro.

## Getting Started
If you want to get started as soon as possible, head over to the [releases page](https://github.com/vincentcox/StaCoAn/releases) and download the executable or archive which corresponds to your operating system.

If you have downloaded the release zip file, extract this. Copy the .apk or .ipa file to the extracted folder.

Drag and drop this file onto the executable. The report will now be generated in the `report` folder.

### From source
`git clone https://github.com/vincentcox/StaCoAn/`

`cd StaCoAn`

Make sure that you have pip3 installed:

`sudo apt-get install python3-pip`

Install the required python packages:

`pip3 install -r requirements.txt `

`python3 main.py yourApp.apk`

### Building the executable

`pip3 install pyinstaller`

__Windows__

`pyinstaller main.py --onefile --add-data jadx:jadx -p jadx --icon icon.ico --name stacoan --clean`

__mac__

`pyinstaller main.py --onefile --add-data jadx:jadx -p jadx --icon icon.ico --name stacoan --clean`

__Linux__

`python3 -m PyInstaller main.py --onefile --add-data jadx:jadx -p jadx --icon icon.ico --name stacoan --clean`


## Contributing
This entire program's value is depending on the wordlists it is using. In the end, the final result is what matters. It is easy to build a wordlist (in comparison to writing actual code), but it has the biggest impact on the end result. You can help the community the most with making wordlists.

If you want an easy way to post your idea's, head over to: http://www.tricider.com/brainstorming/2pdrT7ONVrB. From there you can add ideas for entries in the wordlist. 

Improving the code is also much appreciated.

If the contribution is high enough, you will be mentioned in the `authors` section.

### Short term roadmap
The following items have a high priority and will be implemented soon:
* Make IPA files also work with this program
* Make DB matches loot-able

## Authors & Contributors
<table>
  <tr>
    <th><center>Project Creator</center></th>
  </tr>
  <tr>
    <td><p align="center"><img src="https://vincentcox.com/wp-content/uploads/IMG_3852-copy.jpg" alt="Drawing" width="200px"/></p> </td>
  </tr>
  <tr>
    <td>
      <div align="center">
        <a href="https://www.linkedin.com/in/ivincentcox/">
          <img src="https://cdnjs.cloudflare.com/ajax/libs/foundicons/3.0.0/svgs/fi-social-linkedin.svg" alt="Linkedin" width="40px"/>
        </a>
        <a href="https://twitter.com/vincentcox_be">
          <img src="https://cdnjs.cloudflare.com/ajax/libs/foundicons/3.0.0/svgs/fi-social-twitter.svg" alt="Twitter" width="40px"/>
        </a>
        <a href="https://vincentcox.com">
          <img src="https://cdnjs.cloudflare.com/ajax/libs/foundicons/3.0.0/svgs/fi-web.svg" alt="Website" width="40px"/>
        </a>
      </div>
    </td>
  </tr>
</table>

## License
The following projects were used in this project:
* [Materialize CSS](http://materializecss.com/): Materialize, a CSS Framework based on Material Design. Used for the general theme of the reports.
* [PRISMJS](http://prismjs.com/): Lightweight, robust, elegant syntax highlighting. Used for the code markup
* [JADX](https://github.com/skylot/jadx): Dex to Java decompiler. Used for decompiling .apk files\*.
* [Fancytree](https://github.com/mar10/fancytree): jQuery tree view / tree grid plugin. Used in the tree-view of the reports.
* [fontawesome](http://fontawesome.io/): Font Awesome, the iconic font and CSS framework. Used for some icons.
* [JSZip](https://stuk.github.io/jszip/): JSZip is a javascript library for creating, reading and editing .zip files, with a lovely and simple API.
* [FileSaver](https://github.com/eligrey/FileSaver.js/): An HTML5 saveAs() FileSaver implementation.  Used in the JSZip library.

All of these projects have their corresponding licenses. Please respect these while you are modifying and redistributing this project.

<p style ="font-size: 0.6em">*: the binary is included in this project. If the dev's from JADX are not comfortable with this, feel free to contact me about this so we can find a solution. </p>

## Acknowledgments
* [Kevin De Koninck](https://github.com/Kevin-De-Koninck): Git master and senpai of patience with my learning process in [pep8](https://www.python.org/dev/peps/pep-0008/). 
* [brakke97](https://twitter.com/skeltavik): He learned me how to hack mobile applications. This project would never exist without him.
* [Aditya Gupta](https://twitter.com/adi1391): Awesome dude, really. Just keep him away from your IoT fridge or coffeemachine. Check out his [website](https://www.attify-store.com/) if you are into IoT hacking.
* [Quintenvi](https://twitter.com/quintenvi): He learned me alot, also non-hacking things.
* [c4b3rw0lf](https://twitter.com/c4b3rw0lf): The awesome dude behind the [VulnOS series](https://www.vulnhub.com/series/vulnos,36/).
* [MacJu89](https://twitter.com/MacJu89): infra & XSS senpai

Many more should be listed here, but this readme file would be TL;DR which is the worst what can happen to a readme file.
