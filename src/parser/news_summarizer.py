from itertools import combinations

import networkx as nx
from nltk.stem.snowball import RussianStemmer
from nltk.tokenize import sent_tokenize, RegexpTokenizer
from transformers import T5ForConditionalGeneration, T5Tokenizer

MODEL_NAME = './result/models_abs_sum/result_third_0'
MAX_INPUT = 512


class NewsSummarizer:
    def __init__(self):
        self.tokenizer_abs = T5Tokenizer.from_pretrained(MODEL_NAME)
        self.model_abs = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)

        self.tokenizer_extr = RegexpTokenizer(r'\w+')
        self.lmtzr = RussianStemmer()

    def get_text_both_sum(self, full_text):
        extr = self.get_text_extract_sum(full_text)
        abst = self.get_text_abstract_sum(extr)
        return abst

    def get_text_abstract_sum(self, full_text):
        input_ids = self.tokenizer_abs.encode(full_text, return_tensors="pt", max_length=512, truncation=True)
        output_ids = self.model_abs.generate(input_ids, max_length=150, num_beams=4, length_penalty=2.0, early_stopping=True)
        result = self.tokenizer_abs.decode(output_ids[0], skip_special_tokens=True)
        return result

    def get_text_extract_sum(self, full_text, n=5):
        tr = self.get_text_rank(full_text)
        top_n = sorted(tr[:n])
        return ' '.join(x[2] for x in top_n)

    def get_text_rank(self, text):
        sentences = sent_tokenize(text)
        words = [set(self.lmtzr.stem(word) for word in self.tokenizer_extr.tokenize(sentence.lower()))
                 for sentence in sentences]
        pairs = combinations(range(len(sentences)), 2)
        scores = [(i, j, self.get_similarity(words[i], words[j])) for i, j in pairs]
        scores = filter(lambda x: x[2], scores)
        g = nx.Graph()
        g.add_weighted_edges_from(scores)
        pr = nx.pagerank(g)
        return sorted(((i, pr[i], s) for i, s in enumerate(sentences) if i in pr), key=lambda x: pr[x[0]], reverse=True)

    @staticmethod
    def get_similarity(s1, s2):
        if not len(s1) or not len(s2):
            return 0.0
        return len(s1.intersection(s2)) / (1.0 * (len(s1) + len(s2)))

