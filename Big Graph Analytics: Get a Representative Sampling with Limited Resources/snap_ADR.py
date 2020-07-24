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


def ADR():
    print("****ADR*****")
    compression = 0.5
    start = timeit.default_timer()
    # phase 1
    print("phase 1 start")
    G = snap.LoadEdgeList(snap.PUNGraph, "Database/ca-GrQc.txt")
    delta_ADR = calDelta(G, compression)

    print("start edgeIS")
    s = timeit.default_timer()
    edgeIS = snap.TIntPrFltH()
    snap.GetBetweennessCentr(G, edgeIS, 1.0)
    e = timeit.default_timer()
    with open("time/caGrQc-ADR.txt", 'a') as file:
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

    for i in delta_ADR:
        delta_ADR[i] = -delta_ADR[i]
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
            data1 = delta_ADR[a]
            data2 = delta_ADR[b]
            delta_ADR[a] = data1 + 1
            delta_ADR[b] = data2 + 1
            i += 1
        else:
            E2.append(tuple)
    print("after phase 1:", delta_ADR)

    # phase 2
    steps = P * 10
    for i in range(steps):
        print("step:", i)
        e1 = random.choice(E)
        e2 = random.choice(E2)

        d1 = abs(delta_ADR[e1[0]] - 1) + abs(delta_ADR[e1[1]] - 1) - abs(delta_ADR[e1[0]]) - abs(delta_ADR[e1[1]])
        delta_ADR[e1[0]] -= 1
        delta_ADR[e1[1]] -= 1
        d2 = abs(delta_ADR[e2[0]] + 1) + abs(delta_ADR[e2[1]] + 1) - abs(delta_ADR[e2[0]]) - abs(delta_ADR[e2[1]])
        if d1 + d2 < 0:
            E.remove(e1)
            E2.append(e1)
            E.append(e2)
            E2.remove(e2)
            # update deg_u
            delta_ADR[e2[0]] += 1
            delta_ADR[e2[1]] += 1
        else:
            delta_ADR[e1[0]] += 1
            delta_ADR[e1[1]] += 1

    print("after phase2:", delta_ADR)
    with open("Data/minGrQc-edges-ADR-0.5.txt", 'w') as file:
        for e in E:
            string = str(e[0]) + " " + str(e[1]) + '\n'
            file.write(string)
    G_ADR = snap.LoadEdgeList(snap.PUNGraph, "Data/minGrQc-edges-ADR-0.5.txt")
    end = timeit.default_timer()

    nodes = G_ADR.Nodes()
    with open("Data/minGrQc-nodes-ADR-0.5.txt", 'w') as file:
        for NI in nodes:
            string = str(NI.GetId()) + '\n'
            file.write(string)

    # cal total delta
    d_ADR = 0
    for i in delta_ADR:
        d_ADR += abs(delta_ADR[i])
    print("ADR delta:", d_ADR)
    print("average delta:", d_ADR / G_ADR.GetNodes())

    print("ADR done")
    with open("time/caGrQc-ADR.txt", 'a') as file:
        string = "compression:" + str(compression) + " time:" + str(end - start) + " node:" + str(G_ADR.GetNodes()) \
                 + " edge:" + str(len(E)) + '\n'
        file.write(string)


if __name__ == '__main__':
    ADR()
