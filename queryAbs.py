#!/usr/bin/python
# -*- coding: utf8 -*-

from gensim import corpora, models, similarities
import os, MySQLdb, re

SIM_THRESHOLD = 0.15

db = MySQLdb.connect(host = "db.arc.poly.edu", user = "research", passwd = "75*London*487", db = "research")
c = db.cursor()

dictionary = corpora.Dictionary.load('genObjects/abstracts/nips.dict')
corpus = corpora.MmCorpus("genObjects/abstracts/nips.mm")
lda = models.LdaModel.load("genObjects/abstracts/nips.lda")
index = similarities.MatrixSimilarity.load("genObjects/abstracts/nips.index")

doc = "We introduce the Randomized Dependence Coefficient (RDC), a measure of non-linear dependence between random variables of arbitrary dimension based on the Hirschfeld-Gebelein-RÃ©nyi Maximum Correlation Coefficient. RDC is defined in terms of correlation of random non-linear copula projections; it is invariant with respect to marginal distribution transformations, has low computational cost and is easy to implement: just five lines of R code, included at the end of the paper."
vec_bow = dictionary.doc2bow(doc.lower().split())
vec_lda = lda[vec_bow]

sims = index[vec_lda]
sims = sorted(enumerate(sims), key=lambda item: -item[1])
#print "Closest Match:"
#print sims[0]

authors = {}

for sim in sims:
    pub_score = sim[1]
    if pub_score >= SIM_THRESHOLD:
        pub_id = sim[0] + 1 #account for start-at-0
        c.execute("SELECT person_id FROM person_publication WHERE publication_id = %s AND type = 'Author'" %pub_id)
        auth_ids = c.fetchall()
        for auth_id in auth_ids:
            if auth_id[0] in authors:
                authors[auth_id[0]] = ((authors[auth_id[0]] + pub_score) / 2) #or add?
            else:
                authors[auth_id[0]] = pub_score

for key,value in authors.items():
	print str(key) + " === " + str(value)

print '-' * 50
authList = sorted(authors, key=authors.get, reverse = True)

for auth in authList:
	print auth
	
print '-' * 50
for key, value in sorted(authors.iteritems(), key=lambda (k,v): (v,k), reverse = True):
    print "%s: %s" % (key, value)