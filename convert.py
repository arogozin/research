#!/usr/bin/python

import os, subprocess, threading, Queue, sys

MAX_THREADS = 10

q_pdf = Queue.Queue()

pdf_path = "pdfs2013" #sys.argv[1]
output_path = "docs2013" #sys.argv[2]

def prepare_pdfs(path):
	numtotal = 0
	for dirname, dirnames, filenames in os.walk(path):
		for filename in filenames:
			if filename.endswith('.pdf'):
				q_pdf.put(os.path.join(dirname, filename))
				numtotal += 1
	print numtotal
                
def convert():
	while True:
		try:
			pdf = q_pdf.get(block = False)
			txt = output_path + '/' + os.path.basename(q_pdf.get()).rstrip('.pdf') + '.txt'
			print "Converting %s to: %s" %(pdf, txt)
			subprocess.call(["pdf2txt.py", "-o", txt, pdf])
		except Queue.Empty:
			break

prepare_pdfs(pdf_path)

while threading.activeCount() < MAX_THREADS + 1:
	thread = threading.Thread(target = convert)
	thread.start()