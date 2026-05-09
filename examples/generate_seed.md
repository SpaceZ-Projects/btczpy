# Generate New Seed

This example shows how to generate a new BIP39 seed phrase (mnemonic) and derive the corresponding BTCZ address.

## Example

```python
from btczpy.mnemonic import Mnemonic
from btczpy.keystore import from_seed

def generate_seed():
    # Generate a new 12-word seed phrase
    seed = Mnemonic("english").make_seed()

    # Create keystore from seed
    keystore = from_seed(seed)

    # Derive first public key
    pubkey = keystore.derive_pubkey(0, 0)

    # Convert public key to BTCZ address
    address = public_key_to_p2pkh(bytes.fromhex(pubkey))

    return seed, address

seed, address = generate_seed()

print("Seed:", seed)
print("Address:", address)
```