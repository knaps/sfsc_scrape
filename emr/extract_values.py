
"""
Given an s3 bucket full of keys, each representing a single court case,
extract the non-html data from those keys.
"""

import sys, json
from datetime import datetime

# return everything from each document except these keys
SKIP_KEYS = ['html',
] 

def mapper(line):
	"""What to do to each key in bucket"""
	try:
		j = json.loads(line)
	except ValueError:
		j = None
	
	s=None
	if j is not None:

		# calculate some extra values i forgot earlier
		j['num_proceedings'] = len(j['proceedings'])
		j['last_filing_date'] = _last_filing_date(j['proceedings'])


		for k in SKIP_KEYS:
			j.pop(k)
		s = json.dumps(j)
	return s

def _last_filing_date(proceedings):
	last_date = None
	for p in proceedings:
		_d = datetime.strptime(p['date'], '%Y-%m-%d')
		if last_date is None:
			last_date = _d

		if _d > last_date:
			last_date = _d
	if last_date is not None:
		ret = last_date.strftime('%Y-%m-%d')
	else:
		ret = ''
	return ret


def main():
	for line in sys.stdin:
		s = mapper(line)
		if s is not None:
			print s

if __name__ == '__main__':
	main()
