import timeit
import random
import math
import snap
import gc
from queue import PriorityQueue
# from memory_profiler import profile
import sys


def calDelta(G, compr):
    # initialize deg_u
    print("start probability")
    deg = {}
    for NI in G.Nodes():
        node = NI.GetId()
        deg[node] = NI.GetInDeg() * compr
    return deg


class CompareAble:
    def __init__(self, priority, jobname):
        self.priority = priority
        self.jobname = jobname

    def __lt__(self, other):
        return self.priority > other.priority


def BM2():
    print("****BM2*****")
    print("phase 1 start")
    compression = 0.1
    # phase 1
    # rounded the deg_u, and apply b-matching
    start = timeit.default_timer()
    G = snap.LoadEdgeList(snap.PUNGraph, "Database/email-Enron.txt")
    print("G size:", sys.getsizeof(G))
    delta_BM2 = calDelta(G, compression)
    gc.collect()
    round_BM2 = {}
    print("start cal round BM2")
    if compression == 0.5:
        for i in delta_BM2:
            data = random.randint(0, 1)
            if data == 0:
                round_BM2[i] = math.ceil(delta_BM2[i])
            else:
                round_BM2[i] = math.floor(delta_BM2[i])
    else:
        for i in delta_BM2:
            round_BM2[i] = round(delta_BM2[i])
    print("end cal round BM2")
    print("start E/E2")
    G_E2 = snap.PUNGraph.New()
    for EI in G.Edges():
        a = EI.GetSrcNId()
        b = EI.GetDstNId()
        if round_BM2[a] >= 1 and round_BM2[b] >= 1:
            round_BM2[a] -= 1
            round_BM2[b] -= 1
        else:
            if not G_E2.IsNode(a):
                G_E2.AddNode(a)
            if not G_E2.IsNode(b):
                G_E2.AddNode(b)
            G_E2.AddEdge(a, b)

    print("E2 size", sys.getsizeof(G_E2))
    print("phase 2 start")
    # phase2
    # calculate dis_u, do vertices classification.
    A = set()
    B = set()
    for NI in G.Nodes():
        node = NI.GetId()
        delta_BM2[node] = -delta_BM2[node] + round(delta_BM2[node]) - round_BM2[node]
        if delta_BM2[node] <= -0.5:
            A.add(node)
        elif -0.5 < delta_BM2[node] < 0:
            B.add(node)
    del round_BM2
    gc.collect()

    queue = PriorityQueue()
    print("Choose edges whose gains>0")
    i = 1
    for EI in G_E2.Edges():
        print(i)
        i += 1
        a = EI.GetSrcNId()
        b = EI.GetDstNId()
        gain1 = abs(delta_BM2[a]) + 2 * abs(delta_BM2[b]) - abs(1 + delta_BM2[a]) - 1
        if gain1 > 0:
            if a in A and b in B and gain1 > 0:
                queue.put(CompareAble(gain1, (a, b)))
        else:
            gain2 = abs(delta_BM2[b]) + 2 * abs(delta_BM2[a]) - abs(1 + delta_BM2[b]) - 1
            if gain2 > 0:
                if a in B and b in A and gain2 > 0:
                    queue.put(CompareAble(gain2, (b, a)))
    del A
    del B

    gc.collect()
    # bipartite
    # sort edges by gains
    print("start bipartite")
    G_Ebp = snap.PUNGraph.New()
    while not queue.empty():
        e = queue.get()
        a = e.jobname[0]
        b = e.jobname[1]

        if not G_Ebp.IsNode(a):
            G_Ebp.AddNode(a)
        if not G_Ebp.IsNode(b):
            G_Ebp.AddNode(b)
        G_Ebp.AddEdge(a, b)

        queue_temp = PriorityQueue()
        while not queue.empty():
            obj = queue.get()
            if obj.jobname[1] != b:
                queue_temp.put(obj)
        delta_BM2[a] += 1
        delta_BM2[b] += 1
        if -1 < delta_BM2[a] < -0.5:
            while not queue_temp.empty():
                obj = queue_temp.get()
                if obj.jobname[0] == a:
                    temp_gain = abs(delta_BM2[a]) + 2 * abs(delta_BM2[obj.jobname[1]]) - abs(delta_BM2[a] + 1) - 1
                    temp_gain = round(temp_gain, 3)
                    if temp_gain > 0:
                        queue.put(CompareAble(temp_gain, (obj.jobname[0], obj.jobname[1])))
        elif delta_BM2[a] > -0.5:
            while not queue_temp.empty():
                obj = queue_temp.get()
                if obj.jobname[0] != a:
                    queue.put(obj)
    print("bipartite end")
    with open("Data/minEmail-edges-BM2-0.1.txt", 'w') as file:
        for EI in G.Edges():
            a = EI.GetSrcNId()
            b = EI.GetDstNId()
            if not G_E2.IsEdge(a, b):
                string = str(a) + " " + str(b) + '\n'
                file.write(string)
        for EI in G_Ebp.Edges():
            string = str(EI.GetSrcNId()) + " " + str(EI.GetDstNId()) + '\n'
            file.write(string)
    del G_E2
    del G_Ebp
    del G
    G_BM2 = snap.LoadEdgeList(snap.PUNGraph, "Data/minEmail-edges-BM2-0.1.txt")
    end = timeit.default_timer()

    new_nodes = G_BM2.Nodes()
    # E+Ebp
    d_BM2 = 0
    for i in delta_BM2:
        d_BM2 += abs(delta_BM2[i])
    print("BM2 delta:", d_BM2)
    print("average delta:", d_BM2 / G_BM2.GetNodes())
    with open("Data/minEmail-nodes-BM2-0.1.txt", 'w') as file:
        for NI in new_nodes:
            string = str(NI.GetId()) + '\n'
            file.write(string)
    print("BM2 done")

    with open("time/email-BM2.txt", 'a') as file:
        string = "compression:" + str(compression) + " time:" + str(end - start) + " node:" + str(G_BM2.GetNodes()) \
                 + " edge:" + str(G_BM2.GetEdges()) + '\n'
        file.write(string)


if __name__ == '__main__':
    BM2()
