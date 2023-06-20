FROM ubuntu:22.04
RUN apt update && DEBIAN_FRONTEND=noninteractive apt install -y texlive-full latexmk git openjdk-8-jdk-headless python3 maven
RUN DEBIAN_FRONTEND=noninteractive apt install -y python3-pip
RUN luaotfload-tool -v -vvv -u
RUN pip3 install fuzzywuzzy python-Levenshtein bibtexparser requests GitPython doi2bib arxivcheck termcolor bibcure
RUN git clone --depth=1 https://github.com/kermitt2/grobid.git /libGrobid
RUN cd /libGrobid ; ./gradlew install
ADD grobid-example /libGrobid-bibtex
RUN cp /libGrobid/grobid-core/build/libs/grobid-core-0.8.0-SNAPSHOT.jar /libGrobid-bibtex/lib/
RUN cd /libGrobid-bibtex; mvn install
ADD . /reviz-code
WORKDIR /reviz
ENTRYPOINT ["/reviz-code/reviz.py"]
