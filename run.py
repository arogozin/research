#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import json
import re
import time
import codecs
from bs4 import BeautifulSoup
import json
from multiprocessing import Lock, Process, Queue, current_process
import unicodedata
import mysqlconn as db
from bibtexparser.bparser import BibTexParser

class WebPage(object):
	
	url = ''
	html = ''
	soup = ''
	
	def __init__(self, url):
		self.url = url
		self.html = self.retrievePage(self.url).read()
		self.soup = self.parsePage(self.html)
	
	
	def retrievePage(self, url):
		request = urllib2.Request(url)
		request.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36')
		response = urllib2.urlopen(request)
		
		if (response.code == 200):
			return response
		else:
			return 'Error.'
	
	
	def parsePage(self, html):
		soup = BeautifulSoup(html)
		
		return soup
	
	def getSoup(self):
		return self.soup;
		
	def getUrl(self):
		return self.url;
	

class YQL(object):
	
	url = ''
	xpath = ''
	result = ''
	
	def __init__(self, url, xpath = ''):
		self.url = url
		self.xpath = xpath
		
		baseUrl  = "https://query.yahooapis.com/v1/public/yql?q="
		query = 'select * from html where url="'+ url +'"'
		if xpath != '':
			query += ' and xpath = "'+ xpath +'"'
		parameters = "&format=json&diagnostics=true&env=store://datatables.org/alltableswithkeys&callback="
		
		requestUrl = baseUrl + urllib2.quote(query.encode("utf8")) + parameters
		self.json = json.loads(self.retrievePage(requestUrl).read())['query']
	
	def retrievePage(self, url):
		request = urllib2.Request(url)
		request.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36')
		response = urllib2.urlopen(request)
		
		if (response.code == 200):
			return response
		else:
			return 'Error.'

class Reviewer(object):
	
	name = ''
	url = ''
	identifier = ''
	
	def __init__(self, name):
		self.name = name
	
	def find(self, splitName = None):
		baseUrl = 'http://papers.nips.cc/search/?q='
		
		if splitName is None:
			name = unicodedata.normalize('NFKD', unicode(self.name)).encode('ascii', 'ignore')
			name = re.sub(r'["|\'][a-zA-Z]+["|\']', '', name)
			
			splitName = name.split(' ')
		
		query = baseUrl + '+'.join(splitName)
		matches = self.findMatches(query)
		
		#return matches;
		#nameMatch = list(max([set(tmp['name']) & set(splitName) for tmp in matches]))
		#print nameMatch
		#until we figure out how to get a proper match...
		
		match = matches[0]
		self.url = "http://papers.nips.cc" + match["link"]
		
		return match
	
	def findMatches(self, query):
		yql = YQL(query, '/html/body/div/div/ul/li/h4/a')
		json = yql.json
		
		results = []
		
		for result in json['results']['a']:
			if '/author/' in result['href']:
				tmp = {}
				tmp['name'] = result['content'].replace(',', '').split(' ')
				tmp['link'] = result['href']
				results.append(tmp)
		return results
		
	def insertPublications(self):
		rev = reviewer.find()
		page = WebPage(self.url);
		
		publications = getPublicationsFromAuthorPage(page)
		
		for publication in publications:
			publication.insert()

#rather than having everything in webpage
class Publication(object):
	
	page = ''
	url = ''
	bibtex = ''
	
	title = ''
	identifier = ''
	abstract = ''
	pages = ''
	year = ''
	booktitle = ''
	
	def __init__(self, page):
		self.page = page
		self.url = page.getUrl()
		self.soup = page.getSoup()
		self.bibtex = self.retrieveBibtex()
		self.title = self.getTitle()
		self.identifier = self.getIdentifier()
		self.abstract = self.getAbstract()
		self.pages = self.bibtex['pages']
		self.year = self.bibtex['year']
		self.booktitle = self.bibtex['booktitle']
	
	def retrieveBibtex(self):
		bibtex_url = self.url + '/bibtex'
		self.bibtex_raw = self.page.retrievePage(bibtex_url)
		bib = BibTexParser(self.bibtex_raw)
		bibtex = bib.get_entry_list()
		
		return bibtex[0]
		
	def getBibtex(self):
		return self.bibtex
	
	def getTitle(self):
		return self.soup.find('h2', {'class': 'subtitle'}).get_text()
		
	def getIdentifier(self):
		return str(re.findall(r"[0-9]+-", self.url)[0])[:-1]
	
	def getAbstract(self):
		return self.soup.find('p', {'class': 'abstract'}).get_text()
		
	def insert(self):
		#temporary printing
		print self.identifier
		print self.title
		print self.abstract
		print self.pages
		print self.year
		print self.booktitle 
		'''timestamp = str(time.strftime("%Y-%m-%d %H-%M-%S"))
		db.cursor.execute("INSERT INTO publications (identifier, title, abstract, pages, year, booktitle, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", self.idenifier, self.title, self.abstract, self.pages, self.year, self.booktitle, timestamp, timestamp))
		db.conn.commit()'''

def getPublicationsFromAuthorPage(page):
	publications = []
	soup = page.getSoup()
	
	for li in soup.find_all('li')[1:]:
		url = "http://papers.nips.cc" + li.a.get('href')
		print url
		pub = Publication(WebPage(url))
		publications.append(pub)
	
	return publications
	
reviewer = Reviewer('Jacob Abernethy')#('Jennifer Wortman Vaughan')
reviewer.insertPublications()
#print reviewer.find()
