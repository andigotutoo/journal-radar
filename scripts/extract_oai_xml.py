#!/usr/bin/env python3
"""Convert downloaded KCI oai_kci XML to correctly paired author-affiliation CSV.
No KCI key required for OAI-PMH, but this tool reads XML that was downloaded
separately; it does not harvest the entire KCI corpus or guess identities.
"""
import argparse
import csv
import re
from pathlib import Path
from xml.etree import ElementTree as ET


def find_text(node, path):
    elem=node.find(path)
    return (elem.text or '').strip() if elem is not None else ''


def extract_file(path):
    root=ET.parse(path).getroot()
    result=[]
    for record in root.findall('.//{*}record'):
        data=record.find('.//{*}oai_kci')
        if data is None:continue
        ji=data.find('./{*}journalInfo')
        ai=data.find('./{*}articleInfo')
        if ji is None or ai is None:continue
        journal=find_text(ji,'./{*}journal-name')
        aid=ai.attrib.get('article-id','')
        if not aid:
            ident=find_text(record,'./{*}header/{*}identifier')
            aid=ident.split('/')[-1] if ident else ''
        title=find_text(ai,'.//{*}title-group/{*}article-title')
        year=find_text(ji,'./{*}pub-year')
        doi=find_text(ai,'./{*}doi')
        url=find_text(ai,'./{*}url')
        for author in ai.findall('.//{*}author-name/{*}author'):
            name=find_text(author,'./{*}name')
            aff=find_text(author,'./{*}affiliation')
            if not name:continue
            result.append({'article_id':aid,'journal':journal,'title':title,
              'year':year,'doi':doi,'url':url,'author':name,'affiliation':aff})
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('xml',nargs='+',help='KCI OAI-PMH oai_kci XML 파일')
    ap.add_argument('-o','--output',default='kci_author_paired.csv')
    args=ap.parse_args()
    rows=[]
    for path in args.xml:rows.extend(extract_file(path))
    cols=['article_id','journal','title','year','doi','url','author','affiliation']
    with open(args.output,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols)
        w.writeheader();w.writerows(rows)
    print(f'{len(rows)} author-publication records exported to {args.output}')

if __name__=='__main__':main()
