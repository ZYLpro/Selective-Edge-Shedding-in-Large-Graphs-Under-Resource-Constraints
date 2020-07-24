import networkx as nx
import node2vec
from gensim.models import Word2Vec
from sklearn.cluster import KMeans



def read_graph(path):
    G = nx.read_edgelist(path)
    for edge in G.edges():
        G[edge[0]][edge[1]]['weight'] = 1
    return G


def learn_embeddings(walks,store, store1):
    walks = [list(map(str, walk)) for walk in walks]
    model = Word2Vec(walks, size=128, window=10, min_count=0, sg=1, workers=1)
    model.wv.save_word2vec_format(store)
    model.save(store1)
    return


def getModel(path, store, store1):
    nx_G = read_graph(path)
    G = node2vec.Graph(nx_G, False, 1, 1)
    G.preprocess_transition_probs()
    walks = G.simulate_walks(10, 100)
    learn_embeddings(walks, store, store1)


def doCluster(store):
    model = Word2Vec.load(store)
    vector = []
    nodes = []
    for node in model.wv.index2word:
        nodes.append(node)
        vector.append(model[node])
    labels = KMeans(n_clusters=5).fit_predict(vector)
    # nodes 和labels 对应
    node2label = {}
    for i in range(len(labels)):
        node2label[nodes[i]] = labels[i]
    print("Kmeans over")
    return node2label


# def domain(path, store, store1):
#     #  第一次生成模型，写入
#     getModel(path, store, store1)
#     model = Word2Vec.load(store1)
#     node2label = Cluster(model)
#     return node2label
#
#
# def doCluster(path, store, store1):
#     # main(path, store, store1)
#     # 直接取模型做聚类
#     model = Word2Vec.load(store1)
#     node2label = Cluster(model)
#     return node2label


# if __name__ == "__main__":
#     # main()
#     model = Word2Vec.load('embedding/ca-GrQc.model')
#     Cluster(model)
