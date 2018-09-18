import urllib2
import time
import json
import codecs

SCRAPE_DELAY_SECONDS = 2.5 # how long to wait between each page load
SCRAPE_TIMEOUT = 20
ERROR_DELAY_SECONDS = 20 # how long to wait when IOError caught on page load
ERROR_RETRY_ATTEMPTS = 5 # how many times do we retry when catching error

def fetch_page(url, post_params=None):
	"""Wraps fetch in try/catch to handle server errors"""
	_attempts = 1
	_continue = True

	html = None
	while _continue:
		try:
			if post_params is not None:
				html = urllib2.urlopen(url, post_params, timeout=SCRAPE_TIMEOUT).read()
			else:
				html = urllib2.urlopen(url, timeout=SCRAPE_TIMEOUT).read()
			html = unicode(html, 'utf-8', 'ignore')
			html = html.replace('\\xa0', ' ')
			_continue = False
		except (IOError, urllib2.URLError) as e:
			_attempts+=1
			print '%s for url %s, attempt %d' % (str(e), url, _attempts)
			if _attempts>ERROR_RETRY_ATTEMPTS:
				_continue = False
			else:
				time.sleep(ERROR_DELAY_SECONDS)
	time.sleep(SCRAPE_DELAY_SECONDS)
	return html
	
def ndj_extract_values(infile, outfile, key_list, exclude=False):
	"""
	Parses every line of a newline-delimited json file and writes a new file,
	extracting only the desired keys.

	Alternatively, extract all keys except for those specifically excluded.
	"""

	with codecs.open(infile, 'r', encoding='utf8') as fin:
		with codecs.open(outfile,'w', encoding='utf8') as fout:
			for l in fin:

				d = {}
				# attempt to parse line
				try:
					rec = json.loads(l.decode('latin-1'))
				except ValueError:
					rec=None

				try:
					rec_keys = rec.keys()
				except:
					rec_keys=None
				
				if rec_keys is not None:
					if exclude:
						for k in rec_keys:
							if k not in key_list:
								d[k] = rec[k]
					else:
						for k in key_list:
							v = None
							if k in rec.keys():
								v = rec[k]
							d[k] = v

					fout.write(json.dumps(d))
					fout.write('\n')