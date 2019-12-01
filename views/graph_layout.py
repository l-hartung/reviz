class GraphLayouter:
    """generates the general layout with node positions for the citation graph using the sugiyama method with
    barycenter heuristic"""

    def __init__(self, graph_json, merges=None):
        """
        initializes layers, nodes and edges for the graph
        :param graph_json: json model of the citation graph
        :param merges: list of lists of nodes that are merged
        """
        self.initialize_layers(graph_json["years"])
        self.create_nodes(graph_json["articles"], merges)
        self.create_edges(graph_json["edges"])

    def create_edges(self, edge_json):
        """
        generates edge objects with their linked nodes
        :param edge_json: edges from the json graph model
        """
        self.edges = []
        for edge in edge_json:
            from_node = self.find_node(edge["from"])
            to_node = self.find_node(edge["to"])
            self.edges.append(Edge(from_node, to_node))
        self.clean_edges()
        self.all_edges = list(self.edges)

    def clean_edges(self):
        """removes duplicates in edges"""
        for from_node in self.all_nodes():
            for to_node in self.all_nodes():
                if from_node == to_node:
                    continue
                dup = list(filter(lambda x: x.from_node == from_node and x.to_node == to_node, self.edges))
                if len(dup) > 1:
                    for d in dup[1:]:
                        self.edges.remove(d)

    def initialize_layers(self, years):
        """
        assigns a layer for each year in the graph
        :param years: years from the graph model
        """
        min_year = min(years)
        max_year = max(years)
        ordered_years = list(range(min_year, max_year + 1))
        self.layers = [Layer(y) for y in ordered_years]

    def all_nodes(self):
        """a view of all nodes, dynamic"""
        nodes = []
        for layer in self.layers:
            nodes += layer.nodes
        return nodes

    def find_node(self, node_name):
        """searches for a node by name. Raises StopIteration if not found"""
        try:
            return next(x for x in self.all_nodes() if x.name == node_name)
        except StopIteration:
            merge_nodes = list(filter(lambda x: x.kind == 'Merge', self.all_nodes()))
            # return next(x for x in merge_nodes if x.data['art1'] == node_name or x.data['art2'] == node_name
            #    or ('art3' in x.data and x.data['art3'] == node_name))
            for x in merge_nodes:
                if x.data['art1']['key'] == node_name or x.data['art2']['key'] == node_name \
                        or ('art3' in x.data and x.data['art3']['key'] == node_name):
                    return x
            raise StopIteration()

    def find_layer_by_name(self, layer_name):
        """searches for a layer by name. Raises StopIteration if not found"""
        return next(
            x for x in self.layers if x.name == layer_name)

    def layers_between(self, first_layer, second_layer):
        """
        calculates the number of layers between two layers
        :param first_layer: first examined layer
        :param second_layer: second layer
        :return: value for the range
        """
        first_index = self.layers.index(first_layer)
        second_index = self.layers.index(second_layer)
        if first_index < second_index:
            # semantically equivalent to (first_index+1):*second_index-1)
            layer_range = slice(first_index + 1, second_index)
        elif second_index < first_index:
            layer_range = slice(second_index + 1, first_index)
        else:
            raise ValueError()
        return self.layers[layer_range]

    def create_nodes(self, articles, merges):
        """
        generates node objects for all nodes in the graph, also considering merge nodes
        :param articles: articles from the graph model
        :param merges: list of lists of nodes that are merged
        """
        # self.all_nodes = [RealNode(a) for a in articles]
        if merges is None:
            for article in articles:
                matching_layer = self.find_layer_by_name(article["year"])
                matching_layer.create_node(article)
        else:
            for merge in merges:
                art1 = next(x for x in articles if x['key'] == merge['art1'])
                art2 = next(x for x in articles if x['key'] == merge['art2'])
                if 'art3' in merge:
                    art3 = next(x for x in articles if x['key'] == merge['art3'])
                matching_layer = self.find_layer_by_name(art1['year'])
                merge_key = art1['key'] + art2['key']
                merge_dict = {'key': merge_key, 'year': matching_layer.name, 'art1': art1, 'art2': art2, 'merge': merge}
                if 'art3' in merge:
                    merge_key += art3['key']
                    merge_dict = {'key': merge_key, 'year': matching_layer.name, 'art1': art1, 'art2': art2, 'art3': art3, 'merge': merge}
                new_node = matching_layer.create_node(merge_dict)
                new_node.kind = "Merge"
            for article in articles:
                merge_art = False
                for merge in merges:
                    if article['key'] == merge['art1'] or article['key'] == merge['art2'] or \
                            ('art3' in merge and article['key'] == merge['art3']):
                        merge_art = True
                        break
                if not merge_art:
                    matching_layer = self.find_layer_by_name(article["year"])
                    matching_layer.create_node(article)

    def insert_dummys(self):
        """inserts dummy nodes for all edges that run between more than one layer, for each of these layers one dummy
        node will be inserted and the original edge is splitted in small edges connecting the dummy nodes"""
        self.calculate_edge_spans()
        self.long_edges = list(filter(lambda e: e.span > 1, self.edges))
        self.short_edges = list(filter(lambda e: e.span <= 1, self.edges))
        for long_edge in self.long_edges:
            first_layer = long_edge.from_node.layer
            second_layer = long_edge.to_node.layer
            layers_between = self.layers_between(first_layer, second_layer)
            previous_node = long_edge.to_node
            for between in layers_between:
                dummyname = "{}/{}/{between.name}".format(long_edge.from_node.name,
                                                          long_edge.to_node.name,
                                                          between.name)
                dummy = between.create_dummy_node(dummyname)
                dummy_edge = Edge(dummy, previous_node, span=1)
                self.edges.append(dummy_edge)
                previous_node = dummy
                long_edge.dummyedges.append(dummy_edge)
            last_edge = Edge(long_edge.from_node,
                             previous_node, span=1)
            long_edge.dummyedges.append(last_edge)
            self.edges.append(last_edge)
        for le in self.long_edges:
            self.edges.remove(le)


    def calculate_edge_spans(self):
        """calculates the layers between the incoming and outgoing node of every edge"""
        for edge in self.edges:
            from_index = self.layers.index(edge.from_node.layer)
            to_index = self.layers.index(edge.to_node.layer)
            edge.span = abs(from_index - to_index)

    def find_neighbors(self, node):
        """
        identifies neighbors of a node in its own layer and the layer left to its own layer and saves these neighbors
        in the node object
        :param node: examined node
        """
        neighbors = []
        sl_neighbors = []
        for edge in self.edges:
            if edge.from_node == node:
                if edge.to_node.layer == node.layer:
                    sl_neighbors.append(edge.to_node)
                else:
                    neighbors.append(edge.to_node)
        node.neighbors = neighbors
        node.sl_neighbors = sl_neighbors

    def calculate_barycenter(self, node):
        """
        calculates the barycenter for a node taking all neighbors of the layer left to its own layer into account
        :param node: examined node
        """
        bary = 0.0
        for n in node.neighbors:
            bary += n.slot
        bary /= len(node.neighbors)
        node.barycenter = bary

    def layer_sweep(self):
        """repositions all nodes of a layer by sorting them according to their barycenters, for nodes with same
        barycenters also neighbors within the same layer are considered"""
        for fixed_id, fixed_layer in enumerate(self.layers):
            if fixed_id + 1 == len(self.layers):
                break
            moving_layer = self.layers[fixed_id+1]
            for node in moving_layer.nodes:
                self.find_neighbors(node)
                if len(node.neighbors) > 0:
                    self.calculate_barycenter(node)
                else:
                    node.barycenter = 0 #1000
            sorted_nodes = sorted(moving_layer.nodes, key=lambda n: n.barycenter, reverse=False)
            for slot, node in enumerate(sorted_nodes):
                node.slot = slot + 1
            barys = set([n.barycenter for n in sorted_nodes])
            bary_nodes = [list(filter(lambda x: x.barycenter == b, sorted_nodes)) for b in barys]
            for b in bary_nodes:
                if len(b) > 1:
                    for node in b:
                        if len(node.sl_neighbors) == 1:
                            n_slot = node.sl_neighbors[0].slot
                            if n_slot > node.slot:
                                other_node = max(b, key=lambda s: s.slot)
                            elif n_slot < node.slot:
                                other_node = min(b, key=lambda s: s.slot)
                            temp = node.slot
                            node.slot = other_node.slot
                            other_node.slot = temp
            sorted_nodes = sorted(moving_layer.nodes, key=lambda n: n.slot, reverse=False)
            moving_layer.nodes = sorted_nodes

    def crossing_minimization(self):
        """generates a graph layout with as few crossing edges as possible"""
        self.layer_sweep()


