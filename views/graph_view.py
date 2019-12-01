import os
from utils.latex import build_all
from views.component_finder import ComponentFinder
from utils.utils import depth_first_search, calculate_indirect_citations
from views import graph_layout
from views.calculate_merges import calculate_merges
from views.author_matching import find_same_authors


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


def generate_correction_table(global_merges, trans_edges_leave):
    """
    generates table containing edge correction and left out transitive edges for the legend
    :param global_merges: list of all merged nodes
    :param trans_edges_leave: list of all left out transitive edges
    :return: tikz code for the table
    """
    mergeCode = ''
    for merge in global_merges:
        mergeCode += edge_correction(merge, 'diff1_from', '+', 'from', 'art1')
        mergeCode += edge_correction(merge, 'diff2_from', '+', 'from', 'art2')
        mergeCode += edge_correction(merge, 'diff1_to', '+', 'to', 'art1')
        mergeCode += edge_correction(merge, 'diff2_to', '+', 'to', 'art2')
        if 'art3' in merge:
            mergeCode += edge_correction(merge, 'diff3_from', '+', 'from', 'art3')
            mergeCode += edge_correction(merge, 'diff3_to', '+', 'to', 'art3')
            mergeCode += edge_correction(merge, 'diff12_from', '-', 'from', 'art3')
            mergeCode += edge_correction(merge, 'diff23_from', '-', 'from', 'art1')
            mergeCode += edge_correction(merge, 'diff13_from', '-', 'from', 'art2')
            mergeCode += edge_correction(merge, 'diff12_to', '-', 'to', 'art3')
            mergeCode += edge_correction(merge, 'diff23_to', '-', 'to', 'art1')
            mergeCode += edge_correction(merge, 'diff13_to', '-', 'to', 'art2')
    transCode = ''
    for trans in trans_edges_leave:
        if trans.from_node.kind == 'Merge':
            from_name = '\\cite[...]{{{}}}'.format(trans.from_node.data['art1']['key'])
        else:
            from_name = '\\cite{{{}}}'.format(trans.from_node.name)
        if trans.to_node.kind == 'Merge':
            to_name = '\\cite[...]{{{}}}'.format(trans.to_node.data['art1']['key'])
        else:
            to_name = '\\cite{{{}}}'.format(trans.to_node.name)
        transCode += '''$+$ ({},{})\\newline'''.format(from_name, to_name)

    if trans_edges_leave != [] and global_merges != []:
        tikzCode = '''
        \\scriptsize
        \\begin{{tabular}}[c]{{p{{3.3cm}}p{{4cm}}}}
        {{Edge corrections \\newline
        for merged nodes:}} &
        {{Left out transitive\\newline
        citations:}} \\\\
        {}& {}
        \\end{{tabular}}'''.format(mergeCode, transCode)
    elif trans_edges_leave != []:
        tikzCode = '''
        \\scriptsize
        \\begin{{tabular}}{{p{{4cm}}}}
        {{Left out transitive\\newline
        citations:}} \\\\
        {}
        \\end{{tabular}}'''.format(transCode)
    elif global_merges != []:
        tikzCode = '''
        \\scriptsize
        \\begin{{tabular}}{{p{{3.5cm}}}}
        {{Edge corrections \\newline
        for merged nodes:}} \\\\
        {}
        \\end{{tabular}}'''.format(mergeCode)
    else:
        tikzCode = ''
    return tikzCode


def edge_correction(merge, d, pm, tf, art):
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
                tc += '''
                ${}$ (\\cite{{{}}},\\cite{{{}}}) \\newline'''.format(pm, diff1, merge[art])
                tc += '''
                ${}$ (\\cite{{{}}},\\cite{{{}}}) \\newline'''.format(pm, diff2, merge[art])
            else:
                tc += '''
                ${}$ (\\cite{{{}}},\\cite{{{}}}) \\newline'''.format(pm, diff, merge[art])
        elif tf == 'from':
            if len(diff) == 12:
                diff1 = diff[:6]
                diff2 = diff[6:]
                tc += '''
                ${}$ (\\cite{{{}}},\\cite{{{}}}) \\newline'''.format(pm, merge[art], diff1)
                tc += '''
                ${}$ (\\cite{{{}}},\\cite{{{}}}) \\newline'''.format(pm, merge[art], diff2)
            else:
                tc += '''
                ${}$ (\\cite{{{}}},\\cite{{{}}}) \\newline'''.format(pm, merge[art], diff)
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


