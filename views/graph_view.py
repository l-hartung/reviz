import os
from modules.myGraph import makeCitationBox, makeNode, makeCitation, makeGraph, makeEdge, stringFromGraph
from modules.mytimer import measureStart, measureEnd, measureEnd2
from utils.latex import build_all, compile_latex
from views.component_finder import ComponentFinder
from utils.utils import depth_first_search, calculate_indirect_citations
from views import graph_layout
from views.calculate_merges import calculate_merges
from views.author_matching import find_same_authors
from modules.config import bibKeyID
from modules.bibtex import generate_bib

flag_include_citations = False


def evaluation(edges, layers, nodes, edge_dict, node_fromEdges, node_toEdges, node_edges, node_counter):
    for edge in edges:
        edge_dict[edge.span] += 1
    for node in nodes:
        if node.kind != 'Dummy':
            node_counter += 1
            fromE = len(list(filter(lambda x: x.from_node == node, edges)))
            toE = len(list(filter(lambda x: x.to_node == node, edges)))
            allE = fromE + toE
            node_fromEdges += fromE
            node_toEdges += toE
            node_edges += allE
    return edge_dict, node_fromEdges, node_toEdges, node_edges, node_counter


def generate_correction_table(global_merges, trans_edges_leave, minimum_citations, citationsToKeep):
    """
    generates table containing edge correction and left out transitive edges for the legend
    :param global_merges: list of all merged nodes
    :param trans_edges_leave: list of all left out transitive edges
    :param minimum_citations: only nodes with the given minimum number of citations are displayed
    :return: tikz code for the table
    """
    mergeCode = ''
    for merge in global_merges:
        mergeCode += edge_correction(merge, 'diff1_from', '+', 'from', 'art1', citationsToKeep)
        mergeCode += edge_correction(merge, 'diff2_from', '+', 'from', 'art2', citationsToKeep)
        mergeCode += edge_correction(merge, 'diff1_to', '+', 'to', 'art1', citationsToKeep)
        mergeCode += edge_correction(merge, 'diff2_to', '+', 'to', 'art2', citationsToKeep)
        if 'art3' in merge:
            mergeCode += edge_correction(merge, 'diff3_from', '+', 'from', 'art3', citationsToKeep)
            mergeCode += edge_correction(merge, 'diff3_to', '+', 'to', 'art3', citationsToKeep)
            mergeCode += edge_correction(merge, 'diff12_from', '-', 'from', 'art3', citationsToKeep)
            mergeCode += edge_correction(merge, 'diff23_from', '-', 'from', 'art1', citationsToKeep)
            mergeCode += edge_correction(merge, 'diff13_from', '-', 'from', 'art2', citationsToKeep)
            mergeCode += edge_correction(merge, 'diff12_to', '-', 'to', 'art3', citationsToKeep)
            mergeCode += edge_correction(merge, 'diff23_to', '-', 'to', 'art1', citationsToKeep)
            mergeCode += edge_correction(merge, 'diff13_to', '-', 'to', 'art2', citationsToKeep)
    transCode = ''
    for trans in trans_edges_leave:
        if (trans.from_node.kind == 'Node' and trans.from_node.citations < minimum_citations and trans.to_node.kind == 'Node' and trans.to_node.citations < minimum_citations):
            continue
        if trans.from_node.kind == 'Merge':
            citationsToKeep.add(trans.from_node.data['art1']['key'])
            from_name = "\\cite[...]{" + str(trans.from_node.data['art1']['key']) + "}"
        else:
            citationsToKeep.add(trans.from_node.name)
            from_name = "\\cite{" + str(trans.from_node.name) + "}"
        if trans.to_node.kind == 'Merge':
            citationsToKeep.add(trans.to_node.data['art1']['key'])
            to_name = "\\cite[...]{" + str(trans.to_node.data['art1']['key']) + "}"
        else:
            citationsToKeep.add(trans.to_node.name)
            to_name = "\\cite{" + str(trans.to_node.name) + "}"
        transCode += "$+$ (" + str(from_name) + "," + str(to_name) + ")\\newline"

    if trans_edges_leave != [] and global_merges != []:
        tikzCode = ""
        tikzCode += "\\scriptsize\n"
        tikzCode += "\\begin{tabular}[c]{p{3.3cm}p{4cm}}\n"
        tikzCode += "{Edge corrections \\newline\n"
        tikzCode += "for merged nodes:} &\n"
        tikzCode += "{Left out transitive\\newline\n"
        tikzCode += "citations:} \\\\\n"
        tikzCode += mergeCode + "& " + transCode + "\n"
        tikzCode += "\\end{tabular}\n"
    elif trans_edges_leave != []:
        tikzCode = ""
        tikzCode += "\\scriptsize\n"
        tikzCode += "\\begin{tabular}{p{4cm}}\n"
        tikzCode += "{Left out transitive\\newline\n"
        tikzCode += "citations:} \\\\\n"
        tikzCode += transCode + "\n"
        tikzCode += "\\end{tabular}\n"
    elif global_merges != []:
        tikzCode = ""
        tikzCode += "\\scriptsize\n"
        tikzCode += "\\begin{tabular}{p{3.5cm}}\n"
        tikzCode += "{Edge corrections \\newline\n"
        tikzCode += "for merged nodes:} \\\\\n"
        tikzCode += mergeCode + "\n"
        tikzCode += "\\end{tabular}\n"
    else:
        tikzCode = ""
    return tikzCode


