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


def ABM():
    print("****ABM*****")
    print("phase 1 start")
    compression = 0.1
    # phase 1
    # rounded the deg_u, and apply b-matching
    start = timeit.default_timer()
    G = snap.LoadEdgeList(snap.PUNGraph, "Database/email-Enron.txt")
    print("G size:", sys.getsizeof(G))
    delta_ABM = calDelta(G, compression)
    gc.collect()
    round_ABM = {}
    print("start cal round ABM")
    if compression == 0.5:
        for i in delta_ABM:
            data = random.randint(0, 1)
            if data == 0:
                round_ABM[i] = math.ceil(delta_ABM[i])
            else:
                round_ABM[i] = math.floor(delta_ABM[i])
    else:
        for i in delta_ABM:
            round_ABM[i] = round(delta_ABM[i])
    print("end cal round ABM")
    print("start E/E2")
    G_E2 = snap.PUNGraph.New()
    for EI in G.Edges():
        a = EI.GetSrcNId()
        b = EI.GetDstNId()
        if round_ABM[a] >= 1 and round_ABM[b] >= 1:
            round_ABM[a] -= 1
            round_ABM[b] -= 1
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
        delta_ABM[node] = -delta_ABM[node] + round(delta_ABM[node]) - round_ABM[node]
        if delta_ABM[node] <= -0.5:
            A.add(node)
        elif -0.5 < delta_ABM[node] < 0:
            B.add(node)
    del round_ABM
    gc.collect()

    queue = PriorityQueue()
    print("Choose edges whose gains>0")
    i = 1
    for EI in G_E2.Edges():
        print(i)
        i += 1
        a = EI.GetSrcNId()
        b = EI.GetDstNId()
        gain1 = abs(delta_ABM[a]) + 2 * abs(delta_ABM[b]) - abs(1 + delta_ABM[a]) - 1
        if gain1 > 0:
            if a in A and b in B and gain1 > 0:
                queue.put(CompareAble(gain1, (a, b)))
        else:
            gain2 = abs(delta_ABM[b]) + 2 * abs(delta_ABM[a]) - abs(1 + delta_ABM[b]) - 1
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
        delta_ABM[a] += 1
        delta_ABM[b] += 1
        if -1 < delta_ABM[a] < -0.5:
            while not queue_temp.empty():
                obj = queue_temp.get()
                if obj.jobname[0] == a:
                    temp_gain = abs(delta_ABM[a]) + 2 * abs(delta_ABM[obj.jobname[1]]) - abs(delta_ABM[a] + 1) - 1
                    temp_gain = round(temp_gain, 3)
                    if temp_gain > 0:
                        queue.put(CompareAble(temp_gain, (obj.jobname[0], obj.jobname[1])))
        elif delta_ABM[a] > -0.5:
            while not queue_temp.empty():
                obj = queue_temp.get()
                if obj.jobname[0] != a:
                    queue.put(obj)
    print("bipartite end")
    with open("Data/minEmail-edges-ABM-0.1.txt", 'w') as file:
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
    G_ABM = snap.LoadEdgeList(snap.PUNGraph, "Data/minEmail-edges-ABM-0.1.txt")
    end = timeit.default_timer()

    new_nodes = G_ABM.Nodes()
    # E+Ebp
    d_ABM = 0
    for i in delta_ABM:
        d_ABM += abs(delta_ABM[i])
    print("ABM delta:", d_ABM)
    print("average delta:", d_ABM / G_ABM.GetNodes())
    with open("Data/minEmail-nodes-ABM-0.1.txt", 'w') as file:
        for NI in new_nodes:
            string = str(NI.GetId()) + '\n'
            file.write(string)
    print("ABM done")

    with open("time/email-ABM.txt", 'a') as file:
        string = "compression:" + str(compression) + " time:" + str(end - start) + " node:" + str(G_ABM.GetNodes()) \
                 + " edge:" + str(G_ABM.GetEdges()) + '\n'
        file.write(string)


if __name__ == '__main__':
    ABM()
