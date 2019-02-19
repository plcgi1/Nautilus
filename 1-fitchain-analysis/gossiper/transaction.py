import rlp
from rlp.sedes import CountableList, text  # big_endian_int
from kademlia.utils import digest
from utils import get_sender
import json
import logging
from exceptions import InvalidTransaction
import Globals

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

tx_fields = ('sender_pk', 'nonce', 'data', 'timestamp', 'signatures', 'validators')


class FitchainTx(rlp.Serializable):
    fields = [
        ('model_id', text),
        ('accuracy', text),
        ('error', text),
        ('roc', text),
        ('auc', text),
    ]


class Transaction(rlp.Serializable):
    fields = [
        ('sender_pk', text),
        ('nonce', text),
        ('data', text),
        ('timestamp', text),
        ('signatures', CountableList(text)),
        ('validators', CountableList(text)),
    ]

    def serialize(self):
        return 'sender_pk:' + self.sender_pk + ' nonce:' + self.nonce

    def __load_data__(self):
        """ Load body of this transaction to generate digest """
        data = self.sender_pk + self.nonce + self.data + self.timestamp + self.get_validators()
        return data

    @property
    def body(self):
        return self.__load_data__()

    @property
    def hash(self):
        """ Return the digest of the unsigned transaction """

        return digest(self.__load_data__())

    def get_validators(self)->str:
        """
        Serialize and stringify list of validators for this transaction
        Return list of validators as a string
        """

        v_str = []
        for v in self.validators:
            if isinstance(v, str):
                v_str.append(v)
            else:
                v_str.append(v.decode())

        return ''.join(v_str)

    @property
    def sender(self):
        return self.sender_pk

    @property
    def signers(self):
        data = self.__load_data__()
        signers = []
        for s in self.signatures:
            signer = get_sender(s, data)
            signers.append(signer)
        return signers

    def is_superior(self, transaction):
        """
        Return true if new transaction has more signatures
        than old transaction
        """

        return len(self.signatures) > len(transaction['signatures'])


def build_transaction(raw_data: list)->Transaction:
    sender_pk = raw_data[0].decode()
    nonce = raw_data[1].decode()
    data = raw_data[2].decode()
    timestamp = raw_data[3].decode()
    signatures = [s.decode() for s in raw_data[4]]
    validators = [v.decode() for v in raw_data[5]]
    return Transaction(sender_pk, nonce, data, timestamp, signatures, validators)



def decode_value(value: bytes, fields=['sender', 'nonce', 'data', 'timestamp'])->dict:
    """ Extract fields from byte-stored chunks """
    ev = json.loads(value)
    body = ''.join([ev[f] for f in fields])
    es = ev['signatures']  # existing signatures
    return {'body': body, 'signatures': es}


def encode_value(data: dict, sender: str, nonce: str, timestamp: str, signatures: dict):
    tx = {}
    data_str = json.dumps(data)
    tx['data'] = data_str
    tx['sender'] = sender
    tx['nonce'] = nonce
    tx['timestamp'] = timestamp
    tx['signatures'] = json.dumps(signatures)
    body = sender + nonce + data_str + timestamp
    tx['hash'] = digest(body).hex()
    return tx


class FitchainTransaction:
    def __init__(self, tx: dict):
        self.tx = tx

        self.valid = False
        self.valid_tx_fields = ['data', 'signatures', 'nonce', 'timestamp', 'sender', 'hash']
        self.valid_data_fields = ['model_id', 'accuracy', 'error', 'eot']

        # check validity and fill fields
        self._is_valid()

    def _is_valid(self):
        """ Process transactions for the fitchain gossiper game """
        log.debug("Checking transaction validity")

        for v in self.valid_tx_fields:
            if v not in self.tx:
                return False
                # raise InvalidTransaction

        # load signatures of this transaction
        sigs = json.loads(self.tx['signatures'])
        if not isinstance(sigs, dict):
            raise InvalidTransaction

        data = json.loads(self.tx['data'])
        for v in self.valid_data_fields:
            if v not in data:
                return False # raise InvalidTransaction

        # retrieve text fields
        nonce = self.tx['nonce']
        sender = self.tx['sender']
        timestamp = self.tx['timestamp']

        # TODO check that this content is matching
        self.body = sender + nonce + self.tx['data'] + timestamp
        body_hash = digest(self.body).hex()
        if body_hash != self.tx['hash']:
            return False  #raise InvalidTransaction

        # check attached signatures (even if they have been checked already)
        for sender in sigs:
            pubkey = bytes.fromhex(sender)
            sig = bytes.fromhex(sigs[sender])
            message = self.body.encode()

            verified = Globals.account.verify_sig_msg(message, sig, pubkey)
            if not verified:
                log.warning('Signature %s from %s is not valid', sig, sender)
                return False

        # valid transaction
        self.valid = True
        # return self.valid

    def get_signatures(self):
        if self.valid:
            return json.loads(self.tx['signatures'])

    def get_body(self):
        if self.valid:
            return self.body
