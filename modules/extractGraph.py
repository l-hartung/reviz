import json
from .config import bibKeyYear, bibKeyAuthor, bibKeyTitle, bibKeyID, bibKeyPrefix, bibRefPrefix
from .mytimer import measureStart, measureEnd


def extractGraph(entries, fileGraphModel, filter=None, filterMode=0):
    g = extractGraphI(entries, filter, filterMode)
    with open(fileGraphModel, "w") as f:
        json.dump(g, f, indent=2)


def extractGraphI(entries, filter=None, filterMode=0):
    measure = measureStart()
    graph = {}
    yearArts = {}
    articles = []
    keymap = []
    inctr = {}
    outctr = {}
    keyToYear = {}
    keepArticles = set()
    keepArticlesKeys = set()
    print("extractGraph -> initialize keymap", flush=True)
    for entry in entries:
        if bibKeyYear in entry and bibKeyAuthor in entry and bibKeyTitle in entry:
            keyToYear[entry[bibKeyID]] = entry[bibKeyYear]
            inFilter = filter is None or entry[bibKeyID] in filter
            if inFilter:
                keepArticles.add(entry[bibKeyID])
            for k, v in entry.items():
                if k.startswith(bibKeyPrefix):
                    kk = int(k[len(bibKeyPrefix):])
                    if inFilter:
                        keepArticlesKeys.add(kk)
                    if len(keymap) <= kk:
                        keymap.extend([None] * (kk - len(keymap) + 1))
                    keymap[kk] = entry[bibKeyID]
                    inctr[entry[bibKeyID]] = set()
                    outctr[entry[bibKeyID]] = set()
    print("initialize inctr, outctr", flush=True)
    for entry in entries:
        if bibKeyYear in entry and bibKeyAuthor in entry and bibKeyTitle in entry:
            a = entry[bibKeyID]
            for k, v in entry.items():
                if k.startswith(bibRefPrefix):
                    kk = int(k[len(bibRefPrefix):])
                    b = keymap[kk]
                    if a != b:
                        if b in inctr and a in outctr and keyToYear[a] >= keyToYear[b]:
                            inctr[b].add(a)
                            outctr[a].add(b)
    print("add all transitive edges", flush=True)
    changed = True
    while changed:
        changed = False
        c = 0
        for k, v_incomings in inctr.items():
            c = c + 1
            for v_incoming in v_incomings:
                oc_vi = outctr[v_incoming]
                for v_outgoing in outctr[k]:
                    if not v_outgoing in oc_vi:
                        oc_vi.add(v_outgoing)
                        inctr[v_outgoing].add(v_incoming)
                        changed = True
    print("calculate which articles to keep", flush=True)
    changed = -1
    changed2 = -1
    while changed != len(keepArticles) or changed2 != len(keepArticlesKeys):
        changed = len(keepArticles)
        changed2 = len(keepArticlesKeys)
        for entry in entries:
            if bibKeyYear in entry and bibKeyAuthor in entry and bibKeyTitle in entry:
                a_id = entry[bibKeyID]
                contained = a_id in keepArticles
                for k, v in entry.items():
                    if k.startswith(bibKeyPrefix):
                        if int(k[len(bibKeyPrefix):]) in keepArticlesKeys:
                            contained = True
                if contained:
                    keepArticles.add(a_id)
                    if filterMode == 1 or filterMode == 3:  # add all the 'old' cited articles
                        for k, v in entry.items():
                            if k.startswith(bibRefPrefix):
                                keepArticlesKeys.add(int(k[len(bibRefPrefix):]))
                            if k.startswith(bibKeyPrefix):
                                keepArticlesKeys.add(int(k[len(bibKeyPrefix):]))
                if filterMode == 2 or filterMode == 3:  # add all the 'new' articles citing us
                    for k, v in entry.items():
                        if k.startswith(bibRefPrefix):
                            if int(k[len(bibRefPrefix):]) in keepArticlesKeys:
                                keepArticles.add(a_id)
    print("keeping", str(len(keepArticles)), "articles")
    print("calculate articles", flush=True)
    for entry in entries:
        if bibKeyYear in entry and bibKeyAuthor in entry and bibKeyTitle in entry:
            a_id = entry[bibKeyID]
            if a_id in keepArticles:
                a_year = entry[bibKeyYear]
                a_title = entry[bibKeyTitle]
                a_authors = entry[bibKeyAuthor]
                if a_year in yearArts:
                    yearArts[a_year].append(a_id)
                else:
                    yearArts[a_year] = [a_id]
                articles.append({"title": a_title, "author": a_authors, "key": a_id, "year": a_year})
    edges = []
    print("calculate edges", flush=True)
    for entry in entries:
        if bibKeyYear in entry and bibKeyAuthor in entry and bibKeyTitle in entry:
            targets = []
            a = entry[bibKeyID]
            if a in keepArticles:
                for k, v in entry.items():
                    if k.startswith(bibRefPrefix):
                        kk = int(k[len(bibRefPrefix):])
                        b = keymap[kk]
                        if a != b:
                            targets.append(b)
                for b in list(set(targets)):
                    if b is not None and b in keepArticles and keyToYear[a] > keyToYear[b]:
                        edges.append({"from": a, "to": b})
    print("keeping", str(len(edges)), "edges")
    graph["year_arts"] = yearArts
    graph["years"] = [int(x) for x in yearArts.keys()]
    graph["articles"] = articles
    graph["edges"] = edges
    measureEnd(measure)
    return graph
