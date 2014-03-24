#!/usr/bin/python
# -*- coding: utf8 -*-

from gensim import corpora, models, similarities
import os

dictionary = corpora.Dictionary.load('genObjects/nips.dict')
corpus = corpora.MmCorpus("genObjects/nips.mm")
lda = models.LdaModel.load("genObjects/nips.lda")

'''
index = similarities.MatrixSimilarity(lda[corpus])
index.save("genObjects/nips.index")
'''

index = similarities.MatrixSimilarity.load("genObjects/nips.index")

docname = "docs/NIPS2012_1283.txt"
print "Query on " + docname
doc = open(docname, 'r').read()
vec_bow = dictionary.doc2bow(doc.lower().split())
vec_lda = lda[vec_bow]

sims = index[vec_lda]
sims = sorted(enumerate(sims), key=lambda item: -item[1])
print "Closest Match:"
print sims[0]

''' GET 2013 DOC TRAINING DONE FIRST
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
'''

#VERIFICATION

def get_txts(path):
	txtlist = []
	for dirname, dirnames, filenames in os.walk(path):
		for filename in filenames:
			if filename.endswith('.txt'):
				txtlist.append(os.path.join(dirname, filename))
	return txtlist

filePath = "docs/"
txts = get_txts(filePath)

print str(sims[0][0]) + " -> " + txts[sims[0][0]]

for i in range(20):
	print str(sims[i]) + " -> " + txts[sims[i][0]]
	
if txts[sims[0][0]] == docname:
	print "SUCCESS"
else:
	print "COMPLETE AND UTTER FAILURE"