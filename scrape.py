# -*- coding: utf-8 -*-

import urllib, urlparse
from datetime import datetime, date
import sys
import argparse
import os
import pickle

from sfscpage import SFSCPage
import utils

SFSC_START_CASE_NUM = 570000
SFSC_POST_URL = 'http://webaccess.sftc.org/scripts/magic94/Mgrqispi94.dll'
SFSC_POST_PARAMS = {'APPNAME': 'WEB',
										'PRGNAME': 'ValidateCaseNumber',
										'ARGUMENTS': 'Case Number {k}',
										'Case Number {k}': None # need to set this value
}
SFSC_CASE_NUM_FORMAT = '{0:06d}'.format # case numbers have trailing zeroes
SFSC_BLOCK_SIZE = 1000 # when hitting invalid streaks, skip ahead to next block

INVALID_PAGES_LIMIT = 5 # stop after hitting this many invalid results in a row

RECORDS_DB_PATH = 'records.db' # file for storing data in

def scrape_page(case_num):
	"""Scrape an individual page based on casenum"""
	post_params = SFSC_POST_PARAMS
	post_params['Case Number {k}']=case_num
	post_params_enc = urllib.urlencode(post_params)

	html = utils.fetch_page(SFSC_POST_URL, post_params_enc)

	page = SFSCPage(html, case_num)
	return page

def scrape_sfsc(start=SFSC_START_CASE_NUM, end=None, skip=[]):
	"""Main loop for scraping a batch of pages"""
	_continue = True
	_invalid_streak = 0
	
	case_num = start
	records = []
	while _continue:
		_case_num_str = SFSC_CASE_NUM_FORMAT(case_num)
		# to-do: Check for "invalid" page result
		print >> sys.stderr, _case_num_str
		if case_num in skip:
			print >> sys.stderr, 'Skipping...'
		
		else:
			page = scrape_page(_case_num_str)
			if page.status()=='multiple_results':
				# append a page for each result
				for f in page.soup.findAll('font'):
					for a in f.findAll('a'):
						_url = urlparse.urljoin(SFSC_POST_URL, a.get('href'))
						_html = utils.fetch_page(_url)
						_page = SFSCPage(_html, _case_num_str)
						yield _page
			else:
				yield page

			# Did we hit too many invalid pages in a row?
			# if so, skip ahead to next block and try again. Keep increasing by block until valid page found
			if page.status()=='invalid':
				_invalid_streak+=1
				print >> sys.stderr, 'Invalid page for case num %d, number %d in a row' % (case_num, _invalid_streak)
				if _invalid_streak>=INVALID_PAGES_LIMIT:
					case_num = (case_num/SFSC_BLOCK_SIZE+1)*SFSC_BLOCK_SIZE-1
					# subtract 1 since it will be added back at end of loop
			else:
				_invalid_streak=0
			# check to see if we should break
			# Did we pass end value?
		case_num+=1
		if end is not None:
			if case_num>end:
				_continue=False


################################################
# Storage of scraped records
################################################
def update_records_db(records):
	"""Add or update records to stored database. records is list of Page objects"""
	result = load_records_db()
	for r in records:
		rd = None
		if r.status()=='valid':
			rd = r.data_as_dict()
		if rd is not None:
			result[rd['full_case_num']] = rd
	with open(RECORDS_DB_PATH,'wb') as f:
		pickle.dump(result, f)

def load_records_db():
	"""Get old stored records"""
	if os.path.exists(RECORDS_DB_PATH):
		with open(RECORDS_DB_PATH, 'rb') as f:
			try:
				result = pickle.load(f)
			except EOFError:
				print >> sys.stderr, 'Empty database file, creating a new one'
				result = {}
	else:
		result = {}
	return result

def db_last_case_num():
	"""Get the last case_num in stored data"""
	records = load_records_db()
	case_nums = sorted([r['case_num'] for r in records.values()], reverse=True)
	return case_nums[0]



################################################
# Main
################################################

def main(args=None):
	"""scrape a range of case numbers, outputting results to stdout"""
	if args is None:
		parser = argparse.ArgumentParser(description='Scrape across a range of case nums')
		parser.add_argument('-s', dest='start_num', action='store', help='Starting casenum to scrape')
		parser.add_argument('-e', dest='end_num', action='store', help='Ending casenum to scrape')
		args = parser.parse_args()

	scraper = scrape_sfsc(int(args.start_num), int(args.end_num))

	print >> sys.stderr, 'Starting scrape at %s' % datetime.now()
	
	for r in scraper:
		if r.data_as_json(html=True) is not None:
			print r.data_as_json(html=True)

if __name__=='__main__':
	sys.exit(main())
	