def generate_tikz_header(tikzpic=True):
    """
    generates head of tex-file
    :param tikzpic: if True include begin{tikzpicture} after begin{document}
    :return: tex-header
    """
    tikzCode = """ 
        \\RequirePackage{luatex85}
        \\documentclass{standalone}
        \\usepackage{tikz}
        \\usepackage[style=alphabetic]{biblatex}
        \\usetikzlibrary{positioning}
        \\usepackage[utf8]{inputenc}
        \\usepackage[T1]{fontenc}
        \\usepackage{filecontents}
        \\usetikzlibrary{graphdrawing}
        \\usetikzlibrary{graphs}
        \\usegdlibrary{layered}
        %\\usegdlibrary{force}
        \\usepackage{tikz-layers}
        \\def\SPSB#1#2{\\rlap{\\textsuperscript{#1}}\\SB{#2}}
        \\def\SP#1{\\textsuperscript{#1}}
        \\def\SB#1{\\textsubscript{#1}}
        \\usepackage{tcolorbox}
        \\DeclareFieldFormat{postnote}{#1}
        
        \\usepackage{stackengine}
        \\setstackgap{L}{.7\\baselineskip}
        \\setstackgap{S}{2.3pt}
        \\def\\stacktype{S}
        \\def\\stackalignment{l}
        \\def\\sesupsub#1#2{\\scriptsize\\stackanchor{#1}{#2}}
        
        \\definecolor{transcolor2}{HTML}{1586D1}
        \\definecolor{transcolor3}{HTML}{1377BA}
        \\definecolor{transcolor4}{HTML}{1068A3}
        \\definecolor{transcolor5}{HTML}{0E598C}
        \\definecolor{transcolordefault}{HTML}{0C4B74}
        
        \\definecolor{authorcolor1}{HTML}{0101DF}
        \\definecolor{authorcolor2}{HTML}{31B404}
        \\definecolor{authorcolor3}{HTML}{DF0101}
        \\definecolor{authorcolor4}{HTML}{F19104}
        \\definecolor{authorcolor5}{HTML}{FE2E9A}
        \\definecolor{authorcolor6}{HTML}{01DFD7}
        \\definecolor{authorcolor7}{HTML}{40FF00}
        
        \\definecolor{citationcolor0}{HTML}{FF0000}
        \\definecolor{citationcolor1}{HTML}{E51900}
        \\definecolor{citationcolor2}{HTML}{CC3300}
        \\definecolor{citationcolor3}{HTML}{B24C00}
        \\definecolor{citationcolor4}{HTML}{996600}
        \\definecolor{citationcolor5}{HTML}{7F7F00}
        \\definecolor{citationcolor6}{HTML}{669900}
        \\definecolor{citationcolor7}{HTML}{4CB200}
        \\definecolor{citationcolor8}{HTML}{33CC00}
        \\definecolor{citationcolor9}{HTML}{19E500}
        \\definecolor{citationcolor10}{HTML}{00FF00}
        
        \\addbibresource{library.bib}
        
        \\begin{document}"""
    if tikzpic:
        tikzCode += '''
        \\begin{tikzpicture}'''
    return tikzCode


def generate_tikz_foot(tikzpic=True):
    """
    generates end of tex-file
    :param tikzpic: if True include end{tikzpicture} before end{document}
    :return: tex-foot
    """
    if tikzpic:
        tikzCode = '''
        \\end{tikzpicture}
        \\end{document}'''
    else:
        tikzCode = '''
        \\end{document}
        '''
    return tikzCode


