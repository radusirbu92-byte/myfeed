"""Collect public RSS and Atom feeds without API keys or third-party dependencies."""
import hashlib, html, json, re, sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

BASE=Path(__file__).resolve().parent
CONFIG=json.loads((BASE/"config.json").read_text(encoding="utf-8"))
OUTPUT=BASE/"data/feed.json"
ATOM="{http://www.w3.org/2005/Atom}"
CONTENT="{http://purl.org/rss/1.0/modules/content/}"

class FeedFinder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls=[]
    def handle_starttag(self,tag,attrs):
        if tag!="link": return
        d=dict(attrs)
        if "alternate" in d.get("rel","").split() and d.get("type","") in ("application/rss+xml","application/atom+xml") and d.get("href"):
            self.urls.append(d["href"])

def get(url):
    if urlparse(url).scheme not in ("https","http"): raise ValueError("Only HTTP(S) URLs supported")
    req=Request(url,headers={"User-Agent":"MyFeed/1.0 personal RSS reader","Accept":"application/rss+xml,application/atom+xml,text/xml,text/html,*/*"})
    with urlopen(req,timeout=25) as response:
        blob=response.read(5000001)
        if len(blob)>5000000: raise ValueError("Feed exceeds 5MB")
        return blob,response.geturl()

def element_text(e,name):
    obj=e.find(name)
    return "".join(obj.itertext()).strip() if obj is not None else ""

def clean(value,size=450):
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",str(value or "")))).strip()[:size]

def date_iso(s):
    if not s:return None
    try: return parsedate_to_datetime(s).astimezone(timezone.utc).isoformat()
    except Exception:pass
    try:
        x=datetime.fromisoformat(s.replace("Z","+00:00"))
        if x.tzinfo is None:x=x.replace(tzinfo=timezone.utc)
        return x.astimezone(timezone.utc).isoformat()
    except Exception:return None

def read_source(source):
    blob,url=get(source["url"])
    try:root=ET.fromstring(blob)
    except ET.ParseError:
        finder=FeedFinder()
        finder.feed(blob.decode("utf-8","replace")[:2000000])
        if not finder.urls:raise ValueError("No RSS/Atom feed advertised on site")
        blob,url=get(urljoin(url,finder.urls[0]))
        root=ET.fromstring(blob)
    if root.tag=="rss" or root.tag.endswith("}RDF"):
        entries=root.findall("./channel/item") or root.findall("./{http://purl.org/rss/1.0/}item")
        def parse(e):
            return (element_text(e,"title"),element_text(e,"link"),element_text(e,"guid") or element_text(e,"link"),element_text(e,"pubDate") or element_text(e,"{http://purl.org/dc/elements/1.1/}date"),element_text(e,"description") or element_text(e,CONTENT+"encoded"))
    elif root.tag in (ATOM+"feed","feed"):
        prefix=ATOM if root.tag.startswith("{") else ""
        entries=root.findall(prefix+"entry")
        def parse(e):
            link=next((l.get("href","") for l in e.findall(prefix+"link") if l.get("rel","alternate")=="alternate"),"")
            return (element_text(e,prefix+"title"),link,element_text(e,prefix+"id") or link,element_text(e,prefix+"published") or element_text(e,prefix+"updated"),element_text(e,prefix+"summary") or element_text(e,prefix+"content"))
    else:raise ValueError("Not a supported RSS/Atom feed")
    if not entries:raise ValueError("Feed has no entries")
    result=[]
    for e in entries[:40]:
        title,link,uid,published,summary=parse(e)
        if urlparse(link).scheme not in ("http","https"):continue
        published=date_iso(published)
        if not published:continue
        result.append({"id":hashlib.sha256((source["name"]+"|"+uid).encode()).hexdigest()[:24],"title":clean(title,240) or "Untitled","summary":clean(summary),"url":link,"published":published,"source":source["name"],"type":source.get("type","website").lower()})
    return result

def main():
    sources=CONFIG.get("sources",[])
    if not isinstance(sources,list) or len(sources)>200:sys.exit("Expected 0 to 200 sources")
    prior=[]
    if OUTPUT.exists():
        try:prior=json.loads(OUTPUT.read_text(encoding="utf-8")).get("items",[])
        except Exception:pass
    allowed={s.get("name") for s in sources}
    items={x["id"]:x for x in prior if x.get("source") in allowed and x.get("id")}
    statuses=[]
    for s in sources:
        try:
            if not s.get("name") or not s.get("url"):raise ValueError("Name or URL missing")
            fetched=read_source(s)
            for x in fetched:items[x["id"]]=x
            statuses.append({"source":s["name"],"ok":True,"count":len(fetched)})
            print("OK",s["name"],len(fetched))
        except Exception as ex:
            statuses.append({"source":s.get("name","Unknown"),"ok":False,"error":str(ex)[:140]})
            print("ERROR",s.get("name"),str(ex),file=sys.stderr)
    result={"updated_at":datetime.now(timezone.utc).isoformat(),"sources":statuses,"items":sorted(items.values(),key=lambda x:x.get("published",""),reverse=True)[:1000]}
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print("Total",len(result["items"]))
if __name__=="__main__":main()
