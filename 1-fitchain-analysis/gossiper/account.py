from eth_keys import keys, KeyAPI
from eth_keyfile import extract_key_from_keyfile, create_keyfile_json
import ecies
import os, getpass
from argparse import ArgumentParser
import json
import datetime
import logging
from transaction import encode_value  # Transaction
import rlp
from rlp.sedes import big_endian_int, text, Binary
import constants
from kademlia.utils import digest
import Globals

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

"""
TODO document please

Create ethereum account from existing keyfile or from scratch

:keyfile:     keyfile to load ethereum account from
:password:
:private_key:
:path:        path to save new keyfile

"""


def verify_signature(message, signature, public_key=None):
    """
    If public_key provided, return true or false if valid
    If public_key is None, return recovered public key from signature

    @param message bytes
    @param signature bytes   b'abc\t0\abcd\...'
    @param public_key bytes  b'abc\t0\abcd\...' or None
    """

    # print('message=', message, type(message))
    # print('public_key=', public_key, type(public_key))
    # print('signature=', signature, type(signature))

    signature = signature.decode()
    if isinstance(message, str):
        message = message.encode()

    log.debug('Verify_signature message %s', message)
    signature = KeyAPI.Signature(bytes.fromhex(signature))
    recovered_pk = signature.recover_public_key_from_msg(bytes(message))
    recovered_pk = recovered_pk.to_hex()
    log.debug('Recovered public key %s', recovered_pk)

    if public_key is None:
        return recovered_pk
    return public_key == recovered_pk


def verify_msg_hash(msg_hash, signature, public_key):
    log.debug('message=%s type %s', msg_hash, type(msg_hash))
    log.debug('public_key=%s type %s', public_key, type(public_key))
    log.debug('signature=%s type %s', signature, type(signature))
    signature = KeyAPI.Signature(bytes.fromhex(signature))
    public_key = KeyAPI.PublicKey(bytes.fromhex(public_key))
    return signature.verify_msg_hash(msg_hash, public_key)

"""
def verify_transaction_v1(key: str, transaction: Transaction, sign=True):

    # Return value of this transaction after verification or
    # False if verification fails

    tx_hash = transaction.hash.hex()
    # if digest of this transaction is not key, return
    if tx_hash != key:
        log.warning('uh oh! transaction hash is not the same')
        return False

    sender_pk = transaction['sender_pk']
    nonce = transaction['nonce']
    validators = transaction['validators']
    # verify sender signature
    signatures = transaction['signatures']
    sender_signature = signatures[0]
    sender_pk = transaction['sender_pk']
    valid_sender = verify_signature(transaction.body, sender_signature, sender_pk)
    if not valid_sender:
        log.warning('Cannot verify sender, aborting.')
        return False

    # sign this transaction and append to signatures
    if sign:
        log.debug('Signing and appending this node signature')
        signa = Globals.account.sign(transaction.body, to_bytes=False)
        signatures = signatures + (signa.encode(), )

    # TODO verify all signatures
    # when state channel is opened, list of required validators is attached
    # to tx['validators']. Here we check if they have signed
    collected_signatures = 0
    for validator_signature, validator_pubkey in zip(signatures, validators):
        recovered_pk = verify_signature(transaction.body, validator_signature)
        if recovered_pk in validators:
            collected_signatures += 1

    if collected_signatures < constants.MIN_NUM_SIGNATURES:
        log.debug('Verifying transaction. But insufficient number of signatures. This transaction is not yet final...rebroadcast')

    # all is text before returning Transaction object
    signatures = [s.decode() for s in signatures]
    validators = [v.decode() for v in validators]

    return Transaction(sender_pk,
                       nonce,
                       transaction['data'],
                       transaction['timestamp'],
                       signatures,
                       validators)
"""


