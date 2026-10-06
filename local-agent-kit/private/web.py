"""Public web broker. No cookies, credentials, scripts, uploads, or OpenAI hosts.
Connections pin a validated public DNS address and revalidate every redirect.
"""
import http.client, ipaddress, socket, ssl, urllib.parse, re, json, zlib
from html.parser import HTMLParser
from xml.etree import ElementTree

BLOCKED=('openai.com','chatgpt.com','chat.com','oaistatic.com','oaiusercontent.com','openai.azure.com','azurefd.net','windows.net')
MAX_BYTES=2_000_000

def validate_url(url):
    p=urllib.parse.urlsplit(url)
    host=(p.hostname or '').encode('idna').decode('ascii').lower().rstrip('.')
    if p.scheme!='https' or not host or p.username or p.password or p.port not in (None,443) or len(url)>3000:
        raise ValueError('Only bounded public HTTPS URLs without credentials on port 443 are allowed')
    if any(host==d or host.endswith('.'+d) for d in BLOCKED): raise ValueError('OpenAI-related destination blocked by private web policy')
    if '.' not in host or any(c in host for c in '%\\') or re.search(r'[\x00-\x20\x7f]',url): raise ValueError('Invalid public hostname/URL')
    try: ipaddress.ip_address(host)
    except ValueError: pass
    else: raise ValueError('IP-literal destinations are blocked')
    return p,host

def public_addresses(host):
    values=list(dict.fromkeys(x[4][0] for x in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)))
    if not values or any(not ipaddress.ip_address(v).is_global or ipaddress.ip_address(v).is_multicast for v in values): raise ValueError('Non-public DNS destination blocked')
    return values

class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self,host,address):
        super().__init__(host,timeout=20,context=ssl.create_default_context(cafile='/etc/ssl/cert.pem'))
        self.address=address
    def connect(self):
        raw=socket.create_connection((self.address,443),self.timeout)
        self.sock=self._context.wrap_socket(raw,server_hostname=self.host)

def fetch(url):
    for _ in range(5):
        p,host=validate_url(url)
        conn=PinnedHTTPS(host,public_addresses(host)[0])
        try:
            path=urllib.parse.urlunsplit(('', '', p.path or '/',p.query,''))
            conn.request('GET',path,headers={'User-Agent':'LocalResearch/1.0','Accept':'text/html,text/plain,application/rss+xml,application/xml','Accept-Encoding':'identity'})
            r=conn.getresponse()
            if r.status in (301,302,303,307,308):
                url=urllib.parse.urljoin(url,r.getheader('location') or '')
                continue
            if r.status!=200: raise ValueError(f'Public website returned HTTP {r.status}')
            kind=(r.getheader('content-type') or '').split(';')[0]
            if kind not in ('text/html','text/plain','application/xhtml+xml','application/rss+xml','text/xml','application/xml'): raise ValueError('Only public text pages are supported')
            raw=r.read(MAX_BYTES+1)
            if len(raw)>MAX_BYTES: raise ValueError('Page exceeds 2 MB limit')
            encoding=(r.getheader('content-encoding') or '').lower()
            if encoding=='gzip' or raw.startswith(b'\x1f\x8b'):
                raw=zlib.decompressobj(16+zlib.MAX_WBITS).decompress(raw,MAX_BYTES+1)
            elif encoding=='deflate':
                raw=zlib.decompressobj().decompress(raw,MAX_BYTES+1)
            elif encoding not in ('','identity'):raise ValueError('Unsupported page compression')
            if len(raw)>MAX_BYTES:raise ValueError('Decoded page exceeds 2 MB limit')
            return url,raw.decode('utf-8',errors='replace'),kind
        finally: conn.close()
    raise ValueError('Redirect limit exceeded')

class Text(HTMLParser):
    def __init__(self): super().__init__(); self.hidden=0; self.parts=[]; self.links=[]; self.anchor=None
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','noscript'): self.hidden+=1
        if tag in ('p','div','br','h1','h2','h3','li'): self.parts.append('\n')
        if tag=='a': self.anchor=[dict(attrs).get('href',''),[]]
    def handle_endtag(self,tag):
        if tag in ('script','style','noscript'): self.hidden=max(0,self.hidden-1)
        if tag=='a' and self.anchor:
            self.links.append({'url':self.anchor[0],'title':' '.join(self.anchor[1]).strip()}); self.anchor=None
    def handle_data(self,data):
        if not self.hidden:self.parts.append(data)
        if self.anchor:self.anchor[1].append(data)

def page(url):
    final,body,kind=fetch(url)
    if kind!='text/plain':
        p=Text();p.feed(body);body='\n'.join(filter(None,(' '.join(x.split()) for x in ''.join(p.parts).splitlines())))
    return {'url':final,'text':body[:30000],'untrusted_content':True,'truncated':len(body)>30000}

def search(query):
    if not isinstance(query,str) or not 2<=len(query.strip())<=350:raise ValueError('Use a short public search query (2–350 characters)')
    if re.search(r'(?i)(bearer\s|api[_ -]?key\s*[:=]|-----BEGIN|sk-[a-zA-Z0-9]{12}|/Users/|/home/)',query):raise ValueError('Query looks like private credentials or a local path; use generic terms')
    url='https://html.duckduckgo.com/html/?'+urllib.parse.urlencode({'q':query})
    # The search provider sees only this query, not the agent conversation.
    p=Text()
    try:
        final,body,_=fetch(url);p.feed(body)
    except (ValueError,OSError):
        pass
    links=[];seen=set()
    for link in p.links:
        u=link['url']
        if u.startswith('//'):u='https:'+u
        if '/l/?' in u:u=urllib.parse.parse_qs(urllib.parse.urlsplit(u).query).get('uddg',[''])[0]
        if u.startswith('/url?'):u=urllib.parse.parse_qs(urllib.parse.urlsplit(u).query).get('q',[''])[0]
        try: _,host=validate_url(u)
        except ValueError:continue
        if host.endswith(('google.com','duckduckgo.com')) or u in seen or not link['title']:continue
        seen.add(u);links.append({'title':link['title'][:300],'url':u})
    if not links:
        # Public HTML search can challenge automation; RSS is a text-only fallback.
        final,body,_=fetch('https://www.bing.com/search?'+urllib.parse.urlencode({'q':query,'format':'rss'}))
        root=ElementTree.fromstring(body)
        for item in root.findall('.//item'):
            u=item.findtext('link','')
            try:validate_url(u)
            except ValueError:continue
            links.append({'title':item.findtext('title',''),'url':u,'snippet':item.findtext('description','')[:500]})
    if not links:raise ValueError('Search returned no usable links; try a known public documentation URL')
    return {'query':query,'search_url':final,'results':links[:8],'untrusted_content':True}
