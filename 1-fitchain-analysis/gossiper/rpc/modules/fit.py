import sys
import rlp
# import asyncio
import logging
import json
sys.path.append('..')
import Globals


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


async def broadcastTransaction(key: bytes, value: bytes, store_local=True):
    if not isinstance(key, bytes):
        key = str(key).encode()
    if not isinstance(value, bytes):
        value = str(value).encode()
    if Globals.kad_server:
        # True if at least one store call succeeded
        # log.debug('from broadcastTransaction key=%s value=%s', key, value)
        res = await Globals.kad_server.server.set_digest(key, value, store_local)
        # log.debug('from broadcastTransaction res=%s', res)
        return res

class RPCModule:
    _chain = None

    def __init__(self, chain=None):
        self._chain = chain

    def set_chain(self, chain):
        self._chain = chain


class Fit(RPCModule):
    '''
    Implements all the methods defined by JSON-RPC API, starting with "fit_"...
    Any attribute without an underscore is publicly accessible.
    '''

    def accounts(self):
        raise NotImplementedError()

    def getTransactionCount(self, address, at_block):
        raise NotImplementedError()

    async def sendTransaction(self, args: dict):
        # log.debug("From Fit.sendTransaction args=%s", args)

        # TODO validate and prepare transaction
        def __validate(s: dict):
            return s

        tx = __validate(args)

        # sign transaction with global account
        assert Globals.account is not None, 'Account has not been set, cannot sign transaction'
        signed_tx = Globals.account.create_transaction(tx)  # signed_tx is dict
        # Send transaction to network
        await broadcastTransaction(signed_tx['hash'], json.dumps(signed_tx))
        return {'key': signed_tx['hash']}

    async def getData(self, key)->dict:
        """
        Convert key to bytes (bytes.fromhex(key)) and submit request to kad server
        Args:
            key (hex string)
        """

        # log.debug('from getData key=%s', key)
        if isinstance(key, str):
            key = bytes(key, 'utf-8')
        if Globals.kad_server:
            res = await Globals.kad_server.server.get_digest(key)

        # Convert bytes to dict
        if res:
            return json.loads(res)
        return {}

    def mining(self):
        return False

    def protocolVersion(self):
        return "1.0"

    def syncing(self):
        raise NotImplementedError()
