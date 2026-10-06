"""Loopback public-search broker. No model prompt endpoint exists here."""
import hmac,json,os,sys
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from web import page,search
TOKEN=os.environ['PRIVATE_AGENT_TOKEN']
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def reply(self,status,value):
        data=json.dumps(value).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_POST(self):
        if not hmac.compare_digest(self.headers.get('Authorization',''), 'Bearer '+TOKEN):return self.reply(401,{'error':'Private capability required'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=5000:raise ValueError('Invalid body length')
            a=json.loads(self.rfile.read(size))
            if self.path=='/search' and set(a)=={'query'}:value=search(a['query'])
            elif self.path=='/fetch' and set(a)=={'url'}:value=page(a['url'])
            else:raise ValueError('Only search(query) and fetch(url) are available')
            self.reply(200,value)
        except Exception as e:self.reply(400,{'error':str(e)})
if __name__=='__main__':
    s=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    Path(sys.argv[1]).write_text(json.dumps({'port':s.server_port}));Path(sys.argv[1]).chmod(0o600)
    s.serve_forever()