class Edge:
    """object for edges"""

    def __init__(self, from_node, to_node, span=None):
        """
        initializes the linking nodes and the span of the edge
        :param from_node: outgoing node of the edge
        :param to_node: incoming node of the edge
        :param span: number of layers between the two nodes of the edge
        """
        self.from_node = from_node
        self.to_node = to_node
        self.span = span
        self.dummyedges = []


class Layer:
    """object for graph layers"""

    def __init__(self, name):
        """
        initializes the name of the layer
        :param name: associated year of the layer
        """
        self.nodes = []
        self.name = str(name)

    def append_node(self, node):
        """appends a node to the layer"""
        self.nodes.append(node)
        node.slot = len(self.nodes)

    def create_node(self, data):
        """
        generates a node object for an article
        :param data: an article of the graph model
        :return: node object
        """
        node = RealNode(data, layer=self)
        self.append_node(node)
        return node

    def create_dummy_node(self, name):
        """
        generates node object for a dummy node
        :param name: dictionary of the merge node
        :return: node object
        """
        dummy = DummyNode(name, self)
        self.append_node(dummy)
        return dummy


class Node:
    """object for nodes"""

    def __init__(self, name, layer):
        """
        initializes name, layer, kind and slot of a node
        :param name: node name
        :param layer: associated layer for the node
        """
        self.name = name
        self.layer = layer
        self.kind = "Abstract"
        self.slot = None


class RealNode(Node):
    """object for real nodes, not dummies"""

    def __init__(self, article_json, layer=None):
        super().__init__(name=article_json["key"], layer=layer)
        self.data = article_json
        self.kind = "Node"


class DummyNode(Node):
    """object for dummy nodes"""

    def __init__(self, name, layer):
        super().__init__(name, layer)
        self.kind = "Dummy"

