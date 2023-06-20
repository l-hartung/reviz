import hashlib
import re
import itertools
import bibtexparser
import json


def key_to_md5(key):
    """
    convert bibtex-key to shortened md5-sum to avoid special characters in the keys
    :param key: bibtex-key of an article
    :return: converted key, first six characters of the key md5-sum
    """
    m = hashlib.md5()
    m.update(key.encode('utf-8'))
    hd = m.hexdigest()
    shorthd = hd[:6]
    if shorthd.isdigit():
        return shorthd + 'a'
    return shorthd


def find_urls(string):
    """
    check if the given string contains an url, used to find the pdfs of all articles
    :param string: link to the pdf of an article
    :return: url if one is found
    """
    url = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', string)
    return url


def compare_edges_numerical(list1, list2):
    """
    compares all incoming or outgoing edges from two nodes to examine if they could be merged
    :param list1: list of all incoming or outgoing edges of a node
    :param list2: list of the second node
    :return: lists of all shared edges and different edges for both articles
    """
    same = 0
    diff1 = 0
    for elem in list1:
        if elem in list2:
            same = same + 1
        else:
            diff1 = diff1 + 1
    diff2 = 0
    for elem in list2:
        if not (elem in list1):
            diff2 = diff2 + 1
    return same, diff1, diff2


def compare_edges(list1, list2):
    """
    compares all incoming or outgoing edges from two nodes to examine if they could be merged
    :param list1: list of all incoming or outgoing edges of a node
    :param list2: list of the second node
    :return: lists of all shared edges and different edges for both articles
    """
    same = []
    diff1 = []
    for elem in list1:
        if elem in list2:
            same.append(elem)
        else:
            diff1.append(elem)
    diff2 = list(set(list2) - set(same))
    return same, diff1, diff2


def compare_candidates(art1, art2, art3, ft):
    """
    compare edges of three nodes and calculate their shared and differed edges to examine if they could be merged
    :param art1: first article to compare
    :param art2: second article
    :param art3: third article
    :param ft: 'from' or 'to', determines if incoming or outgoing edges are examined
    :return: lists of shared edges and different edges in all combinations
    """
    same = []
    diff1 = []
    diff2 = []
    diff3 = []
    diff12 = []
    diff13 = []
    diff23 = []
    for elem in art1[ft]:
        if (elem in art2[ft]) and (elem in art3[ft]):
            same.append(elem)
        elif (elem in art2[ft]) and (elem not in art3[ft]):
            diff12.append(elem)
        elif (elem not in art2[ft]) and (elem in art3[ft]):
            diff13.append(elem)
        else:
            diff1.append(elem)
    for elem in art2[ft]:
        if (elem in same) or (elem in diff12):
            continue
        elif (elem in art3[ft]) and (elem not in art1[ft]):
            diff23.append(elem)
        else:
            diff2.append(elem)
    for elem in art3[ft]:
        if (elem in same) or (elem in diff23) or (elem in diff13):
            continue
        else:
            diff3.append(elem)
    return same, diff1, diff2, diff3, diff12, diff23, diff13


def article_match_criterion(c1, c2):
    """
    check if two merge candidates(consisting of two nodes each) share an article
    :param c1: first merge candidate
    :param c2: second candidate
    :return: True iff the candidates share an article
    """
    if c1['art1'] == c2['art1'] or c1['art1'] == c2['art2']:
        return True
    if c1['art2'] == c2['art1'] or c1['art2'] == c2['art2']:
        return True
    return False


def find_author(author_json):
    '''
    detect correct surnames of all authors out of the author-bibtex-field
    :param author_json: author-field of an article from json export
    :return: list of all surnames
    '''
    if ',' not in author_json:
        pattern = re.compile(r"(?P<name>[A-Za-z\-]+)(?: +and +| +AND +|$)")
    else:
        pattern = re.compile(r"(?:^|and +|AND +)(?P<name>[A-Za-z\- ]+)")
    authors = pattern.findall(author_json)
    return authors


def depth_first_search(efrom, edge, eto, draw_edges, stack, tel):
    '''
    depth-first-search to detect transitive edges
    :param efrom: node from which the current edge rises
    :param edge: current edge to examine
    :param eto: node to which the current edge goes to
    :param draw_edges: list of all edges that will be drawn in the resulting graph
    :param stack: list of elements to remember for the depth-first-search, empty at the beginning
    :param tel: list of transitive edges that have already been found and will not be drawn in the resulting graph
    :return: True iff the search was successful and the latest stack
    '''
    elist = filter(lambda e: e.from_node == efrom and e != edge and e not in tel, draw_edges)
    elist_it1, elist_it2 = itertools.tee(elist, 2)
    for elem in elist_it1:
        if eto == elem.to_node:
            stack.append(elem)
            return True, stack
    for ed in elist_it2:
        if not (ed in stack):  # in order to avoid infinite loops!
            stack.append(ed)
            s, stack = depth_first_search(ed.to_node, edge, eto, draw_edges, stack, tel)
            if not s:
                stack.pop()
            else:
                return True, stack
    return False, stack


def calculate_indirect_citations(node, edges, citations):
    """
    depth-first-search to calculate the number of indirect citations for an article
    :param node: name of the current node
    :param edges: list of all existing edges in the graph
    :param citations: list to save all citations, empty at the beginning
    :return: list of all citations
    """
    edge_list = list(filter(lambda e: e['to'] == node, edges))
    for edge in edge_list:
        f_node = edge['from']
        if f_node not in citations:
            citations.append(f_node)
            citations = calculate_indirect_citations(f_node, edges, citations)
    return citations


def bib_to_json(jsonpath, bib):
    """
    cnverts bibtex file in json with same composition as the parsifal json export
    :param jsonpath: path to resulting json file
    :param bib: path to bibtex file
    """
    with open(bib) as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    entries = []
    for e in bib_database.entries:
        e['bibtex_key'] = e.pop('ID')
        e['document_type'] = e.pop('ENTRYTYPE')
        entries.append(e)
    j = {'final selection articles': entries}
    with open(jsonpath, 'w') as jf:
        json.dump(j, jf, indent=2)
