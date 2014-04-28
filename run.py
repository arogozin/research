#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from modules.tokenizer import Tokenizer


abstract = 'Despite the large amount of literature on upper bounds on complexity of convex analysis, surprisingly little is known about the fundamental hardness of these problems. The extensive use of convex optimization in machine learning and statistics makes such an understanding critical to understand fundamental computational limits of learning and estimation. In this paper, we study the complexity of stochastic convex optimization in an oracle model of computation. We improve upon known results and obtain tight minimax complexity estimates for some function classes. We also discuss implications of these results to the understanding the inherent complexity of large-scale learning and estimation problems.'


tokens = Tokenizer(abstract)

print tokens.getTokens()
