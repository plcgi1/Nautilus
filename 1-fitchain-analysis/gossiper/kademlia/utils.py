"""
General catchall for functions that don't make sense as methods.
"""
import hashlib
import operator
import asyncio
import json
from eth_utils import keccak


async def gather_dict(d):
    cors = list(d.values())
    results = await asyncio.gather(*cors)
    return dict(zip(d.keys(), results))


def digest(s):
    if not isinstance(s, bytes):
        s = str(s).encode('utf8')
    return keccak(s)


class OrderedSet(list):
    """
    Acts like a list in all ways, except in the behavior of the
    :meth:`push` method.
    """

    def push(self, thing):
        """
        1. If the item exists in the list, it's removed
        2. The item is pushed to the end of the list
        """
        if thing in self:
            self.remove(thing)
        self.append(thing)


def sharedPrefix(args):
    """
    Find the shared prefix between the strings.

    For instance:

        sharedPrefix(['blahblah', 'blahwhat'])

    returns 'blah'.
    """
    i = 0
    while i < min(map(len, args)):
        if len(set(map(operator.itemgetter(i), args))) != 1:
            break
        i += 1
    return args[0][:i]


def bytesToBitString(bites):
    bits = [bin(bite)[2:].rjust(8, '0') for bite in bites]
    return "".join(bits)


class BlockEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode("ASCII")  # utf-8
        # base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


def checkJson(expectedFields, data):
    """ Return valid true or false """
    if not data:
        return False
    for f in expectedFields:
        try:
            data[f]
        except Exception as e:
            print('Request mismatch (missing field) ' + str(e))
            return False
    return True


def bytes_to_hex(bytestring):
    res = []
    for c in bytestring:
        res.append('{:x}'.format(c))
    return ''.join(res)


def hex_to_bytes(hexstring):
    return bytes(bytearray.fromhex(hexstring))


def string_to_elements(string):
    """
    :string: elements separated by colon as in s1:s2:s3
    Return list of elements
    """

    ss = string.split(':')
    elements = []
    for s in ss:
        if s:
            elements.append(bytes.fromhex(s))
    return elements


def elements_to_string(elements):
    assert(isinstance(elements, list) == True)
    string = ''
    for e in elements:
        if e:
            string = string + e + ':'
    return string


def add_element(element, string):
    """
    Add element to string in colon separated format
    Return string with new element
    """

    elements = string_to_elements(string)
    elements.append(element)
    return elements_to_string(elements)
