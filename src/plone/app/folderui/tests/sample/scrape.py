#scrape wikisource and wikipedia for public domain speech transcripts to use
# as example content. 
#
# TODO: parse date into datetime.
# TODO: add str(speech.date.year) to speech.keywords
# TODO: add a dict mapping political party to speaker, add this to keywords
# TODO: some serialization of the objects into text format
#



import urllib2
from lxml.html import parse, etree
import time


SCRAPE_UA = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.11)'
MANIFEST = """http://en.wikipedia.org/wiki/United_States_presidential_inauguration#List_of_inaugural_ceremonies"""
TABLECLASS = 'wikitable'


class Speech(object):
    pass #attrs = (title, keywords, description, date, text)


def recursive_plaintext(e):
    text = u''
    if e.text is not None:
        text += e.text
    for c in e:
        text += recursive_plaintext(c)
    if e.tail is not None:
        text += e.tail
    return text

def get_manifest_table():
    req = urllib2.Request(MANIFEST, headers={'User-Agent':SCRAPE_UA})
    html = urllib2.urlopen(req)
    doc = parse(html).getroot()
    listing_tbl = doc.xpath(".//table[@class='wikitable sortable']")[0]
    return listing_tbl


def get_speech(url):
    speech = Speech()
    req = urllib2.Request(url, headers={'User-Agent':SCRAPE_UA})
    html = urllib2.urlopen(req)
    doc = parse(html).getroot()
    cdiv = doc.xpath(".//div[@id='bodyContent']")[0]
    speech.text = u''
    for para in cdiv.xpath('p'):
        ptext = recursive_plaintext(para).strip()
        if ptext:
            speech.text += ('<p>%s</p>\n' % ptext)
    speech.description = doc.xpath("./head/meta[@name='keywords']")[0].get('content')
    speech.title = doc.xpath("./head/title")[0].text
    return speech


def get_speech_documents():
    results = []
    listing_tbl = get_manifest_table()
    rows = listing_tbl.xpath('.//tr')[1:-1]
    for row in rows:
        time.sleep(2) #as courtesy to wikisource.org
        cols = row.xpath('.//td')
        if len(cols) >= 6:
            atags = cols[5].xpath(".//a")
            for a in atags:
                url = a.get('href')
                if url.find('wikisource.org') != -1:
                    speech = get_speech(url)
                else:
                    continue
            if cols:
                speech.date = cols[0].text
        results.append(speech)
    return results


if __name__ == '__main__':
    for speech in get_speech_documents():
        print speech.title
        print speech.description
        print speech.date
        print speech.text
        print '%s\n\n' % ('-'*78)




