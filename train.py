#!/usr/bin/python

import logging, gensim, bz2
logging.basicConfig(format='%(message)s', level=logging.INFO)

dictionary = gensim.corpora.Dictionary.load("genObjects/nips.dict")
print dictionary

corpus = gensim.corpora.MmCorpus("genObjects/nips.mm")
print corpus

lda = gensim.models.ldamodel.LdaModel(corpus=corpus, id2word=dictionary, num_topics=100, update_every=1, chunksize=100, passes=5)
lda.save("genObjects/nips.lda")