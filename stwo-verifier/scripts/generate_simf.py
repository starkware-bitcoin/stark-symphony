#!/usr/bin/env python3
import json
import sys
from typing import List, Tuple, Any


def u256_from_bytes_be(b: bytes) -> int:
    return int.from_bytes(b, byteorder="big", signed=False)


def u256_hex(i: int) -> str:
    return "0x" + format(i, "064x")


def bytes32_from_list(byte_list: List[int]) -> bytes:
    assert len(byte_list) == 32, "Expected 32 bytes"
    return bytes(byte_list)


def parse_qm31_from_json(node: Any) -> Tuple[int, int, int, int]:
    # JSON shape for QM31 is [[[a,b],[c,d]]] or [[a,b],[c,d]] in some places
    # Normalize to ((a,b),(c,d))
    x = node
    # Unwrap one level if needed
    if isinstance(x, list) and len(x) == 1 and isinstance(x[0], list):
        x = x[0]
    # Now expect [[a,b],[c,d]]
    (ab, cd) = x
    a, b = ab
    c, d = cd
    return int(a), int(b), int(c), int(d)


def fmt_qm31(q: Tuple[int, int, int, int]) -> str:
    a, b, c, d = q
    return f"qm31({a}, {b}, {c}, {d})"


def indent(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line else line for line in text.splitlines())


def split_equal_chunks(lst: List[Any], n_chunks: int) -> List[List[Any]]:
    assert n_chunks > 0, "n_chunks must be positive"
    assert len(lst) % n_chunks == 0, "List length must be divisible by number of chunks"
    chunk_size = len(lst) // n_chunks
    return [lst[i * chunk_size : (i + 1) * chunk_size] for i in range(n_chunks)]


