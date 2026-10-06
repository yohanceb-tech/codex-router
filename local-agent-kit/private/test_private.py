#!/usr/bin/env python3
"""Negative controls for the private public-web boundary and launcher."""
import unittest,sys,json,gzip,os,tempfile,importlib
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import web,launch
class PrivateTests(unittest.TestCase):
    def test_blocked_urls(self):
        for u in ['https://openai.com/','https://api.openai.com./','https://api.OPENAI.com/','https://chatgpt.com/','https://api.openai.com\u3002/','https://x.openai.azure.com/','http://example.com/','https://127.0.0.1/','https://[::1]/','https://user:pass@example.com/','https://example.com:8443/','https://example.com/\nHeader:bad','https://%6fpenai.com/']:
            with self.subTest(url=u),self.assertRaises(ValueError):web.validate_url(u)
        self.assertEqual(web.validate_url('https://docs.python.org/3/library/asyncio.html')[1],'docs.python.org')
    def test_dns_rejects_mixed_private(self):
        with patch.object(web.socket,'getaddrinfo',return_value=[(2,1,6,'',('93.184.216.34',443)),(2,1,6,'',('127.0.0.1',443))]):
            with self.assertRaises(ValueError):web.public_addresses('example.com')
    def test_redirect_rechecks_before_connection(self):
        class Response:
            status=302
            def getheader(self,name):return 'https://api.openai.com/'
        class Conn:
            def request(self,*a,**k):pass
            def getresponse(self):return Response()
            def close(self):pass
        with patch.object(web,'public_addresses',return_value=['93.184.216.34']),patch.object(web,'PinnedHTTPS',return_value=Conn()) as ctor:
            with self.assertRaises(ValueError):web.fetch('https://example.com/')
            self.assertEqual(ctor.call_count,1)
    def test_compressed_text_is_bounded(self):
        class Response:
            status=200
            def getheader(self,name):return {'content-type':'text/plain','content-encoding':'gzip'}.get(name)
            def read(self,n):return gzip.compress(b'x'*(web.MAX_BYTES+1))
        class Conn:
            def request(self,*a,**k):pass
            def getresponse(self):return Response()
            def close(self):pass
        with patch.object(web,'public_addresses',return_value=['93.184.216.34']),patch.object(web,'PinnedHTTPS',return_value=Conn()):
            with self.assertRaises(ValueError):web.fetch('https://example.com/')
    def test_sensitive_queries_rejected_before_network(self):
        with patch.object(web,'fetch') as fetch:
            for q in ['api_key=abc123','/Users/person/private-project','Bearer abc123','-----BEGIN PRIVATE KEY-----','x'*351]:
                with self.assertRaises(ValueError):web.search(q)
            fetch.assert_not_called()
    def test_bound_files_stale_write_and_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['PRIVATE_PROJECT_ROOT']=tmp
            import files_mcp as files
            files=importlib.reload(files)
            p=Path(tmp)/'app.js';p.write_text('original')
            files.call('read_project_file',{'path':'app.js'})
            p.write_text('someone else changed this')
            with self.assertRaisesRegex(ValueError,'file changed'):
                files.call('write_project_file',{'path':'app.js','content':'overwrite'})
            self.assertEqual(p.read_text(),'someone else changed this')
            files.call('read_project_file',{'path':'app.js'})
            files.call('write_project_file',{'path':'app.js','content':'updated'})
            self.assertEqual(p.read_text(),'updated')
            for path in ['../outside','/tmp/outside']:
                with self.assertRaises(ValueError):files.call('read_project_file',{'path':path})
            with self.assertRaises(ValueError):files.call('search_project_context',{'root':'/tmp','query':'anything'})
            files.call('read_project_file',{'path':'new.js'})
            files.call('write_project_file',{'path':'new.js','content':'new file'})
            self.assertEqual((Path(tmp)/'new.js').read_text(),'new file')
    def test_config_has_no_hosted_features(self):
        import tomllib
        c=tomllib.loads(launch.config(12345))
        self.assertEqual(c['model_provider'],'private-ollama')
        self.assertFalse(c['model_providers']['private-ollama']['requires_openai_auth'])
        self.assertFalse(c['analytics']['enabled']);self.assertFalse(c['feedback']['enabled'])
        self.assertEqual(set(c['mcp_servers']),{'files','web'})
        self.assertFalse(c['features']['plugins'])
if __name__=='__main__':unittest.main()
