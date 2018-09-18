# -*- coding: utf-8 -*-

"""
Moves records between NDJ-formatted files and S3 keys
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gevent import monkey; monkey.patch_all()
from geventconnpool import ConnectionPool
from geventconnpool import retry
import gevent
import gevent.pool
from gevent import sleep

import sfscpage
import json
from s3bucket import S3Bucket


BUCKETS_IN_POOL = 40


POOL_SIZE = 30
POOL = gevent.pool.Pool(POOL_SIZE)

class S3BucketPool(ConnectionPool):
  def __init__(self, n_buckets):
    self.buckets = []
    for _i in xrange(n_buckets):
      self.buckets.append(S3Bucket())
      sleep(1)

  def get_bucket(self):
    # grab a bucket
    bucket = None
    while bucket is None:
      if len(self.buckets)>0:
        bucket=self.buckets.pop(0)
      else:
        # wait for others to free up
        sleep(1)
    return bucket

  def return_bucket(self, bucket):
    self.buckets.append(bucket)


def ndj_to_s3(infile, start_line=0):
  """Take newline-delimited json file of SFSC pages and ship each row to s3 as a key"""

  with open(infile, 'rb') as f:
    _linenum=0
    for l in f:
      print _linenum
      if _linenum>=start_line:
        POOL.spawn(json_to_s3, l)
        sleep(0)
      _linenum+=1
    POOL.join()

def s3_to_ndj(bucket):
  """Print all keys in S3 bucket"""

  for k in bucket.bucket.list():
    POOL.spawn(print_s3,k)
    sleep(0)
  POOL.join()

def print_s3(key):
  """Take contents of an s3 key and print json line"""
  print key.get_contents_as_string()
      

def json_to_s3(line, bucket_pool):
  """Push single line of ndj file to s3"""
  try:
    d = json.loads(line)
  except ValueError, AttributeError:
    d = None

  p = None
  if d is not None:

    bucket = bucket_pool.get_bucket()
    p = sfscpage.SFSCPage(d['html'], d['case_num'], bucket)
    print d['full_case_num']
    p.put_s3()
    bucket_pool.return_bucket(bucket)

def main(args=None):
  if args is None:
    args=sys.argv
  fname = args[1]
  start = 0
  if len(args)>2:
    start = int(args[2])
  ndj_to_s3(fname, start)

if __name__=='__main__':
  sys.exit(main())