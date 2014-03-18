#!/usr/bin/python

import urllib2
from bs4 import BeautifulSoup
from bibtexparser.bparser import BibTexParser
import simplejson as json
from datetime import datetime
import calendar
import re

def prettyPrint(_obj):
	print json.dumps(_obj, indent=4)

def storedNIPS(_id, table):
	'''Checks if a field exists within the given data store by comparing nips ids'''
	if len(table) != 0:
		for record in table:
			if table[record]["nips_id"] == _id:
				return True
	return False
	
class Publication(object):
	'''A paper from Advances in Neural Information Processing Systems''' 
	def __init__(self, _id, _url, _title):
		print "Creating publication with nips_id: " + _id
		self.publication = dict();
		self.publication["timestamp"] = calendar.timegm(datetime.utcnow().utctimetuple())
		self.publication["title"] = _title
		self.publication["nips_id"] = _id
		self.soup = BeautifulSoup(urllib2.urlopen(_url).read())
		self.process(_url)
	
	def process(self, _url):
		self.publication["abstract"] = self.soup.find_all('p')[1].get_text()
		
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
		self.person["timestamp"] = calendar.timegm(datetime.utcnow().utctimetuple());
		self.person["nips_id"] = _id
		self.soup = BeautifulSoup(urllib2.urlopen(_url).read())
		self.person["name"] = self.soup.h2.get_text()
	
	def returnPerson(self):
		return self.person
		
class Author(Person):
	def __init__(self, _id, _url):
		Person.__init__(self, _id, _url)
		
class Editor(Person):
	def __init__(self, _id, _url):
		Person.__init__(self, _id, _url)
	
def processNIPS(_url):
	#temporary representation of laravel default record ids
	publications_id = 1
	authors_id = 1
	editors_id = 1
	author_publication_id = 1
	editor_publication_id = 1
	
	soup = BeautifulSoup(urllib2.urlopen(_url).read())
	
	for link in soup.find_all('ul')[1].find_all('li'):
	#link = soup.find_all('ul')[1].find_all('li')[0]
	
		#publications
		p_url = "http://papers.nips.cc" + link.a.get('href')
		p_id = link.a.get('href').split("/")[2][0:4] #NOT EVERY NIPS ID IS A 4 DIGIT NUMBER!
		p_title = link.a.get_text()
		pub = Publication(p_id, p_url, p_title)
		
		publications[publications_id] = pub.returnPublication()
		publications_id += 1
		
		#authors / author_publication
		author_soup = BeautifulSoup(urllib2.urlopen(p_url).read())
		
		for link in author_soup.find_all('ul')[1].find_all('li'):
			a_id = re.sub("\D","",link.a.get('href').split('/')[2])
			a_url = "http://papers.nips.cc" + link.a.get('href')
			
			if not storedNIPS(a_id, authors):
				auth = Author(a_id, a_url)
				authors[authors_id] = auth.returnPerson()
				authors_id += 1;
				
			author_publication[author_publication_id] = dict()
			author_publication[author_publication_id]["author_id"] = a_id
			author_publication[author_publication_id]["publication_id"] = p_id
			author_publication_id += 1
		
		#editors / editor_publication
		editor_counter = 0
		while soup.find_all('div')[2].contents[editor_counter] != soup.find_all('ul')[1]:
			contender = soup.find_all('div')[2].contents[editor_counter]
			if "</a>" in str(contender):
				e_id = re.sub("\D", "", contender.get('href').split('/')[2])
				e_url = "http://papers.nips.cc" + contender.get('href')
				
				if not storedNIPS(e_id, editors):
					ed = Editor(e_id, e_url)
					editors[editors_id] = ed.returnPerson()
					editors_id += 1;
				
				editor_publication[editor_publication_id] = dict()
				editor_publication[editor_publication_id]["editor_id"] = e_id
				editor_publication[editor_publication_id]["publication_id"] = p_id
				editor_publication_id += 1
			editor_counter += 1

nips_url = "http://papers.nips.cc/book/advances-in-neural-information-processing-systems-26-2013"

publications = dict()
authors = dict()
editors = dict()
author_publication = dict()
editor_publication = dict()

processNIPS(nips_url)