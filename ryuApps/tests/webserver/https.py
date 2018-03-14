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
        if self.path == '/toaster/v1/': 
            self.path = '/toaster/v1/mudfile.json'
        else:
            self.send_error(404,'Not Found')
        try:
            sendReply = False
            if self.path.endswith('.json'):
                content_type = 'application/mud+json'
                sendReply = True
            if sendReply == True:
                fd = open(os.path.join('toaster','v1','mudfile.json'),'r')
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.end_headers()
                self.wfile.write(fd.read())
                fd.close()
            return
        except IOError:
            self.send_error(404,'Not Found')

def run(server_class=BaseHTTPServer.HTTPServer, handler_class=HandleMUDHttps):
	httpd = BaseHTTPServer.HTTPServer(('localhost', 443), handler_class)
	httpd.socket = ssl.wrap_socket (httpd.socket, certfile='./server.pem', server_side=True)
	print "Server Ready to serve..."
	httpd.serve_forever()

#httpd = BaseHTTPServer.HTTPServer(('localhost', 443), SimpleHTTPServer.SimpleHTTPRequestHandler)
#httpd.socket = ssl.wrap_socket (httpd.socket, certfile='./server.pem', server_side=True)
#print "Server Ready to serve..."
#httpd.serve_forever()

if __name__=="__main__":
	run()