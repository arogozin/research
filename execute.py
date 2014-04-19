#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import json
import re
import Queue
import time
import unicodedata
import MySQLdb
from bs4 import BeautifulSoup
from bibtexparser.bparser import BibTexParser

DB = MySQLdb.connect(host = "db.arc.poly.edu", user = "research", passwd = "75*London*487", db = "research")
C = DB.cursor()
BASE_URL = "http://papers.nips.cc"

class WebPage(object):
	'''Any web page to be soupified'''
	
	def __init__(self, _url):
		self.url = _url
		self.html = self.retrievePage(self.url).read()
		self.soup = self.parsePage(self.html)
	
	def retrievePage(self, _url):
		request = urllib2.Request(_url)
		request.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36')
		response = urllib2.urlopen(request)
		
		if (response.code == 200):
			return response
		else:
			return 'Error.'
	
	def parsePage(self, html):
		soup = BeautifulSoup(html)
		
		return soup


class Book(object):
	'''A single NIPS proceeding corresponding to one year'''

	def __init__(self, _page):
		self.page = _page
		self.url = _page.url
		self.soup = _page.soup
		self.title = self.retrieveTitle()
		self.editors = self.retrieveEditors()
		self.publications = self.retrievePublications()
		
	def retrieveTitle(self):
		return self.soup.find('h2', {'class': 'subtitle'}).getText()
		
	def retrieveEditors(self):
		print "RETRIEVING: " + self.title + " editors"
		editors = []
		for item in self.soup.find('br').findAllPrevious('a'):
			if 'author' in item.get('href'):
				url = BASE_URL + item.get('href')
				editor = Person(WebPage(url))
				print editor.name
				editors.append(editor)
				
		return editors

	def retrievePublications(self):
		print "RETRIEVING: " + self.title + " publications"
		publications = []
		for li in self.soup.findAll('ul')[1].findAll('li'):
			url = BASE_URL + li.a.get('href')
			publication = Publication(WebPage(url))
			print publication.title
			publications.append(publication)
		
		return publications

	def insertAndPivot(self):
		for editor in self.editors:
			C.execute("SELECT * FROM people WHERE identifier = %s" %(editor.identifier))
			record = C.fetchone()
			
			if not record:
				print "INSERTING: " + editor.name + " to database"
				timestamp = time.strftime("%Y-%m-%d %H-%M-%S")
				C.execute("INSERT INTO people (created_at, updated_at, name, identifier) VALUES (%s, %s, %s, %s)", (timestamp, timestamp, editor.name, editor.identifier))
				DB.commit()

			for publication in self.publications:
				publication.insertAndPivot("Author")
				
				C.execute("SELECT id FROM publications WHERE identifier = %s" %(publication.identifier))
				publication_id = C.fetchone()
				C.execute("SELECT id FROM people WHERE identifier = %s" %(editor.identifier))
				editor_id = C.fetchone()
				
				C.execute("SELECT * FROM person_publication WHERE person_id = %s AND publication_id = %s AND type = %s", (editor_id, publication_id, "Editor"))
				record = C.fetchone()
				
				if not record:
					print "INSERTING PIVOT: " + editor.name + " <-> " + publication.title
					timestamp = time.strftime("%Y-%m-%d %H-%M-%S")
					C.execute("INSERT INTO person_publication (created_at, updated_at, person_id, publication_id, type) VALUES (%s, %s, %s, %s, %s)", (timestamp, timestamp, editor_id, publication_id, "Editor"))
					DB.commit()
	

