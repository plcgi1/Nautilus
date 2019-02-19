import random
import asyncio
import logging
import json
import sys
from rpcudp.protocol import RPCProtocol
# import rlp
# from rlp.sedes import big_endian_int, CountableList, text
from kademlia.node import Node
from kademlia.routing import RoutingTable
from kademlia.utils import digest, string_to_elements

sys.path.append('..')
from chain import Blockchain
from transaction import decode_value  # Transaction, tx_fields, build_transaction
from transaction import FitchainTransaction
# from account import verify_transaction_v1
import Globals


log = logging.getLogger(__name__)

# TODO this is set by smart contract
MIN_NUM_SIGNATURES = 4

# Instantiate the blockchain
blockchain = Blockchain()


class KademliaProtocol(RPCProtocol):
    def __init__(self, sourceNode, storage, ksize):
        RPCProtocol.__init__(self)
        self.router = RoutingTable(self, ksize, sourceNode)
        self.storage = storage
        self.sourceNode = sourceNode

    def getRefreshIDs(self):
        """
        Get ids to search for to keep old buckets up to date.
        """
        ids = []
        for bucket in self.router.getLonelyBuckets():
            print('DEBUG *bucket.range=', *bucket.range)
            rid = random.randint(*bucket.range).to_bytes(32, byteorder='big')
            ids.append(rid)
        return ids

    def rpc_stun(self, sender):
        return sender

    def rpc_ping(self, sender, nodeid):
        source = Node(nodeid, sender[0], sender[1])
        self.welcomeIfNewNode(source)
        return self.sourceNode.id

    def rpc_store(self, sender, nodeid, key: bytes, value: bytes):
        """
        Perform RPC store to local storage. There are two types of
        store requests, both represented as (key, value) pairs.
        A node can store (hash, transaction) or (hash, signature)
        """

        log.debug("Someone with nodeid %s from %s asked me to store key=%s value=%s", nodeid.hex(), sender, key, value)
        # TODO
        # inspect message, verify transactions, store to local storage
        # or update signatures
        dirty = False

        source = Node(nodeid, sender[0], sender[1])
        self.welcomeIfNewNode(source)

        # Decode payload from json
        tx = json.loads(value)
        log.debug('Decoded transaction%s type=%s', tx, type(tx))

        # Load tx as a fitchain transaction
        ftx = FitchainTransaction(tx)
        # check validity of transaction
        if not ftx.valid:
            return False

        # if this transaction already exists, update signatures
        if self.storage.contains(key):
            # retrieve body and signatures from storage
            stored_ftx = decode_value(self.storage.get(key))  # e_value -> stored_ftx
            body, stored_sigs = stored_ftx['body'], stored_ftx['signatures']

            # in both cases check the signatures of ftx
            new_sigs = ftx.get_signatures()
            for sender in new_sigs:
                # if sender is not stored already, add him and his signature
                if sender not in stored_sigs:  # verify only new signatures
                    # update local signatures
                    stored_ftx['signatures'][sender] = new_sigs[sender]
                    dirty = True

        else:  # not in storage
            body = ftx.get_body()
            log.debug('Storing ftx')
            self.storage[key] = json.dumps(ftx.tx)

        if dirty:
            log.debug('Updating local storage with new signatures')
            self.storage[key] = json.dumps(e_value)
            # TODO broadcast to neighbors, except the node you received from
            # res = await Globals.kad_server.server.set_digest(key, ftx.tx, store_local)
            log.debug('sourceNode: %s', self.sourceNode)
        return True

        """
        # if both fields in this tx, then this is a transaction
        if 'data' in tx and 'signatures' in tx:
            # load signatures of this transaction
            new_sigs = json.loads(tx['signatures'])  # {'pubkey_sender': 'signature'}
            dirty = False

            # if this transaction already exists, update signatures
            if self.storage.contains(key):
                e_value = decode_value(self.storage.get(key))
                body = e_value['body']
                es = e_value['signatures']
            else:  # not in local storage
                # extract body
                # TODO check these fields exist
                body = tx['sender'] + tx['nonce'] + tx['data'] + tx['timestamp']
                es = tx['signatures']

            # extra check (optional)
            body_hash = digest(body).hex()
            assert key.decode() == body_hash, 'Corrupted transaction. Skipping...'
            log.debug("calculated hash %s claimed hash %s key %s", body_hash, tx['hash'], key.decode())


            # in both cases check the signatures
            for sender in new_sigs:
                if sender not in es:  # verify only new signatures
                    pubkey = bytes.fromhex(sender)
                    sig = bytes.fromhex(new_sigs[sender])
                    message = body.encode()
                    is_valid = Globals.account.verify_sig_msg(message, sig, pubkey)
                    if not is_valid:
                        log.debug('from rpc_store signature is not valid!')
                        return False
                    else:  # update local signatures
                        e_value['signatures'][sender] = new_sigs[sender]
                        dirty = True
            if dirty:
                log.debug('Updating local storage with new signatures')
                self.storage[key] = json.dumps(ev)

        # only signature
        elif 'signatures' in tx:
            new_sigs = tx['signatures']
            if self.storage.contains(key):
                e_value = decode_value(self.storage.get(key))
                body = e_value['body']
                es = e_value['signatures']
            else:
                log.info('Cannot verify signature of non existing transaction.')
                return False
            for sender in new_sigs:
                if sender not in es:  # verify only new signatures
                    pubkey = bytes.fromhex(sender)
                    sig = bytes.fromhex(new_sigs[sender])
                    message = body.encode()
                    # log.debug('SENDER COMPARISON %s == %s ', sender, es)
                    is_valid = Globals.account.verify_sig_msg(message, sig, pubkey)
                    if not is_valid:
                        log.debug('from rpc_store signature is not valid!')
                        return False
                    else:  # update local signatures
                        e_value['signatures'][sender] = new_sigs[sender]
                        dirty = True
            if dirty:
                log.debug('Updating local storage with new signatures')
                self.storage[key] = json.dumps(e_value)
        # no data nor signatures (non valid transaction)
        else:
            log.debug('This request is not valid. Skipping')
            return False
        """

    def rpc_find_node(self, sender, nodeid, key):
        log.info("finding neighbors of %i in local table",
                 int(nodeid.hex(), 16))
        source = Node(nodeid, sender[0], sender[1])
        self.welcomeIfNewNode(source)
        node = Node(key)
        neighbors = self.router.findNeighbors(node, exclude=source)
        return list(map(tuple, neighbors))

    def rpc_find_value(self, sender, nodeid, key):
        source = Node(nodeid, sender[0], sender[1])
        self.welcomeIfNewNode(source)
        value = self.storage.get(key, None)
        if value is None:
            return self.rpc_find_node(sender, nodeid, key)
        return {'value': value}

    async def callFindNode(self, nodeToAsk, nodeToFind):
        address = (nodeToAsk.ip, nodeToAsk.port)
        result = await self.find_node(address, self.sourceNode.id,
                                      nodeToFind.id)
        return self.handleCallResponse(result, nodeToAsk)

    async def callFindValue(self, nodeToAsk, nodeToFind):
        address = (nodeToAsk.ip, nodeToAsk.port)
        result = await self.find_value(address, self.sourceNode.id,
                                       nodeToFind.id)
        return self.handleCallResponse(result, nodeToAsk)

    async def callPing(self, nodeToAsk):
        address = (nodeToAsk.ip, nodeToAsk.port)
        result = await self.ping(address, self.sourceNode.id)
        return self.handleCallResponse(result, nodeToAsk)

    async def callStore(self, nodeToAsk, key, value):
        address = (nodeToAsk.ip, nodeToAsk.port)
        result = await self.store(address, self.sourceNode.id, key, value)
        return self.handleCallResponse(result, nodeToAsk)

    def welcomeIfNewNode(self, node):
        """
        Given a new node, send it all the keys/values it should be storing,
        then add it to the routing table.

        @param node: A new node that just joined (or that we just found out
        about).

        Process:
        For each key in storage, get k closest nodes.  If newnode is closer
        than the furtherst in that list, and the node for this server
        is closer than the closest in that list, then store the key/value
        on the new node (per section 2.5 of the paper)
        """
        if not self.router.isNewNode(node):
            return

        log.info("never seen %s before, adding to router", node)
        for key, value in self.storage.items():
            keynode = Node(digest(key))
            neighbors = self.router.findNeighbors(keynode)
            if len(neighbors) > 0:
                last = neighbors[-1].distanceTo(keynode)
                newNodeClose = node.distanceTo(keynode) < last
                first = neighbors[0].distanceTo(keynode)
                thisNodeClosest = self.sourceNode.distanceTo(keynode) < first
            if len(neighbors) == 0 or (newNodeClose and thisNodeClosest):
                asyncio.ensure_future(self.callStore(node, key, value))
        self.router.addContact(node)

    def handleCallResponse(self, result, node):
        """
        If we get a response, add the node to the routing table.  If
        we get no response, make sure it's removed from the routing table.
        """
        if not result[0]:
            log.warning("no response from %s, removing from router", node)
            self.router.removeContact(node)
            return result

        log.info("got successful response from %s", node)
        self.welcomeIfNewNode(node)
        return result
