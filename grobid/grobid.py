from grobid.grobid_api_client import GrobidClient
import json
from utils.utils import find_urls, key_to_md5
import requests
import os


def run_grobid(jsFile, pdf, tei):
    with open(jsFile, 'r') as file:
        jsonfile = json.load(file)

    client = GrobidClient(config_path='/reviz-code/grobid/grobid-config.json')

    finalArticles = jsonfile['final selection articles']

    for article in finalArticles:
        if article['note'] is not None:
            print(article['title'])
            if find_urls(article['note']):
                print(find_urls(article['note']))
                url = find_urls(article['note'])[0]
                r = requests.get(url, allow_redirects=True)
                name = os.path.join(pdf, key_to_md5(article['title']) + '.pdf')
                with open(name, 'wb') as f:
                    f.write(r.content)
                client.process_citations(name, tei)
            elif os.path.isfile(article['note']):
                print(article['note'])
                client.process_citations(article['note'], tei)
            else:
                print('{} was not found'.format(article['note']))
                continue
