

def generate_key():
    import ecdsa
    from ecdsa.ecdsa import generator_secp256k1
    from ecdsa.util import number_to_string
    from lib.crypto import (
        public_key_from_private_key,
        public_key_to_p2pkh,
        serialize_privkey
    )

    privkey = number_to_string(
        ecdsa.util.randrange(pow(2, 256)),
        generator_secp256k1.order()
    )
    wif = serialize_privkey(privkey, True, 'p2pkh')
    pubkey = public_key_from_private_key(privkey, True)
    address = public_key_to_p2pkh(bytes.fromhex(pubkey))

    return wif, address