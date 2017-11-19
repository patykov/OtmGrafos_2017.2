from graph_tool.all import *
from load_graph import loadGraph
import sys
import time
import numpy as np


def heuristica_1(g):
    sub = GraphView(g, vfilt=g.vertex_properties['type'].a==1, efilt=g.edge_properties['used'].a==1)
    paths = shortest_distance(g, weights=g.edge_properties['weight'])
    count=0
    connected, comp = is_connected(sub)

    while (not connected):
        used_v = [v for v in sub.vertices()]
        for v in used_v:
            print(comp[v])
        wanted_paths = [[paths[i], comp[i]] for i in used_v]
        [s, t] = get_min_path(wanted_paths, comp.a, used_v)
        new_vertices, new_edges = shortest_path(g, g.vertex(s), g.vertex(t), weights=g.edge_properties['weight'])
        for v in new_vertices:
            if g.vertex_properties['type'][v] == 0:
                g.vertex_properties['type'][v] = 2
        for e in new_edges:
            g.edge_properties['used'][e] = 1
        sub = GraphView(g, vfilt=g.vertex_properties['type'].a>0, efilt=g.edge_properties['used'].a==1)
        connected, comp = is_connected(sub)
        print('It: {} vertices: {} edges: {}'. format(count, len([v for v in sub.vertices()]), len([e for e in sub.edges()])))
        time.sleep(2)
        # break
        count+=1

    print(min_spanning_tree(sub, weights=sub.edge_properties['weight']))


def get_min_path(wanted_paths, comps, used_v):
    min_paths = []
    for [p, comp] in wanted_paths:
        pi = [[int(i), p_] for i, p_ in enumerate(p) if ((i in used_v) and (comps[i] != comp))]
        s = min(pi, key=lambda x: x[1])
        print(s)
        pi.remove(s)
        t = min(pi, key=lambda x: x[1])
        print(t)
        min_paths.append([[s[0],t[0]], t[1]])
    min_path = min(min_paths, key=lambda x: x[1])
    print(min_paths)
    print(min_path, comps[min_path[0][0]], comps[min_path[0][1]])
    return min_path[0]


def is_connected(g):
    comp, hist = label_components(g)
    if (len(np.unique(comp.a))==1):
        return True, comp
    return False, comp


if __name__ == '__main__':
    graphPath = sys.argv[1]

    start_time = time.time()
    g = loadGraph(graphPath)
    g.edge_properties['used']  = g.new_edge_property("bool")
    after_load_graph = time.time()

    r1 = heuristica_1(g)

    print("--- %s seconds --- end" % (time.time() - after_load_graph))


    

