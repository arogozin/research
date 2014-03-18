#!/usr/bin/python
# -*- coding: utf8 -*-

import urllib2, Queue, threading, re, time, MySQLdb
from bs4 import BeautifulSoup
from bibtexparser.bparser import BibTexParser

db = MySQLdb.connect(host = "db.arc.poly.edu", user = "research", passwd = "75*London*487", db = "research")
c = db.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS publications (
				id INT NOT NULL AUTO_INCREMENT,
				created_at VARCHAR(100) NOT NULL,
				updated_at VARCHAR(100) NOT NULL,
				title VARCHAR(100) NOT NULL,
				nips_id INT NOT NULL,
				abstract TEXT,
				pages VARCHAR(10) NOT NULL,
				year INT NOT NULL, 
				booktitle VARCHAR(100) NOT NULL,
				PRIMARY KEY ( id )
			)""")
c.execute("""CREATE TABLE IF NOT EXISTS people (
				id INT NOT NULL AUTO_INCREMENT,
				created_at VARCHAR(100) NOT NULL,
				updated_at VARCHAR(100) NOT NULL,
				name VARCHAR(100) NOT NULL,
				nips_id INT NOT NULL,
				PRIMARY KEY ( id )
			)""")
c.execute("""CREATE TABLE IF NOT EXISTS person_publication (
				id INT NOT NULL AUTO_INCREMENT,
				created_at VARCHAR(100) NOT NULL,
				updated_at VARCHAR(100) NOT NULL,
				person_id INT NOT NULL,
				publication_id INT NOT NULL,
				type VARCHAR(10),
				PRIMARY KEY ( id )
			)""")

MAX_THREADS = 10

p_queue = Queue.Queue()
a_queue = Queue.Queue()
e_queue = Queue.Queue()
	
class Publication(object):
	'''A paper from Advances in Neural Information Processing Systems''' 
	def __init__(self, _id, _url, _title):
		print "Creating publication with nips_id: " + _id
		self.publication = dict();
		self.publication["title"] = _title
		self.publication["nips_id"] = _id
		self.soup = BeautifulSoup(urllib2.urlopen(_url).read())
		self.process(_url)
	
	def process(self, _url):
		self.publication["abstract"] = self.soup.find_all('p')[1].get_text().encode('utf-8')
		
		bibtex = urllib2.urlopen(_url + "/bibtex").read()
		texname = _url.split("/")[4][5:] + ".bib"
		with open('bibtex/' + texname, 'w') as bibfile:
			bibfile.write(bibtex)
			
		bibfile = open('bibtex/' + texname, 'r')
		bp = BibTexParser(bibfile)
		elist = bp.get_entry_list()
		
		self.publication["booktitle"] = elist[0]["booktitle"]
		self.publication["pages"] = elist[0]["pages"]
		self.publication["year"] = elist[0]["year"]
		
		bibfile.close()
	
	def returnPublication(self):
		return self.publication

class Person(object):
	'''An author or editor of a NIPS publication'''
	def __init__(self, _id, _url):
		print "Creating person with the nips_id: " + _id
		self.person = dict()
		self.person["nips_id"] = _id
		self.soup = BeautifulSoup(urllib2.urlopen(_url).read())
		self.person["name"] = self.soup.h2.get_text().encode('utf-8')
	
	def returnPerson(self):
		return self.person
	
def prepareNIPS(_url):
	'''Stores parsed data in corresponding queue'''
	pub_soup = BeautifulSoup(urllib2.urlopen(_url).read())	
	#editors
	# - all editors are the same for every publication under a nips year
	editor_counter = 0
	while pub_soup.find_all('div')[2].contents[editor_counter] != pub_soup.find_all('ul')[1]:
		contender = pub_soup.find_all('div')[2].contents[editor_counter]
		if "</a>" in str(contender):
			ed_id = re.sub("\D", "", contender.get('href').split('/')[2])
			ed_url = "http://papers.nips.cc" + contender.get('href')
			print "Adding editor to queue: " + str(ed_id)
			e_queue.put([ed_id, ed_url]) #per_inc_id as first item
			#per_inc_id += 1
		editor_counter += 1
		
	for link in pub_soup.find_all('ul')[1].find_all('li'):
		#publications
		pub_id = re.search(r'/[0-9]+-', link.a.get('href')).group()[1:-1]
		pub_url = "http://papers.nips.cc" + link.a.get('href')
		pub_title = link.a.get_text().encode('utf-8')
		print "Adding publication to queue: " + str(pub_id)
		p_queue.put([pub_id, pub_url, pub_title])
		
		#authors
		auth_soup = BeautifulSoup(urllib2.urlopen(pub_url).read())
		
		for link in auth_soup.find_all('ul')[1].find_all('li'):
			auth_id = re.sub("\D","",link.a.get('href').split('/')[2])
			auth_url = "http://papers.nips.cc" + link.a.get('href')
			print "Adding author to queue: " + str(auth_id)
			a_queue.put([auth_id, auth_url, pub_id])


def processPublications():
	while True:
		try:
			p_info = p_queue.get(block = False)
			pub = Publication(p_info[0], p_info[1], p_info[2])
			p = pub.returnPublication()
			
			c.execute("SELECT * FROM publications WHERE nips_id = %s" %(p["nips_id"]))
			record = c.fetchone()
			
			if not record:
				timestamp = time.strftime("%Y-%m-%d %H-%M-%S")
				c.execute("INSERT INTO publications (created_at, updated_at, title, nips_id, abstract, pages, year, booktitle) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (timestamp, timestamp, p["title"], p["nips_id"], p["abstract"], p["pages"], p["year"], p["booktitle"]))
				db.commit()	
				
		except Queue.Empty:
			break;
	
def processEditors():
	while True:
		try:
			e_info = e_queue.get(block = False)
			ed = Person(e_info[0], e_info[1])
			e = ed.returnPerson()
			
			c.execute("SELECT * FROM people WHERE nips_id = %s" %(e["nips_id"]))
			record = c.fetchone()
			
			if not record:
				timestamp = time.strftime("%Y-%m-%d %H-%M-%S")
				c.execute("INSERT INTO people (created_at, updated_at, name, nips_id) VALUES (%s, %s, %s, %s)", (timestamp, timestamp, e["name"], e["nips_id"]))
				db.commit()
			
		except Queue.Empty:
			break;
	
	c.execute("SELECT id FROM publications")
	pub_ids = c.fetchall()
	c.execute("SELECT id FROM people")
	ed_ids = c.fetchall()
	
	for eds in ed_ids:
		for pubs in pub_ids:
			timestamp = time.strftime("%Y-%m-%d %H-%M-%S")
			c.execute("INSERT INTO person_publication (created_at, updated_at, person_id, publication_id, type) VALUES (%s, %s, %s, %s, %s)", (timestamp, timestamp, eds, pubs, "Editor"))
			db.commit()
					
def processAuthors():
	while True:
		try:
			a_info = a_queue.get(block = False)
			auth = Person(a_info[0], a_info[1])
			a = auth.returnPerson()
			
			c.execute("SELECT * FROM people WHERE nips_id = %s" %(a["nips_id"]))
			record = c.fetchone()
			
			if not record:
				timestamp = time.strftime("%Y-%m-%d %H-%M-%S")
				c.execute("INSERT INTO people (created_at, updated_at, name, nips_id) VALUES (%s, %s, %s, %s)", (timestamp, timestamp, a["name"], a["nips_id"]))
				db.commit()
			
			c.execute("SELECT id FROM publications WHERE nips_id = %s" %(a_info[2]))
			p_id = c.fetchone()
			c.execute("SELECT id FROM people WHERE nips_id = %s" %(a["nips_id"]))
			a_id = c.fetchone()
			
			timestamp = time.strftime("%Y-%m-%d %H-%M-%S")
			c.execute("INSERT INTO person_publication (created_at, updated_at, person_id, publication_id, type) VALUES (%s, %s, %s, %s, %s)", (timestamp, timestamp, a_id, p_id, "Author"))
			db.commit()
			
		except Queue.Empty:
			break;

nips_url = "http://papers.nips.cc/book/advances-in-neural-information-processing-systems-26-2013"

prepareNIPS(nips_url)
processPublications()
processEditors()
processAuthors()

'''
while threading.activeCount() < MAX_THREADS + 1:
	thread = threading.Thread(target = process ... )
	thread.start()
'''