def edge_correction(merge, d, pm, tf, art, citationsToKeep):
    """
    generates strings for all left out or incorrect edges due to merge nodes
    :param merge: merge node with all individual nodes
    :param d: list of differences in the nodes
    :param pm: plus or minus depending on whether an edge is added or subtracted in the corrections
    :param tf: from or to deponding on whether it is an incoming or outgoing edge
    :param art: observed node in the merge node
    :return: string to add in the legend
    """
    tc = ''
    for diff in merge[d]:
        if tf == 'to':
            if len(diff) == 12:
                diff1 = diff[:6]
                diff2 = diff[6:]
                citationsToKeep.add(diff1)
                citationsToKeep.add(diff2)
                citationsToKeep.add(merge[art])
                tc += "$" + str(pm) + "$ (\\cite{" + str(diff1) + "},\\cite{" + str(merge[art]) + "}) \\newline"
                tc += "$" + str(pm) + "$ (\\cite{" + str(diff2) + "},\\cite{" + str(merge[art]) + "}) \\newline"
            else:
                citationsToKeep.add(diff)
                citationsToKeep.add(merge[art])
                tc += "$" + str(pm) + "$ (\\cite{" + str(diff) + "},\\cite{" + str(merge[art]) + "}) \\newline"
        elif tf == 'from':
            if len(diff) == 12:
                diff1 = diff[:6]
                diff2 = diff[6:]
                citationsToKeep.add(diff1)
                citationsToKeep.add(diff2)
                citationsToKeep.add(merge[art])
                tc += "$" + str(pm) + "$ (\\cite{" + str(merge[art]) + "},\\cite{" + diff1 + "}) \\newline"
                tc += "$" + str(pm) + "$ (\\cite{" + str(merge[art]) + "},\\cite{" + diff2 + "}) \\newline"
            else:
                citationsToKeep.add(diff)
                citationsToKeep.add(merge[art])
                tc += "$" + str(pm) + "$ (\\cite{" + str(merge[art]) + "},\\cite{" + diff + "}) \\newline"
    return tc


def find_correct_node_key(item, merges):
    """
    checks whether edge concerns a merge node and returns its name if so
    :param item: node name
    :param merges: list of all merge nodes
    :return: corrected node name
    """

    for merge in merges:
        if item == merge['art1'] or item == merge['art2'] or ('art3' in merge and item == merge['art3']):
            if 'art3' in merge:
                item = merge['art1'] + merge['art2'] + merge['art3']
            else:
                item = merge['art1'] + merge['art2']
            return item
    return item


def find_merge_keys(merge, index, merges):
    """
    identifies and modifies correct node name of edges connecting merge nodes
    :param merge: examined merge node
    :param index: set of edges, same_from...
    :param merges: list of all merge nodes
    """
    merge[index] = list(set([find_correct_node_key(item, merges) for item in merge[index]]))


