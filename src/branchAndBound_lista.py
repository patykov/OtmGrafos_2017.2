import argparse
from graph_tool.all import *
from load_graph import loadGraph
from heuristica import heuristica_1
import itertools
import sys
import time
import numpy as np


def draw_tree(tree):
    global output
    g_type = g_global.vertex_properties['type']
    v_prop = g_global.new_vertex_property("string")
    for v in g_global.vertices():
        v_prop[v] = str(int(g_type[v]))
    sub = GraphView(g_global, efilt=tree.a==1)
    graph_draw(sub, vertex_fill_color=g_type, vertex_text=v_prop,
        output_size=(700, 700),
        output=output+".pdf")

def LI_superior(g):
    weight = g.edge_properties['weight']
    tree = min_spanning_tree(g, weights=weight, root=root) # Prim
    used_edges_weight = [e for i, e in enumerate(weight.a) if tree.a[i]]
    used_edges = [e for e in g.edges() if tree[e]]
    connected_v = list(itertools.chain(*[[e.source(), e.target()] for e in used_edges]))
    return {'value': sum(used_edges_weight), 
            'is_viable': set(connected_v).issuperset(set(terminals))}

def LI_inferior(g):
    sub = GraphView(g, vfilt=g.vertex_properties['type'].a>0)
    comp, hist = label_components(sub)
    wanted_comp = comp.a[int(root)]
    num_edges = int(hist[wanted_comp]-1)
    e_weights = [[e, g.edge_properties['weight'][e]] for e in g.edges()]
    e_weights = sorted(e_weights, key=lambda x: x[1])
    li_inf = sum([e[1] for e in e_weights[:num_edges]])
    used_v = list(itertools.chain(*[[e[0].source(), e[0].target()] for e in e_weights[:num_edges]]))
    used_v, count_v = np.unique([v for v in used_v if g.vertex_properties['type'][v]==0], return_counts=True)
    return li_inf, (used_v[np.argmax(count_v)] if len(used_v)>0 else None)

def check_complete(g):
    g2 = complete_graph(len(g.get_vertices()))
    s = similarity(g, g2)
    if (s == 1.0):
        return True
    return False

def pre_processing(g):
    vertices = [v for v in g.vertices() if g.vertex_properties['type'][v] != 1]
    for v in vertices:
        degree = v.out_degree()
        # Removing non-Terminal vertex with dregree 1.
        if degree ==1:
            g.clear_vertex(v)
            g.vertex_properties['type'][v] = -1
        # Changing a non-Terminal vertex with dregree 2 to a new edge 
        # with the corresponding weight of the removed edges from the vertex.
        if degree == 2:
            s, t = [e.target() for e in v.all_edges()]
            new_weight = sum([g.edge_properties['weight'][e] for e in v.all_edges()])
            new_edge = g.add_edge(s,t)
            g.edge_properties['weight'][new_edge] = new_weight
            g.clear_vertex(v)
            g.vertex_properties['type'][v] = -1

def save_time(count, pre_proc, pos_proc, output, after_branch_bound, after_pos_processing):
    new_text = output+".txt"
    with open(new_text, 'w') as file:
        file.write('Total iterations: {}, lim_inf: {}, lim_sup: {}\n'.format(count, li_inf_global, li_sup_global))
        file.write("--- %s seconds --- Load graph\n" % (after_load_graph - start_time))
        if pre_proc:
            file.write("--- %s seconds --- Pre-processing\n" % (after_preprocessing - after_load_graph))
        file.write("--- %s seconds --- Branch and Bound\n" % (after_branch_bound - after_preprocessing))
        if pos_proc:
            file.write("--- %s seconds --- Pos processing\n" % (after_pos_processing - after_branch_bound))
        file.write("--- %s seconds --- All" % (after_pos_processing - start_time))

def pos_processing(li_sup_global, pos_proc):
    sub = GraphView(g_global, vfilt=g_global.vertex_properties['type'].a>0)
    weight = sub.edge_properties['weight']
    tree = min_spanning_tree(sub, weights=weight, root=root) # Prim

    if pos_proc:    
        print('Pos-processing...')
        used_edges = [e for e in sub.edges() if tree[e]]
        vertices = [v for v in sub.vertices() if ((sub.vertex_properties['type'][v] == 2) 
                                            and ((v.out_degree()+v.in_degree())==1))]
        
        while (len(vertices) > 0):
            for v in vertices:
                edge = [e for e in v.all_edges()][0]
                weight = sub.edge_properties['weight'][edge]
                li_sup_global -= weight
                tree[edge] = 0
                sub.clear_vertex(v)
            vertices = [v for v in sub.vertices() if ((sub.vertex_properties['type'][v] == 2) 
                                            and ((v.out_degree()+v.in_degree())==1))]

    return tree

