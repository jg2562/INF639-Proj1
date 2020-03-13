import random
import numpy as np
import socket
import struct
import sys
import hashlib

HOST = ''
PORT = 8888
# puf_err_per = 0.01
puf_err_per = 0.00
rep_errs = 10
# np.random.seed(0)

def connectSocket(host, port):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((host,port))
	return s
	
def loadPuf(filename, err_per):
		
	puf = np.loadtxt(filename, dtype=np.bool)
	
	mutate_matrix = np.random.rand(len(puf), len(puf[0]))
	xor_matrix = mutate_matrix < err_per
	print("Injected {} errors into puf".format(np.sum(xor_matrix)))

	return np.logical_xor(puf,xor_matrix)

def lookupLocations(locs, puf):
	vals = np.array([puf[loc[0]][loc[1]] for loc in locs])
	err_xor = np.arange(len(locs)) < rep_errs
	np.random.shuffle(err_xor)
	vals = np.logical_xor(vals, err_xor)
	print("Injected {} errors into response".format(np.sum(err_xor)))
	return  vals

def runPufTransaction(puf,conn):

	recv_size = struct.unpack("!I", conn.recv(4))
	raw_locs =  conn.recv(recv_size[0])
	locs = np.frombuffer(raw_locs,dtype=np.int)
	locs = np.reshape(locs, (-1,2))

	m = hashlib.sha256()
	response = lookupLocations(locs,puf)
	m.update(response.tobytes())
	response = m.digest()
	
	conn.send(struct.pack('!I', m.digest_size))
	conn.send(response)

	valid = struct.unpack("!?", conn.recv(1))

	print("valid: " + str(valid[0]))

s = connectSocket(HOST,PORT)
try:
	puf = loadPuf("puf.txt", puf_err_per)
	runPufTransaction(puf,s)
finally:
	s.shutdown(socket.SHUT_RDWR)
	s.close()
	s = None



