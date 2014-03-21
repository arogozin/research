#!/usr/bin/python
# -*- coding: utf8 -*-

from gensim import corpora, models, similarities
import os

dictionary = corpora.Dictionary.load('genObjects/abstracts/nips.dict')
corpus = corpora.MmCorpus("genObjects/abstracts/nips.mm")
lda = models.LdaModel.load("genObjects/abstracts/nips.lda")
index = similarities.MatrixSimilarity.load("genObjects/abstracts/nips.index")

doc = "Structured sparse estimation has become an important technique in many areas of data analysis. Unfortunately, these estimators normally create computational difficulties that entail sophisticated algorithms. Our first contribution is to uncover a rich class of structured sparse regularizers whose polar operator can be evaluated efficiently. With such an operator, a simple conditional gradient method can then be developed that, when combined with smoothing and local optimization, significantly reduces training time vs. the state of the art. We also demonstrate a new reduction of polar to proximal maps that enables more efficient latent fused lasso."
vec_bow = dictionary.doc2bow(doc.lower().split())
vec_lda = lda[vec_bow]

sims = index[vec_lda]
sims = sorted(enumerate(sims), key=lambda item: -item[1])
print "Closest Match:"
print sims[0]