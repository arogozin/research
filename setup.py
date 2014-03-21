#!/usr/bin/python

from gensim import corpora, models, similarities
import logging, os
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

def get_txts(path):
	txtlist = []
	for dirname, dirnames, filenames in os.walk(path):
		for filename in filenames:
			if filename.endswith('.txt'):
				txtlist.append(os.path.join(dirname, filename))
	return txtlist

filePath = "docs/"
txts = get_txts(filePath)

#load converted pdfs into a documents list
documents = []
for txt in txts:
	doc = open(txt,'r')
	print "Adding %s to documents." %txt
	documents.append(doc.read())
	doc.close()

#remove common words and tokenize
print "Removing stopwords"
stoplist = [line.rstrip() for line in open('stopwords.txt')]
print "Tokenizing"
texts = [[word for word in document.lower().split() if word not in stoplist]
			for document in documents]

#remove words that only appear once -- this takes forever
print "Removing single-appearance words"
all_tokens = sum(texts, [])
tokens_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
texts = [[word for word in text if word not in tokens_once]
			for text in texts]

#create and save a dictionary of all processed documents (now texts)
dictionary = corpora.Dictionary(texts)
dictionary.save("genObjects/nips.dict")

#create and save a corpus of texts
corpus = [dictionary.doc2bow(text) for text in texts]
corpora.MmCorpus.serialize('genObjects/nips.mm', corpus)

'''
class MyCorpus(object):
	def __iter__(self):
		for line in open('docs/NIPS2012_0048.txt')
			#this assumes there is one document per line in the file, this cannot do!
			yield dictionary.doc2bow(line.lower().split())
		for dirname, dirnames, filenames in os.walk(path):
			for filename in filenames:
				if filename.endswith('.txt'):
					doc = open(os.path.join(dirname, filename,'r')
						yield dictionary.doc2bow(doc.lower().split())

# remove common words and tokenize
stoplist = [line.rstrip() for line in open('stopwords.txt')]

dictionary = corpora.Dictionary(line.lower().split() for line in open('docs/NIPS2012_0048.txt'))
stop_ids = [dictionary.token2id[stopword] for stopword in stoplist
            if stopword in dictionary.token2id]
once_ids = [tokenid for tokenid, docfreq in dictionary.dfs.iteritems() if docfreq == 1]
dictionary.filter_tokens(stop_ids + once_ids) # remove stop words and words that appear only once
dictionary.compactify() # remove gaps in id sequence after words that were removed
dictionary.save('genObjects/test.dict')
print(dictionary)

corpus = MyCorpus
corpora.MmCorpus.serialize('genObjects/test.mm', corpus)
'''