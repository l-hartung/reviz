import json
import xml.etree.ElementTree as et
from model.citation_matching import citation_matching
import os
from model.generate_bib import generate_bib
from utils.utils import key_to_md5, find_urls, find_author


def run_graph(jsFile, tei, tex):
    with open(jsFile, 'r') as file: #encoding='utf8'
        jsonfile = json.load(file)

    articles = jsonfile['final selection articles']

    for article in articles:
        article['bibtex_key'] = key_to_md5(article['bibtex_key'])

    with open(os.path.join(tex, 'library.bib'), 'w') as l:
        l.write(generate_bib(articles))

    graph = {}
    years = []
    for article in articles:
        if article['note'] is None:
            continue
        if article['year'] is not None:
            years.append(int(article['year']))

    graph['years'] = years
    graph['year_arts'] = {}
    for year in range(min(years), max(years)+1):
        this_year_arts = []
        for article in articles:
            if article['note'] is None:
                continue
            if int(article['year']) == year:
                this_year_arts.append(article['bibtex_key'])
        graph['year_arts'][year] = this_year_arts

    graph['articles'] = []
    for article in articles:
        authors = find_author(article['author'])
        if article['note'] is None:
            continue
        article_dict = {'title': article['title'],
                        'author': authors,
                        'key': article['bibtex_key'],
                        'year': article['year']}
        graph['articles'].append(article_dict)

    graph['edges'] = []
    namespace = '{http://www.tei-c.org/ns/1.0}'
    for article in articles:
        if article['note'] is not None:
            if find_urls(article['note']):
                tei_file = os.path.join(tei, key_to_md5(article['title']) + '.tei.xml')
            else:
                xmlName = os.path.basename(article['note'])[:-4]
                tei_file = os.path.join(tei, '{}.tei.xml'.format(xmlName))
            if not os.path.isfile(tei_file):
                print('tei-file not found for', article['title'])
                continue
            print(tei_file)
            xml = et.parse(tei_file)
            root = xml.getroot()
            for ref in xml.findall('.//{}biblStruct'.format(namespace)):
                reftitle = ref.find('.//{}title'.format(namespace)).text
                if reftitle is None:
                    reftitle = 'Ohne Titel'
                if ref.find('.//{}idno[@type="doi"]'.format(namespace)) is not None:
                    refdoi = ref.find('.//{}idno[@type="doi"]'.format(namespace)).text
                else:
                    refdoi = None
                refauthors = []
                for author in ref.findall('.//{}surname'.format(namespace)):
                    refauthors.append(author.text)
                for art in articles:
                    artauthors = find_author(art['author'])
                    if len(artauthors) > 0:
                        artauthor = artauthors[0]
                    else:
                        artauthor = "unbekannt"
                    if 'doi' not in art:
                        art['doi'] = ''
                    if art['title'] is not article['title']:  # article should not cite itself
                        if citation_matching(art['doi'], refdoi, art['title'], reftitle, artauthors, refauthors):
                            graph['edges'].append({'from': article['bibtex_key'],
                                                   'to': art['bibtex_key']})
                            break

    with open(os.path.join(tex, 'graph-model.json'), 'w') as jf:
        json.dump(graph, jf, indent=2)
