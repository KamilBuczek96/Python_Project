import Edge as E
import Graph as G

graf =G.Graph(10, True)
print("Czy graf jest skierowany ? : ", graf.is_directed())
print("Rozmiar grafu: ",graf.n)

for x in range(graf.n):
    graf.add_node(x)

print("Wektor wierzhcolkow grafu:")
graf.show_vector()

graf.add_edge(E.Edge(0,1,2))
graf.add_edge(E.Edge(0,3,4))
graf.add_edge(E.Edge(0,2,3))
graf.add_edge(E.Edge(1,5,3))
graf.add_edge(E.Edge(2,5,3))
graf.add_edge(E.Edge(3,2,1))
graf.add_edge(E.Edge(3,4,3))
graf.add_edge(E.Edge(2,4,2))
graf.add_edge(E.Edge(5,9,2))
graf.add_edge(E.Edge(4,6,8))
graf.add_edge(E.Edge(9,6,6))
graf.add_edge(E.Edge(4,7,2))
graf.add_edge(E.Edge(7,8,3))

print("Macierz sasiedztwa grafu:")
graf.show_matrix()
print("Liczba krawedzi: ", graf.e())
print("Liczba wierzchołkow: ", graf.v())
graf.iternodes()
print("Sąsiednie wierzchołki: ")
graf.iteradjacent(2)
print("Krawędzie: ")
graf.iteredges()
