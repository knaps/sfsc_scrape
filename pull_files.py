"""
Given records that may contain links to court documents, pull out those
links and download and save the documents
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

def fetch_pdf(url, browser):
	"""Given a link to a SFSC court document, return the PDF file"""
	pass

	# grab link page

	# search soup for pdf file

	# grab pdf file and return it

def docs_from_records(records):
	"""
	Given a list of tuples (full_court_num, data), download pdfs linked to in each tuple.
	Yield dicts of the data + pdfs attached to the 'proceedings' value
	"""
	# Need selenium server running:
	# java -jar selenium-server-standalone-2.35.0.jar -role node -hub http://localhost:4444/grid/register -browser browserName=htmlunit
	browser = webdriver.Remote("http://127.0.0.1:4444/wd/hub",desired_capabilities=webdriver.DesiredCapabilities.HTMLUNITWITHJS)
	for r in records:
		for p in r['proceedings']:
			p['fetched_document'] = None
			if p['document'] is not None:
				p['fetched_document'] = fetch_pdf(['document'])
		yield r