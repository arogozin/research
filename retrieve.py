#!/usr/bin/python
import os
import subprocess
from multiprocessing import Lock, Process, Queue, current_process

def worker(work_queue, done_queue):
    try:
        for doc in iter(work_queue.get, 'STOP'):
            textPath = convert(doc)
            done_queue.put("%s - %s got %s." % (current_process().name, doc, textPath))
    except Exception, e:
        done_queue.put("%s failed on %s with: %s" % (current_process().name, doc, e.message))
    return True

def convert(filepath):
    print "Converting "+ filepath
    textPath = 'docs/'+os.path.splitext(filepath)[0]+'.txt'
    pdfPath = 'pdfs/'+filepath
    subprocess.call(["pdf2txt.py", "-o", textPath, pdfPath])
    return textPath

def main():
    workers = 10
    work_queue = Queue()
    done_queue = Queue()
    processes = []

    for dirname, dirnames, filenames in os.walk('pdfs'):
        for filename in filenames:
            if filename.endswith('.pdf'):
                print "Putting "+ filename +" into QUEUE."
                work_queue.put(filename)

    for w in xrange(workers):
        p = Process(target=worker, args=(work_queue, done_queue))
        p.start()
        processes.append(p)
        work_queue.put('STOP')

    for p in processes:
        p.join()

    done_queue.put('STOP')

    for status in iter(done_queue.get, 'STOP'):
        print status

if __name__ == '__main__':
    main()