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

class WebPage(object):
    
    url = ''
    html = ''
    soup = ''
    result = ''
    
    def __init__(self, url):
        self.url = url
        self.html = self.retrievePage(self.url)
        self.soup = self.parsePage(self.html)
        
    def retrievePage(self, url):
        request = urllib2.Request(url)
        request.add_header('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36')
        response = urllib2.urlopen(request)
        
        if (response.code == 200):
            return response.read()
        else:
            return 'Error.'

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
            
    def getAuthorIdentifierFromLink(self, url):
        return str(re.findall(r"-[0-9]+", url)[0])[1:]
    
    def getPublicationIdentifierFromLink(self, url):
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

#print getAuthorProfileUrl('Miguel Carreira-Perpiñán')

#page = WebPage('https://nips.cc/Conferences/2012/Committees')
#reviewers = page.getReviewers()

publicationPage = WebPage('http://papers.nips.cc/paper/4192-a-denoising-view-of-matrix-completion')
authors = publicationPage.getPublicationAuthors()
abstract = publicationPage.getPublicationAbstract()

print db.cursor.execute("SELECT * FROM reviewers")