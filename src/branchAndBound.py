from graph_tool.all import *
from load_graph import loadGraph
import itertools
import sys
import time
import numpy as np


def draw_tree(tree):
    g_type = g_global.vertex_properties['type']
    v_prop = g_global.new_vertex_property("string")
    for v in g_global.vertices():
        v_prop[v] = str(int(g_type[v]))
    sub = GraphView(g_global, efilt=tree.a==1)
    graph_draw(sub, vertex_fill_color=g_type, vertex_text=v_prop,
        output_size=(500, 500),
        output="../Images/"+name+"_"+str(myTime)+"s.pdf")

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
    num_edges = len(sub.get_vertices())-1
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
    # print(len(g.get_edges()))
    # print(len([v for v in g.vertices() if g.vertex_properties['type'][v] >= 0]))

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

    # Removing the most expensive edge on a cycle
    vertices = [v for v in g.vertices() if g.vertex_properties['type'][v] >= 0]
    for v in vertices[:1]:
        paths = [p for p in all_paths(g, v, v) if len(p)>3]
        # Removing duplicated paths
        set_paths = [set(p) for p in paths]
        for set_p in set_paths:
            same_paths = [i for i, p in enumerate(paths) if set(p)==set_p]
            for sp in same_paths[:-1]:
                del paths[sp]
        edges = [list(itertools.chain(*[g.edge(pj, p[j+1], all_edges=True) for j, pj in enumerate(p[:-1])]))
                 for p in paths]
        max_weights = [max([g.edge_properties['weight'][ej] for ej in e]) for e in edges]
        max_edges = list(itertools.chain(*[[ej for ej in e if g.edge_properties['weight'][ej] == w] 
                    for e, w in zip(edges, max_weights)]))

        for e in np.unique(max_edges):
            ### BUG - Is not removing all of the edges!!! ###
            g.remove_edge(e)

    # print(len(g.get_edges()))
    # print(len([v for v in g.vertices() if g.vertex_properties['type'][v] >= 0]))

def print_time(count, after_branch_bound, after_pos_processing):
    new_text = "../Images/"+name+"_"+str(myTime)+"s.txt"
    with open(new_text, 'w') as file:
        file.write('Total iterations: {}, lim_inf: {}, lim_sup: {}\n'.format(count, li_inf_global, li_sup_global))
        file.write("--- %s seconds --- Load graph\n" % (after_load_graph - start_time))
        file.write("--- %s seconds --- Pre-processing\n" % (after_preprocessing - after_load_graph))
        file.write("--- %s seconds --- Branch and Bound\n" % (after_branch_bound - after_preprocessing))
        file.write("--- %s seconds --- Pos processing\n" % (after_pos_processing - after_branch_bound))
        file.write("--- %s seconds --- All" % (time.time() - start_time))
    raise Exception

def pos_processing():
    global li_inf_global, li_sup_global
    sub = GraphView(g_global, vfilt=g_global.vertex_properties['type'].a>0)
    weight = sub.edge_properties['weight']
    tree = min_spanning_tree(sub, weights=weight, root=root) # Prim
    used_edges = [e for e in sub.edges() if tree[e]]

    vertices = [v for v in sub.vertices() if ((sub.vertex_properties['type'][v] == 2) 
                                        and ((v.out_degree()+v.in_degree())==1))]
    while (len(vertices) > 0):
        for v in vertices:
            edge = [e for e in v.all_edges()][0]
            weight = sub.edge_properties['weight'][edge]
            li_sup_global -= weight
            tree[edge] = 0
        vertices = [v for v in sub.vertices() if ((sub.vertex_properties['type'][v] == 2) 
                                        and ((v.out_degree()+v.in_degree())==1))]
    draw_tree(tree)

def close_and_save():
    after_branch_bound = time.time()
    pos_processing()
    after_pos_processing = time.time()
    print_time(count, after_branch_bound, after_pos_processing)

def branch_and_bound(g):
    global count
    count +=1
    if (time.time() - after_preprocessing) > myTime:
        close_and_save()

     # Get superior LI with vertices that HAVE to be in the solution {1, 2}
    sub_sup = GraphView(g, vfilt=g.vertex_properties['type'].a>0)
    li_sup = LI_superior(sub_sup)
    # Get inferior LI with vertices that are not FORBIDDEN {0, 1, 2}
    sub_inf = GraphView(g, vfilt=g.vertex_properties['type'].a>=0)
    li_inf, next_v = LI_inferior(sub_inf)

    # Check if is a valid solution
    if (is_complete or li_sup['is_viable']):
        # print ('Viable: {}, {}'. format(li_inf, li_sup['value']))
        global li_sup_global, g_global
        if li_sup['value'] < li_sup_global:
            li_sup_global = li_sup['value']
            g_global = g.copy()

        # Found the best solution for the branch!
        if abs(li_sup['value']-li_inf) < 1:
            return li_inf

    not_seen = [i for i in g.vertices() if g.vertex_properties['type'][i] == 0]
    if len(not_seen) > 0:
        next_v = (next_v if next_v != None else np.random.choice(not_seen))

        # # Left
        sub_left = g.copy()
        sub_left.vertex_properties['type'][next_v] = 2
        li_inf_left = branch_and_bound(sub_left)

        # # Right 
        sub_right = g.copy()
        sub_right.vertex_properties['type'][next_v] = -1
        li_inf_right = branch_and_bound(sub_right)

        # Updates global inf_LI
        global li_inf_global
        li_inf_global = max(li_inf_right, li_inf_left, li_inf_global)

    else:
        return li_inf



if __name__ == '__main__':
    graphPath = sys.argv[1]
    myTime = int(sys.argv[2])

    # Load Graph
    start_time = time.time()
    g = loadGraph(graphPath)
    name = graphPath.split('/')[-1].split('.')[0]
    after_load_graph = time.time()

    # Pre-processing
    pre_processing(g)
    is_complete = check_complete(g)
    root = [v for v in g.vertices() if g.vertex_properties['type'][v] == 1][0]
    after_preprocessing = time.time()

    # Starting
    terminals = [v for v in g.vertices() if g.vertex_properties['type'][v]==1]
    sub_sup = GraphView(g, vfilt=g.vertex_properties['type'].a>=0)
    li_sup_global = LI_superior(sub_sup)['value']
    li_inf_global, next_v = LI_inferior(g)
    g_global = g.copy()

    count = 0
    last_li_inf = branch_and_bound(g)

    close_and_save()



# limiete inferioi
# pegar o hnumero minomo de aresta do conj T + possiveis vertices e somar o valor das menores arestas

#pos otimizacao
# remover nos nao terminais de grau 1

    

