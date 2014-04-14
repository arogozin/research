#!/usr/bin/python

from gensim import corpora, models, similarities
import MySQLdb
#import logging
#logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

db = MySQLdb.connect(host = "db.arc.poly.edu", user = "research", passwd = "75*London*487", db = "research")
c = db.cursor()

#PREPARE DOCUMENTS CORPUS
documents = []
c.execute("SELECT abstract FROM publications LIMIT 20")
docs = c.fetchall()
for doc in docs:
	documents.append(doc[0])

stoplist = [line.rstrip() for line in open('/usr/share/research/old/stopwords.txt')]
texts = [[word for word in document.lower().split() if word not in stoplist]
			for document in documents]
all_tokens = sum(texts, [])
tokens_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
texts = [[word for word in text if word not in tokens_once]
			for text in texts]

dictionary = corpora.Dictionary(texts)
corpus = [dictionary.doc2bow(text) for text in texts]
corpora.MmCorpus.serialize('smallSim/nips.mm', corpus)
mm = corpora.MmCorpus('smallSim/nips.mm')

lda = models.ldamodel.LdaModel(corpus=mm, id2word=dictionary, num_topics=100, update_every=1, chunksize=1, passes=5)
index = similarities.MatrixSimilarity(lda[mm])

#PREPARE QUERY CORPUS
docsQuery1 = []
c.execute("SELECT abstract FROM publications LIMIT 3")
docs = c.fetchall()
for doc in docs:
	docsQuery1.append(doc[0])

texts = [[word for word in document.lower().split() if word not in stoplist]
			for document in docsQuery1]
all_tokens = sum(texts, [])
tokens_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
texts = [[word for word in text if word not in tokens_once]
			for text in texts]

#corpusQ = [dictionary.doc2bow(doc.lower().split()) for doc in docsQuery1]
corpusQ = [dictionary.doc2bow(text) for text in texts]
corpora.MmCorpus.serialize('smallSim/nipsQ.mm', corpusQ)
mmQ = corpora.MmCorpus('smallSim/nipsQ.mm')
vec_lda = lda[mmQ] #or corpusQ works the same way

#SIM TEST
for sims in index[vec_lda]:
	sims = sorted(enumerate(sims), key=lambda item: -item[1])
	print sims[:10]