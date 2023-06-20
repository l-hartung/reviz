from fuzzywuzzy import fuzz


def find_same_authors(articles, threshold):
    """
    examines all combination of articles for shared authors, checks if their score of shared authors is high enough,
    checks for combinations of these candidates
    :param articles: list of all articles from graph model
    :param threshold: determines if the score of shared authors of two articles is high enough
    :return: list of lists of articles with same authors
    """
    matches = []
    all_matches = []
    scores = []
    for a1 in articles:
        for a2 in articles:
            flag = True
            if a1 == a2:
                continue
            for m in matches:
                if (m['art1'] == a1 and m['art2'] == a2) or (m['art2'] == a1 and m['art1'] == a2):
                    flag = False
            if flag:
                counter, number = find_matching_authors(a1['author'], a2['author'])
                if counter != 0:
                    score = counter / number
                    scores.append(score)
                    match = {'art1': a1, 'art2': a2, 'score': score}
                    all_matches.append(match)
    max_score = max(scores)
    for m in all_matches:
        m['score'] /= max_score
    matches = [x for x in all_matches if x['score'] >= threshold]
    sorted_matches = sorted(matches, key=lambda x: x['score'], reverse=True)
    list_matches = []
    for sm in sorted_matches:
        m1 = sm['art1']['key']
        m2 = sm['art2']['key']
        list_matches.append([m1, m2])
    available_matches = list(list_matches)
    matching_author_list = []
    for sm in list_matches:
        if sm in available_matches:
            available_matches.remove(sm)
            sm_current, available_matches = cluster_candidates(sm, list_matches, available_matches)
            matching_author_list.append(sm_current)
    return matching_author_list


def find_matching_authors(artauthors, otherauthors):
    """
    calculates the total number of authors and the number of shared authors taking into account first authors
    :param artauthors: authors of first examined article
    :param otherauthors: authors of second article
    :return: two paramenters to calculate the score of the two articles
    """
    counter = 0
    number = len(artauthors) + len(otherauthors)
    if len(artauthors) == 0 or len(otherauthors) == 0:
        return counter, number
    for author in artauthors:
        if author == artauthors[0]:
            if author == otherauthors[0]:
                counter += 5
                number -= 1
            elif next((a for a in otherauthors if fuzz.ratio(author.upper(), a.upper()) >= 95), None) is not None:
                counter += 3
                number -= 1
        elif author == otherauthors[0]:
            counter += 3
            number -= 1
        elif next((a for a in otherauthors if fuzz.ratio(author.upper(), a.upper()) >= 95), None) is not None:
            counter += 1
            number -= 1
    return counter, number


def candidate_matches(o, sm_current, list_matches):
    """
    checks if an article shares authors with all other articles in a list
    :param o: examined article
    :param sm_current: list of articles that share authors
    :param list_matches: list of all combinations of two articles that share authors
    :return: True iff o shares articles with all articles in sm_current
    """
    for elem in sm_current:
        if [elem, o] not in list_matches and [o, elem] not in list_matches:
            return False
    return True


def cluster_candidates(sm, list_matches, av_matches):
    """
    finds clusters of articles that share authors
    :param sm: combination of two articles that share authors
    :param list_matches: list of all combinations of two articles that share authors
    :param av_matches: all combinations of two articles that share authors that are still available for other combinations
    :return: updates list of currently examined articles that share authors, updates list of available matches
    """
    sm_current = list(sm)
    for elem in av_matches:
        for i in range(2):
            if elem[i] in sm_current:
                if elem[1 - i] not in sm_current:
                    if candidate_matches(elem[1 - i], sm_current, list_matches):
                        sm_current.append(elem[1 - i])
    for elem in list(av_matches):
        if elem[0] in sm_current or elem[1] in sm_current:
            av_matches.remove(elem)
    return sm_current, av_matches