class Person(object):
	'''An author, editor, or reviewer of a NIPS publication'''
	
	def __init__(self, _page, _affiliation = None):
		self.page = _page
		self.url = _page.url
		self.soup = _page.soup
		self.name = self.retrieveName()
		self.identifier = self.retrieveIdentifier()
		self.affiliation = _affiliation
	
	def retrieveName(self):
		return unicodedata.normalize('NFKD', unicode(self.soup.find('h2', {'class': 'subtitle'}).getText())).encode('ascii', 'ignore')

	def retrieveIdentifier(self):
		return str(re.sub("\D", "", self.url))
	
	def retrievePublications(self):
		print "RETRIEVING: " + self.name + " publications"
		publications = []
		for li in self.soup.findAll('li')[1:]:
			url = BASE_URL + li.a.get('href')
			publication = Publication(WebPage(url))
			publications.append(publication)
			
		return publications
		
	def insert(self):
		C.execute("SELECT * FROM people WHERE identifier = %s" %(self.identifier))
		record = C.fetchone()
		
		if not record:
			print "INSERTING: " + self.name + " to database"
			timestamp = time.strftime("%Y-%m-%d %H-%M-%S")
			C.execute("INSERT INTO people (created_at, updated_at, name, identifier) VALUES (%s, %s, %s, %s)", (timestamp, timestamp, self.name, self.identifier))
			DB.commit()
			
	def insertAndPivot(self, _type):
		C.execute("SELECT * FROM people WHERE identifier = %s" %(self.identifier))
		record = C.fetchone()
		
		if not record:
			print "INSERTING: " + self.name + " to database"
			timestamp = time.strftime("%Y-%m-%d %H-%M-%S")
			C.execute("INSERT INTO people (created_at, updated_at, name, identifier) VALUES (%s, %s, %s, %s)", (timestamp, timestamp, self.name, self.identifier))
			DB.commit()
			
			publications = self.retrievePublications()
			
			for publication in publications:
				publication.insert()
				
				C.execute("SELECT id FROM publications WHERE identifier = %s" %(publication.identifier))
				publication_id = C.fetchone()
				C.execute("SELECT id FROM people WHERE identifier = %s" %(self.identifier))
				person_id = C.fetchone()
				
				C.execute("SELECT * FROM person_publication WHERE person_id = %s AND publication_id = %s AND type = %s", (person_id, publication_id, _type))
				record = C.fetchone()
				
				if not record:
					print "INSERTING PIVOT: " + self.name + " <-> " + publication.title
					timestamp = time.strftime("%Y-%m-%d %H-%M-%S")
					C.execute("INSERT INTO person_publication (created_at, updated_at, person_id, publication_id, type) VALUES (%s, %s, %s, %s, %s)", (timestamp, timestamp, person_id, publication_id, _type))
					DB.commit()
	