def generate_tikz_header(bib):
    tikzCode = ""
    tikzCode += "% if using pdflatex and large graphs, then run 'pdflatex --extra-mem-bot=10000000 graph.tex'\n"
    if flag_include_citations:
        tikzCode += "\\documentclass[multi]{standalone}\n"
    else:
        tikzCode += "\\documentclass{standalone}\n"
    tikzCode += "\\usepackage{hyperref}\n"
    tikzCode += "\\usepackage{tikz}\n"
    tikzCode += "\\usepackage[utf8]{inputenc}\n"
    tikzCode += "\\usepackage[backend=biber,style=numeric]{biblatex}\n"
    tikzCode += "\\usetikzlibrary{positioning}\n"
    tikzCode += "\\usepackage[T1]{fontenc}\n"
    tikzCode += "\\usepackage{filecontents}\n"
    tikzCode += "\\usetikzlibrary{graphs}\n"
    tikzCode += "\\usepackage{tikz-layers}\n"
    tikzCode += "\\def\SPSB#1#2{\\rlap{\\textsuperscript{#1}}\\SB{#2}}\n"
    tikzCode += "\\def\SP#1{\\textsuperscript{#1}}\n"
    tikzCode += "\\def\SB#1{\\textsubscript{#1}}\n"
    tikzCode += "\\usepackage{tcolorbox}\n"
    tikzCode += "\\DeclareFieldFormat{postnote}{#1}\n"
    tikzCode += "\\usepackage{stackengine}\n"
    tikzCode += "\\setstackgap{L}{.7\\baselineskip}\n"
    tikzCode += "\\setstackgap{S}{2.3pt}\n"
    tikzCode += "\\def\\stacktype{S}\n"
    tikzCode += "\\def\\stackalignment{l}\n"
    tikzCode += "\\def\\sesupsub#1#2{\\scriptsize\\stackanchor{#1}{#2}}\n"
    tikzCode += "\\definecolor{transcolor2}{HTML}{1586D1}\n"
    tikzCode += "\\definecolor{transcolor3}{HTML}{1377BA}\n"
    tikzCode += "\\definecolor{transcolor4}{HTML}{1068A3}\n"
    tikzCode += "\\definecolor{transcolor5}{HTML}{0E598C}\n"
    tikzCode += "\\definecolor{transcolordefault}{HTML}{0C4B74}\n"
    tikzCode += "\\definecolor{authorcolor1}{HTML}{0101DF}\n"
    tikzCode += "\\definecolor{authorcolor2}{HTML}{31B404}\n"
    tikzCode += "\\definecolor{authorcolor3}{HTML}{DF0101}\n"
    tikzCode += "\\definecolor{authorcolor4}{HTML}{F19104}\n"
    tikzCode += "\\definecolor{authorcolor5}{HTML}{FE2E9A}\n"
    tikzCode += "\\definecolor{authorcolor6}{HTML}{01DFD7}\n"
    tikzCode += "\\definecolor{authorcolor7}{HTML}{40FF00}\n"
    tikzCode += "\\definecolor{citationcolor0}{HTML}{FF0000}\n"
    tikzCode += "\\definecolor{citationcolor1}{HTML}{E51900}\n"
    tikzCode += "\\definecolor{citationcolor2}{HTML}{CC3300}\n"
    tikzCode += "\\definecolor{citationcolor3}{HTML}{B24C00}\n"
    tikzCode += "\\definecolor{citationcolor4}{HTML}{996600}\n"
    tikzCode += "\\definecolor{citationcolor5}{HTML}{7F7F00}\n"
    tikzCode += "\\definecolor{citationcolor6}{HTML}{669900}\n"
    tikzCode += "\\definecolor{citationcolor7}{HTML}{4CB200}\n"
    tikzCode += "\\definecolor{citationcolor8}{HTML}{33CC00}\n"
    tikzCode += "\\definecolor{citationcolor9}{HTML}{19E500}\n"
    tikzCode += "\\definecolor{citationcolor10}{HTML}{00FF00}\n"
    if bib is None or bib == "":
        tikzCode += "\\bibliography{literature.bib}\n"
    else:
        tikzCode += "\\bibliography{" + bib + "}\n"
    tikzCode += "\\begin{document}\n"
    return tikzCode


def generate_tikz_foot():
    tikzCode = ""
    if flag_include_citations:
        tikzCode += "\\newpage\n"
        tikzCode += "\\begingroup\n"
        tikzCode += "\\sloppy\n"
        tikzCode += "\\printbibliography[heading=none]\n"
        tikzCode += "\\endgroup\n"
    tikzCode += "\\end{document}\n"
    return tikzCode


