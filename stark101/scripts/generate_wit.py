import json
import sys

with open(sys.argv[1], 'r') as f:
    proof = json.load(f)

def format_fri_layer(layer):
    return f"(({str(layer[0])}, {str(layer[1])}, {str(layer[2])}, list!{str(layer[3])}, {str(layer[4])}, list!{str(layer[5])}))"

p_evals = ", ".join(f"({str(x[0])}, list!{str(x[1])})" for x in proof["evals"])
fri_layers = ", ".join(format_fri_layer(layer) for layer in proof["fri_layers"])

res = {
    "P_MT_ROOT": {
        "value": str(proof["p_mt_root"]),
        "type": "u256",
    },
    "P_EVALS": {
        "value": f"({p_evals})",
        "type":  "((u32, List<u256, 32>), (u32, List<u256, 32>), (u32, List<u256, 32>))",
    },
    "FRI_LAYERS": {
        "value": f"list![{fri_layers}]",
        "type": "List<((u256, u32, u32, List<u256, 32>, u32, List<u256, 32>), 32)",
    },
    "FRI_LAST_LAYER": {
        "value": str(proof["fri_last_layer"]),
        "type": "u32",
    },
}

print(json.dumps(res, indent=4))
