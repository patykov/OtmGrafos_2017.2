from graph_tool.all import *
from load_graph import loadGraph
import sys
import time
import numpy as np


def draw_tree(g):
    sub = GraphView(g, vfilt=g.vertex_properties['type'].a==1)
    graph_draw(g, vertex_fill_color=g.vertex_properties['type'], vorder=g.vertex_properties['type'],
        edge_color=g.edge_properties['weight'], 
        output_size=(500, 500),
        output="subgraph-iso-embed.pdf")

def LI(g):
    weight = g.edge_properties['weight']
    tree = min_spanning_tree(g, weights=weight)
    used_edges_weight = [e for i, e in enumerate(weight.a) if tree.a[i]]
    return sum(used_edges_weight)

# def LI(g):
#     v = [i for i in g.vertices() if g.vertex_properties['type'][i] == 0][0]
#     g.vertex_properties['type'][v] = 2
#     edges_weights = [g.edge_properties['weight'][e] for e in v.all_edges()]
#     if len(edges_weights) > 1:
#         sum_two_min = sum(sorted(edges_weights)[:2])
#         if sum_two_min < max(g.edge_properties['weight'].a):
#             return v, True
#         else:
#             return v, False
#     return v, False

def viable(g):
    comp, hist = label_components(g)
    if (len(np.unique(comp.a))==1):
        print(comp.a)
        return True
    return False

def is_connected(g):
    comp, hist = label_components(g)
    if (len(np.unique(comp))==1):
        return True
    return False


if __name__ == '__main__':
    graphPath = sys.argv[1]

    start_time = time.time()
    g = loadGraph(graphPath)
    after_load_graph = time.time()

    # Starting
    connected = False#is_connected(g)
    sub = GraphView(g, vfilt=g.vertex_properties['type'].a==1)
    fobj = LI(sub)
    L = [sub.copy()]
    count = 0

    while len(L)>0:
        print('\nIteration {}'.format(count))
        count+=1
        # Choose a node
        l = L.pop()
        # Get LI
        li = LI(l)
        # Check if is a valid solution
        if viable(l):
            print('Is viable')
            fobj = min(fobj, li)
            print(fobj)

        not_seen = [i for i in g.vertices() if g.vertex_properties['type'][i] == 0]
        if len(not_seen) > 0:
            new_v = np.random.choice(not_seen)
            g.vertex_properties['type'][new_v] = -1

            # Right 
            sub_right = g.copy()
            sub_right = GraphView(sub_right, vfilt=sub_right.vertex_properties['type'].a>0)
            print('right: {}'.format(len([v for v in sub_right.vertices()])))
            L.append(sub_right)

            # Left
            sub_left = g.copy()
            sub_left.vertex_properties['type'][new_v] = 2
            sub_left = GraphView(sub_left, vfilt=sub_left.vertex_properties['type'].a>0)
            print('left: {}'.format(len([v for v in sub_left.vertices()])))
            L.append(sub_left)
            



    # draw_tree(g)
    print('Total iterations: {}, fobj: {}'.format(count, fobj))
    print("--- %s seconds --- end" % (time.time() - after_load_graph))


    

