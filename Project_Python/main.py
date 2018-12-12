import Edge as E
import Graph as G

graf =G.Graph(7, False)
print("Czy graf jest skierowany ? : ", graf.is_directed())
print("Rozmiar grafu: ",graf.n)

for x in range(graf.n):
    graf.add_node(x)

print("Wektor wierzhcolkow grafu:")
graf.show_vector()

graf.add_edge(E.Edge(0,2,1))
graf.add_edge(E.Edge(0,6,1))
graf.add_edge(E.Edge(2,6,1))
graf.add_edge(E.Edge(6,3,1))
graf.add_edge(E.Edge(3,5,1))
graf.add_edge(E.Edge(0,4,1))
graf.add_edge(E.Edge(1,5,1))
graf.add_edge(E.Edge(4,3,1))
graf.add_edge(E.Edge(4,5,1))

print("Liczba krawedzi: ", graf.e())
print("Liczba wierzchołkow: ", graf.v())
print("Macierz sasiedztwa grafu:")
graf.show_matrix()

print("DFS dla startowego weirzchołka 2: ",graf.DFS(2))
print("DFS dla startowego weirzchołka 5: ",graf.DFS(5))