def view_sugiyama(graph, tex):
    """
    render graph model to citation graph without optimizations
    :param graph: json graph model
    :param tex: folder where to put generated files
    """

    years = graph['years']
    min_year = min(years)
    max_year = max(years)

    cf = ComponentFinder(graph)
    cf.merge_components()
    subgraphs = cf.get_subgraphs()

    tikzCode = generate_tikz_header(False)

    tikzCode += '''
        {\\renewcommand{\\arraystretch}{2}%
        \\begin{tabular}{l}
        '''

    for subgraph in subgraphs:
        subgraph['years'] = years
        gl = graph_layout.GraphLayouter(subgraph)
        gl.insert_dummys()
        gl.crossing_minimization()

        tikzCode += '''
        \\begin{tikzpicture}[every node/.style={draw, rounded corners, text opacity=100, fill=white, minimum width=1.7cm},
        every edge/.style={draw=black, ->, >=stealth}]
        '''

        x_factor = 2
        y_factor = 0.8
        for layer_id, layer in enumerate(gl.layers):
            if len(layer.nodes) > 0:
                for node in layer.nodes:
                    if node.kind == 'Dummy':
                        node.x_coordinate = layer_id * x_factor
                        node.y_coordinate = node.slot * y_factor
                    else:
                        tikzCode += '''
                        \\node ({}) at ({},{}) {{\\cite{{{}}}}};'''.format(node.name, layer_id*x_factor, node.slot*y_factor, node.name)
            else:
                tikzCode += '''
                \\node [draw=none, opacity=0] at ({},{}) {{}};'''.format(layer_id*x_factor, y_factor)
        tikzCode += '''
        \\begin{scope}[on background layer]'''
        for edge in gl.short_edges:
            tikzCode += '''
            \\draw ({}) edge[bend right] ({});'''.format(edge.from_node.name, edge.to_node.name)
        for edge in gl.long_edges:
            dummy_list = []
            start = edge.from_node.name
            end = edge.to_node.name
            for de in edge.dummyedges:
                dummy_list.append(de.from_node)
            del dummy_list[-1]
            dummy_list.reverse()
            middle = ''
            for dummy in dummy_list:
                middle += ' -- ({},{})'.format(dummy.x_coordinate, dummy.y_coordinate)
            tikzCode += '''
            \\draw ({}) edge[bend right] ({});'''.format(start, end)

        if subgraph == subgraphs[-1]:
            years_dist = max_year - min_year + 1
            previous = 0
            for year in range(0, years_dist):
                if year == 0:
                    tikzCode += '''
                        \\node ({})[draw=none] {{{}}};'''.format(year, '|')
                else:
                    tikzCode += '''
                        \\node ({})[right= 0.29cm of {}, draw=none] {{{}}};'''.format(year, previous, '|')
                    previous = year

            scale_const = 2
            tikzCode += '''\\draw[thick, ->] (0,0) -- ({},0);'''.format(scale_const * years_dist - 1)

            for year in range(0, years_dist):
                tikzCode += '''
                        \\node ({}) [below= 0.07cm of {}, draw=none] {{{}}};'''.format(min_year + year, year,
                                                                                       min_year + year)

        tikzCode += '''
        \\end{scope}
        \\end{tikzpicture}
        \\\\
        '''

    tikzCode += '''
    \\end{tabular}
    } %end arraystretch'''

    tikzCode += generate_tikz_foot(False)

    with open(os.path.join(tex, 'graph.tex'), 'w') as file:
        file.write(tikzCode)

    build_all('graph', tex)


