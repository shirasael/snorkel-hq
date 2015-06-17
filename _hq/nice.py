__author__ = 'code-museum'

import zmq

ZMQ_REQUEST = zmq.REQ
ZMQ_REPLY = zmq.REP
ZMQ_POLL_IN = zmq.POLLIN

def zmq_poll(socket, timeout=3000):
    return socket.poll(timeout) == ZMQ_POLL_IN
