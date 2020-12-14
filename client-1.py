#
# Event-driven client that connects to a server and
# periodically sends an update message to it.  Each 
# update is acked by the server.
#
# Tested with Python 2.7.8 and Twisted 14.0.2
#
import optparse

from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor

def parse_args():
	usage = """usage: %prog [options] [hostname]:port 

	python client.py 127.0.0.1:port """

	parser = optparse.OptionParser(usage)

	_, addresses = parser.parse_args()

	if not addresses:
		print parser.format_help()
		parser.exit()

	def parse_address(addr):
		if ':' not in addr:
			host = '127.0.0.1'
			port = addr
        	else:
			host, port = addr.split(':', 1)

		if not port.isdigit():
			parser.error('Ports must be integers.')

		return host, int(port)

	return parse_address(addresses[0])


class Client(Protocol):

	acks = 0
	connected = False

	def connectionMade(self):
		self.connected = True
		reactor.callLater(5, self.sendUpdate)

	def sendUpdate(self):
		print "Sending update"
		try:
			self.transport.write('<update>')
		except Exception, ex1:
			print "Exception trying to send: ", ex1.args[0]
		if self.connected == True:
			reactor.callLater(5, self.sendUpdate)

	def dataReceived(self, data):
		print 'Received ' + data
		self.acks += 1

	def connectionLost(self, reason):
		self.connected = False
		self.done()

	def done(self):
		self.factory.finished(self.acks)


class CFactory(ClientFactory):

	protocol = Client # tell base class what proto to build

	def __init__(self):
		print '@__init__'
		self.acks = 0

	def finished(self, arg):
		self.acks = arg
		self.report()

	def report(self):
		print 'Received %d acks' % self.acks

	def clientConnectionFailed(self, connector, reason):
		print 'Failed to connect to:', connector.getDestination()
		self.finished()

	def clientConnectionLost(self, connector, reason):
		print 'Lost connection.  Reason:', reason


if __name__ == '__main__':
	address = parse_args()

	factory = CFactory()

	host, port = address
	print "Connecting to host " + host + " port " + str(port)

	reactor.connectTCP(host, port, factory)

	reactor.run()
