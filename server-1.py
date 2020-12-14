#
# Event-driven server that periodically accepts
# messages from connected clients.  Each message
# is followed by an acknowledgment. 
#
# Tested with Python 2.7.8 and Twisted 14.0.2
#
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory
import time

class Server(Protocol):
	def connectionMade(self):
		print "Connected from", self.transport.client
		try:
			self.transport.write('<connection up>')
		except Exception, e:
			print e.args[0]
		self.ts = time.time()

	def sendAck(self):
		print "sendAck"
		self.ts = time.time()
		try:
			self.transport.write('<Ack>')
		except Exception, e:
			print e.args[0]

	def dataReceived(self, data):
		print 'dataReceived ' + data
		self.sendAck()

	def connectionLost(self, reason):
		print "Disconnected from", self.transport.client

class ServerFactory(Factory):

	protocol = Server

	def __init__(self, fname):
		print "@__init__"
		self.fname = fname
		self.records = []

	def startFactory(self):
		print "@startFactory"
		self.fp = open(self.fname, 'w+')

	def stopFactory(self):
		print "@stopFactory"
		self.fp.close()

if __name__=='__main__':

	reactor.listenTCP(8888, ServerFactory('log'))

	reactor.run()
