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

    # Decommitments
    # JSON provides per-tree decommitments; we need (trace_decommitment, cp_decommitment) per query
    # For current proofs there is 1 query.
    decommitments = data["decommitments"]
    trace_proof_nodes = [u256_from_bytes_be(bytes32_from_list(x)) for x in decommitments[1]["hash_witness"]]
    cp_proof_nodes = [u256_from_bytes_be(bytes32_from_list(x)) for x in decommitments[2]["hash_witness"]]

    # Queried values (M31)
    queried = data["queried_values"]
    trace_m31 = queried[1]  # 4 values
    cp_m31 = queried[2]     # 16 values

    # FRI commitments
    fri = data["fri_proof"]
    first_commitment_b = bytes32_from_list(fri["first_layer"]["commitment"]) if isinstance(fri["first_layer"]["commitment"], list) else bytes(fri["first_layer"]["commitment"])
    inner_layers = fri.get("inner_layers", [])
    inner_commitments_b = [bytes32_from_list(layer["commitment"]) for layer in inner_layers]

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

    # Decommitments array: only one query in provided proof
    trace_evals_m31_str = "[" + ", ".join(f"[{int(x)}]" for x in trace_m31) + "]"
    cp_evals_m31_str = "[" + ", ".join(str(int(x)) for x in cp_m31) + "]"
    trace_merkle_str = "list![" + ", ".join(u256_hex(x) for x in trace_proof_nodes) + "]"
    cp_merkle_str = "list![" + ", ".join(u256_hex(x) for x in cp_proof_nodes) + "]"
    decommitments_str = (
        "[\n        (\n            (" + trace_evals_m31_str + ", " + trace_merkle_str + "),\n            (" + cp_evals_m31_str + ", " + cp_merkle_str + "),\n        )\n    ]"
    )

    # OODS evals (QM31)
    trace_oods_str = "[" + ", ".join("[" + fmt_qm31(q) + "]" for q in trace_oods_qm31) + "]"
    cp_oods_str = "[" + ", ".join(fmt_qm31(q) for q in cp_oods_qm31) + "]"
    oods_evals_str = f"(\n        {trace_oods_str},\n        {cp_oods_str},\n    )"

    # FRI commitments (no alphas): (u256, List<u256, MAX_FRI_LAYERS>, LinePoly)
    first_commitment_str = u256_hex(u256_from_bytes_be(first_commitment_b))
    inner_commitments_str = "[" + ", ".join(u256_hex(u256_from_bytes_be(c_b)) for c_b in inner_commitments_b) + "]"
    last_layer_str = fmt_qm31(last_coeffs_qm31)
    fri_commitments_str = f"(\n        {first_commitment_str},\n        {inner_commitments_str},\n        {last_layer_str},\n    )"

    # PoW nonce
    pow_nonce = int(data.get("proof_of_work", 0))

    # Assemble final proof
    proof_str = (
        "let proof: Proof = (\n"
        f"    {commitments_str},\n"
        f"    {decommitments_str},\n"
        f"    {oods_evals_str},\n"
        f"    {fri_commitments_str},\n"
        f"    {pow_nonce}\n"
        ");"
    )

    print(proof_str)


if __name__ == "__main__":
    main()
