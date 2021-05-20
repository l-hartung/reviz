from utils.utils import compare_edges, compare_edges_numerical, article_match_criterion, compare_candidates
from views.component_finder import CandidateComponentFinder
import gc


def calculate_merge_three(matches, candidate, subgraph, deviation, len_factor, dev_factor):
    """
    calculates possible merges of three nodes and selects the best of them
    :param matches: list of two-merge-candidates that share articles and could possibly be merged together
    :param candidate: currently examined merge candidate of two nodes
    :param subgraph: currently examined subgraph
    :param deviation: number of edges that are allowed to deviate within a merge node
    :param len_factor: factor to weight the number of all shared edges
    :param dev_factor: factor to weight the number of differed edges
    :return: list of best candidates to merge three nodes
    """
    mt = []
    for match in matches:
        if candidate == match:
            continue
        if (candidate['art1'] == match['art1']) or (candidate['art2'] == match['art1']):
            art1 = list(filter(lambda x: candidate['art1'] == x['key'], subgraph['articles']))[0]
            art2 = list(filter(lambda x: candidate['art2'] == x['key'], subgraph['articles']))[0]
            art3 = list(filter(lambda x: match['art2'] == x['key'], subgraph['articles']))[0]
        elif (candidate['art1'] == match['art2']) or (candidate['art2'] == match['art2']):
            art1 = list(filter(lambda x: candidate['art1'] == x['key'], subgraph['articles']))[0]
            art2 = list(filter(lambda x: candidate['art2'] == x['key'], subgraph['articles']))[0]
            art3 = list(filter(lambda x: match['art1'] == x['key'], subgraph['articles']))[0]
        same_f, diff1_f, diff2_f, diff3_f, diff12_f, diff23_f, diff13_f = compare_candidates(art1, art2, art3,
                                                                                             'from')
        same_t, diff1_t, diff2_t, diff3_t, diff12_t, diff23_t, diff13_t = compare_candidates(art1, art2, art3,
                                                                                             'to')
        diff_sum = diff1_f + diff2_f + diff3_f + diff1_t + diff2_t + diff3_t
        diff_sum_2 = diff12_f + diff12_t + diff23_f + diff23_t + diff13_f + diff13_t
        if (len(diff_sum) <= deviation) and (len(diff_sum_2) <= deviation):
            c_len = float(len(same_f) + len(same_t))
            score = c_len * len_factor - len(diff_sum) * dev_factor
            three_candidate = {
                'art1': art1['key'], 'art2': art2['key'], 'art3': art3['key'], 'same_from': same_f,
                'diff1_from': diff1_f, 'diff2_from': diff2_f, 'diff3_from': diff3_f, 'diff12_from': diff12_f,
                'diff23_from': diff23_f, 'diff13_from': diff13_f, 'same_to': same_t, 'diff1_to': diff1_t,
                'diff2_to': diff2_t, 'diff3_to': diff3_t, 'diff12_to': diff12_t, 'diff23_to': diff23_t,
                'diff13_to': diff13_t, 'dev': len(diff_sum), 'dev2': len(diff_sum_2), 'score': score
            }
            mt.append(three_candidate)
    return mt


