import logging
import asyncio
from aiohttp import web
from argparse import ArgumentParser
import os
import getpass
import Globals
from account import Account
import kademlia.network as kad
from rpc import RPCDispatcher

# from kademlia.network import Server
# import json
# import rlp
# from rlp.sedes import text, big_endian_int, CountableList, List
# from kademlia.utils import BlockEncoder, checkJson
# from transaction import FitchainTx
# from rpc.modules.fit import Fit
# from werkzeug.wrappers import Request, Response
# from werkzeug.serving import run_simple
# from jsonrpc import JSONRPCResponseManager, dispatcher

# FIXME move to config
SAVE_STATE_EVERY_SECS = 60000

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# handler = logging.StreamHandler()
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# log.addHandler(handler)


class Server(object):
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = int(server_port)
        self.rpc_ip = server_ip
        self.rpc_port = 4242
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(True)


class Gossiper(Server):
    def __init__(self, server_ip, server_port, bootstrap_ip=None, bootstrap_port=None):
        super().__init__(server_ip, server_port)
        self.server = kad.Server(ksize=20, alpha=5)
        self.server.listen(interface=server_ip, port=server_port)
        self.rpcserver = None
        # create filename to store state of this node
        node_state_file = os.path.join('data/', 'state-node-' + self.server.node.id.hex())
        self.server.saveStateRegularly(node_state_file, frequency=SAVE_STATE_EVERY_SECS)
        if bootstrap_ip or bootstrap_port:
            self.loop.run_until_complete(self.server.bootstrap([(bootstrap_ip, int(bootstrap_port))]))

    @property
    def id(self, long_id=False, as_hex=True):
        if long_id:
            return self.server.node.id.long_id
        if as_hex:
            return self.server.node.id.hex()
        return self.server.node.id

    def run(self):
        self.loop.run_forever()

    def stop(self):
        self.server.stop()

    def close(self):
        self.loop.close()

    def start_rpc(self, rpc_ip, rpc_port):
        log.info('Starting RPC server at %s:%s', rpc_ip, rpc_port)
        self.rpc_ip = rpc_ip
        self.rpc_port = rpc_port
        self.rpcserver = web.Application()
        # Create RPC dispatcher and add it as handler to the server
        rpc_dispatcher = RPCDispatcher()
        self.rpcserver.router.add_post('/', rpc_dispatcher.handle_request)
        web.run_app(self.rpcserver, host=self.rpc_ip, port=self.rpc_port)

    """
    # FIXME yes it would be better to trigger from here
    async def set_key(self, key, data):
        await self.server.set(key, data)

    # FIXME likewise
    async def get_key(self, key):
        await self.server.get(key)
    """


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-i', '--interface', default='0.0.0.0', dest='server_ip',
                        help='interface to listen to')
    parser.add_argument('-p', '--port', default=42000, type=int,
                        help='port to listen on', dest='server_port')
    parser.add_argument('-b', '--bootstrap', dest='bootstrap', help='bootstrap_ip:bootstrap_port')
    parser.add_argument('--rpc', action='store_true', help='rpc server listening address')
    parser.add_argument('--rpcaddr', dest='rpc_addr', help='rpc server listening address')
    parser.add_argument('--rpcport', dest='rpc_port', type=int, help='rpc server listening port')
    parser.add_argument("-k", "--keyfile", dest="keyfilePath",
                        help="Ethereum keystore file", metavar="FILE")

    args = parser.parse_args()
    server_ip = args.server_ip
    server_port = args.server_port
    rpc_active = args.rpc
    rpc_addr = args.rpc_addr or '127.0.0.1'
    rpc_port = args.rpc_port or 4242
    bootstrap_ip, bootstrap_port = None, None

    if args.bootstrap:
        bootstrap_ip, bootstrap_port = str(args.bootstrap).split(':')

    # check keystore file exists
    if not os.path.exists(args.keyfilePath):
        parser.error("The file %s does not exist!" % args.keyfilePath)

    # Unlock ethereum account
    password = getpass.getpass()
    Globals.account = Account(keyfile=args.keyfilePath, password=password, private_key=None)
    sender_address = Globals.account.address
    sender_pubkey = Globals.account.public_key.to_bytes().hex()

    # FIXME load existing previous state
    node_last_state = 'data/node_last_state_FIXME'
    if os.path.exists(node_last_state):
        log.debug('Loading previous node state from %s', node_last_state)
        kad_server = Gossiper.server.loadState(node_last_state)

    # kademlia protocol for node discovery
    kad_server = Gossiper(server_ip, server_port, bootstrap_ip, bootstrap_port)
    Globals.kad_server = kad_server
    node_id = kad_server.id
    # log.debug('node_id = %s', node_id)

    # Create RPC Server
    if rpc_active:
        kad_server.start_rpc(rpc_addr, rpc_port)
    try:
        kad_server.run()
        # jsonrpc_server.run()
    except KeyboardInterrupt:
        # kad_server.stop()
        kad_server.close()
        # jsonrpc_server.close()
        print('Bye!')
