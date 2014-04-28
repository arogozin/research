#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from pattern.en import parsetree, pprint
from pattern.search import search

abstract = 'Despite the large amount of literature on upper bounds on complexity of convex analysis, surprisingly little is known about the fundamental hardness of these problems. The extensive use of convex optimization in machine learning and statistics makes such an understanding critical to understand fundamental computational limits of learning and estimation. In this paper, we study the complexity of stochastic convex optimization in an oracle model of computation. We improve upon known results and obtain tight minimax complexity estimates for some function classes. We also discuss implications of these results to the understanding the inherent complexity of large-scale learning and estimation problems.'

class Tokenizer:
    
    removeElements = ['IN', 'DT', 'VBG', 'VBZ', 'VBN', 'PRP', 'TO', 'VB']
    tokens = []
    tree = ''
    
    def __init__(self, text):
        self.tree = parsetree(abstract,
                    tokenize = True,            # Split punctuation marks from words?
                    tags = True,                # Parse part-of-speech tags? (NN, JJ, ...)
                    chunks = True,              # Parse chunks? (NP, VP, PNP, ...)
                    relations = True,           # Parse chunk relations? (-SBJ, -OBJ, ...)
                    lemmata = True,             # Parse lemmata? (ate => eat)
                    encoding = 'utf-8')         # Input string encoding.
        self.tokens = self.tokenize()
        
        print self.tokens
        
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

tokenizer = Tokenizer(abstract)