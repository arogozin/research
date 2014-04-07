#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib2
import re
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
    result = ''
    bibtex_raw = ''
    
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
    
    def retrieveBibtex(self):
        bibtex_url = self.url + '/bibtex'
        self.bibtex_raw = self.retrievePage(bibtex_url)
        bib = BibTexParser(self.bibtex_raw)
        bibtex = bib.get_entry_list()
        
        return bibtex
        
    def getUrl(self):
        return self.url
    

    def getReviewers(self):
        reviewers = Queue()
        [reviewers.put(item.split(' (')[0]) for item in self.soup.find_all('p')[-1].get_text().split('\n')]        
        return reviewers

    def prepareResult(self, url, soup):
        result = {}
        result['url'] = url
        result['title'] = soup.title.get_text()#.encode('ascii', 'ignore')
        
        return result

    def parsePage(self, html):
        soup = BeautifulSoup(html)
        
        return soup

    def getSoup(self):
        return self.soup
    

    def getPublicationTitle(self):
        return self.soup.find('h2', {'class': 'subtitle'}).get_text()
    

    def getPublicationAuthors(self):
        result = []
        tmp = [author.find('a').get_text() for author in self.soup.findAll('li', {'class': 'author'})]
        for item in tmp:
            author = {}
            author['name'] = item
            author['url'] = getAuthorProfileUrl(item)
            
            result.append(author)
            
        return result

    def getAuthorIdentifierFromLink(self, url = None):
        if url is None:
            return str(re.findall(r"-[0-9]+", self.url)[0])[1:]
        else:
            return str(re.findall(r"-[0-9]+", url)[0])[1:]
    

    def getPublicationIdentifierFromLink(self, url = None):
        if url is None:
            return str(re.findall(r"[0-9]+-", self.url)[0])[:-1]
        else:
            return str(re.findall(r"[0-9]+-", url)[0])[:-1]
    

    def getPublicationAbstract(self):
        return self.soup.find('p', {'class': 'abstract'}).get_text()
    

    def normalizeList(self, inputList):
        result = []
        
        for listItem in inputList:
            item = listItem.encode('utf-8').decode('utf-8')
            item = unicodedata.normalize('NFKD', item).encode('ascii', 'ignore')
            item = re.sub(r'["|\'][a-zA-Z]+["|\']', '', item)
            result.append(item)
        return result
    

    def getConferencePublications(self):
        return ['http://papers.nips.cc' + link.find('a').get('href') for link in self.soup.findAll('ul')[1].findAll('li')]

    

    def getConferenceEditors(self):
        results = []
        
        for item in self.soup.find('br').findAllPrevious('a'):
            if 'author' in item.get('href'):
                author = {}
                author['name'] = item.getText()
                author['url'] = 'http://papers.nips.cc' + item.get('href')
                results.append(author)
        return results
        #return self.soup.find('h2', {'class': 'subtitle'}).findAllNext('a')
        

    def getAuthorPublications(self):
        return ['http://papers.nips.cc' + link.find('a').get('href') for link in self.soup.findAll('li', {'class': 'paper'})]
    


def getAuthorProfileUrl(name, splitName = None, url = None):
    searchBaseUrl = 'http://papers.nips.cc/search/?q='
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore')
    name = re.sub(r'["|\'][a-zA-Z]+["|\']', '', name)
    
    if splitName is None:
        splitName = name.split(' ')
    
    if url is None:
        query = '+'.join(splitName)#name.replace(' ', '+')
        searchUrl = searchBaseUrl + query
        
        results = WebPage(searchUrl)
        soup = results.getSoup()
        
        if soup.h4 is not None:
            if soup.h4.a is not None:
                url = soup.h4.a.get('href')
    
    url = "http://papers.nips.cc" + url
    
    authorUrlName = '-'.join(splitName).replace(' ', '-').replace('.', '').encode('utf-8').decode('utf-8')
    authorUrlName = unicodedata.normalize('NFKD', authorUrlName).encode('ascii', 'ignore')
    authorUrlName = authorUrlName.lower()
    
    if len(splitName) == 1:
        if authorUrlName in url:
            return url
    elif len(splitName) == 2:
        if authorUrlName in url:
            return url
        else:
            return getAuthorProfileUrl(name, [splitName[-1]])
    elif len(splitName) == 3:
        if authorUrlName in url:
            return url
        else:
            result = getAuthorProfileUrl(name, [splitName[0], splitName[1]])
            if (result is None):
                result = getAuthorProfileUrl(name, [splitName[0], splitName[2]])
            if (result is None):
                result = getAuthorProfileUrl(name, [splitName[1], splitName[2]])
            if (result is None):
                return getAuthorProfileUrl(name, [splitName[-1]])
            else:
                return result
    elif len(splitName) == 4:
        if authorUrlName in url:
            return url
        else:
            result = getAuthorProfileUrl(name, [splitName[0], splitName[1], splitName[2]])
            if (result is None):
                result = getAuthorProfileUrl(name, [splitName[0], splitName[1], splitName[3]])
            if (result is None):
                result = getAuthorProfileUrl(name, [splitName[0], splitName[2], splitName[3]])
            if (result is None):
                result = getAuthorProfileUrl(name, [splitName[1], splitName[2], splitName[3]])
            if (result is None):
                return getAuthorProfileUrl(name, [splitName[-1]])
            else:
                return result
    else:
        return None


class Publication(object):
    
    page = ''
    
    def __init__(self, page):
        self.page = page
    
    def insertPublication(self):
        db.cursor.execute("INSERT INTO publications (identifier, title, abstract) VALUES (%s, %s, %s)", (self.page.getPublicationIdentifierFromLink(), self.page.getPublicationTitle(), self.page.getPublicationAbstract()))
        db.conn.commit()
    

# publication = Publication(WebPage('http://papers.nips.cc/paper/4874-inferring-neural-population-dynamics-from-multiple-partial-recordings-of-the-same-neural-circuit'))
# 
# print publication.getPublication()

page = WebPage('http://papers.nips.cc/paper/5140-documents-as-multiple-overlapping-windows-into-grids-of-counts')
pub = Publication(page)
#pub.insertPublication()
print page.retrieveBibtex()
