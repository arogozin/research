#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from pattern.en import parsetree, pprint
from pattern.search import search

class Tokenizer:
    
    removeElements = ['IN', 'DT', 'VBG', 'VBZ', 'VBN', 'PRP', 'TO', 'VB']
    tokens = []
    tree = ''
    
    def __init__(self, text):
        self.tree = parsetree(text,
                    tokenize = True,            # Split punctuation marks from words?
                    tags = True,                # Parse part-of-speech tags? (NN, JJ, ...)
                    chunks = True,              # Parse chunks? (NP, VP, PNP, ...)
                    relations = True,           # Parse chunk relations? (-SBJ, -OBJ, ...)
                    lemmata = True,             # Parse lemmata? (ate => eat)
                    encoding = 'utf-8')         # Input string encoding.
        self.tokens = self.tokenize()
        
    def tokenize(self):
        tokens = []
        
        result = []
        
        for topic in self.tree:
            for chunk in topic.chunks:
                if chunk.type == "NP":
                    tmp = [(w.string, w.type) for w in chunk.words if w.type not in self.removeElements]
                    tokens.append(tmp)
        
        tokens = filter(None, tokens)
        
        for token in tokens:
            terms = []
            
            for word in token:
                terms.append(word[0])
        
            result.append(" ".join(terms))
        
        result = list(set(result))
        
        return result
    
    def getTree(self):
        return self.tree
    
    def getTokens(self):
        return self.tokens