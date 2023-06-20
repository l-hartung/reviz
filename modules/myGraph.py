def makeGraph():
    return [{}, {}, {}]


def makeNameMapping(graph, name):
    if name in graph[2]:
        return graph[2][name]
    else:
        res = "node" + str(len(graph[2]))
        graph[2][name] = res
        return res


def makeNode(graph, name, x, y, citations):
    n = makeNameMapping(graph, name)
    res = [n, x, y, citations]
    graph[0][n] = res
    return res


def makeEdge(graph, name_from, name_to, col, width):
    n1 = makeNameMapping(graph, name_from)
    n2 = makeNameMapping(graph, name_to)
    res = [n1, n2, col, width]
    graph[1][n1 + n2] = res
    return res


def makeCitation(citationBox, col, ref):
    return (col, ref, citationBox)


def makeCitationBox(col=None, citations=None, indirect_col=None, indirect_citations=None):
    return (col, citations, indirect_col, indirect_citations)


def stringFromGraph(graph):
    x_factor = 1.2
    y_factor = 0.6
    years = set()
    for n in graph[0].values():
        years.add(n[1])
    years = sorted(years)
    print("years", years)
    # header
    res = "\\begin{tikzpicture}[every node/.style={draw, rounded corners, text opacity=100, fill=white, minimum width=1cm},every edge/.style={draw=black, ->, >=stealth}]\n"
    # nodes:
    nodes = []
    for n in graph[0].values():
        i = years.index(n[1])
        while len(nodes) <= i:
            nodes.append([])
        nodes[i].append(n)
        n[1] = i * x_factor
    for nByYear in nodes:
        for n in nByYear:
            n[2] = 0
    for x in range(len(nodes)):
        nByYear = nodes[len(nodes) - 1 - x]  # iterate from right to left
        for n in nByYear:
            # current node is n
            remainingRepetitions = 100
            changed = True
            while changed and remainingRepetitions > 0:
                print("repetition", remainingRepetitions)
                remainingRepetitions = remainingRepetitions - 1
                changed = False
                maychange = n[2]
                n[2] = 0  # reset to bottom
                for e in graph[1].values():
                    if e[0] == n[0]:  # edge from this node to the left
                        p1 = graph[0][e[1]]
                        for n2 in graph[0].values():
                            if n2[1] > p1[1] and n2[1] < n[1]:  # other node is somewhere in between x coordinates
                                dymax = n2[2] - p1[2] + y_factor
                                dymin = n2[2] - p1[2] - y_factor
                                dx = n2[1] - p1[1]
                                d2x = n[1] - p1[1]
                                maxy = dymax / dx * d2x
                                miny = dymin / dx * d2x
                                if maxy < miny:
                                    t = maxy
                                    maxy = miny
                                    miny = t
                                if n[2] < maxy and n[2] > miny:
                                    n[2] = maxy + 0.1
                                    changed = changed or abs(n[2] - maychange) > y_factor
                    if e[1] == n[0]:  # edge from this node to the right
                        p1 = graph[0][e[0]]
                        for n2 in graph[0].values():
                            if n2[1] < p1[1] and n2[1] > n[1]:  # other node is somewhere in between x coordinates
                                dymax = p1[2] - n2[2] + y_factor
                                dymin = p1[2] - n2[2] - y_factor
                                dx = p1[1] - n2[1]
                                d2x = p1[1] - n[1]
                                maxy = dymax / dx * d2x
                                miny = dymin / dx * d2x
                                if maxy < miny:
                                    t = maxy
                                    maxy = miny
                                    miny = t
                                if n[2] < maxy and n[2] > miny:
                                    n[2] = maxy + 0.1
                                    changed = changed or abs(n[2] - maychange) > y_factor
                for n2 in graph[0].values():
                    if n2[2] > 0:  # other node has some outgoing edges
                        dy = n[2] - n2[2]
                        if dy < y_factor and dy > 0:
                            n[2] = n2[2] + dy + 0.1
                            changed = changed or abs(n[2] - maychange) > y_factor
    for nByYear in nodes:
        i = 0
        for n in nByYear:
            print("stringFromGraph", "node", n)
            res += stringFromNode(n)
    # edges:
    res += "\\begin{scope}[on background layer]\n"
    for e in graph[1].values():
        print("stringFromGraph", "edge", e)
        res += stringFromEdge(e)
    res += "\\end{scope}\n"
    # years:
    for i in range(len(years)):
        res += "\\node (yearIndicator" + str(i) + ")[draw=none] at (" + str(i * x_factor) + ",-0.75) {|};\n"
        res += "\\node (yearLabel" + str(i) + ")[draw=none] at (" + str(i * x_factor) + ",-1.5) {" + str(years[i]) + "};\n"
        if i > 0:
            if years[i - 1] != years[i] - 1:
                res += "\\draw[thick,dotted] (" + str((i - 1) * x_factor) + ",-0.75) -- (" + str((i) * x_factor) + ",-0.75);\n"
            else:
                res += "\\draw[thick] (" + str((i - 1) * x_factor) + ",-0.75) -- (" + str((i) * x_factor) + ",-0.75);\n"
    res += "\\draw[thick, ->] (" + str((len(years) - 1) * x_factor) + ",-0.75) -- (" + str((len(years) - 0.5) * x_factor) + ",-0.75);\n"
    # footer:
    res += "\\end{tikzpicture}\n"
    res += "\\\\\n"
    return res


def stringFromEdge(edge):
    return "\\draw (" + str(edge[0]) + ") edge[line width=" + str(edge[3]) + "pt, color=" + str(edge[2]) + "] (" + str(edge[1]) + ");\n"


def stringFromNode(node):
    res = "\\node (" + str(node[0]) + ") [inner sep=0pt, align=center] at (" + str(node[1]) + "," + str(node[2]) + ") {"
    if len(node[3]) > 1:
        res += "\\bgroup \\def\\arraystretch{1}\\begin{tabular}{@{}c@{}}"
    for i in range(len(node[3]) - 1):
        res += stringFromCitation(node[3][i])
        res += "\\\\"
    res += stringFromCitation(node[3][-1])
    if len(node[3]) > 1:
        res += "\\end{tabular} \\egroup"
    res += "};\n"
    return res


def stringFromCitation(citation):
    return "\\textcolor{" + str(citation[0]) + "}{\\cite{" + str(citation[1]) + "}" + stringFromCitationBox(citation[2]) + "}"


def stringFromCitationBox(citationBox):
    if len(citationBox) != 4:
        return ""
    for i in range(4):
        if citationBox[i] is None:
            return ""
    res = "\\sesupsub"
    res += "{\\tcbox[colback=" + str(citationBox[0]) + ", colframe=" + str(citationBox[0]) + ", arc=0pt, outer arc=0pt, boxsep=0pt, left=0.3pt, right=0.3pt, top=0pt, bottom=0pt]{\\textbf{\\color{white} " + str(citationBox[1]) + "}}}"
    res += "{\\tcbox[colback=" + str(citationBox[2]) + ", colframe=" + str(citationBox[2]) + ", arc=0pt, outer arc=0pt, boxsep=0pt, left=0.3pt, right=0.3pt, top=0pt, bottom=0pt]{\\textbf{\\color{white} " + str(citationBox[3]) + "}}}"
    return res
