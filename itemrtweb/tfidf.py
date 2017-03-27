import math
import numpy as np

def build_lexicon(corpus):
    lexicon = set()
    for doc in corpus:
        lexicon.update([word for word in doc.split()])
    return lexicon

def tf(term, document):
  return freq(term, document)

def freq(term, document):
  return document.split().count(term)

def l2_normalizer(vec):
    denom = np.sum([el**2 for el in vec])
    return [(el / math.sqrt(denom)) for el in vec]

def numDocsContaining(word, doclist):
    doccount = 0
    for doc in doclist:
        if freq(word, doc) > 0:
            doccount +=1
    return doccount

def idf(word, doclist):
    n_samples = len(doclist)
    df = numDocsContaining(word, doclist)
    return np.log(n_samples / 1+df)

def build_idf_matrix(idf_vector):
    idf_mat = np.zeros((len(idf_vector), len(idf_vector)))
    np.fill_diagonal(idf_mat, idf_vector)
    return idf_mat

def tfidfl2(mydoclist):
    vocabulary = build_lexicon(mydoclist)
    doc_term_matrix = []
    for doc in mydoclist:
        tf_vector = [tf(word, doc) for word in vocabulary]
        doc_term_matrix.append(tf_vector)
    my_idf_vector = [idf(word, mydoclist) for word in vocabulary]
    my_idf_matrix = build_idf_matrix(my_idf_vector)
    doc_term_matrix_tfidf = []
    #performing tf-idf matrix multiplication
    for tf_vector in doc_term_matrix:
        doc_term_matrix_tfidf.append(np.dot(tf_vector, my_idf_matrix))
    doc_term_matrix_tfidf_l2 = []
    for tf_vector in doc_term_matrix_tfidf:
        l2 = l2_normalizer(tf_vector)
        cleannan = [0 if str(x) == 'nan' else x for x in l2]
        doc_term_matrix_tfidf_l2.append(cleannan)

    return my_idf_matrix, doc_term_matrix_tfidf_l2

def tfidftest(mydoclist, my_idf_matrix, vocabulary1):
    vocabulary = build_lexicon(vocabulary1)
    doc_term_matrix = []
    for doc in mydoclist:
        tf_vector = [tf(word, doc) for word in vocabulary]
        doc_term_matrix.append(tf_vector)
    doc_term_matrix_tfidf = []
    for tf_vector in doc_term_matrix:
        doc_term_matrix_tfidf.append(np.dot(tf_vector, my_idf_matrix))
    doc_term_matrix_tfidf_l2 = []
    for tf_vector in doc_term_matrix_tfidf:
        doc_term_matrix_tfidf_l2.append(l2_normalizer(tf_vector))
    return doc_term_matrix_tfidf_l2
