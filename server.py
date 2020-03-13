import random
import numpy as np
import socket
import struct
import sys
import hashlib
import time

HOST = ''
PORT = 8888
key_size = 100
max_rbc = 5
# np.random.seed(0)

def createSocket(host, port):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	try:
		s.bind((host,port))
	except socket.error as msg:
		print('Bind failed. Error Code : ' + str(msg))
		sys.exit()

		
	s.listen(10)
	return s
	
def challengePuf(filename):
	return np.loadtxt(filename, dtype=np.bool)

def moveFlippedBits(bits, size):
	if bits == []:
		bits.append(0)
		return

	bit_i = bits.pop()
	bit_i += 1

	if bit_i < size:
		bits.append(bit_i)
		return

	moveFlippedBits(bits,size)
	bits.append(0)

def challengeResponse(response,challenge):
	m = hashlib.sha256()
	m.update(challenge.tobytes())
	hashed = m.digest()
	return hashed == response


def verifyResponse(response, challenge):
	start_time = time.time()
	valid = challengeResponse(response, challenge)
	
	flipped_bits = []
	if not valid:
		print("Performing RBC")
		flipped_bits.append(0)

		times = min(max_rbc, len(challenge))
		while len(flipped_bits) < times:
			m = hashlib.sha256()
			xored = np.zeros_like(challenge)
			for bit_loc in flipped_bits:
				xored[bit_loc] = 1
			guess = np.logical_xor(challenge,xored)

			if challengeResponse(response,guess):
				valid = True
				break
			moveFlippedBits(flipped_bits, len(challenge))

	
	print("{} error(s) found in {} s".format(len(flipped_bits),time.time()-start_time))
	return valid, len(flipped_bits)

def acceptPufTransaction(puf,s):
	conn,addr = s.accept()
	try:
		print("Connection from: " + str(addr))

		locs = np.random.randint(0,len(puf), size=(key_size,2), dtype=np.int)

		send_size = struct.pack('!I', locs.nbytes)
		conn.send(send_size)

		conn.send(locs.tobytes())

		recv_size = struct.unpack('!I',conn.recv(4))
		response = conn.recv(recv_size[0])

		challenge = np.array(np.array([puf[loc[0]][loc[1]] for loc in locs]))
		valid = verifyResponse(response, challenge)

		print("valid: " + str(valid[0]))
		conn.send(struct.pack("!?", valid[0]))
	finally:
		conn.shutdown(socket.SHUT_RDWR)
		conn.close()
		conn = None


s = createSocket(HOST,PORT)
try:
	for i in range(20):
		puf = challengePuf("puf.txt")
		acceptPufTransaction(puf,s)
finally:
	s.shutdown(socket.SHUT_RDWR)
	s.close()
	s = None



