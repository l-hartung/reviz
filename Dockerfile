FROM python:3.7.5-buster
RUN apt-get update && apt-get install -y texlive-full latexmk
RUN luaotfload-tool -v -vvv -u
RUN pip install fuzzywuzzy python-Levenshtein bibtexparser requests
ADD . /reviz-code
WORKDIR /reviz
ENTRYPOINT ["python", "/reviz-code/reviz.py"]