def view_sugiyama(graph, tex, withSingleNodes, without_dummy_nodes, bibfile):
    """
    render graph model to citation graph without optimizations
    :param graph: json graph model
    :param tex: folder where to put generated files
    :param withSingleNodes: single nodes without any edges are displayed (in case of False are these nodes left out)
    :param without_dummy_nodes: dummy nodes are added (False) for better placement of nodes in case of long edges or left out (True)
    """
    citationsToKeep = set()
    years = graph['years']
    min_year = min(years)
    max_year = max(years)
    cf = ComponentFinder(graph, withSingleNodes)
    cf.merge_components()
    subgraphs = cf.get_subgraphs()
    tikzCode = generate_tikz_header(bibfile)
    tikzCode += "{\\renewcommand{\\arraystretch}{2}\n"
    tikzCode += "\\begin{tabular}{l}\n"
    for subgraph in subgraphs:
        subgraph['years'] = years
        gl = graph_layout.GraphLayouter(subgraph)
        gl.insert_dummys(False, without_dummy_nodes)
        gl.crossing_minimization()
        tikzCode += "\\begin{tikzpicture}[every node/.style={draw, rounded corners, text opacity=100, fill=white, minimum width=1.7cm},every edge/.style={draw=black, ->, >=stealth}]\n"
        x_factor = 2
        y_factor = 0.8
        for layer_id, layer in enumerate(gl.layers):
            if len(layer.nodes) > 0:
                for node in layer.nodes:
                    if node.kind == 'Dummy':
                        node.x_coordinate = layer_id * x_factor
                        node.y_coordinate = node.slot * y_factor
                    else:
                        citationsToKeep.add(node.name)
                        tikzCode += "\\node (" + str(node.name) + ") at (" + str(layer_id * x_factor) + "," + str(node.slot * y_factor) + ") {\\cite{" + str(node.name) + "}};\n"
            else:
                tikzCode += "\\node[draw=none, opacity=0] at (" + str(layer_id * x_factor) + "," + str(y_factor) + ") {};\n"
        tikzCode += "\\begin{scope}[on background layer]\n"
        for edge in gl.short_edges:
            tikzCode += "\\draw (" + str(edge.from_node.name) + ") edge[bend right] (" + str(edge.to_node.name) + ");\n"
        for edge in gl.long_edges:
            dummy_list = []
            start = edge.from_node.name
            end = edge.to_node.name
            for de in edge.dummyedges:
                dummy_list.append(de.from_node)
            del dummy_list[-1]
            dummy_list.reverse()
            tikzCode += "\\draw (" + str(start) + ") edge[bend right] (" + str(end) + ");\n"
        if subgraph == subgraphs[-1]:
            years_dist = max_year - min_year + 1
            previous = 0
            for year in range(0, years_dist):
                if year == 0:
                    tikzCode += "\\node (" + str(year) + ")[draw=none] {|};\n"
                else:
                    tikzCode += "\\node (" + str(year) + ")[right= 0.29cm of " + str(previous) + ", draw=none] {|};\n"
                    previous = year
            scale_const = 2
            tikzCode += "\\draw[thick, ->] (0,0) -- (" + str(scale_const * years_dist - 1) + ",0);\n"
            for year in range(0, years_dist):
                tikzCode += "\\node (" + str(min_year + year) + ") [below= 0.07cm of " + str(year) + ", draw=none] {" + str(min_year + year) + "};\n"
        tikzCode += "\\end{scope}\n"
        tikzCode += "\\end{tikzpicture}\n"
        tikzCode += "\\\\"
    tikzCode += "\\end{tabular}\n"
    tikzCode += "}\n"
    tikzCode += generate_tikz_foot()
    print(tikzCode)
    with open(os.path.join(tex, 'graph.tex'), 'w') as file:
        file.write(tikzCode)
    compile_latex('graph', tex)


