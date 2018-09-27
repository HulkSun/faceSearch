import numpy as np


def cosine_distance(vector_a, vector_b):
    vector_a = np.mat(vector_a)
    vector_b = np.mat(vector_b)
    num = float(vector_a * vector_b.T)
    denom = np.linalg.norm(vector_a) * np.linalg.norm(vector_b)
    cos = num / denom
    sim = cos * 0.5 + 0.5
    return sim


def euclidean_distance(vector_a, vector_b):
    return np.sqrt(np.sum(np.square(np.mat(vector_a) - np.mat(vector_b))))


def cal_sim(vector_a, vector_b, switch=1):
    if switch:
        return cosine_distance(vector_a, vector_b)
    else:
        return euclidean_distance(vector_a, vector_b)
