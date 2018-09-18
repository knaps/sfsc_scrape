courtdocs
=========
courtdocs is a tool for scraping and analyzing the San Francisco Superior Court system's public database for civil court documents.

I created this tool as a potential asset for journalistic work, intending to listen for new court cases that related to people of public interest. The original motivation was when a former boss went through a [high profile court case](https://www.thedailybeast.com/ojs-lawyer-and-the-woman-abusing-princeling-of-silicon-valley) - I had heard of various civil lawsuits against him but wanted to know if there were more out there.

As far as I can tell, use of this tool is legal since these are publicly available documents, but IANAL so use at your own risk.

# Project Details
The project currently pulls metadata but does not retrieve full document PDFs. Metadata includes who the plaintiff and defendent are, and any prodedural events happening during the case.

To get started:
```
python scrape.py 570000 600000 > records.ndjson
```
This will start the scraper at courtcase number 570000, run until case number 600000, and save records to records.ndjson in [newline-delimited JSON](http://ndjson.org/) format.