def view_sugiyama_summary(graph, tex, deviation, transitivities, trans_bold, citations, authors_colored, withSingleNodes, minimum_citations, without_dummy_nodes, dont_show_edge_corrections, y_factor, bibfile, bibcontent):
    """
    render graph model into citation graph with optional optimizations
    :param graph: json graph model
    :param tex: folder where to put tex-files
    :param deviation: maximum allowed edge deviations for merge nodes
    :param transitivities: summarizes transitive edges
    :param trans_bold: adapt line width of transitive edges
    :param citations: count number of direct and indirect citations for every noce
    :param authors_colored: threshold for coloring publications with same authors
    :param withSingleNodes: single nodes without any edges are displayed (in case of False are these nodes left out)
    :param minimum_citations: only nodes with the given number of citations are displayed
    :param without_dummy_nodes: dummy nodes are added (False) for better placement of nodes in case of long edges or left out (True)
    :param dont_show_edge_corrections: list of edge corrections are left out
    """
    measure = measureStart()
    print("start view_sugiyama_summary XXX")
    citationsToKeep = set()
    texfile = os.path.join(tex, 'graph_summary.tex')
    if bibcontent is None:
        biboutfile = "literatur.bib"
    else:
        biboutfile = os.path.join(tex, 'graph_summary.bib')
    years = graph['years']
    min_year = min(years)
    max_year = max(years)
    # for evaluation
    edge_dict = {}
    node_fromEdges = 0
    node_toEdges = 0
    node_edges = 0
    node_counter = 0.0
    for i in range(max_year - min_year + 1):
        edge_dict[i] = 0
    mygraph = makeGraph()
    measureEnd2(measure, "init")
    measure = measureStart()
    if authors_colored >= 0 and authors_colored <= 1:
        match_authors = find_same_authors(graph['articles'], authors_colored)
        cluster_color_dict = {1: 'authorcolor1', 2: 'authorcolor5', 3: 'authorcolor4', 4: 'authorcolor2', 5: 'authorcolor3', 6: 'authorcolor7', 7: 'authorcolor6', -1: 'black'}
        match_author_dict = {art['key']: 'black' for art in graph['articles']}
        for id, match in enumerate(match_authors):
            for m in match:
                if id + 1 in cluster_color_dict:
                    match_author_dict[m] = cluster_color_dict[id + 1]
    measureEnd2(measure, "matching authors")
    measure = measureStart()
    cf = ComponentFinder(graph, withSingleNodes)
    cf.merge_components()
    measureEnd2(measure, "merge components")
    measure = measureStart()
    subgraphs = cf.get_subgraphs()
    measureEnd2(measure, "get subgraphs")
    measure = measureStart()
    tikzCode = generate_tikz_header(biboutfile)
    tikzCode += "{\\renewcommand{\\arraystretch}{2}\n"
    tikzCode += "\\begin{tabular}{l}\n"
    global_merges = []
    trans_edges_leave = []
    minYHelper = 0
    maxYHelper = -y_factor
    for subgraph in subgraphs:
        minYHelper = maxYHelper + y_factor
        merges = calculate_merges(subgraph, deviation, minimum_citations)
        for merge in merges:
            global_merges.append(merge)
            for merge in merges:
                find_merge_keys(merge, 'same_from', merges)
                find_merge_keys(merge, 'same_to', merges)
                if 'art3' in merge:
                    find_merge_keys(merge, 'diff12_from', merges)
                    find_merge_keys(merge, 'diff13_from', merges)
                    find_merge_keys(merge, 'diff23_from', merges)
                    find_merge_keys(merge, 'diff12_to', merges)
                    find_merge_keys(merge, 'diff13_to', merges)
                    find_merge_keys(merge, 'diff23_to', merges)
        subgraph['years'] = years
        gl = graph_layout.GraphLayouter(subgraph, merges=merges)
        gl.insert_dummys(minimum_citations, without_dummy_nodes)
        gl.crossing_minimization()
        cit_list = []
        for node in gl.all_nodes():
            indcitations = []
            if node.kind != "Dummy":
                if node.kind == "Merge":
                    node.citations1 = len(list(filter(lambda x: x['to'] == node.data['art1']['key'], graph['edges'])))
                    node.indcitations1 = len(calculate_indirect_citations(node.data['art1']['key'], graph['edges'], indcitations))
                    node.citations2 = len(list(filter(lambda x: x['to'] == node.data['art2']['key'], graph['edges'])))
                    node.indcitations2 = len(calculate_indirect_citations(node.data['art2']['key'], graph['edges'], indcitations))
                    cit_list.append(node.indcitations1)
                    cit_list.append(node.indcitations2)
                    if 'art3' in node.data:
                        node.citations3 = len(list(filter(lambda x: x['to'] == node.data['art3']['key'], graph['edges'])))
                        node.indcitations3 = len(calculate_indirect_citations(node.data['art3']['key'], graph['edges'], indcitations))
                        cit_list.append(node.indcitations3)
                else:
                    node.citations = len(list(filter(lambda x: x.to_node.name == node.name, gl.all_edges)))
                    node.indcitations = len(calculate_indirect_citations(node.name, graph['edges'], indcitations))
                    cit_list.append(node.indcitations)
        if citations:
            max_cit = max(cit_list)
        citation_color_dict = {
            0: 'citationcolor0',
            1: 'citationcolor1',
            2: 'citationcolor2',
            3: 'citationcolor3',
            4: 'citationcolor4',
            5: 'citationcolor5',
            6: 'citationcolor6',
            7: 'citationcolor7',
            8: 'citationcolor8',
            9: 'citationcolor9',
            10: 'citationcolor10',
        }
        x_factor = 2.3
        dummy_factor = 0.5
        merge_two_factor = 1.2
        merge_three_factor = 1.5
        y = minYHelper
        for layer_id, layer in enumerate(gl.layers):
            maxYHelper = max(maxYHelper, y)
            y = minYHelper
            if len(layer.nodes) > 0:
                for node in layer.nodes:
                    color = 'black'
                    color1 = 'black'
                    color2 = 'black'
                    color3 = 'black'
                    if node.kind == 'Dummy':
                        node.x_coordinate = layer_id * x_factor
                        node.y_coordinate = y
                        y += y_factor * dummy_factor
                    else:
                        if node.kind == 'Merge':
                            if authors_colored >= 0 and authors_colored <= 1:
                                color1 = match_author_dict[node.data['art1']['key']]
                                color2 = match_author_dict[node.data['art2']['key']]
                                if 'art3' in node.data:
                                    color3 = match_author_dict[node.data['art3']['key']]
                            if citations:
                                if node.citations1 == 0:
                                    fill1 = citation_color_dict[0]
                                else:
                                    fill1 = citation_color_dict[round(node.citations1 / max_cit * 10)]
                                if node.citations2 == 0:
                                    fill2 = citation_color_dict[0]
                                else:
                                    fill2 = citation_color_dict[round(node.citations2 / max_cit * 10)]
                                if node.indcitations1 == 0:
                                    indfill1 = citation_color_dict[0]
                                else:
                                    indfill1 = citation_color_dict[round(node.citations1 / max_cit * 10)]
                                if node.indcitations2 == 0:
                                    indfill2 = citation_color_dict[0]
                                else:
                                    indfill2 = citation_color_dict[round(node.citations2 / max_cit * 10)]
                            if 'art3' in node.data:
                                y += 0.5
                                name = node.name
                                if citations:
                                    if node.citations3 == 0:
                                        fill3 = citation_color_dict[0]
                                    else:
                                        fill3 = citation_color_dict[round(node.citations3 / max_cit * 10)]
                                    if node.indcitations3 == 0:
                                        indfill3 = citation_color_dict[0]
                                    else:
                                        indfill3 = citation_color_dict[round(node.indcitations3 / max_cit * 10)]
                                    box1 = makeCitationBox(fill1, node.citations1, indfill1, node.indcitations1)
                                    box2 = makeCitationBox(fill2, node.citations2, indfill2, node.indcitations2)
                                    box3 = makeCitationBox(fill3, node.citations3, indfill3, node.indcitations3)
                                else:
                                    box1 = makeCitationBox()
                                    box2 = makeCitationBox()
                                    box3 = makeCitationBox()
                                citationsToKeep.add(node.data['art1']['key'])
                                citationsToKeep.add(node.data['art2']['key'])
                                citationsToKeep.add(node.data['art3']['key'])
                                c1 = makeCitation(box1, color1, node.data['art1']['key'])
                                c2 = makeCitation(box2, color2, node.data['art2']['key'])
                                c3 = makeCitation(box3, color3, node.data['art3']['key'])
                                n = makeNode(mygraph, name, min_year + layer_id, y, [c1, c2, c3])
                                y += merge_three_factor
                            else:
                                y += 0.2
                                name = node.name
                                if citations:
                                    box1 = makeCitationBox(fill1, node.citations1, indfill1, node.indcitations1)
                                    box2 = makeCitationBox(fill2, node.citations2, indfill2, node.indcitations2)
                                else:
                                    box1 = makeCitationBox()
                                    box2 = makeCitationBox()
                                citationsToKeep.add(node.data['art1']['key'])
                                citationsToKeep.add(node.data['art2']['key'])
                                c1 = makeCitation(box1, color1, node.data['art1']['key'])
                                c2 = makeCitation(box2, color2, node.data['art2']['key'])
                                n = makeNode(mygraph, name, min_year + layer_id, y, [c1, c2])
                                y += merge_two_factor
                        else:
                            if (node.citations < minimum_citations):
                                continue
                            if authors_colored >= 0 and authors_colored <= 1:
                                color = match_author_dict[node.name]
                            if citations:
                                if node.citations == 0:
                                    fill = citation_color_dict[0]
                                else:
                                    fill = citation_color_dict[round(node.citations / max_cit * 10)]
                                if node.indcitations == 0:
                                    indfill = citation_color_dict[0]
                                else:
                                    indfill = citation_color_dict[round(node.indcitations / max_cit * 10)]
                                box = makeCitationBox(fill, node.citations, indfill, node.indcitations)
                            else:
                                box = makeCitationBox()
                            citationsToKeep.add(node.name)
                            c1 = makeCitation(box, color, node.name)
                            n = makeNode(mygraph, node.name, min_year + layer_id, y, [c1])
                            y += y_factor

        def _check_if_edge(edge):
            if edge.from_node.kind == 'Merge':
                m_f = edge.from_node.data['merge']
                if 'art3' in m_f:
                    if edge.to_node.name not in m_f['diff12_from'] and edge.to_node.name not in m_f['diff23_from'] \
                            and edge.to_node.name not in m_f['diff13_from'] and edge.to_node.name not in m_f['same_from']:
                        return True
                else:
                    if edge.to_node.name not in m_f['same_from']:
                        return True
            elif edge.to_node.kind == 'Merge':
                m_t = edge.to_node.data['merge']
                if 'art3' in m_t:
                    if edge.from_node.name not in m_t['diff12_to'] and edge.from_node.name not in m_t['diff23_to'] \
                            and edge.from_node.name not in m_t['diff13_to'] and edge.from_node.name not in m_t['same_to']:
                        return True
                else:
                    if edge.from_node.name not in m_t['same_to']:
                        return True
            return False

        draw_edges = list(filter(lambda x: not _check_if_edge(x), gl.all_edges))
        edge_weight_dict = []
        if transitivities:
            for edge in gl.all_edges:
                ed = {'from': edge.from_node.name, 'to': edge.to_node.name, 'weight': 1}
                edge_weight_dict.append(ed)
            for edge in draw_edges:
                trans = True
                efrom = edge.from_node
                eto = edge.to_node
                stack = []
                s, stack = depth_first_search(efrom, edge, eto, draw_edges, stack, trans_edges_leave)
                if s:
                    for elem in stack:
                        if elem in trans_edges_leave:
                            trans = False
                    if trans:
                        trans_edges_leave.append(edge)
                        leave_ewi = next(x for x in edge_weight_dict if edge.from_node.name == x['from'] and edge.to_node.name == x['to'])
                        if leave_ewi['weight'] > 1:
                            additional_weight = leave_ewi['weight'] - 1
                        else:
                            additional_weight = 0
                        if trans_bold:
                            ewi = next(x for x in edge_weight_dict if stack[-1].from_node.name == x['from'] and stack[-1].to_node.name == x['to'])
                            ewi['weight'] += 1 + additional_weight
        if trans_bold:
            weight_color_dict = {1: (0.4, 'black'), 2: (1.5, 'black'), 3: (1.9, 'black'), 4: (2.3, 'black'), 5: (2.7, 'black'), -1: (3.1, 'black')}
        else:
            weight_color_dict = {1: (0.4, 'black')}
        for edge in gl.short_edges:
            if edge in trans_edges_leave:
                continue
            no_edge = _check_if_edge(edge)
            if not no_edge:
                if ((edge.from_node.kind == 'Node' and edge.from_node.citations < minimum_citations) or (edge.to_node.kind == 'Node' and edge.to_node.citations < minimum_citations)):
                    continue
                if transitivities:
                    ewi = next(x for x in edge_weight_dict if edge.from_node.name == x['from'] and edge.to_node.name == x['to'])
                    if ewi['weight'] in weight_color_dict:
                        weight, color = weight_color_dict[ewi['weight']]
                    else:
                        weight, color = weight_color_dict[-1]
                else:
                    weight, color = weight_color_dict[1]
                e = makeEdge(mygraph, edge.from_node.name, edge.to_node.name, color, weight)
        for edge in gl.long_edges:
            if edge in trans_edges_leave:
                continue
            no_edge = _check_if_edge(edge)
            if not no_edge:
                if ((edge.from_node.kind == 'Node' and edge.from_node.citations < minimum_citations) or (edge.to_node.kind == 'Node' and edge.to_node.citations < minimum_citations)):
                    continue
                start = edge.from_node.name
                end = edge.to_node.name
                dummy_list = []
                for de in edge.dummyedges:
                    dummy_list.append(de.from_node)
                if (len(dummy_list) > 0):
                    del dummy_list[-1]
                dummy_list.reverse()
                if transitivities:
                    ewi = next(x for x in edge_weight_dict if edge.from_node.name == x['from'] and edge.to_node.name == x['to'])
                    if ewi['weight'] in weight_color_dict:
                        weight, color = weight_color_dict[ewi['weight']]
                    else:
                        weight, color = weight_color_dict[-1]
                else:
                    weight, color = weight_color_dict[1]
                e = makeEdge(mygraph, start, end, color, weight)
        if subgraph == subgraphs[-1]:
            years_dist = max_year - min_year + 1
        eval_trans_edges = []
        for edge in draw_edges:
            if edge not in trans_edges_leave:
                eval_trans_edges.append(edge)
        edge_dict, node_fromEdges, node_toEdges, node_edges, node_counter = evaluation(gl.all_edges, gl.layers, gl.all_nodes(), edge_dict, node_fromEdges, node_toEdges, node_edges, node_counter)
    tikzCode += stringFromGraph(mygraph)
    measureEnd2(measure, "merge and output as tikz")
    measure = measureStart()
    # evaluation
    print(edge_dict)
    print(node_counter)
    node_fromEdges /= node_counter
    node_toEdges /= node_counter
    node_edges /= node_counter
    node_dict = {'fromEdgesPerNode': node_fromEdges, 'toEdgesPerNode': node_toEdges, 'edgesPerNode': node_edges}
    print(node_dict)
    print("before correction-table")
    if (not (dont_show_edge_corrections)):
        correction_table = generate_correction_table(global_merges, trans_edges_leave, minimum_citations, citationsToKeep)
    else:
        correction_table = ''
    print("after correction-table")
    tikzCode += "\\hspace{0.3cm}\n"
    tikzCode += "\\setlength{\\tabcolsep}{1pt}\n"
    tikzCode += "\\renewcommand{\\arraystretch}{1}\n"
    tikzCode += "\\scriptsize\n"
    if trans_bold or citations or (authors_colored >= 0 and authors_colored <= 1):
        if trans_bold and not citations and not (authors_colored >= 0 and authors_colored <= 1):
            tikzCode += "\\begin{tabular}{p{5cm}}\n"
        else:
            tikzCode += "\\begin{tabular}[c]{p{2.6cm}p{5.3cm}}\n"
    if authors_colored >= 0 and authors_colored <= 1:
        color = 'authorcolor1'
    else:
        color = 'black'
    if citations:
        tikzCode += generate_tikz_citations(authors_colored >= 0 and authors_colored <= 1)
        tikzCode += generate_tikz_citationColor()
    if (authors_colored >= 0 and authors_colored <= 1) and not citations:
        tikzCode += "\\begin{tikzpicture}\n"
        tikzCode += "\\node[draw=black, rounded corners, text=" + str(color) + "] { [R] };\n"
        tikzCode += "\\end{tikzpicture} \\newline\n"
        tikzCode += "R: Reference, \\newline\n"
        tikzCode += "colored articles \\newline share authors &\n"
    if trans_bold:
        tikzCode += generate_tikz_bold()
    if trans_bold or citations or (authors_colored >= 0 and authors_colored <= 1):
        tikzCode += "\\end{tabular}\n"
    if years_dist <= 5:
        if correction_table != '':
            if citations or trans_bold or (authors_colored >= 0 and authors_colored <= 1):
                tikzCode += "\\\\"
    tikzCode += correction_table
    tikzCode += "\\end{tabular}\n"
    tikzCode += "}\n"
    tikzCode += generate_tikz_foot()
    print(tikzCode)
    with open(texfile, 'w') as file:
        file.write(tikzCode)
    measureEnd2(measure, "footer")
    #    exit()
    measure = measureStart()
    generate_bib(biboutfile, [x for x in bibcontent if x[bibKeyID] in citationsToKeep])
    compile_latex('graph_summary', tex)
    measureEnd2(measure, "pdflatex + biber")
    measure = measureStart()


