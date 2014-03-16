#!/usr/bin/python

import os
import subprocess
import threading
import Queue

MAX_THREADS = 10

q_pdf = Queue.Queue()
q_thread = Queue.Queue()

pdf_path = "pdfs"
output_path = "docs"

def get_pdfs(path):
    pdfs = []
    
    for dirname, dirnames, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith('.pdf'):
                pdfs.append(os.path.join(dirname, filename))
    return pdfs

pdfs = get_pdfs(pdf_path)

for pdf in pdfs:
	q_pdf.put(pdf)

def convert(txt, pdf):
	print "Converting %s to: %s" %(pdf, txt)
	subprocess.call(["pdf2txt.py", "-o", txt, pdf])

for i in range(MAX_THREADS):
	pdf = q_pdf.get()
	txt = output_path + '/' + os.path.basename(pdf).rstrip('.pdf') + '.txt' #os.path.splitext(pdf)[0]
	thread = threading.Thread(target=convert, args=(txt,pdf))
	thread.start()
	q_thread.put(thread)

q_thread.join()

print "DONE!"