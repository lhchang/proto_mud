import BaseHTTPServer, SimpleHTTPServer
import ssl
import os
import json

'''
Inherited HTTP handler so we deliver only the MUD JSON file
'''

class HandleMUDHttps(BaseHTTPServer.BaseHTTPRequestHandler):
    # Modify the GET method to deliver the JSON if URL exists otherwise send an error that file does not exists
    def do_GET(self): 
        content_type = ''
        path_vars = self.path.split('/')
        try:
            sendReply = False
            if self.path.endswith('.json'):
                mudfile = path_vars[len(path_vars)-1]
                content_type = 'application/mud+json'
                sendReply = True
            if sendReply == True:
                #fd = open(os.path.join('toaster','v1','mudfile.json'),'r')
                try:
                    fd = open(os.path.join('toaster','v1',mudfile),'r')
                    fs = os.fstat(fd.fileno())
                    data = fd.read()
                    self.send_response(200, 'OK')
                    self.send_header('Content-Length', len(data))
                    self.send_header('Content-type', content_type)
                    self.send_header('Last-Modified', self.date_time_string(fs.st_mtime))
                    self.send_header
                    self.end_headers()
                    self.wfile.write(data)
                    fd.close()
                    return
                except (IOError, ValueError) as e:
                    print 'Error opening file: %s' %e
            else:
                fd = open(os.path.join('index.html'), 'r')
                self.send_response(200, 'OK')
                self.wfile.write(fd.read()) 
                fd.close()
                return
            return
        except IOError:
            self.send_error(404,'Not Found')
            return



#def run(server_class=BaseHTTPServer.HTTPServer, handler_class=SimpleHTTPServer.SimpleHTTPRequestHandler):
def run(server_class=BaseHTTPServer.HTTPServer, handler_class=HandleMUDHttps):
    httpd = BaseHTTPServer.HTTPServer(('0.0.0.0',443), handler_class)
    httpd.socket = ssl.wrap_socket (httpd.socket, certfile='./server.pem', server_side=True)
    print "Server Ready to serve..."
    httpd.serve_forever()
    

if __name__=="__main__":
	run()