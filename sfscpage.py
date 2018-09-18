# -*- coding: utf-8 -*-

import re
import time
from bs4 import BeautifulSoup as BS
from datetime import datetime, date
import json
import urllib
import sys

import utils
import config

class SFSCPage:
	_case_re = re.compile('Case Number: (.*)$')
	_title_re = re.compile('Title: ?((.*)(?: ?VS\. ?| VS | vs\. | vs )(.*))$')
	_title_no_vs_re = re.compile('Title: (.*)')
	_cause_re = re.compile('Cause of Action: (.*)')
	_invalid_re = re.compile('Case Number.*Is Invalid')
	_multiple_results_re = re.compile('More that one case exists with number.*')

	_blank_str = '&amp;nbsp'

	def __init__(self, html, case_num):
		try:
			soup = BS(html, 'html5lib')
		except TypeError:
			soup = None
			time.sleep(utils.ERROR_DELAY_SECONDS)
		self.case_num = case_num
		self.html = html
		self.soup = soup
		self.scraped_at = datetime.now()
		self.court_name = None
		self.full_case_num = None
		self.title = None
		self.plaintiff = None
		self.defendant = None
		self.cause_action = None
		self.proceedings = None
		#self.first_filing_date = None
		#self.last_filing_date = None

		if self.status()=='valid':
			self._process_fonts(soup.findAll('font'))
			self._process_table(soup.find('table'))

	def _process_fonts(self, fonts):
		self.court_name = fonts[0].text
		self.full_case_num = self._case_re.match(fonts[1].text).group(1)

		title_match = self._title_re.match(fonts[2].text)
		if title_match is not None:
			self.title = title_match.group(1).title()
			self.plaintiff = title_match.group(2).title()
			self.defendant = title_match.group(3).title()
		else:
			# title didn't have plaintiff/defendant. Try without
			self.title = self._title_no_vs_re.match(fonts[2].text).group(1)

		self.cause_action = self._cause_re.match(fonts[3].text).group(1).title()

	def _process_table(self, table):
		rows = None
		try:
			rows = table.findAll('tr')
		except AttributeError:
			pass
		proceedings = []
		if rows is not None:
			for r in rows[1:]:
				rec = {}
				tds = r.findAll('td')
				try:
					rec['date'] = datetime.strptime(tds[0].text.encode('utf-8'), u'%b-%d-%Y')
					rec['proceeding'] = self._strip_whitespace(tds[1].text)
					
					rec['document'] = None
					if tds[2] != self._blank_str:
						for a in tds[2].findAll('a'):
							if a.get('href') is not None:
								rec['document']=a.get('href')
					proceedings.append(rec)
				except ValueError:
					pass
		self.proceedings=proceedings

	def _strip_whitespace(self, s):
	    """Remove newline characters and combine whitespace."""
	    s = s.replace('\n', ' ').replace('\r', ' ')
	    s = re.sub(r'\s+', ' ', s)
	    return s

	def first_filing_date(self):
		return min([p['date'] for p in self.proceedings])

	def last_filing_date(self):
		return max([p['date'] for p in self.proceedings])

	def status(self):
		"""Classifies whether the page loaded is a valid case, invalid, multiple
		records, etc"""
		status = 'unknown'
		if self.soup is not None:
			if self.soup.find(text=self._invalid_re) is not None:
				status = 'invalid'
			elif self.soup.find(text=self._multiple_results_re) is not None:
				status = 'multiple_results'
			else:
				_fonts = self.soup.findAll('font')
				if _fonts:
					if len(_fonts)>1:
						if self._case_re.match(_fonts[1].text) is not None:
							status = 'valid'

		return status

	def data_as_dict(self, html=False):
		"""
		Returns a dict of this page's data as a dict, or None if page isn't valid case representation.
		html=True will append the full page html to the dict
		"""
		d = None
		if self.status()=='valid':
			d = {
				'full_case_num': self.full_case_num,
				'case_num': self.case_num,
				'cause_action': self.cause_action,
				'court_name': self.court_name,
				'defendant': self.defendant,
				'plaintiff': self.plaintiff,
				'first_filing_date': self.first_filing_date(),
				'last_filing_date': self.last_filing_date(),
				'proceedings': self.proceedings,
				'proceedings_cnt': self.proceedings_cnt(),
				'proceedings_words': self.proceedings_words(),
				'title': self.title,
				'scraped_at': self.scraped_at,
				'status': self.status(),
				'has_doc': self.has_doc()
			}
			if html:
				d['html'] = self.html
		return d

	def data_as_json(self, html=False):
		"""Returns a json object, or None if invalid page"""
		d = self.data_as_dict(html=html)
		new = None
		if d is not None:
			new = d.copy()
			#convert dates to strs
			new['first_filing_date'] = None

			# format dates
			for _key in ('first_filing_date', 'last_filing_date'):
				if d[_key] is not None:
					new[_key] = d[_key].strftime('%Y-%m-%d')
			new['scraped_at'] = d['scraped_at'].strftime('%Y-%m-%d %H:%M:%S')
			
			# format dates in proceedings
			_procs = []
			for p in d['proceedings']:
				newp = dict(p.items())
				newp['date'] = p['date'].strftime('%Y-%m-%d')
				_procs.append(newp)
			new['proceedings'] = _procs
		
		result = None
		if new is not None:
			result = json.dumps(new)
		return result

	def valid(self):
		return self.status()=='valid'

	def has_doc(self):
		"""Does this case have a document in its proceedings table?"""
		result = False
		for p in self.proceedings:
			if p['document'] is not None:
				result=True
		return result

	def proceedings_cnt(self):
		"""Return number of proceedings"""
		return len(self.proceedings)
	
	def proceedings_words(self):
		"""Return number of words found in proceedings"""
		words = 0
		for p in self.proceedings:
			words += len(re.findall(r'\w+', p['proceeding']))
		return words