def parse_fri_layer_decommitment(layer: Any, n_queries: int) -> str:
    # Witnesses per query (QM31)
    witnesses_json = layer["fri_witness"]
    witnesses_qm31: List[Tuple[int, int, int, int]] = []
    for w in witnesses_json:
        inner = w
        while isinstance(inner, list) and len(inner) == 1:
            inner = inner[0]
        witnesses_qm31.append(parse_qm31_from_json(inner))

    # Hash witnesses are concatenated across queries – split equally
    hash_witness_concat = layer["decommitment"]["hash_witness"]
    hash_witness_chunks = split_equal_chunks(hash_witness_concat, n_queries)

    # Build FriLayerDecommitment = [ (QM31, MerkleProof32); NUM_FRI_QUERIES ]
    query_items: List[str] = []
    for i in range(n_queries):
        witness_q = fmt_qm31(witnesses_qm31[i])
        proof_nodes_hex = [
            u256_hex(u256_from_bytes_be(bytes32_from_list(x))) for x in hash_witness_chunks[i]
        ]
        proof_str = "list![" + ", ".join(proof_nodes_hex) + "]"
        item = (
            "(\n"
            "            " + witness_q + ",\n"
            "            " + proof_str + "\n"
            "        )"
        )
        query_items.append(item)

    inner = ",\n        ".join(query_items)
    return (
        "[\n"
        "        " + inner + "\n"
        "    ]"
    )


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: convert_proof.py <proof.json>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]

    with open(path, "r") as f:
        data = json.load(f)

    # Commitments: 3 roots (const, trace, cp)
    comm_lists: List[List[int]] = data["commitments"]
    const_root_b = bytes32_from_list(comm_lists[0])
    trace_root_b = bytes32_from_list(comm_lists[1])
    cp_root_b = bytes32_from_list(comm_lists[2])

    const_root = u256_from_bytes_be(const_root_b)
    trace_root = u256_from_bytes_be(trace_root_b)
    cp_root = u256_from_bytes_be(cp_root_b)

    # OODS sampled values (QM31)
    sampled_values = data["sampled_values"]
    # Trace evals QM31: 4 columns × 1 offset
    trace_oods_json = sampled_values[1]
    trace_oods_qm31: List[Tuple[int, int, int, int]] = []
    for col in trace_oods_json:
        # col shape: [[[[a,b],[c,d]]]] or similar nesting → get inner QM31
        # peel layers until we reach the pair-of-pairs
        inner = col
        while isinstance(inner, list) and len(inner) == 1:
            inner = inner[0]
        trace_oods_qm31.append(parse_qm31_from_json(inner))

    # CP eval QM31: 16 partitions
    cp_oods_json = sampled_values[2]
    cp_oods_qm31: List[Tuple[int, int, int, int]] = []
    for part in cp_oods_json:
        inner = part
        while isinstance(inner, list) and len(inner) == 1:
            inner = inner[0]
        cp_oods_qm31.append(parse_qm31_from_json(inner))

    # Decommitments: values and Merkle proofs are concatenated across queries
    decommitments = data["decommitments"]
    n_queries: int = int(data.get("config", {}).get("fri_config", {}).get("n_queries", 1))
    trace_hash_concat = decommitments[1]["hash_witness"]
    cp_hash_concat = decommitments[2]["hash_witness"]
    trace_hash_chunks = split_equal_chunks(trace_hash_concat, n_queries)
    cp_hash_chunks = split_equal_chunks(cp_hash_concat, n_queries)

    # Queried values (M31) are also concatenated
    queried = data["queried_values"]
    trace_vals_concat = [int(x) for x in queried[1]]
    cp_vals_concat = [int(x) for x in queried[2]]
    trace_val_chunks = split_equal_chunks(trace_vals_concat, n_queries)
    cp_val_chunks = split_equal_chunks(cp_vals_concat, n_queries)

    # FRI config and commitments
    fri = data["fri_proof"]
    # n_queries defined above
    layers = fri.get("layers")
    if layers is not None:
        layer_commitments_b = [
            bytes32_from_list(layer["commitment"]) if isinstance(layer["commitment"], list) else bytes(layer["commitment"])  # type: ignore[arg-type]
            for layer in layers
        ]
    else:
        # Backward compatibility: separate first + inner
        first_commitment_b = bytes32_from_list(fri["first_layer"]["commitment"]) if isinstance(fri["first_layer"]["commitment"], list) else bytes(fri["first_layer"]["commitment"])  # type: ignore[arg-type]
        inner_layers = fri.get("inner_layers", [])
        inner_commitments_b = [bytes32_from_list(layer["commitment"]) for layer in inner_layers]
        layer_commitments_b = [first_commitment_b] + inner_commitments_b

    # Last layer polynomial coefficients (QM31 list)
    last_layer_poly = fri["last_layer_poly"]
    coeffs_json = last_layer_poly["coeffs"]
    last_coeffs_qm31: Tuple[int, int, int, int]
    assert len(coeffs_json) == 1, "Expected only one coefficient"
    last_coeffs_qm31 = parse_qm31_from_json(coeffs_json[0])

    # Prepare SimplicityHL serialization
    # Commitments tuple
    commitments_str = (
        f"(\n        {u256_hex(const_root)},\n        {u256_hex(trace_root)},\n        {u256_hex(cp_root)},\n    )"
    )

    # Decommitments array: build per query using the split chunks
    decommitment_items: List[str] = []
    for i in range(n_queries):
        trace_evals_m31_str = "[" + ", ".join(f"[{int(x)}]" for x in trace_val_chunks[i]) + "]"
        cp_evals_m31_str = "[" + ", ".join(str(int(x)) for x in cp_val_chunks[i]) + "]"
        trace_merkle_str = "list![" + ", ".join(
            u256_hex(u256_from_bytes_be(bytes32_from_list(x))) for x in trace_hash_chunks[i]
        ) + "]"
        cp_merkle_str = "list![" + ", ".join(
            u256_hex(u256_from_bytes_be(bytes32_from_list(x))) for x in cp_hash_chunks[i]
        ) + "]"
        decommitment_items.append(
            "(\n            (" + trace_evals_m31_str + ", " + trace_merkle_str + "),\n            (" + cp_evals_m31_str + ", " + cp_merkle_str + "),\n        )"
        )
    decommitments_inner = ",\n        ".join(decommitment_items)
    decommitments_str = (
        "[\n        " + decommitments_inner + "\n    ]"
    )

    # OODS evals (QM31)
    trace_oods_str = "[" + ", ".join("[" + fmt_qm31(q) + "]" for q in trace_oods_qm31) + "]"
    cp_oods_str = "[" + ", ".join(fmt_qm31(q) for q in cp_oods_qm31) + "]"
    oods_evals_str = f"(\n        {trace_oods_str},\n        {cp_oods_str},\n    )"

    # FRI commitments (unified): ([u256; NUM_FRI_LAYERS], LinePoly)
    commitments_arr_str = "[" + ", ".join(u256_hex(u256_from_bytes_be(c_b)) for c_b in layer_commitments_b) + "]"
    last_layer_str = fmt_qm31(last_coeffs_qm31)
    fri_commitments_str = f"(\n        {commitments_arr_str},\n        {last_layer_str},\n    )"

    # FRI decommitments (unified array)
    fri_layers_list = layers if layers is not None else [fri["first_layer"]] + inner_layers
    fri_layer_decommitments_strs = [parse_fri_layer_decommitment(layer, n_queries) for layer in fri_layers_list]
    fri_decommitments_inner = ",\n".join(indent(s, 8) for s in fri_layer_decommitments_strs)
    fri_decommitments_str = (
        "[\n"
        + "        " + fri_decommitments_inner + "\n"
        + "    ]"
    )

    # PoW nonce
    pow_nonce = int(data.get("proof_of_work", 0))

    # Assemble final proof
    proof_str = (
        "let proof: StarkProof = (\n"
        f"    {commitments_str},\n"
        f"    {decommitments_str},\n"
        f"    {oods_evals_str},\n"
        f"    {fri_commitments_str},\n"
        f"    {fri_decommitments_str},\n"
        f"    {pow_nonce}\n"
        ");"
    )

    print(proof_str)


if __name__ == "__main__":
    main()