def generate_tikz_citationColor():
    tikzCode = ""
    tikzCode += "\\begin{tikzpicture}\n"
    tikzCode += "\\node at (-1,0.15) {least};\n"
    tikzCode += "\\node at (3,0.15) {most};\n"
    tikzCode += "\\node at (-1,-0.15) {citations};\n"
    tikzCode += "\\node at (3,-0.15) {citations};\n"
    tikzCode += "\\draw[citationcolor0, line width=8] (0,0) -- (0.2,0);\n"
    tikzCode += "\\draw[citationcolor1, line width=8] (0.2,0) -- (0.4,0);\n"
    tikzCode += "\\draw[citationcolor2, line width=8] (0.4,0) -- (0.6,0);\n"
    tikzCode += "\\draw[citationcolor3, line width=8] (0.6,0) -- (0.8,0);\n"
    tikzCode += "\\draw[citationcolor4, line width=8] (0.8,0) -- (1.0,0);\n"
    tikzCode += "\\draw[citationcolor5, line width=8] (1.0,0) -- (1.2,0);\n"
    tikzCode += "\\draw[citationcolor6, line width=8] (1.2,0) -- (1.4,0);\n"
    tikzCode += "\\draw[citationcolor7, line width=8] (1.4,0) -- (1.6,0);\n"
    tikzCode += "\\draw[citationcolor8, line width=8] (1.6,0) -- (1.8,0);\n"
    tikzCode += "\\draw[citationcolor9, line width=8] (1.8,0) -- (2.0,0);\n"
    tikzCode += "\\draw[citationcolor10, line width=8] (2.0,0) -- (2.2,0);\n"
    tikzCode += "\\end{tikzpicture}\n"
    return tikzCode


