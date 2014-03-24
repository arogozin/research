#!/usr/bin/python

import threading
import time
import Queue
import string
import random
import simplejson as json

MAX_THREADS = 10

queue = Queue.Queue()

class Thing(object):
	def __init__(self, increment_id, id_1, id_2):
		self.thing = dict()
		self.thing["id"] = increment_id
		self.thing["foo"] = id_1
		self.thing["bar"] = id_2
		self.wasteTime()
	
	def wasteTime(self):
		time.sleep(1)
		return
	
def prettyPrint(_obj):
	print json.dumps(_obj, indent=4)
	
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def fill():
	print "FILLING ..."
	increment_id = 1
	for i in range(50):
		id_1 = id_generator()
		id_2 = id_generator(3)
		queue.put([increment_id, id_1, id_2])
		increment_id += 1
	print "DONE"
		
def process():
	print "PROCESSING ..."
	
	while True:
		try:
			info = queue.get(block = False)
			thing = Thing(info[0], info[1], info[2])
			print "thing(%s,%s,%s)" % (info[0], info[1], info[2])
		except Queue.Empty:
			break
			
	print "DONE"

fill()
#process() #will take forever (about 1000 seconds)
while threading.activeCount() < MAX_THREADS + 1:
	thread = threading.Thread(target = process)
	thread.start()