def view_sugiyama_summary(graph, tex, deviation, transitivities, trans_bold, citations, authors_colored):
    """
    render graph model into citation graph with optional optimizations
    :param graph: json graph model
    :param tex: folder where to put tex-files
    :param deviation: maximum allowed edge deviations for merge nodes
    :param transitivities: summarizes transitive edges
    :param trans_bold: adapt line width of transitive edges
    :param citations: count number of direct and indirect citations for every noce
    :param authors_colored: color publications with same authors
    """

    years = graph['years']
    min_year = min(years)
    max_year = max(years)

    # for evaluation
    edge_dict = {}
    node_fromEdges = 0
    node_toEdges = 0
    node_edges = 0
    node_counter = 0.0
    for i in range(max_year-min_year+1):
        edge_dict[i] = 0

    if authors_colored:
        match_authors = find_same_authors(graph['articles'], 0.3)

        cluster_color_dict = {1: 'authorcolor1',
                             2: 'authorcolor5',
                             3: 'authorcolor4',
                             4: 'authorcolor2',
                             5: 'authorcolor3',
                             6: 'authorcolor7',
                             7: 'authorcolor6',
                             -1: 'black'}

        match_author_dict = {art['key']:'black' for art in graph['articles']}

        for id, match in enumerate(match_authors):
            for m in match:
                if id+1 in cluster_color_dict:
                    match_author_dict[m] = cluster_color_dict[id+1]

    cf = ComponentFinder(graph)
    cf.merge_components()
    subgraphs = cf.get_subgraphs()

    tikzCode = generate_tikz_header(False)

    tikzCode += '''
        {\\renewcommand{\\arraystretch}{2}%
        \\begin{tabular}[t]{l}
        '''

    global_merges = []
    trans_edges_leave = []

    for subgraph in subgraphs:
        merges = calculate_merges(subgraph, deviation)
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
        gl.insert_dummys()
        gl.crossing_minimization()

        tikzCode += '''
        \\begin{tikzpicture}[every node/.style={draw, rounded corners, text opacity=100, fill=white, minimum width=1.7cm},
        every edge/.style={draw=black, ->, >=stealth}]
        '''

        cit_list = []
        for node in gl.all_nodes():
            if citations:
                indcitations = []
                if node.kind != "Dummy":
                    if node.kind == "Merge":
                        node.citations1 = len(list(filter(lambda x: x['to'] == node.data['art1']['key'], graph['edges'])))
                        node.indcitations1 = len(
                            calculate_indirect_citations(node.data['art1']['key'], graph['edges'], indcitations))
                        node.citations2 = len(list(filter(lambda x: x['to'] == node.data['art2']['key'], graph['edges'])))
                        node.indcitations2 = len(
                            calculate_indirect_citations(node.data['art2']['key'], graph['edges'], indcitations))
                        cit_list.append(node.indcitations1)
                        cit_list.append(node.indcitations2)
                        if 'art3' in node.data:
                            node.citations3 = len(list(filter(lambda x: x['to'] == node.data['art3']['key'], graph['edges'])))
                            node.indcitations3 = len(
                                calculate_indirect_citations(node.data['art3']['key'], graph['edges'], indcitations))
                            cit_list.append(node.indcitations3)
                    else:
                        node.citations = len(list(filter(lambda x: x.to_node.name == node.name, gl.all_edges)))
                        node.indcitations = len(calculate_indirect_citations(node.name, graph['edges'], indcitations))
                        cit_list.append(node.indcitations)
            else:
                if node.kind!= "Dummy":
                    if node.kind == 'Merge':
                        node.citations1 = ''
                        node.citations2 = ''
                        node.indcitations1 = ''
                        node.indcitations2 = ''
                        if 'art3' in node.data:
                            node.citations3 = ''
                            node.indcitations3 = ''
                    else:
                        node.citations = ''
                        node.indcitations = ''

        if citations:
            max_cit = max(cit_list)

        citation_color_dict = {0: 'citationcolor0',
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
        y_factor = 1
        dummy_factor = 0.5
        merge_two_factor = 1.2
        merge_three_factor = 1.5
        for layer_id, layer in enumerate(gl.layers):
            y = 0.0
            if len(layer.nodes) > 0:
                for node in layer.nodes:
                    color = 'black'
                    color1 = 'black'
                    color2 = 'black'
                    color3 = 'black'
                    if node.kind == 'Dummy':
                        node.x_coordinate = layer_id * x_factor
                        node.y_coordinate = y
                        y += y_factor*dummy_factor
                    else:
                        if node.kind == 'Merge':
                            if authors_colored:
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
                                    box1 = '\\sesupsub{{\\tcbox[colback={}, colframe={}, arc=0pt, outer arc=0pt, boxsep=0pt, left=0.3pt, right=0.3pt, top=0pt, bottom=0pt]{{\\textbf{{\\color{{white}} {}}}}}}}{{\\tcbox[colback={}, colframe={}, arc=0pt, outer arc=0pt, boxsep=0pt, left=0.3pt, right=0.3pt, top=0pt, bottom=0pt]{{\\textbf{{\\color{{white}} {}}}}}}}'.format(fill1, fill1, node.citations1, indfill1, indfill1, node.indcitations1)
                                    box2 = '\\sesupsub{{\\tcbox[colback={}, colframe={}, arc=0pt, outer arc=0pt, boxsep=0pt, left=0.3pt, right=0.3pt, top=0pt, bottom=0pt]{{\\textbf{{\\color{{white}} {}}}}}}}{{\\tcbox[colback={}, colframe={}, arc=0pt, outer arc=0pt, boxsep=0pt, left=0.3pt, right=0.3pt, top=0pt, bottom=0pt]{{\\textbf{{\\color{{white}} {}}}}}}}'.format(fill2, fill2, node.citations2, indfill2, indfill2, node.indcitations2)
                                    box3 = '\\sesupsub{{\\tcbox[colback={}, colframe={}, arc=0pt, outer arc=0pt, boxsep=0pt, left=0.3pt, right=0.3pt, top=0pt, bottom=0pt]{{\\textbf{{\\color{{white}} {}}}}}}}{{\\tcbox[colback={}, colframe={}, arc=0pt, outer arc=0pt, boxsep=0pt, left=0.3pt, right=0.3pt, top=0pt, bottom=0pt]{{\\textbf{{\\color{{white}} {}}}}}}}'.format(fill3, fill3, node.citations3, indfill3, indfill3, node.indcitations3)
                                else:
                                    box1 = ''
                                    box2 = ''
                                    box3 = ''
                                table = '''\\bgroup \\def\\arraystretch{{1}}\\begin{{tabular}}{{@{{}}c@{{}}}} \\textcolor{{{}}}{{\\cite{{{}}}{}}} \\\\ \\textcolor{{{}}}{{\\cite{{{}}}{}}} \\\\ \\textcolor{{{}}}{{\\cite{{{}}}{}}} \\end{{tabular}} \\egroup'''.format(
                                    color1, node.data['art1']['key'], box1, color2,  node.data['art2']['key'], box2, color3, node.data['art3']['key'], box3)
                                tikzCode += '''
                                \\node ({}) [inner sep=0pt, align=center] at ({},{}) {{{}}};'''.format(
                                    name, layer_id*x_factor, y, table)
                                y += merge_three_factor
                            else:
                                y += 0.2
                                name = node.name
                                if citations:
                                    box1 = '\\sesupsub{{\\tcbox[colback={}, colframe={}, arc=0pt, outer arc=0pt, boxsep=0pt, left=0.3pt, right=0.3pt, top=0pt, bottom=0pt]{{\\textbf{{\\color{{white}}{}}}}}}}{{\\tcbox[colback={}, colframe={}, arc=0pt, outer arc=0pt, boxsep=0pt, left=0.3pt, right=0.3pt, top=0pt, bottom=0pt]{{\\textbf{{\\color{{white}}{}}}}}}}'.format(fill1, fill1, node.citations1, indfill1, indfill1, node.indcitations1)
                                    box2 = '\\sesupsub{{\\tcbox[colback={}, colframe={}, arc=0pt, outer arc=0pt, boxsep=0pt, left=0.3pt, right=0.3pt, top=0pt, bottom=0pt]{{\\textbf{{\\color{{white}}{}}}}}}}{{\\tcbox[colback={}, colframe={}, arc=0pt, outer arc=0pt, boxsep=0pt, left=0.3pt, right=0.3pt, top=0pt, bottom=0pt]{{\\textbf{{\\color{{white}}{}}}}}}}'.format(fill2, fill2, node.citations2, indfill2, indfill2, node.indcitations2)
                                else:
                                    box1 = ''
                                    box2 = ''
                                table = '''\\bgroup \\def\\arraystretch{{1}}  \\begin{{tabular}}{{@{{}}c@{{}}}} \\rule{{0pt}}{{4mm}}\\textcolor{{{}}}{{\\cite{{{}}} {}}} \\\\ \\textcolor{{{}}}{{\\cite{{{}}} {}}}\\rule{{0pt}}{{4mm}}\\end{{tabular}} \\egroup'''.format(
                                    color1, node.data['art1']['key'], box1, color2, node.data['art2']['key'], box2
                                )
                                tikzCode += '''
                                \\node ({}) [inner sep=0pt, align=center] at ({},{}) {{{}}};'''.format(
                                    name, layer_id*x_factor, y, table)
                                y += merge_two_factor
                        else:
                            if authors_colored:
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
                                box = '\\sesupsub{{\\tcbox[colback={}, colframe={}, arc=0pt, outer arc=0pt, boxsep=0pt, left=0.3pt, right=0.3pt, top=0pt, bottom=0pt]{{\\textbf{{\\color{{white}}{}}}}}}}{{\\tcbox[colback={}, colframe={}, arc=0pt, outer arc=0pt, boxsep=0pt, left=0.3pt, right=0.3pt, top=0pt, bottom=0pt]{{\\textbf{{\\color{{white}}{}}}}}}}'.format(fill, fill, node.citations, indfill, indfill, node.indcitations)
                            else:
                                box = ''
                            tikzCode += '''
                            \\node ({})[text={}] at ({},{}) {{\\cite{{{}}} {}}};'''.format(node.name, color, layer_id*x_factor, y, node.name, box)
                            y += y_factor

            else:
                tikzCode += '''
                \\node [draw=none, opacity=0] at ({},{}) {{}};'''.format(layer_id*x_factor, y_factor)
        tikzCode += '''
        \\begin{scope}[on background layer]'''

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
                        leave_ewi = next(x for x in edge_weight_dict if
                                         edge.from_node.name == x['from'] and edge.to_node.name == x['to'])
                        if leave_ewi['weight'] > 1:
                            additional_weight = leave_ewi['weight'] - 1
                        else:
                            additional_weight = 0
                        if trans_bold:
                            ewi = next(x for x in edge_weight_dict if stack[-1].from_node.name == x['from'] and stack[-1].to_node.name == x['to'])
                            ewi['weight'] += 1 + additional_weight

        # if trans_bold:
        #     weight_color_dict = {1: (0.4, 'black'),
        #                          2: (1.4, 'black'),
        #                          3: (1.7, 'black'),
        #                          4: (2.0, 'black'),
        #                          5: (2.3, 'black'),
        #                          -1: (2.6, 'black')
        #                          }
        if trans_bold:
            weight_color_dict = {1: (0.4, 'black'),
                                 2: (1.5, 'black'),
                                 3: (1.9, 'black'),
                                 4: (2.3, 'black'),
                                 5: (2.7, 'black'),
                                 -1: (3.1, 'black')
                                 }
        else:
            weight_color_dict = {1: (0.4, 'black')}

        for edge in gl.short_edges:
            if edge in trans_edges_leave:
                continue
            no_edge = _check_if_edge(edge)
            if not no_edge:
                if transitivities:
                    ewi = next(x for x in edge_weight_dict if edge.from_node.name == x['from'] and edge.to_node.name == x['to'])
                    if ewi['weight'] in weight_color_dict:
                        weight, color = weight_color_dict[ewi['weight']]
                    else:
                        weight, color = weight_color_dict[-1]
                else:
                    weight, color = weight_color_dict[1]
                tikzCode += '''
                \\draw ({}) edge[bend right, line width={}pt, color={}] ({});'''.format(edge.from_node.name,
                                                                            weight, color, edge.to_node.name)
        for edge in gl.long_edges:
            if edge in trans_edges_leave:
                continue
            no_edge = _check_if_edge(edge)
            if not no_edge:
                dummy_list = []
                start = edge.from_node.name
                end = edge.to_node.name
                for de in edge.dummyedges:
                    dummy_list.append(de.from_node)
                del dummy_list[-1]
                dummy_list.reverse()
                middle = ''
                for dummy in dummy_list:
                    middle += ' -- ({},{})'.format(dummy.x_coordinate, dummy.y_coordinate)
                if transitivities:
                    ewi = next(
                        x for x in edge_weight_dict if edge.from_node.name == x['from'] and edge.to_node.name == x['to'])
                    if ewi['weight'] in weight_color_dict:
                        weight, color = weight_color_dict[ewi['weight']]
                    else:
                        weight, color = weight_color_dict[-1]
                else:
                    weight, color = weight_color_dict[1]
                tikzCode += '''
                \\draw ({}) edge[bend right, line width={}pt, color={}] ({});'''.format(start, weight, color, end)

        if subgraph == subgraphs[-1]:
            years_dist = max_year - min_year + 1
            previous = 0
            for year in range(0, years_dist):
                if year == 0:
                    tikzCode += '''
                        \\node ({})[draw=none] at (0,-0.75) {{{}}};'''.format(year, '|')
                else:
                    tikzCode += '''
                        \\node ({})[right= 0.57cm of {}, draw=none] {{{}}};'''.format(year, previous, '|')
                    previous = year

            scale_const = 2.2
            tikzCode += '''\\draw[thick, ->] (0,-0.75) -- ({},-0.75);'''.format(scale_const * years_dist - 1)

            for year in range(0, years_dist):
                tikzCode += '''
                        \\node ({}) [below= 0.07cm of {}, draw=none] {{{}}};'''.format(min_year + year, year,
                                                                                       min_year + year)

        tikzCode += '''
        \\end{scope}
        \\end{tikzpicture}
        \\\\
        '''

        eval_trans_edges = []
        for edge in draw_edges:
            if edge not in trans_edges_leave:
                eval_trans_edges.append(edge)
        # für Kanten: gl.all_edges, draw_edges, eval_trans_edges
        edge_dict, node_fromEdges, node_toEdges, node_edges, node_counter = evaluation(gl.all_edges, gl.layers,
                                                                                       gl.all_nodes(), edge_dict,
                                                                                       node_fromEdges, node_toEdges,
                                                                                       node_edges, node_counter)
    # evaluation
    print(edge_dict)
    print(node_counter)
    node_fromEdges /= node_counter
    node_toEdges /= node_counter
    node_edges /= node_counter
    node_dict = {'fromEdgesPerNode': node_fromEdges, 'toEdgesPerNode': node_toEdges, 'edgesPerNode': node_edges}
    print(node_dict)

    correction_table = generate_correction_table(global_merges, trans_edges_leave)

    tikzCode += '''
    \\hspace{0.3cm}
    \\setlength{\\tabcolsep}{1pt}
    \\renewcommand{\\arraystretch}{1}%
    \\scriptsize'''

    if trans_bold or citations or authors_colored:
        if trans_bold and not citations and not authors_colored:
            tikzCode += '''
            \\begin{tabular}{p{5cm}}'''
        else:
            tikzCode += '''
            \\begin{tabular}[c]{p{2.6cm}p{5.3cm}}'''

    trans_bold_legend = '''
    \\begin{tikzpicture}
    \\draw[line width=2.5, ->] (0,0) -- (1,0);
    \\end{tikzpicture} \\parbox[c]{3cm}{left out transitive edges increase arrow size}'''

    if authors_colored:
        color = 'authorcolor1'
    else:
        color = 'black'

    if citations:
        tikzCode += '''
        \\begin{tikzpicture}'''
        tikzCode += '''
        \\node [draw=black, rounded corners, text={}] {{ [R] \\sesupsub{{{}}}{{{}}} }};'''.format(color, 'a', 'b')
        tikzCode += '''
        \\end{tikzpicture} \\newline'''
        tikzCode += '''
        R: Reference '''
        if authors_colored:
            tikzCode += '''\\newline (colored articles \\newline share authors) \\newline'''
        else:
            tikzCode += '''\\newline'''
        tikzCode += '''
        a: direct citations \\newline
        b: indirect citations &'''

        tikzCode += '''
        least \\begin{tikzpicture}'''
        tikzCode += '''
        \\draw[{}, line width=8] (0,0) -- (0.2,0);
        \\draw[{}, line width=8] (0.2,0) -- (0.4,0);
        \\draw[{}, line width=8] (0.4,0) -- (0.6,0);
        \\draw[{}, line width=8] (0.6,0) -- (0.8,0);
        \\draw[{}, line width=8] (0.8,0) -- (1.0,0);
        \\draw[{}, line width=8] (1.0,0) -- (1.2,0);
        \\draw[{}, line width=8] (1.2,0) -- (1.4,0);
        \\draw[{}, line width=8] (1.4,0) -- (1.6,0);
        \\draw[{}, line width=8] (1.6,0) -- (1.8,0);
        \\draw[{}, line width=8] (1.8,0) -- (2.0,0);
        \\draw[{}, line width=8] (2.0,0) -- (2.2,0);'''.format('citationcolor0', 'citationcolor1', 'citationcolor2',
                                                                'citationcolor3', 'citationcolor4', 'citationcolor5',
                                                                'citationcolor6', 'citationcolor7', 'citationcolor8',
                                                                'citationcolor9', 'citationcolor10')
        tikzCode += '''
        \\end{tikzpicture} \\parbox[c]{1.4cm}{most \\newline citations} \\newline '''
        tikzCode += '''\\rule{{0pt}}{{0.8cm}}'''

    if authors_colored and not citations:
        tikzCode += '''
               \\begin{tikzpicture}'''
        tikzCode += '''
               \\node [draw=black, rounded corners, text={}] {{ [R] }};'''.format(color)
        tikzCode += '''
        \\end{tikzpicture} \\newline
        R: Reference, \\newline
         colored articles \\newline share authors &'''

    if trans_bold:
        tikzCode += '''{}'''.format(trans_bold_legend)

    if trans_bold or citations or authors_colored:
        tikzCode += '''
        \\end{tabular}'''

    if years_dist <= 5:
        if correction_table != '':
            if citations or trans_bold or authors_colored:
                tikzCode += '\\\\'

    tikzCode += correction_table

    tikzCode += '''
    \\end{tabular}
    } %end arraystretch'''

    tikzCode += generate_tikz_foot(False)


    with open(os.path.join(tex, 'graph_summary.tex'), 'w') as file:
        file.write(tikzCode)

    build_all('graph_summary', tex)