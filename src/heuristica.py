import argparse
from graph_tool.all import *
from load_graph import loadGraph
import sys
import time
import numpy as np


def heuristica_1(g, start_time, end_time):
    count=0
    g.edge_properties['used'] =  g.new_edge_property("bool")
    e_used = g.edge_properties['used']
    v_type = g.vertex_properties['type']
    weight = g.edge_properties['weight']
    terminals = [v for v in g.vertices() if v_type[v] == 1]
    sub = GraphView(g, vfilt=v_type.a>0, efilt=e_used.a==1)
    connected, comp = is_connected(sub)

    while (not connected) and (time.time()-start_time < end_time):
        used_v = [v for v in sub.vertices()]

        # GRASP
        if (np.random.random() > 0.7):
            selected = np.random.choice(used_v)
            # Remove vertex from solution if its a steiner vertex
            if v_type[selected] == 2:
                v_type[selected] = 0
            # Remove edges from solution
            for e in selected.all_edges():
                e_used[e] = 0
            used_v.remove(selected)
        
        [s, t] = get_min_paths(g, used_v, comp, terminals)
        new_vertices, new_edges = shortest_path(g, g.vertex(s), g.vertex(t), weights=weight)
        for v in new_vertices:
            if v_type[v] == 0:
                v_type[v] = 2
        for e in new_edges:
            e_used[e] = 1

        sub = GraphView(g, vfilt=v_type.a>0, efilt=e_used.a==1)
        connected, comp = is_connected(sub)
        count+=1

    sol = get_tree_sum(g, terminals[0])

    return sol, count

def get_tree_sum(g, root):
    final_sub = GraphView(g, efilt=g.edge_properties['used'].a==1)
    tree = min_spanning_tree(final_sub, weights=g.edge_properties['weight'], root=root) # Prim
    used_edges_weight = [e for i, e in enumerate(g.edge_properties['weight'].a) if tree.a[i]]
    return sum(used_edges_weight)


def draw_tree(g):
    global output
    g_type = g.vertex_properties['type']
    v_prop = g.new_vertex_property("string")
    for v in g.vertices():
        v_prop[v] = str(int(g_type[v]))
    sub = GraphView(g, efilt=g.edge_properties['used'].a==1)
    graph_draw(sub, vertex_fill_color=g_type, vertex_text=v_prop,
        output_size=(500, 500),
        output=output+".pdf")

def get_min_paths(g, used_v, comp, terminals):
    min_paths = []
    for v in used_v:
        myComp = comp[v]
        targets = [t for t in terminals if comp[t] != myComp]
        if len(targets) > 0:
            paths = shortest_distance(g, source=v, target=targets, weights=g.edge_properties['weight'])
            if len(targets) == 1:
                min_paths.append([[v, targets[0]], paths])
            else:
                paths = [[i, p] for i,p in enumerate(paths) if p != np.inf]
                if len(paths)>0:
                    min_dist = min(paths, key=lambda x: x[1])
                    min_paths.append([[v, targets[min_dist[0]]], min_dist[1]])
    min_path = min(min_paths, key=lambda x: x[1])

    # Randomly selecting a path with de lowest distance
    same_dist = [s for s in min_paths if s[1] == min_path[1]]
    selected_id = np.random.randint(0, len(same_dist))

    return same_dist[selected_id][0]

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

def is_connected(g):
    comp, hist = label_components(g)
    if (len(np.unique(comp.a))==1):
        return True, comp
    return False, comp

def check_complete(g):
    g2 = complete_graph(len(g.get_vertices()))
    s = similarity(g, g2)
    if (s == 1.0):
        return True
    return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-graphPath', '--graphPath', help='Full path to graph to be loaded.')
    parser.add_argument('-time', '--time', type=int, help='Time in seconds to run the branch and bound algorithm.')
    parser.add_argument('-pre_proc', '--pre_proc', help="Turn on pre-processing.", action='store_true', default=False)
    args = parser.parse_args()
    
    graphPath = args.graphPath
    name = graphPath.split('/')[-1].split('.')[0]
    myTime = args.time
    pre_proc = args.pre_proc

    output = "../Images/Heuristica/{}_{}s{}".format(name, myTime, ("_pre" if pre_proc else ""))

    # Loading Graph
    start_time = time.time()
    g = loadGraph(graphPath)
    after_load_graph = time.time()

    # Pre-processing
    is_complete = check_complete(g)
    if (not is_complete) and pre_proc:
        pre_processing(g)
    after_pre_processing = time.time()

    # Heuristica
    sol, count = heuristica_1(g, myTime, after_load_graph)
    after_heuristica = time.time()

    new_text = output+".txt"
    with open(new_text, 'w') as file:
        file.write('Total iterations: {}, Sol: {}\n'.format(count, sol))
        file.write("--- %s seconds --- Load graph\n" % (after_load_graph - start_time))
        if pre_proc:
            file.write("--- %s seconds --- Pre Processing\n" % (after_pre_processing - after_load_graph))
        file.write("--- %s seconds --- Heuristic\n" % (after_heuristica - after_pre_processing))
        file.write("--- %s seconds --- All" % (after_heuristica - start_time))

    # draw_tree(g)


    

