from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from socket import *
import struct

def initiate_camera(sock):
	size = sock.sendto(struct.pack('>BB', 0x30, 0x67), ('192.168.4.153', 8070))
	size += sock.sendto(struct.pack('>BB', 0x30, 0x66), ('192.168.4.153', 8070))
	size += sock.sendto(struct.pack('>BB', 0x42, 0x76), ('192.168.4.153', 8080))
	return (size == 6)

def packet_is_image_start(buf):
	for i in range(0, len(buf)-1):
		if(buf[i] == 0xff and buf[i+1] == 0xd8):
			return True
	return False

def packet_is_image_end(buf):
	for i in range(0, len(buf)-1):
		if(buf[i] == 0xff and buf[i+1] == 0xd9):
			return True
	return False

class CamHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		if self.path.endswith('.mjpg'):
			self.send_response(200)
			self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
			self.end_headers()
			frame = bytearray()
			while camera_initialized:
				(buf, rinfo) = s.recvfrom(4096)
				port = rinfo[1]
				if(port == 8080):
					if(packet_is_image_start(buf)):
						frame = bytearray(buf)[8:]
					else:
						frame += bytearray(buf)[8:]
					if(packet_is_image_end(buf)):
						self.send_header('Content-type', 'image/jpeg')
						self.send_header('Content-length', len(frame))
						self.end_headers()
						self.wfile.write(frame)
						self.wfile.write(b"\r\n--jpgboundary\r\n")
			return

		if self.path.endswith('.html'):
			self.send_response(200)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			self.wfile.write(b'<html><head></head><body><img src="http://127.0.0.1:8081/cam.mjpg"/></body></html>')
			return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""

if __name__ == '__main__':
	s = socket(AF_INET, SOCK_DGRAM)
	s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
	s.bind(('',0))
	camera_initialized = initiate_camera(s)
	server = ThreadedHTTPServer(('localhost', 8081), CamHandler)
	print("server started at http://127.0.0.1:8081/cam.html")
	server.serve_forever()