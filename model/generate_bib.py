def generate_bib(articles):
    """
    genereates bibtex-file with the articles from json export
    :param articles: list of articles from json export
    :return: content for bibtex-file
    """
    bib = '''
    '''

    for article in articles:
        bib += '''@{0}{{{1},
        '''.format(article['document_type'], article['bibtex_key'])
        if article['title'] != '':
            bib += '''title = {{{}}},
            '''.format(article['title'])
        if article['author'] != '':
            bib += '''author = {{{}}},
            '''.format(article['author'])
        if article['year'] != '':
            bib += '''year = {{{}}},
            '''.format(article['year'])
        if 'journal' in article and article['journal'] != '':
            bib += '''journal = {{{}}},
            '''.format(article['journal'])
        if 'doi' in article and article['doi'] != '':
            bib += '''doi = {{{}}},
            '''.format(article['doi'])
        if 'issn' in article and article['issn'] != '':
            bib += '''issn = {{{}}},
            '''.format(article['issn'])
        if 'volume' in article and article['volume'] != '':
            bib += '''volume = {{{}}},
            '''.format(article['volume'])
        if 'pages' in article and article['pages'] != '':
            bib += '''pages = {{{}}},
            '''.format(article['pages'])
        if 'publisher' in article and article['publisher'] != '':
            bib += '''publisher = {{{}}},
            '''.format(article['publisher'])
        if 'url' in article and article['url'] != '':
            bib += '''url = {{{}}},
            '''.format(article['url'])
        bib += '''}
        '''

    return bib