def calculate_merges(subgraph, deviation, minimum_citations):
    """
    calculates all possible node-merges of a subgraph given a specific number of edge deviations allowed for merge nodes
    and selects the best of them
    :param subgraph: currently examined subgraph
    :param deviation: number of edges that are allowed to deviate within a merge node
    :param minimum_citations: only nodes with the given number of citations are merged
    :return: list of all calculated merges with their particular articles and shared or differed edges
    """
    merge_candidates = []
    len_factor = 1
    dev_factor = 0.5
    for i in range(len(subgraph['articles'])):
        art1 = subgraph['articles'][i]
        for j in range(i+1,len(subgraph['articles'])-1,1):
            art2 = subgraph['articles'][j]
            if (art1['key'] == art2['key']) or (art1['year'] != art2['year']):
                continue
            if any(filter(lambda mc: mc['art1'] == art2['key'] and mc['art2'] == art1['key'], merge_candidates)):
                continue
            if(len(art1['to'])<minimum_citations or len(art2['to'])<minimum_citations):
                continue
            
            same_fromSize = 0
            diff1_fromSize = 0
            for elem in art1['from']:
                if elem in art2['from']:
                    same_fromSize = same_fromSize + 1
                else:
                    diff1_fromSize = diff1_fromSize + 1
            diff2_fromSize = 0
            for elem in art2['from']:
                if not(elem in art1['from']):
                    diff2_fromSize = diff2_fromSize + 1
            
            same_toSize = 0
            diff1_toSize = 0
            for elem in art1['to']:
                if elem in art2['to']:
                    same_toSize = same_toSize + 1
                else:
                    diff1_toSize = diff1_toSize + 1
            diff2_toSize = 0
            for elem in art2['to']:
                if not(elem in art1['to']):
                    diff2_toSize = diff2_toSize + 1
            
            diff_sumSize = diff1_fromSize + diff2_fromSize + diff1_toSize + diff2_toSize
            if (diff_sumSize <= deviation) and (same_fromSize + same_toSize > 0):
                same_from, diff1_from, diff2_from = compare_edges(art1['from'], art2['from'])
                same_to, diff1_to, diff2_to = compare_edges(art1['to'], art2['to'])
                c_len = float(same_fromSize + same_toSize)
                score = c_len * len_factor - diff_sumSize * dev_factor
                candidate = {
                    'art1': art1['key'], 'art2': art2['key'], 'same_from': same_from, 'diff1_from': diff1_from,
                    'diff2_from': diff2_from, 'same_to': same_to, 'diff1_to': diff1_to, 'diff2_to': diff2_to,
                    'dev': diff_sumSize, 'score': score
                }
                merge_candidates.append(candidate)

    ccf = CandidateComponentFinder(merge_candidates)
    candidate_components = ccf.merge_candidate_components()

    print("iterate through candidate components...")
    merges = []
    for comp in candidate_components:
        indices = list(range(len(comp)))
        while len(indices) > 0:
            merge_three_candidates = []
            merge_three = None
            index = indices.pop(0)
            candidate = comp[index]
            flag = False
            for m in merges:
                if 'art3' in m:
                    if (candidate['art1'] == m['art1']) or (candidate['art1'] == m['art2']) \
                            or (candidate['art1'] == m['art3']) or (candidate['art2'] == m['art1']) \
                            or (candidate['art2'] == m['art2']) or (candidate['art2'] == m['art3']):
                        flag = True
                        break
            if flag:
                continue
            candidates = []
            for i in indices:
                candidates.append(comp[i])
            matches = list(filter(lambda c: article_match_criterion(candidate, c), candidates))
            merge_three_candidates = calculate_merge_three(matches, candidate, subgraph, deviation, len_factor, dev_factor)
            candidates.append(candidate)
            for c in candidates:
                matches = list(filter(lambda x: article_match_criterion(c, x), candidates))
                mt = calculate_merge_three(matches, c, subgraph, deviation, len_factor, dev_factor)
                for m in mt:
                    merge_three_candidates.append(m)
            if len(merge_three_candidates) != 0:
                score = 0
                for mtc in merge_three_candidates:
                    if mtc['score'] > score:
                        score = mtc['score']
                        merge_three = mtc
                if merge_three is not None:
                    merges.append(merge_three)
                    for match in matches:
                        if comp.index(match) in indices:
                            indices.remove(comp.index(match))
                    for can in candidates:
                        if (can['art1'] == merge_three['art3']) or (can['art2'] == merge_three['art3']):
                            if comp.index(can) in indices:
                                indices.remove(comp.index(can))


        indices = list(range(len(comp)))
        while len(indices) > 0:
            index = indices.pop(0)
            candidate = comp[index]
            flag = False
            for m in merges:
                if 'art3' in m:
                    if (candidate['art1'] == m['art1']) or (candidate['art1'] == m['art2']) \
                            or (candidate['art1'] == m['art3']) or (candidate['art2'] == m['art1']) \
                            or (candidate['art2'] == m['art2']) or (candidate['art2'] == m['art3']):
                        flag = True
                        break
            if flag:
                continue
            candidates = []
            for i in indices:
                candidates.append(comp[i])
            matches = list(filter(lambda c: article_match_criterion(candidate, c), candidates))
            if len(matches) == 0:
                merges.append(candidate)
            else:
                score = candidate['score']
                best = candidate
                for match in matches:
                    if match['score'] > score:
                        score = match['score']
                        best = match
                    toBeRemoved = comp.index(match)
                    if toBeRemoved in indices:
                        indices.remove(comp.index(match))
                    else :
                        print("The following item is not in indices:")
                        print(toBeRemoved)
                        print("indices:")
                        print(indices)
                merges.append(best)
    return merges