def generate_tikz_citations(sharedAuthors):
    tikzCode = ""
    tikzCode += "\\begin{tikzpicture}\n"
    tikzCode += "\\node[draw=black, rounded corners, text=black] at (-1.5,0) {[R] \\sesupsub{a}{b}};\n"
    tikzCode += "\\node[align=left,minimum width=3,text width=3cm] at (0,-0.6) {R: Reference};\n"
    if sharedAuthors:
        tikzCode += "\\node[align=left,minimum width=3,text width=3cm] at (0,-1.4) {colored articles};\n"
        tikzCode += "\\node[align=left,minimum width=3,text width=3cm] at (0,-1.8) {share authors};\n"
        tikzCode += "\\node[align=left,minimum width=3,text width=3cm] at (0,-2.2) {a: direct citations};\n"
        tikzCode += "\\node[align=left,minimum width=3,text width=3cm] at (0,-2.6) {b: indirect citations};\n"
    else:
        tikzCode += "\\node[align=left,minimum width=3,text width=3cm] at (0,-1) {a: direct citations};\n"
        tikzCode += "\\node[align=left,minimum width=3,text width=3cm] at (0,-1.4) {b: indirect citations};\n"
    tikzCode += "\\end{tikzpicture}\n"
    return tikzCode


def generate_tikz_bold():
    tikzCode = ""
    tikzCode += "\\begin{tikzpicture}\n"
    tikzCode += "\\draw[line width=2.5, ->] (0,0) -- (1,0);\n"
    tikzCode += "\\node[align=left,minimum width=3,text width=4cm] at (3.2,0) {left out transitive edges increase arrow size};\n"
    tikzCode += "\\end{tikzpicture}\n"
    return tikzCode
