from os.path import dirname, join
import json

from stark101.prover import prove
from stark101.field import FieldElement

project_dir = dirname(dirname(__file__))


def serialize(item) -> bytes:
    if isinstance(item, bytes):
        return item
    elif isinstance(item, list):
        return 

proof = prove()
queue = []

for item in proof:
    if isinstance(item, bytes):
        queue.append(item.hex())
    elif isinstance(item, FieldElement):
        queue.append(item.to_bytes().hex())
    elif isinstance(item, list):
        queue.extend([x.hex() for x in item[::-1]])  # Merkle auth in reversed order
    else:
        raise NotImplementedError(item)
    
# Generate test data
#     
# print('\n\n[')
# for x in queue:
#     print(f'\t0x{x} ;')
# print(']')

with open(join(project_dir, 'build/proof.json'), 'w') as f:
    f.write(json.dumps(queue))
