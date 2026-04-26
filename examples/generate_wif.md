
# Generate WIF and Address

This example shows how to generate a random private key, convert it to **WIF (Wallet Import Format)**, and derive the corresponding BTCZ address.

## Example

```python
def generate_key():
    import ecdsa
    from ecdsa.ecdsa import generator_secp256k1
    from ecdsa.util import number_to_string
    from btczpy.crypto import (
        public_key_from_private_key,
        public_key_to_p2pkh,
        serialize_privkey
    )

    # Generate random private key (32 bytes)
    privkey = number_to_string(
        ecdsa.util.randrange(pow(2, 256)),
        generator_secp256k1.order()
    )

    # Convert private key to WIF (compressed, P2PKH)
    wif = serialize_privkey(privkey, True, 'p2pkh')

    # Derive public key (compressed)
    pubkey = public_key_from_private_key(privkey, True)

    # Convert public key to BTCZ address
    address = public_key_to_p2pkh(bytes.fromhex(pubkey))

    return wif, address

wif, address = generate_key()

print("WIF:", wif)
print("Address:", address)