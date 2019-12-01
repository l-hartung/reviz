import json
from utils.latex import build_all
import os


def run_flow(jsFile, tex):
    with open(jsFile, 'r') as file:
        jsonfile = json.load(file)

    sources = jsonfile['sources']
    articles = jsonfile['all articles']
    num_articles = articles.__len__()
    final_selection = jsonfile['final selection articles']
    num_final = final_selection.__len__()

    src = {}
    status_dict = {'A': 0, 'D': 0, 'R': 0}
    for article in articles:
        sourceID = article['source_id']
        status = article['status']
        status_dict[status] += 1
        for source in sources:
            if sourceID == source['id']:
                sourceName = source['name']
                if sourceName in src:
                    src[sourceName] += 1
                else:
                    src[sourceName] = 1

    src_list = list(src)
    num_srcs = src_list.__len__()

    tikzCode = '''
    \\documentclass{standalone}
    \\usepackage{tikz}
    \\usetikzlibrary{graphdrawing}
    \\usetikzlibrary{graphs}
    \\usegdlibrary{layered}
    
    \\begin{document}
    \\definecolor{babypink}{rgb}{1.0, 0.92, 0.8}
    \\begin{tikzpicture} [every node/.style={draw=black}, every edge/.style={draw=black, ->, thick, >=stealth}]
    \\graph [layered layout] {'''

    for i in range(num_srcs):
        tikzCode += '''
        {{s{} [align=center, as={{{}\\\\(n={})}}]}} -> [minimum layers=2]
        {{I [align=center, as={{Records identified for review\\\\(n={})}}]}};'''.format(i, src_list[i], src[src_list[i]], num_articles)

    tikzCode += '''
    I -> [minimum layers=2] {{D[align=center, as={{Records after duplicates removed\\\\(n={})}}]}};'''.format(num_articles - status_dict['D'])

    tikzCode += '''
    D -> [minimum layers=2] {{A[align=center, as={{Accepted records\\\\(n={})}}]}};
    D -> [minimum layers=2] {{E[align=center, as={{Records rejected by\\\\exclusion criteria (n={})}}]}};'''.format(status_dict['A'],
                                                                   num_articles - status_dict['D'] - status_dict['A'])

    tikzCode += '''
    A -> [minimum layers=2] {{Q[align=center, as={{Records rejected by\\\\quality criteria (n={})}}]}};
    A -> [minimum layers=2] {{F[align=center, color=red, text=black, fill=babypink, as={{Final selection records\\\\(n={})}}]}};'''.format(status_dict['A'] - num_final, num_final)

    tikzCode += '''
    {[same layer] D, E};
    {[same layer] A, Q};'''

    tikzCode += '''
    };
    \\end{tikzpicture}
    \\end{document}'''

    with open(os.path.join(tex, 'flow.tex'), 'w') as file:
        flow_file = file.write(tikzCode)

    build_all('flow', tex)