class Account:

    def __init__(self, keyfile=None, password=None, private_key=None, path='./'):
        if isinstance(password, str):
            password = password.encode()

        # create new account if none given
        if all(p is None for p in [keyfile, private_key]):
            private_key = os.urandom(32)
            if password is None:
                password = os.urandom(10)

            if len(password):
                log.info('-'*15, 'Save this password somewhere', '-'*15)
                log.info('<', password.hex(), '>')
                log.info('-'*58)
            else:
                log.info('-'*5, '<empty password>', '-'*5)

            keyfile_data = create_keyfile_json(private_key, password)
            # filename = 'keyfile--'+keyfile_data['address']
            filename = os.path.join(path, 'keyfile--'+keyfile_data['address'])
            with open(filename, 'w') as file:
                file.write(json.dumps(keyfile_data))

        # load account from existing keyfile
        else:
            if private_key is None:
                private_key = extract_key_from_keyfile(keyfile, password)

        # init stuff for this account
        self.private_key = KeyAPI.PrivateKey(private_key)
        self.public_key = keys.PublicKey.from_private(self.private_key)
        self.address = self.public_key.to_address()
        self.nonce = 0
        log.debug('public_key=%s type %s', self.public_key, type(self.public_key))
        log.debug('address=%s, type %s', self.address, type(self.address))
        """ convert and keep private_key, public_key, signature in to_bytes() """

    def sign(self, message: bytes, to_bytes=True):
        """
        Return (str) signature of message signed with private key (hex)

        @param message str or bytes
        """

        if not isinstance(message, bytes):
            message = message.encode()
        signature = self.private_key.sign_msg(message)
        if to_bytes:
            return signature.to_bytes()
        return signature.to_bytes().hex()

    def encrypt(self, message, public_key=None):
        """
        Return message encrypted with public key

        @param message bytes
        @param public_key bytes
        """
        if isinstance(message, str):
            message = message.encode()

        if public_key is None:
            public_key = self.public_key
        else:
            public_key = KeyAPI.PublicKey(public_key)
        return ecies.encrypt(message, public_key)

    def decrypt(self, encrypted_message):
        """
        Return decrypted message with private key

        @param encrypted_message bytes
        """
        return ecies.decrypt(encrypted_message, self.private_key)

    def create_transaction(self, data: dict)->dict:
        """ Create transaction from this account and return tx dict

        Args:
            Body content of transaction

        Return:
            dict augmented and signed transaction
        """

        # FIXME (TEST ONLY) this should be set from smart contract
        """
        validators = ['0x3d4a8e640bdcf0c640ea42e5c25877afc572101c',
                      '0x40210576d9262a214aac7494e85718ec3a12ec54',
                      '0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe',
                      '0x95d4ca7b9c8cc4f00871d95378f94ca24197ee2e']
        """
        # log.debug('From create_transaction data=%s', data)
        data_str = json.dumps(data)  # make data a string
        sender = self.public_key.to_bytes().hex()
        nonce = str(self.nonce)
        now = str(int(datetime.datetime.utcnow().timestamp()))
        body = sender + nonce + data_str + now
        # body_hash = digest(body).hex()
        # log.debug('from create_transaction message=%s type=%s', body, type(body))
        # log.debug('From create_transaction body_hash = %s', body_hash)
        signatures = {sender: self.sign(body).hex()}
        tx = encode_value(data, sender, nonce, now, signatures)
        self.nonce += 1
        return tx

    def verify_sig_msg(self, message: bytes, signature: bytes, pubkey: bytes):
        """ Verifies that message has been signed by pubkey
        Args:
            message: bytes of message to verify

            signature: bytes of signature to verify

            pubkey: public key that signed this message

        Returns:
            Boolean (True if signature is valid)
        """
        log.debug('from verify_sig_msg message=%s type=%s', message, type(message))
        public_key = KeyAPI.PublicKey(pubkey)
        sig = KeyAPI.Signature(signature)
        return sig.verify_msg(message, public_key)
