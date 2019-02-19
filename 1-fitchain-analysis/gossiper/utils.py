"""    
def bytes_to_hex(bytestring):
    res = []
    for c in bytestring:
        res.append('{:x}'.format(c))
    return ''.join(res)

def hex_to_bytes(hexstring):
    return bytes(bytearray.fromhex(hexstring))
"""

from eth_keys import KeyAPI

def get_sender(signature, message):
    """ 
        @param signature bytes 
        @param message bytes 
    """
    
    if isinstance(signature, bytes):
        signature = KeyAPI.Signature(signature)
    if not isinstance(message, bytes):
        message = bytes(message)
        
    return signature.recover_public_key_from_msg(message)

    
