import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
import requests
from flask import Flask, jsonify, request
from account import Account, verify_signature
import utils as ut


class Block:
    def __init__(self, index, difficulty, timestamp, transactions=[], proof=''):
        self.block = {
            'index': index,
            'difficulty' : difficulty,
            'timestamp': timestamp,
            'transactions': transactions,
            'proof': proof,
            'previous_hash': '',
        }
        
    def filter(self, fields):
        return { field: self.block[field] for field in BLOCK_FIELDS }
    

# TODO move into Block class
# fields that get signed
BLOCK_FIELDS = ['index', 'difficulty', 'timestamp',
                'transactions', 'proof', 'previous_hash']
    
def filter_block(block):
    assert(isinstance(block, dict) == True)
    return { field: block[field] for field in BLOCK_FIELDS}

    
class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()
        self.difficulty = 4
        
        # Create the genesis block
        self.new_block(previous_hash='1', proof=100, account=None)

    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

        
    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            #print(f'{last_block}')
            #print(f'{block}')
            #print("\n-----------\n")
            
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False
            print('block index %s hash check passed'%current_index)
            
            # Check that the Proof of Work is correct
            #if not self.valid_proof(last_block['proof'], block['proof']):
            #    return False
            #print('block index %s valid proof passed'%current_index)

            validator_signatures = block['validators']
            print('block index %s hash check passed'%current_index)
            for s in validator_signatures:
                print(s)
            print("\n------------\n")
            
            print('%s transactions in block %s' % (len(block['transactions']),
                                                   current_index))
            
            # validate each transaction in the block
            for tx_idx, tx in block['transactions']:
                sender_pubkey = bytes.fromhex(tx['sender_pubkey'])
                signature = bytes.fromhex(tx['signature'])
                data = tx['data']
                valid = verify_sender(data, signature, sender_pubkey)
                print('block index %s tx=%s verified %s'%(current_index, tx_idx, valid))
                if not valid:
                    return False
            last_block = block
            current_index += 1
        return True
    

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                # Check if the length is longer and the chain is valid
                chain_is_valid = self.valid_chain(chain)
                print('CHAIN FROM %s valid=%s'%(node, chain_is_valid))
                if length > max_length and chain_is_valid:
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash, account, consensus='pow'):
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :param account: The Account object to sign this block
        :param consensus: Consensus algorithm to mine new block (pow | poa) 
        :return: New Block
        """
        if account is None and len(self.chain) > 1:
            raise RuntimeError('Cannot sign new block ')

        block = {
            'index': len(self.chain) + 1,
            'difficulty' : self.difficulty,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
    
        if account:
            # filter, serialize, and sign block. Then add miner pubkey
            block_data = json.dumps(filter_block(block),
                                    sort_keys=True,
                                    cls=ut.BlockEncoder)
            signature = account.sign(block_data)
            # add signature and miner_pubkey to this block
            block['signature'] = signature.hex()
            block['miner_pubkey'] = account.public_key.to_bytes().hex()
        
        # Reset the current list of transactions
        self.current_transactions = []

        # send new block to all validators
        if consensus == 'poa':
            validators = []
            for node in self.nodes:
                #print('DEBUG sending block to node', block_data)
                # re-encode block before sending to validator
                block_data = json.dumps(block, sort_keys=True,
                                        cls=ut.BlockEncoder)
                #print('DEBUG sending block ', block_data)
                print("asking node %s to validate" %node)
                response = requests.post(f'http://{node}/nodes/validate',
                                         json={'block':block_data})
                if response.status_code == 200:
                    # TODO async collect signatures and append them to this block
                    #print("DEBUG RESPONSE.TEXT", response.text, response)
                    validator = response.json()['signature']
                    validators.append(validator)
            block['validators'] = validators

        # Finally append this block to chain
        self.chain.append(block)
        print('New block #%s txs=%s prev_hash=%s' %(block['index'],
                                                    len(block['transactions']),
                                                    block['previous_hash']))

        # TODO save to local storage

        # TODO Merkle root of block header. Transactions stored somewhere else :)
        return block

    def add_block(self, block):
        """ Helper for proof-of-authority algo """
        self.chain.append(block)
        
    def new_transaction(self, sender_address, sender_pubkey,
                        amount, data, signature):
        """
        Creates a new transaction to append to the next mined Block

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :param signature: Signature of stringified data
        :return: The index of the Block that will hold this transaction
        """
        
        self.current_transactions.append({
            'sender_address': sender_address,
            'sender_pubkey' : sender_pubkey,
            'amount': amount,
            'data'  : data,
            'signature': signature,
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: Block
        """

        # Dictionary must be Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block,
                                  sort_keys=True,
                                  cls=ut.BlockEncoder).encode()
        # TODO switch to kekkac as we go to ethereum
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
         - p is the previous proof, and p' is the new proof
        """

        proof = 0
        while self.valid_proof(last_proof, proof, self.difficulty) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof, difficulty=4):
        """
        Validates the Proof

        :param last_proof: Previous Proof
        :param proof: Current Proof
        :return: True if correct, False if not.
        """
        
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:difficulty] == difficulty*"0"


# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine_pos():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    delta = time() - last_block['timestamp']
    
    #if delta < 5:
    #    blockchain.difficulty = blockchain.difficulty + 1
        
    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    """
    blockchain.new_transaction(
        sender="0",
        amount=1,
        data="",
        signature="",
    )
    """
    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    # pass account to sign this block 
    block = blockchain.new_block(proof, previous_hash, account)
    
    
    response = {
        'message': "New Block Mined",
        'index': block['index'],
        'delta': delta,
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/mine_poa', methods=['GET'])
def mine_poa():
    # We run the proof of authority algorithm to get the next block
    last_block = blockchain.last_block
    # TODO can get rid of this 
    proof = ''
    
    #print('last_block=', last_block)
    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    # pass account to sign this block 
    block = blockchain.new_block(proof, previous_hash, account, consensus='poa')
    
    response = {
        'message': "New Block Authorized",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200




@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
        
    # Check required fields are in the POST request
    required = ['amount', 'data']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # TODO check balance (if amount is active)
    amount = values['amount']
    data = values['data']
    data = json.dumps(data, sort_keys=True).encode()
        
    # Sign this data before adding to transaction
    signature = account.sign(data)
    
    # Create a new Transaction (all fields converted to hex
    sender_address = account.address
    sender_pubkey  = account.public_key.to_bytes().hex()
    signature = signature.hex()
    index = blockchain.new_transaction(sender_address,
                                       sender_pubkey,
                                       amount,
                                       data,
                                       signature)

    response = {'message': 'New transaction added to Block {index}'}
    
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: No list of nodes have been provided", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'Added new nodes to sidechain',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {
            'message': 'Local chain has been replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Local chain is the most authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200


@app.route('/nodes/validate', methods=['POST'])
def validate():
    values = request.get_json()
    block = json.loads(values.get('block'))
    miner_pubkey = block['miner_pubkey']
    block_signature = block['signature']

    # if block is valid, sign it and return
    block_data = json.dumps(filter_block(block),
                            sort_keys=True,
                            cls=ut.BlockEncoder)
    valid = verify_sender(block_data,
                   bytes.fromhex(block_signature),
                   bytes.fromhex(miner_pubkey))

    # if block is valid, return signature of this validator
    if valid:
        response = {'signature': account.sign(block_data).hex() }
        
    return jsonify(response), 200
    

if __name__ == '__main__':
    from argparse import ArgumentParser
    import os
    import getpass

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=4242, type=int, help='port to listen on')

    parser.add_argument("-k", "--keyfile", dest="keyfilePath",
                        help="Ethereum keystore file", metavar="FILE")
    
    args = parser.parse_args()
    print('Ethereum keyfile', args.keyfilePath)
    if not os.path.exists(args.keyfilePath):
        parser.error("The file %s does not exist!" % args.keyfilePath)

    # unlock ethereum account
    #password = getpass.getpass()
    password = 'PoI6i4y8bheuxzxUeGGOCqM4OqZh53'
    port = args.port
    account = Account(keyfile=args.keyfilePath, password=password, private_key=None)
    app.run(host='0.0.0.0', port=port)


