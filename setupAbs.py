#!/usr/bin/python

from gensim import corpora, models, similarities
import logging, MySQLdb
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

db = MySQLdb.connect(host = "db.arc.poly.edu", user = "research", passwd = "75*London*487", db = "research")
c = db.cursor()

c.execute("SELECT abstract FROM publications")
abstracts = c.fetchall()

documents = [item[0] for item in abstracts]

#remove common words and tokenize
print "Removing stopwords"
stoplist = [line.rstrip() for line in open('stopwords.txt')]
print "Tokenizing"
texts = [[word for word in document.lower().split() if word not in stoplist]
			for document in documents]

#remove words that only appear once
print "Removing single-appearance words"
all_tokens = sum(texts, [])
tokens_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
texts = [[word for word in text if word not in tokens_once]
			for text in texts]

#create and save a dictionary of all processed documents (now texts)
dictionary = corpora.Dictionary(texts)
print dictionary
dictionary.save("genObjects/abstracts/nips.dict")

#create and save a corpus of texts
corpus = [dictionary.doc2bow(text) for text in texts]
corpora.MmCorpus.serialize('genObjects/abstracts/nips.mm', corpus)

mm = corpora.MmCorpus('genObjects/abstracts/nips.mm')
print mm

lda = models.ldamodel.LdaModel(corpus=mm, id2word=dictionary, num_topics=100, update_every=1, chunksize=100, passes=5)
lda.save("genObjects/abstracts/nips.lda")

index = similarities.MatrixSimilarity(lda[mm])
index.save("genObjects/abstracts/nips.index")