def close_and_save(li_sup_global, count, pre_proc, pos_proc, output):
    after_branch_bound = time.time()
    tree = pos_processing(li_sup_global, pos_proc)
    after_pos_processing = time.time()
    save_time(count, pre_proc, pos_proc, output, after_branch_bound, after_pos_processing)
    print('Drawing tree...')
    draw_tree(tree)
    sys.exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-graphPath', '--graphPath', help='Full path to graph to be loaded.')
    parser.add_argument('-time', '--time', type=int, help='Time in seconds to run the branch and bound algorithm.')
    parser.add_argument('-pre_proc', '--pre_proc', help="Turn on pre-processing.", action='store_true', default=False)
    parser.add_argument('-pos_proc', '--pos_proc', help="Turn on pos-processing.", action='store_true', default=False)
    args = parser.parse_args()
    
    graphPath = args.graphPath
    name = graphPath.split('/')[-1].split('.')[0]
    myTime = args.time
    pre_proc = args.pre_proc
    pos_proc = args.pos_proc

    output = "../Images/B_and_B/{}_{}s{}{}".format(name, str(myTime), ("_pre" if pre_proc else ""), ("_pos" if pos_proc else ""))

    # Load Graph
    print('Loading....')
    start_time = time.time()
    g = loadGraph(graphPath)
    after_load_graph = time.time()

    # Pre-processing
    is_complete = check_complete(g)
    if pre_proc and (not is_complete):
        print('Pre-processing...')
        pre_processing(g)
    root = [v for v in g.vertices() if g.vertex_properties['type'][v] == 1][0]
    after_preprocessing = time.time()

    # Starting
    terminals = [v for v in g.vertices() if g.vertex_properties['type'][v]==1]
    h_g = g.copy()
    li_sup_global, h_count = heuristica_1(h_g, after_preprocessing, 10)
    li_inf_global, next_v = LI_inferior(h_g)
    g_global = h_g
    start_g = g.copy()
    L = [start_g]
    count = 0

    print('Branch and bound...')
    while len(L) > 0:
        if (time.time() - after_preprocessing) > myTime:
            close_and_save(li_sup_global, count, pre_proc, pos_proc, output)

        count +=1
        l = L.pop()

         # Get superior LI with vertices that HAVE to be in the solution {1, 2}
        sub_sup = GraphView(l, vfilt=l.vertex_properties['type'].a>0)
        li_sup = LI_superior(sub_sup)
        # Get inferior LI with vertices that are not FORBIDDEN {0, 1, 2}
        sub_inf = GraphView(l, vfilt=l.vertex_properties['type'].a>=0)
        li_inf, next_v = LI_inferior(sub_inf)
        need_to_explore = True

        # Check if is a valid solution
        if (is_complete or li_sup['is_viable']):
            if li_sup['value'] < li_sup_global:
                li_sup_global = li_sup['value']
                li_inf_global = li_inf
                g_global = l.copy()

            elif li_sup['value'] == li_sup_global:
                if li_inf > li_inf_global:
                    li_inf_global = li_inf
                    g_global = l.copy()

            # Found the best solution for the branch!
            if li_sup['value'] <= li_inf:
                need_to_explore = False
                
        if need_to_explore:
            not_seen = [i for i in l.vertices() if l.vertex_properties['type'][i] == 0]
            if len(not_seen) > 0:
                if next_v == None:
                    v_degrees = [vj.out_degree() for vj in not_seen]
                    next_v = not_seen[np.argmax(v_degrees)]

                # # Right 
                sub_right = l.copy()
                sub_right.vertex_properties['type'][next_v] = -1
                sub_right.clear_vertex(next_v)
                L.append(sub_right)

                # # Left
                sub_left = l.copy()
                sub_left.vertex_properties['type'][next_v] = 2
                L.append(sub_left)

    close_and_save(li_sup_global, count, pre_proc, pos_proc, output)
