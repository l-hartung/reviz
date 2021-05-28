class ComponentFinder:
    """
    calculates independant components (subraphs) within a graph
    """

    def __init__(self, graph, withSingleNodes):
        """
        initializes the components, each article/node gets its own component
        :param graph: model of the currently examined graph
        """
        self.graph = graph
        self.components = []
        self.withSingleNodes = withSingleNodes 
        for article in graph['articles']:
            c = [article['key']]
            self.components.append(c)

    def merge_components(self):
        """
        merges all components that are connected with edges
        :return: list of calculated components
        """
        for edge in self.graph['edges']:
            f = edge['from']
            t = edge['to']
            c1 = self.search_component(f)
            c2 = self.search_component(t)
            if c1 == c2:
                continue
            new_c = c1+c2
            self.components.remove(c1)
            self.components.remove(c2)
            self.components.append(new_c)
        return self.components

    def search_component(self, c):
        """
        searches the associated component for a node
        :param c: examined node
        :return: associated component
        """
        for comp in self.components:
            if c in comp:
                return comp
        raise AttributeError("Component not found!")

    def find_article(self, bibtex_key):
        """
        finds article with the given bibtex-key in the list of all articles of the graph
        :param bibtex_key: key for the article to be found
        :return: the detected article object
        """
        for art in self.graph["articles"]:
            if art["key"] == bibtex_key:
                return art
        raise AttributeError("Article not found")

    def find_edge(self, bibtex_key):
        """
        find all edges that go out or coming in of the article with the given bibtex-key
        :param bibtex_key: key of the examined article
        :return: list of all detected edges
        """
        edges = []
        for edge in self.graph['edges']:
            if edge['from'] == bibtex_key: # or edge['to'] == bibtex_key:
                edges.append(edge)
        return edges

    def get_subgraphs(self):
        """
        creates object with all articles, edges and years for every calculated component
        :return: list of all subgraph objects
        """
        one_comps = []
        for component in self.components:
            if len(component) == 1:
                one_comps += component
        for component in one_comps:
            self.components.remove(next(i for i in self.components if component in i))
        if self.withSingleNodes and len(one_comps) > 0:
            self.components.append(one_comps)
        subgraphs = []
        for component in self.components:
            subgraph = {}
            subgraph['articles'] = [self.find_article(key) for key in component]
            years = []
            edges = []
            for article in subgraph['articles']:
                years.append(int(article['year']))
                edge_list = self.find_edge(article['key'])
                for edge in edge_list:
                    edges.append(edge)
            subgraph['years'] = years
            edges_rem_dup = [i for n, i in enumerate(edges) if i not in edges[n+1:]]  # remove duplicates in edges
            subgraph['edges'] = edges_rem_dup
            subgraph['year_arts'] = {}
            for year in range(min(years), max(years) + 1):
                this_year_arts = []
                for article in subgraph['articles']:
                    # if article['note'] is None:
                    #     continue
                    if int(article['year']) == year:
                        this_year_arts.append(article['key'])
                subgraph['year_arts'][str(year)] = this_year_arts
            for article in subgraph['articles']:
                eFrom = []
                eTo = []
                for edge in subgraph['edges']:
                    if edge['from'] == article['key']:
                        eFrom.append(edge['to'])
                    if edge['to'] == article['key']:
                        eTo.append(edge['from'])
                article['from'] = eFrom
                article['to'] = eTo
            subgraphs.append(subgraph)
        return subgraphs


class CandidateComponentFinder:
    """
    calculates connected components of candidates for merge nodes so that candidates for three-merges can be searched
    """

    def __init__(self, mc):
        """
        initializes one component for every merge candidate
        :param mc: list of candidates for merge nodes, each candidate consists of two nodes
        """
        self.mc = mc
        self.components = [[c] for c in mc]

    def merge_candidate_components(self):
        """
        merges all components that share candidates
        :return:
        """
        for candidate in self.mc:
            c1 = self.search_candidate_component(candidate)
            c2_list = self.search_by_candidate(candidate, c1)
            comp = c1
            for c2 in c2_list:
                comp += c2
                self.components.remove(c2)
            self.components.remove(c1)
            self.components.append(comp)
        return self.components

    def search_candidate_component(self, c):
        """
        searches the associated component for a candidate
        :param c: examined candidate
        :return: associated component
        """
        for comp in self.components:
            if c in comp:
                return comp
        raise AttributeError("Component not found!")

    def search_by_candidate(self, c, c_own):
        """
        checks if to components share a candidate
        :param c: examined component
        :param c_own: current component
        :return: True iff components share a candidate
        """
        def _match_criterion(c_other):
            if any(filter(lambda x: c['art1'] == x['art1'] or c['art1'] == x['art2'], c_other)):
                return True
            if any(filter(lambda x: c['art2'] == x['art1'] or c['art2'] == x['art2'], c_other)):
                return True
            return False
        l = filter(lambda c_other: (c_other != c_own) and _match_criterion(c_other), self.components)
        return list(l)