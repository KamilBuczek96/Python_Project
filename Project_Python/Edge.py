class Edge:
    """Klasa dla krawędzi skierowanej z wagą."""

    def __init__(self, source, target, weight=1):
        """Konstruktor krawędzi.."""
        self.source = source
	self.numer = 1
        self.target = target
        self.weight = weight

    def __repr__(self):
        """Zwraca reprezentacje napisowa krawędzi.."""
        if self.weight == 1:
            return "Edge(%s, %s)" % (
                repr(self.source), repr(self.target))
        else:
            return "Edge(%s, %s, %s)" % (
                repr(self.source), repr(self.target), repr(self.weight))

    def __cmp__(self, other):
        """Porównywanie krawędzi. I jeszcze tutaj dziadostawa"""
        if self.weight > other.weight:
            return 1
        if self.weight < other.weight:
            return -1
        if self.source > other.source:
            return 1
        if self.source < other.source:
            return -1
        if self.target > other.target:
            return 1
        if self.target < other.target:
            return -1
        return 0

    def __hash__(self):
        """Krawędzie są hashowalne."""
        #return hash(repr(self))
        return hash((self.source, self.target, self.weight))

    def __invert__(self):
        """asdasdasdasdasZwraca krawędź o przeciwnym kierunku."""
        return Edge(self.target, self.source, self.weight)

