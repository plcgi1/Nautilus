import time
from itertools import takewhile
import operator
from collections import OrderedDict
import logging
import plyvel
import rlp
import json
# import dbm
# import os

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class IStorage:
    """
    Local storage for this node.
    IStorage implementations of get must return the same type as put in by set
    """

    def __setitem__(self, key, value):
        """
        Set a key to the given value.
        """
        raise NotImplementedError

    def __getitem__(self, key):
        """
        Get the given key.  If item doesn't exist, raises C{KeyError}
        """
        raise NotImplementedError

    def get(self, key, default=None):
        """
        Get given key.  If not found, return default.
        """
        raise NotImplementedError

    def iteritemsOlderThan(self, secondsOld):
        """
        Return the an iterator over (key, value) tuples for items older
        than the given secondsOld.
        """
        raise NotImplementedError

    def __iter__(self):
        """
        Get the iterator for this storage, should yield tuple of (key, value)
        """
        raise NotImplementedError


class ForgetfulStorage(IStorage):
    def __init__(self, ttl=604800):
        """
        By default, max age is a week.
        """
        self.data = OrderedDict()
        self.path = '/tmp/gossiperdb/'
        # self.db = dbm.open(self.path, 'c')
        self.ttl = ttl
        """
        if os.path.exists(self.path+'.db'):
            data = dbm.open(self.path, 'c')
            for k in data.keys():
                self.data[k] = data[k]
        """

    def __persist__(self):
        """
        for key in self.data:
            log.debug('persisting k=%s v=%s', key, self.data[key])
            self.db[key] = self.data[key]
        """
        pass

    def __setitem__(self, key, value):
        log.debug('Total storage entries %i', len(self.data)+1)

        if key in self.data:
            del self.data[key]
        self.data[key] = (time.monotonic(), value)
        self.cull()

    def contains(self, key):
        return key in self.data

    @property
    def size(self):
        return len(self.data)

    def cull(self):
        for _, _ in self.iteritemsOlderThan(self.ttl):
            self.data.popitem(last=False)
        self.__persist__()

    def get(self, key, default=None):
        self.cull()
        if key in self.data:
            return self[key]
        return default

    def __getitem__(self, key):
        self.cull()
        return self.data[key][1]

    def __iter__(self):
        self.cull()
        return iter(self.data)

    def __repr__(self):
        self.cull()
        return repr(self.data)

    def iteritemsOlderThan(self, secondsOld):
        minBirthday = time.monotonic() - secondsOld
        zipped = self._tripleIterable()
        matches = takewhile(lambda r: minBirthday >= r[1], zipped)
        return list(map(operator.itemgetter(0, 2), matches))

    def _tripleIterable(self):
        ikeys = self.data.keys()
        ibirthday = map(operator.itemgetter(0), self.data.values())
        ivalues = map(operator.itemgetter(1), self.data.values())
        return zip(ikeys, ibirthday, ivalues)

    def items(self):
        self.cull()
        ikeys = self.data.keys()
        ivalues = map(operator.itemgetter(1), self.data.values())
        return zip(ikeys, ivalues)


class PermanentStorage(IStorage):
    """ LevelDB storage """
    def __init__(self, leveldb_path='/tmp/gossiperdb/'):
        self.db = plyvel.DB(leveldb_path, create_if_missing=True)

    def __decode_record(self, record, encode="hex")->dict:
        """ Transform a bytearray from leveldb and extracts fields to generate a dict """

        res = {}
        record = record.decode()  # from bytes to str
        record = json.loads(record)  # from str to dict
        for field in record:
            if field == "tree":  # if tree, we need to rlp decode
                dec_tree = bytes.fromhex(record[field])
                dec_tree = rlp.decode(dec_tree)  # list of bytearray
                if encode == "hex":
                    res[field] = [e.hex() for e in dec_tree]
                else:
                    res[field] = dec_tree
            else:                # other fields pass through
                res[field] = record[field]
        return res

    def __setitem__(self, key, value):
        """ Warning: overwrites an existing key """
        log.debug('Total storage entries %i', self.size)
        v = value
        if isinstance(v, str):
            v = value.encode()
        self.db.put(key, v)

    def get(self, key, default=None):
        if key in self.db:
            res = self.db.get(key.encode())
            log.debug('From permanent storage get key = %s value=%s', key, res)
            return res
        return default

    def __getitem__(self, key: str)->bytes:
        """ Select value from key """
        log.debug('From permanent storage __getitem__ key=%s', key)
        k = key.encode()
        record = self.db.get(k)
        # key does not exist
        if not record:
            return b''
        return record  # self.__decode_record(record)

    def iteritemsOlderThan(self, secondsOld):
        minBirthday = time.monotonic() - secondsOld
        zipped = self._tripleIterable()
        matches = takewhile(lambda r: minBirthday >= r[1], zipped)
        return list(map(operator.itemgetter(0, 2), matches))

    def _tripleIterable(self):
        keys = []
        values = []
        for key, value in self.db:
            keys.append(key)
            values.append(value)
        birthday = map(operator.itemgetter(0), values)
        values = map(operator.itemgetter(1), values)
        return zip(keys, birthday, values)

    def disconnect(self):
        self.db.close()

    def items(self):
        keys = []
        values = []
        for key, value in self.db:
            keys.append(key)
            values.append(value)
        return zip(keys, values)

    def contains(self, key):
        return key in self.db

    @property
    def size(self):
        n = 0
        for k in self.db:
            n += 1
        return n




class DB:
    """ LevelDB wrapper """
    def __init__(self, leveldb_path):
        self.db = plyvel.DB(leveldb_path, create_if_missing=True)

    def __decode_record(self, record, encode="hex"):
        """ Transform a bytearray from leveldb and extracts fields to generate a dict """

        res = {}
        record = record.decode() # from bytes to str
        record = json.loads(record) # from str to dict
        for field in record:
            if field == "tree":  # if tree, we need to rlp decode
                dec_tree = bytes.fromhex(record[field])
                dec_tree = rlp.decode(dec_tree) # list of bytearray
                if encode=="hex":
                    res[field] = [e.hex() for e in dec_tree]
                else:
                    res[field] = dec_tree
            else:                # other fields pass through
                res[field] = record[field]
        return res

    def disconnect(self):
        self.db.close()

    def select(self, key:str, filter=None, encode="hex")->dict:
        """ Select value[filter] from key record """

        k = key.encode()
        record = self.db.get(k)
        # key does not exist
        if not record:
            return None
        return self.__decode_record(record)

    def select_all(self, encode="hex"):
        """ hex encode to jsonify (cannot serialize bytes) """
        res = {}
        for key, value in self.db:
            res[key.decode()] = self.__decode_record(value)
        return res

    def insert(self, key, value):
        """ Warning: overwrites an existing key """
        v = value
        if isinstance(v, str):
            v = value.encode()
        self.db.put(key.encode(), v)

    def delete(self, key):
        k = key.encode()
        return self.db.delete(k)
