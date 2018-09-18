# -*- coding: utf-8 -*-

"""Initialize new MongoDB collection and bulk import documents"""

import sys
from datetime import datetime, date
from pymongo import MongoClient
import json

MONGO_URL = 'mongodb://52.0.31.153'
MONGO_DB_NAME = 'courtdocs'
MONGO_COLL_NAME = 'docs'
try:
	MONGO_CLIENT = MongoClient(MONGO_URL)
except:
	MONGO_CLIENT = None
	print >> sys.stderr, 'Failed to connect to MongoDB server'

def _record_gen(fname):
	"""Generator to read records from a file to be uploaded to mongo"""
	with open(fname) as f:
		for r in f:
			rec = strs_to_datetime(json.loads(r))
			yield rec

def upload_docs(fname):
	"""Load docs from JSON file and send to mongo"""
	db = MONGO_CLIENT[MONGO_DB_NAME]
	
	coll = db[MONGO_COLL_NAME]
	coll.insert([r for r in _record_gen(fname)])

def strs_to_datetime(rec):
	"""Convert date strings into python datetimes"""
	
	rec['scraped_at'] = datetime.strptime(rec['scraped_at'], '%Y-%m-%d %H:%M:%S')
	for key in ('first_filing_date', 'last_filing_date'):
		t = tuple([int(x) for x in rec[key].split('-')]+[0,0,0])
		rec[key] = datetime(*t)
	for p in rec['proceedings']:
		t = tuple([int(x) for x in p['date'].split('-')]+[0,0,0])
		p['date'] = datetime(*t)

	return rec
