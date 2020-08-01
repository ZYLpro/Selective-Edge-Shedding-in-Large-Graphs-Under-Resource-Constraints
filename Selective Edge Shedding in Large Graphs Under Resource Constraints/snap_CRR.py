import timeit
import random
import snap
import gc


def calDelta(G, compr):
    # initialize deg_u
    deg = {}
    for NI in G.Nodes():
        node = NI.GetId()
        degree = NI.GetInDeg()
        deg[node] = degree * compr
        print("probability", node, "  ", degree * compr)
    return deg


def takeThird(elem):
    return elem[2]


def CRR():
    print("****CRR*****")
    compression = 0.5
    start = timeit.default_timer()
    # phase 1
    print("phase 1 start")
    G = snap.LoadEdgeList(snap.PUNGraph, "Database/ca-GrQc.txt")
    delta_CRR = calDelta(G, compression)

    print("start edgeIS")
    s = timeit.default_timer()
    edgeIS = snap.TIntPrFltH()
    snap.GetBetweennessCentr(G, edgeIS, 1.0)
    e = timeit.default_timer()
    with open("time/caGrQc-CRR.txt", 'a') as file:
        string = "compression:" + str(compression) + " edgeIS time:" + str(e - s) + '\n'
        file.write(string)
    print("end edgeIS")

    P = compression * edgeIS.Len()
    # sort edges by their betweenness Centrality
    edgeIS.SortByDat()
    it = edgeIS.BegI()
    edges = []
    while not it.IsEnd():
        pair = (it.GetKey().GetVal1(), it.GetKey().GetVal2())
        edges.append(pair)
        it.Next()
    edges.reverse()
    del edgeIS
    gc.collect()

    for i in delta_CRR:
        delta_CRR[i] = -delta_CRR[i]
    # initial sampling edge set
    E = []
    E2 = []
    P = round(P)
    print(P)
    i = 0
    print("------")
    for tuple in edges:
        if i <= P:
            E.append(tuple)
            a = tuple[0]
            b = tuple[1]
            data1 = delta_CRR[a]
            data2 = delta_CRR[b]
            delta_CRR[a] = data1 + 1
            delta_CRR[b] = data2 + 1
            i += 1
        else:
            E2.append(tuple)
    print("after phase 1:", delta_CRR)

    # phase 2
    steps = P * 10
    for i in range(steps):
        print("step:", i)
        e1 = random.choice(E)
        e2 = random.choice(E2)

        d1 = abs(delta_CRR[e1[0]] - 1) + abs(delta_CRR[e1[1]] - 1) - abs(delta_CRR[e1[0]]) - abs(delta_CRR[e1[1]])
        delta_CRR[e1[0]] -= 1
        delta_CRR[e1[1]] -= 1
        d2 = abs(delta_CRR[e2[0]] + 1) + abs(delta_CRR[e2[1]] + 1) - abs(delta_CRR[e2[0]]) - abs(delta_CRR[e2[1]])
        if d1 + d2 < 0:
            E.remove(e1)
            E2.append(e1)
            E.append(e2)
            E2.remove(e2)
            # update deg_u
            delta_CRR[e2[0]] += 1
            delta_CRR[e2[1]] += 1
        else:
            delta_CRR[e1[0]] += 1
            delta_CRR[e1[1]] += 1

    print("after phase2:", delta_CRR)
    with open("Data/minGrQc-edges-CRR-0.5.txt", 'w') as file:
        for e in E:
            string = str(e[0]) + " " + str(e[1]) + '\n'
            file.write(string)
    G_CRR = snap.LoadEdgeList(snap.PUNGraph, "Data/minGrQc-edges-CRR-0.5.txt")
    end = timeit.default_timer()

    nodes = G_CRR.Nodes()
    with open("Data/minGrQc-nodes-CRR-0.5.txt", 'w') as file:
        for NI in nodes:
            string = str(NI.GetId()) + '\n'
            file.write(string)

    # cal total delta
    d_CRR = 0
    for i in delta_CRR:
        d_CRR += abs(delta_CRR[i])
    print("CRR delta:", d_CRR)
    print("average delta:", d_CRR / G_CRR.GetNodes())

    print("CRR done")
    with open("time/caGrQc-CRR.txt", 'a') as file:
        string = "compression:" + str(compression) + " time:" + str(end - start) + " node:" + str(G_CRR.GetNodes()) \
                 + " edge:" + str(len(E)) + '\n'
        file.write(string)


if __name__ == '__main__':
    CRR()
