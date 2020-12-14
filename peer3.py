#
# Event-driven code that behaves as either a client or a server
# depending on the argument.  When acting as client, it connects 
# to a server and periodically sends an update message to it.  
# Each update is acked by the server.  When acting as server, it
# periodically accepts messages from connected clients.  Each
# message is followed by an acknowledgment.
#
# Tested with Python 2.7.8 and Twisted 14.0.2
#
import optparse

from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor
import time
import os
import sys


N = 3
data_spl = ' '
check0 = 0
check = 0
checkN =0
check_coor = 0
def parse_args():
	usage = """usage: %prog [options] [client|server|client-server|server-client|server-server|client-client] [number of process] [hostname]:(listen or connect)port (listen or connect)port

	python peer.py server 0 127.0.0.1:port """

	parser = optparse.OptionParser(usage)
	_, args = parser.parse_args()
	print args
	if len(args) > 4 or len(args)<3:
		parser.exit()
	elif len(args) == 4:
		peertype, number_of_process, addresses1, addresses2 = args
		addresses=addresses1+'&'+addresses2
	else:
		peertype, number_of_process, addresses = args
	def parse_address(addr):
		if ':' not in addr:
			host = '127.0.0.1'
			port = addr
        	else:
			host, port = addr.split(':', 1)
			print("port= "+port)

		#if not port.isdigit():
		#	parser.error('Ports must be integers.')

		return host, port
	return peertype, int(number_of_process), parse_address(addresses)

	def parse_address(addr):
		if ':' not in addr:
			host = '127.0.0.1'
			port = addr
        	else:
			host, port = addr.split(':', 1)

		if not port.isdigit():
			parser.error('Ports must be integers.')

		return host, int(port)

	return peertype, parse_address(addresses)


class Peer(Protocol):

	acks = 0
	connected = False
	
	def __init__(self, factory, peer_type ,num_of_process):
		global checkN
		self.pt = peer_type
		self.factory = factory
		self.num_of_process=num_of_process
		self.ts=time.time()
		self.id=0
		if self.num_of_process ==N-1 or self.num_of_process == 0:
			checkN += 1
			self.id = checkN
	def connectionMade(self):
		global check0, check_coor, check
		
		if self.pt == 'server':
			print "Connected from", self.transport.client
			if check_coor == 10:
				self.coordinator()
			self.connected = True
			reactor.callLater(2, self.sendUpdate)
		else:
			self.connected = True
			if self.id >= 2:
				reactor.callLater(2, self.sendUpdate)
		
				

	def sendUpdate(self):
		global check0, check, check_coor
		if check_coor == -1:
			self.coordinator()
			check=0
			check_coor=10
		else:
			if check == 1 or (check0 == 0 and self.num_of_process == 0):
				if check_coor == 0:
					self.mutual_exclusion()
					self.sendAck()
					check = 0
					check0 = 1
				
					
		if self.connected == True:
			reactor.callLater(2, self.sendUpdate)

	def sendAck(self):
		global check0
		
		self.ts = time.time()
		print "sendAck"
		try:
			
			self.transport.write('<skitalli>*'+str(self.num_of_process)+'^^')
		except Exception, e:
			print e.args[0]
		
		
	def dataReceived(self, data):
		global data_spl, check, check0, check_coor
		if data_spl != ' ':
			data = data_spl + data
		if '^^' in data:
			data, data1 =data.split('^^', 1)
		data_spl = data1
		
		print('ta data pou perimenoun :'+data_spl)
		
		if self.pt == 'client':
			print 'Client received ' + data
			if '<skitalli>' in data:
				data1, data2 = data.split('*', 1)
				if data2 == str(self.num_of_process-1):
					check = 1
					check_coor=0
			if '<coordinator>' in data:
					check=0
					data1, data2 = data.split('*', 1)	
					if data2 < str(self.num_of_process):
						self.coordinator()
						check_coor=-1
			if '<ok>' in data:
				check=0
			if '<new_coordinator>' in data:
				print "\t\t"+str(self.num_of_process)+": NEW COORDINATOR\n"
				check=1
				check_coor=0
				
		else:
			print 'Server received ' + data
			if '<skitalli>' in data:
				data1, data2 = data.split('*', 1)
				if data2 == str(N-1):
					check=1
					check_coor=0
				 	check0=0
			if '<ok>' in data:
				data1, data2 = data.split('*', 1)
				if data2 == str(N-1) and self.num_of_process == 1:
					try:
						self.transport.write('<new_coordinator>*'+'^^')
					except Exception, e:
						print e.args[0]	
			 
	def connectionLost(self, reason):
		print "Disconnected"
		if self.pt == 'client':
			self.connected = False
			self.done()

	def done(self):
		self.factory.finished(self.acks)
	def mutual_exclusion(self):
		print "mutual exclusion"
		time.sleep(2)
	def coordinator(self):
		print "send Coordinator"
		if self.pt == 'server':
			try:
				
				self.transport.write('<coordinator>*'+str(self.num_of_process)+'^^')
			except Exception, e:
				print e.args[0]
		if self.pt == 'client':
			try:
				self.transport.write('<ok>*'+str(self.num_of_process)+'^^')
			except Exception, e:
				print e.args[0]
		
			
