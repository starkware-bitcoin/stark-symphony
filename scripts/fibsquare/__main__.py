from os.path import dirname, join
import json

from fibsquare.prover import prove

project_dir = dirname(dirname(__file__))

_, res = prove()

with open(join(project_dir, '../target/proof.json'), 'w') as f:
    f.write(json.dumps(res, indent=4))
