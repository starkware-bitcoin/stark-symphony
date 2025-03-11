import json
import sys

with open(sys.argv[1], 'r') as f:
    proof = json.load(f)

sep0 = ",\n                "
sep1 = ",\n             "

def format_layer(layer):
    return f"""
        (
            {layer[0]},
            {layer[1]},
            {layer[2]},
            list![
                {sep0.join(str(x) for x in layer[3])}
            ],
            {layer[4]},
            list![
                {sep0.join(str(x) for x in layer[5])}
            ]
        )"""

layers = sep1.join(format_layer(x) for x in proof['fri_layers'])

res = f"""
let proof: FibSquareProof = (
    {proof['p_mt_root']},
    (
        (
            {proof['evals'][0][0]},
            list![
                {sep0.join(str(x) for x in proof['evals'][0][1])}
            ],
        ),
        (
            {proof['evals'][1][0]},
            list![
                {sep0.join(str(x) for x in proof['evals'][1][1])}
            ],
        ),
        (
            {proof['evals'][2][0]},
            list![
                {sep0.join(str(x) for x in proof['evals'][2][1])}
            ],
        ),
    ),
    list![
        {layers}
    ],
    (
        {proof['last_layer'][0]},
        {proof['last_layer'][1]}
    )
);
"""

print(res)
