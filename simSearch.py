#!/usr/bin/python

from gensim import corpora, models, similarities
import MySQLdb
import json
from collections import OrderedDict
from operator import itemgetter
import logging
#logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

FILE_PATH = "simObjects/"
CHUNKSIZE = 100
db = MySQLdb.connect(host = "db.arc.poly.edu", user = "research", passwd = "75*London*487", db = "research")
c = db.cursor()


def prettyPrint(obj):

	print json.dumps(obj, indent=4)


def tokenize(stoplist, documents):

	texts = [[word for word in document.lower().split() if word not in stoplist]
			for document in documents]
	all_tokens = sum(texts, [])
	tokens_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
	texts = [[word for word in text if word not in tokens_once]
				for text in texts]
	
	return texts


def generateAndSave(texts, prefix, train = True, dictionary = None):

	if dictionary == None:
		dictionary = corpora.Dictionary(texts)
		dictionary.save(FILE_PATH + prefix + ".dict")
		
	corpus = [dictionary.doc2bow(text) for text in texts]
	corpora.MmCorpus.serialize(FILE_PATH + prefix + ".mm", corpus)
	
	if train:
		mm = corpora.MmCorpus(FILE_PATH + prefix + ".mm")
		lda = models.ldamodel.LdaModel(corpus=mm, id2word=dictionary, num_topics=100, update_every=1, chunksize=CHUNKSIZE, passes=5)
		lda.save(FILE_PATH + prefix + ".lda")
		
		index = similarities.MatrixSimilarity(lda[mm])
		index.save(FILE_PATH + prefix + ".index")
	
	
def printSimSearch(index, vec, numResults):

	print "Enumerated Similarities Matrix:"
	for sims in index[vec]:
		sims = sorted(enumerate(sims), key=lambda item: -item[1])
		print sims[:numResults]
		
	print "Standard Similarities Matrix:"
	for sims in index[vec]:
		print sims[:numResults]


def similaritySearch(index, vec, numResults):
	
	similarities = []
	
	for sims in index[vec]:
		sims = sorted(enumerate(sims), key=lambda item: -item[1])
		similarities.append(sims[:numResults])
		
	return similarities


def fetchReviewers():
	
	reviewers = []
	rev_ids = []
	
	c.execute("SELECT person_id FROM person_publication WHERE type = 'Reviewer'")
	raw_ids = c.fetchall()
	for _id in raw_ids:
		rev_ids.append(_id[0])
	
	rev_ids = list(set(rev_ids)) #remove duplicates
	
	for _id in rev_ids:
		c.execute("SELECT name FROM people WHERE id = " + str(_id))
		reviewer = c.fetchone()
		reviewers.append(reviewer[0])
		
	return reviewers
	

def fetchNipsDocuments(year, limit = None):

	documents = []
	id2doc = []
	
	if limit:
		c.execute("SELECT abstract, id FROM publications WHERE year = %s LIMIT %s" %(year, limit))
	else:
		c.execute("SELECT abstract, id FROM publications WHERE year = " + str(year))
		
	docs = c.fetchall()
	for doc in docs:
		c.execute("SELECT type FROM person_publication WHERE id = " + str(doc[1]))
		personType = c.fetchone()
		if personType != "Reviewer":
			if doc[0] == "Abstract Missing":
				c.execute("SELECT title FROM publications WHERE id = " + str(doc[1]))
				title = c.fetchone()
				documents.append(title[0])
			else:
				documents.append(doc[0])
			id2doc.append(doc[1])

	return documents, id2doc
	

def fetchReviewerDocuments(reviewerName):

	documents = []
	id2doc = []
	
	c.execute('SELECT id FROM people WHERE name = "%s"' %reviewerName)
	reviewer = c.fetchone()
	c.execute("SELECT publication_id FROM person_publication WHERE person_id = %s and type = 'Reviewer'" %reviewer[0])
	publications = c.fetchall()
	for publication in publications:
		c.execute("SELECT abstract FROM publications WHERE id = " + str(publication[0]))
		abstract = c.fetchone()
		if abstract not in documents:
			documents.append(abstract[0])
			id2doc.append(publication[0])
			
	return documents, id2doc


def updateSimList(sim, simTuplesList):
	
	docList = []
	scoreList = []
	
	for _tuple in simTuplesList:
		docList.append(_tuple[0])
		scoreList.append(_tuple[1])
	
	if sim[0] not in docList:
		simTuplesList[scoreList.index(min(scoreList))] = sim
	elif sim[1] > simTuplesList[docList.index(sim[0])][1]:
		simTuplesList[docList.index(sim[0])] = sim
	
	return simTuplesList
	

def getTopTen(similarities):
	
	topTen = []
	
	for sim in similarities[0][:10]:
		topTen.append(sim)
	
	for similarity in similarities[1:]:
		for sim in similarity:
			updateSimList(sim, topTen)
						
	return topTen


def main():

	#PRELIMINARIES
	results = {}
	nipsYear = 2013
	simResults = 10
	
	reviewers = fetchReviewers()
	
	stoplist = [line.rstrip() for line in open('/usr/share/research/old/stopwords.txt')]
	filePrefix = "sim"
	filePrefixQuery = "simQ"
	
	
	#ALL DOCUMENTS
	documents, id2NipsDoc = fetchNipsDocuments(nipsYear)
	
	texts = tokenize(stoplist, documents)
	generateAndSave(texts, filePrefix)
	
	dictionary = corpora.Dictionary.load(FILE_PATH + filePrefix + ".dict")
	lda = models.LdaModel.load(FILE_PATH + filePrefix + ".lda")
	index = similarities.MatrixSimilarity.load(FILE_PATH + filePrefix + ".index")
	
	
	#REVIEWER DOCUMENTS
	for name in reviewers:
		reviewerDocs, id2RevDoc = fetchReviewerDocuments(name)
			
		reviewerTexts = tokenize(stoplist, reviewerDocs)
		generateAndSave(reviewerTexts, filePrefixQuery, False, dictionary)
		
		mmQ = corpora.MmCorpus(FILE_PATH + filePrefixQuery + ".mm")
		vec_lda = lda[mmQ] #or corpusQ works almost the same way
		
		
		#SIMILARITY PROCESS
		sims = similaritySearch(index, vec_lda, simResults)
		topTen = getTopTen(sims)
	
		data = {}
		for item in topTen:
			c.execute("SELECT title FROM publications WHERE id = " + str(id2NipsDoc[item[0]]))
			publication = c.fetchone()
			data[publication[0]] = str(item[1])
		
		results[name] = OrderedDict(sorted(data.items(), key=itemgetter(1), reverse = True))
	
	prettyPrint(results)
		
	with open('results.txt', 'w') as outfile:
		json.dump(results, outfile)
		
	
if __name__ == "__main__":
	main()