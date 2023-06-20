from fuzzywuzzy import fuzz
import re
from views.author_matching import find_matching_authors


def find_doi(input):
    """
    checks if the doi of an article is syntactically correct or empty
    :param input: doi of an article
    :return: correct doi if found, otherwise None
    """
    if input is None:
        return None
    regex = r"(\d\d\.\d+\/\S+)"
    regex = re.compile(regex)
    m = regex.search(input)
    if m is not None:
        return m.group()
    return None


def citation_matching(doi_art, doi_ref, title_art, title_ref, author_art, authors_ref, without_interactive_queries):
    """
    checks if a reference and an article of the citation graph match, if yes a citation is found
    :param doi_art: doi of the article
    :param doi_ref: doi of the reference
    :param title_art: article title
    :param title_ref: reference title
    :param author_art: article authors
    :param authors_ref: reference authors
    :param without_interactive_queries: true for interactive mode
    :return: True iff a match is found
    """
    doi_art = find_doi(doi_art)
    doi_ref = find_doi(doi_ref)
    if doi_art == doi_ref and doi_art is not None and doi_ref is not None:
        return True
    else:
        lev = fuzz.ratio(title_art.upper(), title_ref.upper())
        lev_partial = fuzz.partial_ratio(title_art.upper(), title_ref.upper())
        if lev > 90 or (lev_partial > 95 and lev > 70):
            counter, number = find_matching_authors(author_art, authors_ref)
            if counter >= 2:
                return True
            else:
                if (without_interactive_queries):
                    return False
                print('Article:  Title = ' + title_art + '\n\t\t  Authors = ' + str(author_art).strip('[]') + '\nReference: Title = ' + title_ref + '\n\t\t  Authors = ' + str(authors_ref).strip('[]'))
                # print(lev, lev_partial)
                if input('Do both entries belong to the same article? (Please enter \'y\' or \'n\')') == 'y':
                    return True
        elif (lev_partial > 90 and lev > 60):
            if (without_interactive_queries):
                return False
            print('Article:  Title = ' + title_art + '\n\t\t  Authors = ' + str(author_art).strip('[]') + '\nReference: Title = ' + title_ref + '\n\t\t  Authors = ' + str(authors_ref).strip('[]'))
            # print(lev, lev_partial)
            if input('Do both entries belong to the same article? (Please enter \'y\' or \'n\')') == 'y':
                return True
