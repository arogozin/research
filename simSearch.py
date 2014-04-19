#!/usr/bin/python

from gensim import corpora, models, similarities
import MySQLdb
import logging
#logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

FILE_PATH = "simObjects/"

def tokenize(stoplist, documents):

	print "Tokenizing"
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
		lda = models.ldamodel.LdaModel(corpus=mm, id2word=dictionary, num_topics=100, update_every=1, chunksize=1, passes=5) #100
		lda.save(FILE_PATH + prefix + ".lda")
		
		index = similarities.MatrixSimilarity(lda[mm])
		index.save(FILE_PATH + prefix + ".index")
	
	
def similaritySearch(index, vec, numResults):

	print "Enumerated Similarities Matrix:"
	for sims in index[vec]:
		sims = sorted(enumerate(sims), key=lambda item: -item[1])
		print sims[:numResults]
		
	print "Standard Similarities Matrix:"
	for sims in index[vec]:
		print sims[:numResults]


def main():
	db = MySQLdb.connect(host = "db.arc.poly.edu", user = "research", passwd = "75*London*487", db = "research")
	c = db.cursor()

	nipsYear = 2013
	simResults = 10
	reviewerName = "Jacob Abernethy"
	stoplist = [line.rstrip() for line in open('/usr/share/research/old/stopwords.txt')]
	filePrefix = "sim"
	filePrefixQuery = "simQ"
	
	#ALL DOCUMENTS
	documents = []
	c.execute("SELECT abstract FROM publications WHERE year = " + str(nipsYear) + " LIMIT 10")
	docs = c.fetchall()
	for doc in docs:
		documents.append(doc[0])
	
	texts = tokenize(stoplist, documents)
	generateAndSave(texts, filePrefix)
	
	dictionary = corpora.Dictionary.load(FILE_PATH + filePrefix + ".dict")
	lda = models.LdaModel.load(FILE_PATH + filePrefix + ".lda")
	index = similarities.MatrixSimilarity.load(FILE_PATH + filePrefix + ".index")
	
	#REVIEWER DOCUMENTS
	docsQuery = []
	c.execute("SELECT id FROM people WHERE name = '%s'" %reviewerName)
	reviewer = c.fetchone()
	c.execute("SELECT publication_id FROM person_publication WHERE person_id = %s and type = 'Reviewer'" %reviewer[0])
	publications = c.fetchall()
	for publication in publications:
		c.execute("SELECT abstract FROM publications WHERE id = " + str(publication[0]))
		abstract = c.fetchone()
		if abstract not in docsQuery:
			docsQuery.append(abstract[0])
		
	textsQ = tokenize(stoplist, docsQuery)
	generateAndSave(textsQ, filePrefixQuery, False, dictionary)
	
	mmQ = corpora.MmCorpus(FILE_PATH + filePrefixQuery + ".mm")
	vec_lda = lda[mmQ] #or corpusQ works almost the same way
	
	similaritySearch(index, vec_lda, 10)
	
	
if __name__ == "__main__":
	main()