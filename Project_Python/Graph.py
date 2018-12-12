import Edge
import copy

class Graph:

    """Klasa dla grafu ważonego, skierowanego lub nieskierowanego."""

    def __init__(self, n, directed=False):
        self.n = n                                  # kompatybilność
        self.directed = directed                    # bool, czy graf skierowany
        self.matrix = [[0] * n for _ in range(n)]   #macierz sąsiedzctwa
        self.vector = [None] * n                          #wektor wierzchołków grafu
        self.vec_licznik=0                             #licznik pozycji w wektorze wierzchołków

    def v(self):                    # zwraca liczbę wierzchołków
        suma=0
        for i in range(self.n):
            if self.vector[i] is not None:
                suma = suma + 1
        return suma

    def e(self):                    # zwraca liczbę krawędzi
        suma=0
        for i in range(self.n):
            for j in range(self.n):
                if self.matrix[i][j] != 0:
                    suma = suma+1
        if self.is_directed():
            return suma
        elif not self.is_directed():
            return suma/2

    def show_matrix(self):
        for i in range(self.n):
            if i == 0:
                for x in range(self.n):
                    print(" |", x, end="")
                print("")
            print(i, end="|")
            for j in range(self.n):
                print(end=" ")
                print(self.matrix[i][j], end="  ")
            print("")

    def show_vector(self):
        for i in range(self.n):
            print(self.vector[i], end=" ")
        print("")

    def is_directed(self):              # bool, czy graf skierowany
        return self.directed

    def add_node(self, node):       # dodaje wierzchołek
        self.vector[self.vec_licznik] = node
        self.vec_licznik = self.vec_licznik+1

    def has_node(self, node):       # bool
        for x in range(self.vector.__len__()):
            if self.vector[x] == node:
                return True
        return False

    def del_node(self, node):       # usuwa wierzchołek
        for x in range(self.vector.__len__()):
            if self.vector[x] == node:
                self.vector[x] = None
                #usuwanie krawedzi z macierzy sasiedztwa ale nie zmieniejszam samej macierzy
                for i in range(self.n):
                    for j in range(self.n):
                        if i== node or j == node:
                            self.matrix[i][j] = 0
                return True
        return False

    def add_edge(self, edge):      # wstawienie krawędzi
        self.matrix[edge.target][edge.source] = edge.weight
        if not self.is_directed():
            self.matrix[edge.source][edge.target] = edge.weight

    def has_edge(self, edge):       # bool
        if self.is_directed():
            for x in range(self.matrix.__len__()):
                for y in range(self.matrix[0].__len__()):
                    if x == edge.target and y == edge.source and edge.weight == self.matrix[x][y]:
                        return True
            return False
        else:
            for x in range(self.matrix.__len__()):
                for y in range(self.matrix[0].__len__()):
                    if (x == edge.target and y == edge.source and edge.weight == self.matrix[x][y]) or (x == edge.source and y == edge.target and edge.weight == self.matrix[x][y]):
                        return True
            return False

    def del_edge(self, edge):      # usunięcie krawędzi
        self.matrix[edge.target][edge.source] = 0
        if not self.is_directed():
            self.matrix[edge.source][edge.target] = 0

    def weight(self, edge):        # zwraca wagę krawędzi
        return edge.weight

    def iternodes(self):            # iterator po wierzchołkach,
        for x in self.vector:
            if x is not None:
                print("Wierzchołek: ", x)

    def iteradjacent(self, node):   # iterator po wierzchołkach sąsiednich
        if self.is_directed():
            for x in range(self.n):
                for y in range(self.n):
                    if x == node and self.matrix[x][y] != 0:
                        print("Wierzchołek sąsiedni: ", y)
                    elif y == node and self.matrix[x][y] != 0:
                        print("Wierzchołek sąsiedni: ", x)

        elif not self.is_directed():
            for x in range(self.n):
                for y in range(self.n):
                    if x == node and self.matrix[x][y] != 0:
                        print("Wierzchołek sąsiedni: ", y)

    def iteroutedges(self, node):   # iterator po krawędziach wychodzących (dla grafu skierowanego)
        for x in range(self.n):
            for y in range(self.n):
                if y == node and self.matrix[x][y] !=0:
                    print("Krawedz wychodzaca z wierzchołka", y," ----> ", x)

    def iterinedges(self, node):    # iterator po krawędziach przychodzących (dla grafu skierowanego)
        for x in range(self.n):
            for y in range(self.n):
                if x == node and self.matrix[x][y] !=0:
                    print("Krawedz przychodzace do wierzchołka", x, " <----- ", y)

    def iteredges(self):            # iterator po krawędziach
        if self.is_directed():
            for x in range(self.n):
                for y in range(self.n):
                    if self.matrix[x][y] != 0:
                        print("Krawędz: (", y, " -> ", x, " )")
        elif not self.is_directed():
            for x in range(self.n):
                for y in range(x, self.n):
                    if self.matrix[x][y] != 0:
                        print("Krawędz: (", y, " -- ", x, " )")

    def copy(self):                 # zwraca kopię grafu
        return copy.deepcopy(self)

    def transpose(self):            # zwraca graf transponowany( graf z przeciwnymi krawedziami, tylko dla skierowanego)
        kopia = copy.deepcopy(self)
        for i in range(kopia.n):
            for j in range(kopia.n):
                kopia.matrix[i][j]= self.matrix[j][i]
        return kopia

    def complement(self):   # zwraca dopełnienie grafu, czyli graf z połączeniami wierzchołkow tylko takimi jak tutaj nie ma
        kopia = copy.deepcopy(self)
        for i in range(kopia.n):
            for j in range(kopia.n):
                if self.matrix[i][j] != 0:
                    kopia.matrix[i][j] = 0
                elif self.matrix[i][j] == 0:
                    kopia.matrix[i][j] = 1
        return kopia

    def subgraph(self, node):      # zwraca podgraf indukowany (graf w ktorym usuwamy weirzchołek node)
        kopia = copy.deepcopy(self)
        kopia.del_node(node)
        return kopia

    def DFS(self,node):
        #tworzenie listy koncowej, stosu oraz listy odwiedzonych wierzcholkow
        wynik = []
        stack = []
        visited = [0]*self.n

        #dodanie node do stacka
        stack.append(node)

        while stack:
            #pobranie ze stosu wierzchołka, dodanie go do listy wynikowej i ustawienie jako odwiedzony
            actual = stack.pop()
            if actual not in wynik:
                wynik.append(actual)
            else:
                continue
            visited[actual] = 1

            #dodanie na stos wrzystkich sasiadow aktualnego

            for x in range(self.n):
                for y in range(self.n):
                    if self.matrix[x][y] != 0 and x == actual and visited[y] != 1:
                        stack.append(y)
                    elif self.matrix[x][y] != 0 and y == actual and visited[x] != 1:
                        stack.append(x)
        return wynik

