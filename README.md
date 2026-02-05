# Fandom-Wiki-Archiver
An archiver for Fandom wikis!

Note:This is still being worked on and supported.  

~~As of now, robots.txt ***isn't considered*** so use this tool with care.~~ This has been worked through! However be sure to stay to wikia, other wiki's haven't been tested yet and it may lead to weird results!

## Installation
- A .exe is coming soon!

## Instructions for use:

~~From the terminal write this:~~

~~python crawl.py domain_of_wiki a_url_to_start_scraping_the_wiki Destination_Directory_for_files~~

1. Open the GUI
2. Put in any URL from the wiki you wish to archive
3. Make a new folder for that archive and choose that folder for the folder
4. Press submit (you can also make a network if you wish!)

## Prerequisites
If you wish to use this there are also some prerequisite things you must download via the terminal:
<ul>
  <li>bs4</li>
    <code>pip install beautifulsoup4</code>
  <li><a href="https://github.com/VeNoMouS/cloudscraper">cloudscraper</a></li>
  <li><a href="https://www.python.org/downloads/">Python 3</a></li>
  <li>Pyvis (optional)-Only for network options</li>
    <code>pip install pyvis</code>
  <li><a href="https://github.com/lexiforest/curl_cffi">Curl_cffi</a></li>
  <li>pyqt5/li>
    <code>pip install pyqt5</code>
</ul>


## A todo list
So far I still need to:
<ul>
  <li><s>make a GUI (wip)</s> Done (WOOHOOO)</li> 
  <li>a .exe executable file</li>
  <s><li>Test the graphing feature</li></s>
  <li>Extend this to other Fan Wikis</li>
  <li>Download Weegeepedia</li>
  <li>Make this work for dynamic html (Javascript and such) - Will require automation</li>
  <li><s>Convert some processes from synchronous to asynchronous</s>></li>
  <li>Download videos too (WIP)-Still need to see how to about doing that.</li>
  <li>Permanent solution for the cloudflare thing</li>
</ul>
