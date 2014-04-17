#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import json
import re
import time
import Queue
import threading
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
		pass
	
	def retrievePublications(self):
		publications = Queue.Queue()
		for li in self.soup.find_all('ul')[1].find_all('li'):
			url = BASE_URL + li.a.get('href')
			publication = Publication(WebPage(url))
			print "Adding %s to publications Queue" %url
			publications.put(publication)
		
		return publications
	

class Person(object):
	'''An author, editor, or reviewer of a NIPS publication'''
	
	def __init__(self, _page, _affiliation = None):
		self.page = _page
		self.url = _page.url
		self.soup = _page.soup
		self.name = self.retrieveName()
		self.identifier = self.retrieveIdentifier()
		self.publications = self.retrievePublications()
	
	def retrieveName(self):
		return self.soup.find('h2', {'class': 'subtitle'}).getText()

	def retrieveIdentifier(self):
		return str(re.findall(r"-[0-9]+", self.url)[0])[:-1]
	
	def retrievePublications(self):
		publications = Queue.Queue()
		for li in self.soup.findAll('li')[1:]:
			url = BASE_URL + li.a.get('href')
			publication = Publication(WebPage(url))
			publications.put(publication)
			
		return publications
		
	def insert(self):
		pass
	

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
		self.authors = self.retrieveAuthors()
		
	def retrieveBibtex(self):
		bibtex_url = self.url + '/bibtex'
		self.bibtex_raw = self.page.retrievePage(bibtex_url)
		bib = BibTexParser(self.bibtex_raw)
		bibtex = bib.get_entry_list()
		
		return bibtex[0]
		
	def retrieveTitle(self):
		return self.soup.find('h2', {'class': 'subtitle'}).getText()
		
	def retrieveIdentifier(self):
		return str(re.findall(r"[0-9]+-", self.url)[0])[:-1]
		
	def retrieveAbstract(self):
		return self.soup.find('p', {'class': 'abstract'}).getText()
		
	def retrieveAuthors(self):
		pass
	
	def insert(self):
		pass
	
	
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
	print name
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
	for match in matches:
		if match['iVal'] >= maxVal:
			result = match['url']
			maxVal = match['iVal']
			
	return result
			
def processReviewer(url, affiliation):
	reviewer = Person(WebPage(url), affiliation)
	while not reviewer.publications.empty():
		pub = reviewer.publications.get();
		pub.insert()
	
	
#NIPS2013 = Book(WebPage("http://papers.nips.cc/book/advances-in-neural-information-processing-systems-26-2013"))
#pub = NIPS2013.publications.get()
#print pub.title

reviewers = getReviewersFromCommitteePage(WebPage("http://nips.cc/Conferences/2013/Committees"))

while not reviewers.empty():
	print findAuthorUrl(reviewers.get()['name'])
