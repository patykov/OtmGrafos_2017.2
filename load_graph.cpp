#include <iostream>
#include <utility>
#include <algorithm>
#include <vector>
#include <fstream>
#include <string>

#include "boost/graph/graph_traits.hpp"
#include "boost/graph/adjacency_list.hpp"


struct Vertex{ int is_terminal;};

int main(int argc, char *argv[])
{
    typedef adjacency_list<vecS, vecS, undirectedS, Vertex> Graph;
    typedef std::pair<int, int> Edge;
    vector<Edge> edgeVec;
    vector<int> terminalVertices;

    int aux_add_edge;
    int aux_add_terminal;
    int vertex_t = -1;
    int s = -1;
    int t = -1;

    string filePath = argv[1];
    string line;
    string subs;
    ifstream myfile (filePath);

    if (myfile.is_open()) {
        while ( getline (myfile,line) ) {
            // Adding edge
            if (line.find("E ") != string::npos){
                aux_add_edge = 0;
                istringstream iss(line);
                do {
                    iss >> subs;
                    // Adding source
                    if (aux_add_edge == 1){
                        s = stoi(subs)-1;
                    }
                    // Adding target
                    if (aux_add_edge == 2){
                        t = stoi(subs)-1;
                    }
                    // Adding edge
                    if (aux_add_edge == 3){
                        edgeVec.push_back(Edge(s,t));
                    }
                    aux_add_edge += 1;
                } while (iss);
            }
            // Adding terminal
            if (line.find("T ") != string::npos){
                aux_add_terminal = 0;
                istringstream iss(line);
                do {
                    iss >> subs;
                    // Getting terminal vertex
                    if (aux_add_terminal == 1){
                        vertex_t = stoi(subs)-1;
                        terminalVertices.push_back(vertex_t);
                    }
                    aux_add_terminal += 1;
                } while (iss);
            }
        }
        myfile.close();
    }

    else cout << "Unable to open file"; 

    //Now we can initialize our graph using iterators from our above vector
    Graph g(edgeVec.begin(), edgeVec.end(), num_vertices(g));

    std::pair<vertex_iter, vertex_iter> vp;
    for (vp = vertices(g); vp.first != vp.second; ++vp.first){

        std::cout << index[*vp.first] <<  " " << std::endl;
    }

    for (int v = 0; v<terminalVertices.size(); ++v){
        g[terminalVertices[v]].is_terminal = 1;
    }

    std::cout << num_edges(g) << "\n";
    std::cout << num_vertices(g) << "\n";

    typedef graph_traits<Graph>::edge_iterator edge_iterator;

    std::pair<edge_iterator, edge_iterator> ei = edges(g);
    for(edge_iterator edge_iter = ei.first; edge_iter != ei.second; ++edge_iter) {
        std::cout << "(" << source(*edge_iter, g) << ", " << target(*edge_iter, g) << ")\n";
    }


    // get the property map for vertex indices
    typedef property_map<Graph, vertex_index_t>::type IndexMap;
    IndexMap index = get(vertex_index, g);
    typedef graph_traits<Graph>::vertex_iterator vertex_iter;
    std::pair<vertex_iter, vertex_iter> vp;
    for (vp = vertices(g); vp.first != vp.second; ++vp.first)
      std::cout << index[*vp.first] <<  " " << std::endl;



    // std::cout << "\n";
    // //Want to add another edge between (A,E)?
    // add_edge(A, E, g);

    // //Print out the edge list again to see that it has been added
    // for(edge_iterator edge_iter = ei.first; edge_iter != ei.second; ++edge_iter) {
    //     std::cout << "(" << source(*edge_iter, g) << ", " << target(*edge_iter, g) << ")\n";
    // }

    //Finally lets add a new vertex - remember the verticies are just of type int
    // int F = add_vertex(g);
    // std::cout << F << "\n";

    // //Connect our new vertex with an edge to A...
    // add_edge(A, F, g);

    // //...and print out our edge set once more to see that it was added
    // for(edge_iterator edge_iter = ei.first; edge_iter != ei.second; ++edge_iter) {
    //     std::cout << "(" << source(*edge_iter, g) << ", " << target(*edge_iter, g) << ")\n";
    // }
    return 0;
}