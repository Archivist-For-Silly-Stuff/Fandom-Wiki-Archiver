# Fandom-Wiki-Archiver
An archiver for Fandom wikis!

Note:This is still being worked on and supported.  

As of now, robots.txt ***isn't considered*** so use this tool with care.

Instructions to use:

From the terminal write this:

python crawl.py domain_of_wiki a_url_to_start_scraping_the_wiki Destination_Directory_for_files

## Prerequisites
If you wish to use this there are also some prerequisite things you must download via the terminal:
<ul>
  <li>bs4</li>
    <code>pip install beautifulsoup4</code>
  <li>requests</li>
    <code>pip install requests</code>
  <li><a href="https://www.python.org/downloads/">Python 3 (For the CLI (Command Line Interface) to work)</a></li>
</ul>

## Instructions
To use this I would suggest running the GUI, the CLI command probably also works, but the GUI is more user friendly.

To archive a wiki first you must go to any wiki page (except for a forum page). Now, navigate down to the footer of the page.

There you will see many links. I want you to click on the link that says Local Sitemap.

Copy this url and this will be the URL you will give into the Archiver GUI.

From there you **should** make a directory specifically for this wiki. Make sure it's empty and that there is absolutely NOTHING else there. Otherwise the process may be hindered.

Copy the path of this directory and give it to the GUI.

Now, run the GUI. Don't worry if it freezes up. Depending on the size of the wiki I approximate that this can last between 15 minutes to 1 hour (taking a scope of 200 pages to a 1000).

## A todo list
So far I still need to:
<ul>
  <li>make a GUI (wip)</li>
  <li>a .exe executable file</li>
  <li>Test the graphing feature</li>
  <li>Extend this to other Fan Wikis</li>
  <li>Download Weegeepedia</li>
  <li>Make this work for dynamic html (Javascript and such)</li>
</ul>
