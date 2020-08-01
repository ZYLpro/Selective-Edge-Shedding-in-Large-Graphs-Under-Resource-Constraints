import timeit
import snap

node2supernode = {}  # key: node, value: supernode
supernode2nodelist = {}  # key: supernode, value: nodes in it

# some values
superedge = set()
exist = {}

def UDS():
    compression = 0.6

    start = timeit.default_timer()
    G = snap.LoadEdgeList(snap.PUNGraph, "Database/email-Enron.txt")
    num_of_node = G.GetNodes()
    num_of_edge = G.GetEdges()
    penaltycount = num_of_node * (num_of_node - 1) / 2 - num_of_edge

    s = timeit.default_timer()
    # cal betweenness Centrality of nodes and edges
    nodeIS = snap.TIntFltH()
    edgeIS = snap.TIntPrFltH()
    snap.GetBetweennessCentr(G, nodeIS, edgeIS, 1.0)
    # for edge in Edges:
    #     print("edge: (%d, %d) centrality: %f" % (edge.GetVal1(), edge.GetVal2(), Edges[edge]))
    e = timeit.default_timer()
    with open("time/email-vldb.txt", 'a') as file:
        string = "compression:" + str(compression) + " edgeIS+nodeIS time:" + str(e - s) + '\n'
        file.write(string)
    num = 0
    # for memorization
    # initialize
    seCost = {}
    nseCost = {}
    for edge in edgeIS:
        num += edgeIS[edge]
    for edge in edgeIS:
        edgeIS[edge] /= num
        val1 = edge.GetVal1()
        val2 = edge.GetVal2()
        edge_pair = (val1, val2)
        superedge.add(edge_pair)
        seCost[edge_pair] = 0
        nseCost[edge_pair] = edgeIS[edge]
        exist[edge_pair] = 1
    del edgeIS

    print("start cal pairs")
    pairs = {}
    # get 2-hop neighbors
    for NI in G.Nodes():
        node = NI.GetId()
        for DstNId in NI.GetOutEdges():  # 1-hop
            NI2 = G.GetNI(DstNId)
            for DstNId2 in NI2.GetOutEdges():  # 2-hop
                is1 = nodeIS[node]
                is2 = nodeIS[DstNId2]
                pairs[(node, DstNId2)] = pow(is1, 2) + pow(is2, 2)
    print("end cal pairs")
    del nodeIS
    # sort nodes
    sorted_pairs = sorted(pairs.items(), key=lambda x: (x[1], x[0][1]))
    del pairs
    print("over")

    # initialize supernodes
    for NI in G.Nodes():
        node = NI.GetId()
        node2supernode[node] = node
        supernode2nodelist[node] = [node, ]

    num_of_compression = compression * num_of_edge
    # print("initial edge num:", num_of_edge)
    # print("target edge num:", num_of_compression)

    EU = 1
    while num_of_edge > num_of_compression and len(sorted_pairs) > 0:
        tuple = sorted_pairs.pop(0)
        a = tuple[0][0]  # a<b
        b = tuple[0][1]
        if node2supernode[a] != node2supernode[b]:
            # merge a and b
            label_a = node2supernode[a]
            label_b = node2supernode[b]
            label_new = str(label_a) + "," + str(label_b)

            node_list1 = supernode2nodelist[label_a]
            node_list2 = supernode2nodelist[label_b]
            for node in node_list1:
                node2supernode[node] = label_new
            for node in node_list2:
                node2supernode[node] = label_new
            # update nodes in ab
            node_list = node_list1 + node_list2
            # add it to the set
            supernode2nodelist[label_new] = node_list

            # RN
            RN = (num_of_node - len(supernode2nodelist.keys()) + 2) / num_of_node

            neighbor_list2 = []
            for node in node_list:
                neighbors = []
                NI = G.GetNI(node)
                for DstNId in NI.GetOutEdges():
                    neighbors.append(DstNId)
                neighbor_list2 = set(neighbor_list2) | set(neighbors)

            neighbor_list = set(neighbor_list2) - set(node_list)

            super_neighbor_list = [node2supernode[x] for x in neighbor_list]
            super_neighbor_list = list(set(super_neighbor_list))

            penalty_list = {}
            isConnect_list = {}
            all_neighbors = []
            for supernode in super_neighbor_list:
                tuple = (label_new, supernode)  # use the formula
                tuple_a = (label_a, supernode)
                tuple_a2 = (supernode, label_a)
                tuple_b = (label_b, supernode)
                tuple_b2 = (supernode, label_b)
                tupleA = tuple_a
                tupleB = tuple_b
                if tuple_a2 not in superedge:
                    if tuple_a not in superedge:  # first time to cal
                        seCost[tupleA] = len(supernode2nodelist[label_a]) * len(
                            supernode2nodelist[supernode]) / penaltycount
                        nseCost[tupleA] = 0
                        exist[tupleA] = 0
                    else:
                        superedge.remove(tupleA)
                else:
                    tupleA = tuple_a2
                    superedge.remove(tupleA)
                all_neighbors.append(tupleA)

                if tuple_b2 not in superedge:
                    if tuple_b not in superedge:
                        seCost[tupleB] = len(supernode2nodelist[label_b]) * len(
                            supernode2nodelist[supernode]) / penaltycount
                        nseCost[tupleB] = 0
                        exist[tupleB] = 0
                    else:
                        superedge.remove(tupleB)
                else:
                    tupleB = tuple_b2
                    superedge.remove(tupleB)
                all_neighbors.append(tupleB)

                superedge.add(tuple)
                seCost[tuple] = seCost[tupleA] + seCost[tupleB]
                nseCost[tuple] = nseCost[tupleA] + nseCost[tupleB]

                del seCost[tupleA]
                del seCost[tupleB]
                del nseCost[tupleA]
                del nseCost[tupleB]

                if seCost[tuple] <= nseCost[tuple]:
                    penalty_list[tuple] = seCost[tuple]
                    isConnect_list[tuple] = 1
                else:
                    penalty_list[tuple] = nseCost[tuple]
                    isConnect_list[tuple] = 0

            penalty_list = sorted(penalty_list.items(), key=lambda x: x[1])
            for temp in penalty_list:
                EU -= temp[1]
                if isConnect_list[temp[0]] == 1:  # connect
                    exist[temp[0]] = 1
                    nseCost[temp[0]] -= seCost[temp[0]]

                    if exist[all_neighbors[0]] == 0:
                        num_of_edge += 1
                    if exist[all_neighbors[1]] == 0:
                        num_of_edge += 1
                    num_of_edge -= 1

                else:
                    exist[temp[0]] = 0
                    seCost[temp[0]] -= nseCost[temp[0]]
                    if exist[all_neighbors[0]] == 1:
                        num_of_edge -= 1
                    if exist[all_neighbors[1]] == 1:
                        num_of_edge -= 1
                del exist[all_neighbors[0]]
                del exist[all_neighbors[1]]
                all_neighbors.pop(0)
                all_neighbors.pop(0)

            # self
            tuple1 = (label_a, label_a)
            tuple21 = (label_a, label_b)
            tuple22 = (label_b, label_a)
            tuple2 = tuple21
            tuple3 = (label_b, label_b)
            if tuple1 not in superedge:
                seCost[tuple1] = len(supernode2nodelist[label_a]) * (
                        len(supernode2nodelist[label_a]) - 1) / (penaltycount * 2)
                nseCost[tuple1] = 0
                exist[tuple1] = 0
            else:
                superedge.remove(tuple1)

            if tuple22 not in superedge:
                if tuple21 not in superedge:
                    seCost[tuple2] = len(supernode2nodelist[label_a]) * len(supernode2nodelist[label_b]) / penaltycount
                    nseCost[tuple2] = 0
                    exist[tuple2] = 0
                else:
                    superedge.remove(tuple2)
            else:
                tuple2 = tuple22
                superedge.remove(tuple2)

            if tuple3 not in superedge:
                seCost[tuple3] = len(supernode2nodelist[label_b]) * (
                        len(supernode2nodelist[label_b]) - 1) / (penaltycount * 2)
                nseCost[tuple3] = 0
                exist[tuple3] = 0
            else:
                superedge.remove(tuple3)

            tuple4 = (label_new, label_new)
            superedge.add(tuple4)
            seCost[tuple4] = seCost[tuple1] + seCost[tuple2] + seCost[tuple3]
            nseCost[tuple4] = nseCost[tuple1] + nseCost[tuple2] + nseCost[tuple3]
            del seCost[tuple1]
            del seCost[tuple2]
            del seCost[tuple3]
            del nseCost[tuple1]
            del nseCost[tuple2]
            del nseCost[tuple3]

            if seCost[tuple4] < nseCost[tuple4]:
                exist[tuple4] = 1
                EU -= seCost[tuple4]
                nseCost[tuple4] -= seCost[tuple4]
                if exist[tuple1] == 0:
                    num_of_edge += 1
                if exist[tuple2] == 0:
                    num_of_edge += 1
                if exist[tuple3] == 0:
                    num_of_edge += 1
                num_of_edge -= 2
            else:
                exist[tuple4] = 0
                EU -= nseCost[tuple4]
                seCost[tuple4] -= nseCost[tuple4]
                if exist[tuple1] == 1:
                    num_of_edge -= 1
                if exist[tuple2] == 1:
                    num_of_edge -= 1
                if exist[tuple3] == 1:
                    num_of_edge -= 1
            del exist[tuple1]
            del exist[tuple2]
            del exist[tuple3]
            # delete supernode a and b
            supernode2nodelist.pop(label_a)
            supernode2nodelist.pop(label_b)
        print(str(num_of_edge))

    getNodeAndEdge()
    end = timeit.default_timer()
    with open("time/email-vldb.txt", 'a') as file:
        string = "RN:" + str(RN) + " EU:" + str(EU) + " edgenumber:" + str(num_of_edge) \
                 + " compression:" + str(compression) + " time:" + str(end - start) + '\n'
        file.write(string)


def getNodeAndEdge():
    superedges = []
    supernodes = []
    for i in supernode2nodelist.keys():
        supernodes.append(i)
    for i in superedge:
        if i in exist.keys() and exist[i] == 1:
            a = i[0]
            b = i[1]
            if a in supernodes and b in supernodes:
                superedges.append(i)

    with open("Data/minEmail-nodes-0.6.txt", "w") as file:
        for i in supernodes:
            file.write(str(i) + '\n')
    with open("Data/minEmail-edges-0.6.txt", "w") as file2:
        for i in superedges:
            file2.write(str(i[0]) + " " + str(i[1]) + '\n')


if __name__ == '__main__':
    UDS()
