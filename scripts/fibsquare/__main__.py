from os.path import dirname, join
import json

from fibsquare.prover import prove
from fibsquare.field import FieldElement

project_dir = dirname(dirname(__file__))


def serialize(item) -> bytes:
    if isinstance(item, bytes):
        return item
    elif isinstance(item, list):
        return 

_, res = prove()

with open(join(project_dir, '../target/proof.json'), 'w') as f:
    f.write(json.dumps(res, indent=4))