class PeerFactory(ClientFactory, ReconnectingClientFactory):

	def __init__(self, peertype, fname, num_of_process):
		print '@__init__'
		self.pt, number_of_process = peertype.split('-', 1)
		int(number_of_process)
		self.acks = 0
		self.fname = fname
		self.records = []
		self.num_of_process=num_of_process
		self.sync=open('synchronization.txt','w+')

	def finished(self, arg):
		self.acks = arg
		self.report()

	def report(self):
		print 'Received %d acks' % self.acks

	def clientConnectionFailed(self, connector, reason):
		print 'Failed to connect to:', connector.getDestination()
		self.finished(0)

	def clientConnectionLost(self, connector, reason):
        	print 'Lost connection.  Reason:', reason
		global check_coor
        	# Connect to another peer with following host and port
        	# Host and port could be read from a list which stores peer information
        	#connector.host = '127.0.0.1'
		check_coor = -1 
		if self.num_of_process == N-1:
			self.sync=open('synchronization.txt','r+')
        		connector.port = 2197
        		ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

	def startFactory(self):
		print "@startFactory"
		#if self.pt == 'server0':
			
		#self.fp = open(self.fname+'.txt', 'w+')

	def stopFactory(self):
		print "@stopFactory"
		#if self.pt == 'server':
		#self.fp.close()

	def buildProtocol(self, addr):
		global N
		if self.num_of_process==N-1:
			self.sync.write(str(N-1))
			self.sync.close()
			
		else:
			while True:
				self.sync=open('synchronization.txt','r+')
				if self.sync.read()!=str(N-1):
					self.sync.close()
					time.sleep(3)
					
				else:
					break
		
		print "@buildProtocol"	
		protocol = Peer(self, self.pt,number_of_process)
		return protocol


if __name__ == '__main__':
	check_synchronization = 0
	peer_type, number_of_process, address= parse_args()
	
	if '&' in address[1]:
		address1 = str(address[1])
		address1, address2 = address1.split('&',1)
		if '-' not in peer_type:
			print("exeis dwsei 2 portes xwris na les se poia kanei listen h' connect h diergasia")
		else:
			peertype1, peertype2 = peer_type.split('-',1)
			

			if peertype1=='server' and peertype2=='client':
				#server
				factory = PeerFactory('server-'+str(number_of_process), 'delivered-messages-'+str(number_of_process), number_of_process)
				reactor.listenTCP(2196+number_of_process, factory)
				print "Starting server @" + address[0] + " port " + str(address[0])
				#client	
				factory = PeerFactory('client-'+str(number_of_process), 'delivered-messages-'+str(number_of_process), number_of_process)
				print "Connecting to host " + address[0] + " port " + address2
				reactor.connectTCP(address[0], int(address2), factory)	
			
			if peertype1=='client' and peertype2=='server':
				#client
				factory1 = PeerFactory('client-'+str(number_of_process), 'delivered-messages-'+str(number_of_process), number_of_process)
				print "Connecting to host " + address[0] + " port " + address1
				reactor.connectTCP(address[0], int(address1), factory1)
				#server	
				factory = PeerFactory('server-'+str(number_of_process), 'delivered-messages-'+str(number_of_process), number_of_process)
				reactor.listenTCP(2196+number_of_process, factory)
				print "Starting server @" + address[0] + " port " + str(address2)
					
			if peertype1=='server' and peertype2=='server':
				#server
				factory = PeerFactory('server-'+str(number_of_process), 'delivered-messages-'+str(number_of_process), number_of_process)
				reactor.listenTCP(2196+number_of_process, factory)
				print "Starting server @" + address[0] + " port " + str(address1)
				#server
				factory1 = PeerFactory('server-'+str(number_of_process), 'delivered-messages-'+str(number_of_process), number_of_process)
				reactor.listenTCP(2196+number_of_process+1, factory1)
				print "Starting server @" + address[0] + " port " + address2
		
			if peertype1=='client' and peertype2=='client':
				#client
				factory = PeerFactory('client-'+str(number_of_process), 'delivered-messages-'+str(number_of_process), number_of_process)
				print "Connecting to host " + address[0] + " port " + address1
				reactor.connectTCP(address[0], int(address1), factory)
				#client
				factory1 = PeerFactory('client-'+str(number_of_process), 'delivered-messages-'+str(number_of_process), number_of_process)
				print "Connecting to host " + address[0] + " port " + address2
				reactor.connectTCP(address[0], int(address2), factory1)
	else:
		if peer_type == 'server':
			factory = PeerFactory('server-'+str(number_of_process), 'delivered-messages-'+str(number_of_process), number_of_process)
			reactor.listenTCP(2196+number_of_process, factory)
			print "Starting server @" + address[0] + " port " + str(2196+number_of_process)	
		else:
			factory = PeerFactory('client-'+str(number_of_process), 'delivered-messages-'+str(number_of_process), number_of_process)
			host, port = address
			print "Connecting to host " + host + " port " + str(port)
			reactor.connectTCP(host, int(port), factory)
			
	reactor.run()
	