class Publication(object):
	'''A paper from Advances in Neural Information Processing Systems'''
	
	def __init__(self, _page):
		self.page = _page
		self.url = _page.url
		self.soup = _page.soup
		self.bibtex = self.retrieveBibtex()
		self.title = self.retrieveTitle()
		self.identifier = self.retrieveIdentifier()
		self.abstract = self.retrieveAbstract()
		self.pages = self.bibtex['pages']
		self.year = self.bibtex['year']
		self.booktitle = self.bibtex['booktitle']
		
	def retrieveBibtex(self):
		bibtex_url = self.url + '/bibtex'
		self.bibtex_raw = self.page.retrievePage(bibtex_url)
		bib = BibTexParser(self.bibtex_raw)
		bibtex = bib.get_entry_list()
		
		return bibtex[0]
		
	def retrieveTitle(self):
		return unicodedata.normalize('NFKD', unicode(self.soup.find('h2', {'class': 'subtitle'}).getText())).encode('ascii', 'ignore')
		
	def retrieveIdentifier(self):
		return str(re.findall(r"[0-9]+-", self.url)[0])[:-1]
		
	def retrieveAbstract(self):
		return self.soup.find('p', {'class': 'abstract'}).getText().encode('utf-8')
		
	def retrieveAuthors(self):
		print "RETRIEVING: " + self.title + " authors"
		authors = []
		for li in self.soup.findAll('ul')[1].findAll('li'):
			url = BASE_URL + li.a.get('href')
			author = Person(WebPage(url))
			authors.append(author)
	
		return authors
		
	def insert(self):
		C.execute("SELECT * FROM publications WHERE identifier = %s" %(self.identifier))
		record = C.fetchone()
		
		if not record:
			print "INSERTING: " + self.title + " to database"
			timestamp = time.strftime("%Y-%m-%d %H-%M-%S")
			C.execute("INSERT INTO publications (created_at, updated_at, title, identifier, abstract, pages, year, booktitle) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (timestamp, timestamp, self.title, self.identifier, self.abstract, self.pages, self.year, self.booktitle))
			DB.commit()

	def insertAndPivot(self, _type):
		C.execute("SELECT * FROM publications WHERE identifier = %s" %(self.identifier))
		record = C.fetchone()
		
		if not record:
			print "INSERTING: " + self.title + " to database"
			timestamp = time.strftime("%Y-%m-%d %H-%M-%S")
			C.execute("INSERT INTO publications (created_at, updated_at, title, identifier, abstract, pages, year, booktitle) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (timestamp, timestamp, self.title, self.identifier, self.abstract, self.pages, self.year, self.booktitle))
			DB.commit()
			
		authors = self.retrieveAuthors()
		
		for author in authors:
			author.insert()
			
			C.execute("SELECT id FROM people WHERE identifier = %s" %(author.identifier))
			author_id = C.fetchone()
			C.execute("SELECT id FROM publications WHERE identifier = %s" %(self.identifier))
			publication_id = C.fetchone()
			
			C.execute("SELECT * FROM person_publication WHERE person_id = %s AND publication_id = %s AND type = %s", (author_id, publication_id, _type))
			record = C.fetchone()
			
			if not record:
				print "INSERTING PIVOT: " + self.title + " <-> " + author.name
				timestamp = time.strftime("%Y-%m-%d %H-%M-%S")
				C.execute("INSERT INTO person_publication (created_at, updated_at, person_id, publication_id, type) VALUES (%s, %s, %s, %s, %s)", (timestamp, timestamp, author_id, publication_id, _type))
				DB.commit()


def getReviewersFromCommitteePage(page):
	reviewers = Queue.Queue()
	tmp = page.soup.find('h1', {'class': 'PageTitle'}).findNext('h2').findNext('h2').findNext('p').getText().split("\n")
	for item in tmp:
		reviewer = {}
		split = item.split(' (')
		reviewer['name'] = split[0]
		reviewer['affiliation'] = split[1][:-1]
		reviewers.put(reviewer)
		
	return reviewers
	
	
def findAuthorUrl(name, splitName = None):
	searchUrl = 'http://papers.nips.cc/search/?q='
	if splitName is None:
		name = unicodedata.normalize('NFKD', unicode(name)).encode('ascii', 'ignore')
		name = re.sub(r'["|\'][a-zA-Z]+["|\']', '', name)
		name = name.lower()
		
		splitName = name.split(' ')
	
	query = searchUrl + '+'.join(splitName)
	results = WebPage(query)
	soup = results.soup
	
	matches = []
	result = None
	
	tmp = soup.findAll('li')
	for item in tmp:
		if item.h4 is not None:
			if item.h4.a is not None:
				match = {}
				match['url'] = "http://papers.nips.cc" + item.h4.a.get('href')
				match['name'] = item.h4.a.getText().rstrip().lstrip().replace(',','').split(' ')
				intersection = [val for val in match['name'] if val.lower() in splitName]
				match['iVal'] = len(intersection)
				matches.append(match)

	for match in matches:
		if match['iVal'] != 0:
			break
		return findAuthorUrl(name, [splitName[0], splitName[1]])

	maxVal = matches[0]['iVal']
	for i in range(len(matches) - 1, -1, -1): #match in matches: #go backwards since first url found is most accurate
		if matches[i]['iVal'] >= maxVal:
			result = matches[i]['url']
			maxVal = matches[i]['iVal']
			
	return result


def processReviewer(reviewer):
	person = Person(WebPage(findAuthorUrl(reviewer['name'])), reviewer['affiliation'])
	print person.name + " (" + person.affiliation + ")"
	person.insertAndPivot("Reviewer")


def main():
	reviewers = getReviewersFromCommitteePage(WebPage("http://nips.cc/Conferences/2013/Committees"))
	
	while not reviewers.empty():
		reviewer = reviewers.get()
		processReviewer(reviewer)

	NIPS2013 = Book(WebPage("http://papers.nips.cc/book/advances-in-neural-information-processing-systems-26-2013"))
	publications = NIPS2013.publications
	NIPS2013.insertAndPivot()


if __name__ == "__main__":
	main()