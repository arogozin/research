#!/usr/bin/python

from gensim import corpora, models, similarities
import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

#PREPARE DOCUMENTS CORPUS
documents = ["RDC is defined in terms of correlation of random non-linear copula projections; it is invariant with respect to marginal distribution transformations, has low computational cost and is easy to implement: just five lines of R code, included at the end of the paper.",
			"Recently, it has been observed that for many text corpora documents evolve into one another in a smooth way, with some features dropping and new ones being introduced.",
			"Psychophysical experiments have demonstrated that the brain integrates information from multiple sensory cues in a near Bayesian optimal manner.",
			"We implement our idea by large margin learning, and develop an alternating descent algorithm to effectively solve the resultant non-convex optimization problem.",
			"Polynomial optimization problems are inherently hard due to nonconvex objectives and constraints.",
			"Transferring knowledge from known categories to novel classes with no or only a few labels however is far less researched even though it is a common scenario.",
			"Many optimization algorithms have also been developed for this same purpose, but how do they compare to humans in terms of both performance and behavior?",
			"Because the representation matrix is often simultaneously sparse and low-rank, we propose a new algorithm, termed Low-Rank Sparse Subspace Clustering (LRSSC), by combining SSC and LRR, and develops theoretical guarantees of when the algorithm succeeds.",
			"We propose a model for demand estimation in multi-agent, differentiated product settings and present an estimation algorithm that uses reversible jump MCMC techniques to classify agents' types.",
			"Structured sparse estimation has become an important technique in many areas of data analysis."]
			
stoplist = [line.rstrip() for line in open('old/stopwords.txt')]
texts = [[word for word in document.lower().split() if word not in stoplist]
			for document in documents]
all_tokens = sum(texts, [])
tokens_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
texts = [[word for word in text if word not in tokens_once]
			for text in texts]
			
dictionary = corpora.Dictionary(texts)
corpus = [dictionary.doc2bow(text) for text in texts]
corpora.MmCorpus.serialize('nips.mm', corpus)
mm = corpora.MmCorpus('nips.mm')

lda = models.ldamodel.LdaModel(corpus=mm, id2word=dictionary, num_topics=100, update_every=1, chunksize=100, passes=5)
index = similarities.MatrixSimilarity(lda[mm])


#PREPARE QUERY CORPUS
docsQuery1 = ["RDC is defined in terms of correlation of random non-linear copula projections; it is invariant with respect to marginal distribution transformations, has low computational cost and is easy to implement: just five lines of R code, included at the end of the paper.",
			"Recently, it has been observed that for many text corpora documents evolve into one another in a smooth way, with some features dropping and new ones being introduced.",
			"Psychophysical experiments have demonstrated that the brain integrates information from multiple sensory cues in a near Bayesian optimal manner.",
			"We implement our idea by large margin learning, and develop an alternating descent algorithm to effectively solve the resultant non-convex optimization problem."]

texts = [[word for word in document.lower().split() if word not in stoplist]
			for document in docsQuery1]
all_tokens = sum(texts, [])
tokens_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
texts = [[word for word in text if word not in tokens_once]
			for text in texts]

#dictionary = corpora.Dictionary(texts)
corpusQ = [dictionary.doc2bow(text) for text in texts]
corpora.MmCorpus.serialize('nipsQ.mm', corpusQ)
mmQ = corpora.MmCorpus('nipsQ.mm')
vec_lda = lda[mmQ]

print mm
print mmQ
for sims in index[vec_lda]:
	sims = sorted(enumerate(sims), key=lambda item: -item[1])
	print sims

'''
doc = "RDC is defined in terms of correlation of random non-linear copula projections; it is invariant with respect to marginal distribution transformations, has low computational cost and is easy to implement: just five lines of R code, included at the end of the paper."
vec_bow = dictionary.doc2bow(doc.lower().split())
vec_lda = lda[vec_bow]

sims = index[vec_lda]
print sims
print
sims = sorted(enumerate(sims), key=lambda item: -item[1])
print sims
'''

#Find similar texts, get authors of most similar texts, see which author appears the most
