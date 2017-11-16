import codecs
from graph_tool.all import *
import sys
import time

def loadGraph(graphPath):
    g = graph_tool.Graph(directed=False)
    g.vertex_properties['type'] = g.new_vertex_property("double") # 0: Not used | 1: terminal vertex | 2: steiner vertex
    g.edge_properties['weight']  = g.new_edge_property("double")
    with codecs.open(graphPath, 'r', 'utf-8') as graphFile:
        lines = graphFile.readlines()

    # Adding all nodes
    numNodes = int([l.split(' ')[-1] for l in lines if l.startswith('Nodes')][0])
    g.add_vertex(numNodes)

    # Adding all edges
    for new_edge in [l for l in lines if l.startswith('E ')]:
        subs = new_edge.split(' ')
        newEdge = g.add_edge(int(subs[1])-1, int(subs[2])-1)
        g.edge_properties['weight'][newEdge] = int(subs[3])

    # Defining terminal vertices
    for new_terminal in [l for l in lines if l.startswith('T ')]:
        subs = new_terminal.split(' ')
        g.vertex_properties['type'][int(subs[1])-1] = 1

    return g


if __name__ == '__main__':
    graphPath = sys.argv[1]

    start_time = time.time()
    g = loadGraph(graphPath)
    print("--- %s seconds ---" % (time.time() - start_time))

    

