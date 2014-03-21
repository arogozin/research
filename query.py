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

#docname = "docs/NIPS2012_1283.txt"
#print "Query on " + docname
#doc = open(docname, 'r').read()
doc = "Keypoint matching between pairs of images using popular descriptors like SIFT or a faster variant called SURF is at the heart of many computer vision algorithms including recognition, mosaicing, and structure from motion. However, SIFT and SURF do not perform well for real-time or mobile applications. As an alternative very fast binary descriptors like BRIEF and related methods use pairwise comparisons of pixel intensities in an image patch. We present an analysis of BRIEF and related approaches revealing that they are hashing schemes on the ordinal correlation metric Kendall’s tau. Here, we introduce Locally Uniform Comparison Image Descriptor (LUCID), a simple description method based on linear time permutation distances between the ordering of RGB values of two image patches. LUCID is computable in linear time with respect to the number of pixels and does not require ﬂoating point computation."
vec_bow = dictionary.doc2bow(doc.lower().split())
vec_lda = lda[vec_bow]

sims = index[vec_lda]
sims = sorted(enumerate(sims), key=lambda item: -item[1])
print "Closest Match:"
print sims[0]

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