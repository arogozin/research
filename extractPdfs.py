#!/usr/bin/python

import urllib2, Queue, threading
from bs4 import BeautifulSoup

MAX_THREADS = 10
queue = Queue.Queue()

def extract(_url):
	soup = BeautifulSoup(urllib2.urlopen(_url).read())
	
	for link in soup.find_all('ul')[1].find_all('li'):
		pdf = "http://papers.nips.cc" + link.a.get('href') + ".pdf"
		print "Adding %s to queue" %pdf
		queue.put(pdf)
	
def download():
	while True:
		try:
			pdf = queue.get(block = False)
			print "Downloading " + pdf
			doc = open("pdfs2013/" + pdf.split('/')[-1], 'w')
			doc.write(urllib2.urlopen(pdf).read())
			doc.close()
		except Queue.Empty:
			break
	
nips_url = "http://papers.nips.cc/book/advances-in-neural-information-processing-systems-26-2013"
extract(nips_url)

while threading.activeCount() < MAX_THREADS + 1:
	thread = threading.Thread(target = download)
	thread.start()