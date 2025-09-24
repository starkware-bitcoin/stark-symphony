#!/usr/bin/env python3
import json
import sys
from typing import List, Tuple, Any, Dict


def u256_from_bytes_be(b: bytes) -> int:
    return int.from_bytes(b, byteorder="big", signed=False)


def u256_hex(i: int) -> str:
    return "0x" + format(i, "064x")


def bytes32_from_list(byte_list: List[int]) -> bytes:
    assert len(byte_list) == 32, "Expected 32 bytes"
    return bytes(byte_list)


def parse_qm31_from_json(node: Any) -> Tuple[int, int, int, int]:
    # JSON shape for QM31 is [[[a,b],[c,d]]] or [[a,b],[c,d]] in some places
    # Normalize to (a, b, c, d)
    x = node
    while isinstance(x, list) and len(x) == 1 and isinstance(x[0], list):
        x = x[0]
    (ab, cd) = x
    a, b = ab
    c, d = cd
    return int(a), int(b), int(c), int(d)


def qm31_value_str(q: Tuple[int, int, int, int]) -> str:
    a, b, c, d = q
    # QM31 unfolded: ((u32, u32), (u32, u32))
    return f"(({a}, {b}), ({c}, {d}))"


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

    # Build FriLayerDecommitment = [ (QM31, MerkleProof32); n_queries ]
    item_strs: List[str] = []
    for i in range(n_queries):
        witness_q = qm31_value_str(witnesses_qm31[i])
        proof_nodes_hex = [u256_hex(u256_from_bytes_be(bytes32_from_list(x))) for x in hash_witness_chunks[i]]
        proof_str = "list![" + ", ".join(proof_nodes_hex) + "]"  # MerkleProof32 remains List
        item_strs.append(f"({witness_q}, {proof_str})")

    return "[" + ", ".join(item_strs) + "]"


def build_types(cols: int, col_offsets: int, cp_parts: int, n_queries: int, n_layers: int) -> Dict[str, str]:
    # Base aliases
    M31 = "u32"
    CM31 = f"({M31}, {M31})"
    QM31 = f"({CM31}, {CM31})"
    MerkleNode = "u256"
    MerkleProof32 = f"List<{MerkleNode}, 32>"  # only List in the schema

    TraceEvalsM31 = f"[[{M31}; {col_offsets}]; {cols}]"
    CPEvalM31 = f"[{M31}; {cp_parts}]"
    TraceDecommitment = f"({TraceEvalsM31}, {MerkleProof32})"
    CpDecommitment = f"({CPEvalM31}, {MerkleProof32})"
    Decommitment = f"({TraceDecommitment}, {CpDecommitment})"

    TraceEvalsQM31 = f"[[{QM31}; {col_offsets}]; {cols}]"
    CPEvalQM31 = f"[{QM31}; {cp_parts}]"
    OodsEvals = f"({TraceEvalsQM31}, {CPEvalQM31})"

    FriQueryDecommitment = f"({QM31}, {MerkleProof32})"
    FriLayerDecommitment = f"[{FriQueryDecommitment}; {n_queries}]"
    FriDecommitments = f"({FriLayerDecommitment}, [{FriLayerDecommitment}; {n_layers}])"

    FriCommitments = f"(u256, [u256; {n_layers}], {QM31})"

    Commitments = "(u256, u256, u256)"

    return {
        "COMMITMENTS": Commitments,
        "DECOMMITMENTS": f"[{Decommitment}; {n_queries}]",
        "OODS_EVALS": OodsEvals,
        "FRI_COMMITMENTS": FriCommitments,
        "FRI_DECOMMITMENTS": FriDecommitments,
        "POW_NONCE": "u64",
    }


def build_witness_from_json(data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    # Commitments: 3 roots (const, trace, cp)
    comm_lists: List[List[int]] = data["commitments"]
    const_root_b = bytes32_from_list(comm_lists[0])
    trace_root_b = bytes32_from_list(comm_lists[1])
    cp_root_b = bytes32_from_list(comm_lists[2])

    const_root = u256_from_bytes_be(const_root_b)
    trace_root = u256_from_bytes_be(trace_root_b)
    cp_root = u256_from_bytes_be(cp_root_b)

    commitments_val = f"({u256_hex(const_root)}, {u256_hex(trace_root)}, {u256_hex(cp_root)})"

    # OODS sampled values (QM31)
    sampled_values = data["sampled_values"]
    # Trace evals QM31: columns × 1 offset
    trace_oods_json = sampled_values[1]
    trace_oods_qm31: List[Tuple[int, int, int, int]] = []
    for col in trace_oods_json:
        inner = col
        while isinstance(inner, list) and len(inner) == 1:
            inner = inner[0]
        trace_oods_qm31.append(parse_qm31_from_json(inner))

    # CP eval QM31: partitions
    cp_oods_json = sampled_values[2]
    cp_oods_qm31: List[Tuple[int, int, int, int]] = []
    for part in cp_oods_json:
        inner = part
        while isinstance(inner, list) and len(inner) == 1:
            inner = inner[0]
        cp_oods_qm31.append(parse_qm31_from_json(inner))

    # Values as arrays (no newlines)
    trace_oods_cols_vals = ["[" + qm31_value_str(q) + "]" for q in trace_oods_qm31]
    trace_oods_val = "[" + ", ".join(trace_oods_cols_vals) + "]"
    cp_oods_val = "[" + ", ".join(qm31_value_str(q) for q in cp_oods_qm31) + "]"
    oods_evals_val = f"({trace_oods_val}, {cp_oods_val})"

    # Decommitments per tree (we have 1 query in tests)
    decommitments = data["decommitments"]
    trace_proof_nodes = [u256_from_bytes_be(bytes32_from_list(x)) for x in decommitments[1]["hash_witness"]]
    cp_proof_nodes = [u256_from_bytes_be(bytes32_from_list(x)) for x in decommitments[2]["hash_witness"]]

    # Queried values (M31)
    queried = data["queried_values"]
    trace_m31 = [int(x) for x in queried[1]]  # 4 values
    cp_m31 = [int(x) for x in queried[2]]     # 16 values

    trace_evals_m31_val = "[" + ", ".join("[" + str(x) + "]" for x in trace_m31) + "]"
    cp_evals_m31_val = "[" + ", ".join(str(x) for x in cp_m31) + "]"
    trace_merkle_val = "list![" + ", ".join(u256_hex(x) for x in trace_proof_nodes) + "]"  # List only for MerkleProof
    cp_merkle_val = "list![" + ", ".join(u256_hex(x) for x in cp_proof_nodes) + "]"

    decommitment_item_val = f"(({trace_evals_m31_val}, {trace_merkle_val}), ({cp_evals_m31_val}, {cp_merkle_val}))"
    decommitments_list_val = "[" + decommitment_item_val + "]"

    # FRI config and commitments
    fri = data["fri_proof"]
    n_queries: int = int(data.get("config", {}).get("fri_config", {}).get("n_queries", 1))
    first_commitment_b = bytes32_from_list(fri["first_layer"]["commitment"]) if isinstance(fri["first_layer"]["commitment"], list) else bytes(fri["first_layer"]["commitment"])
    inner_layers = fri.get("inner_layers", [])
    n_layers: int = len(inner_layers)
    inner_commitments_b = [bytes32_from_list(layer["commitment"]) for layer in inner_layers]

    first_commitment_val = u256_hex(u256_from_bytes_be(first_commitment_b))
    inner_commitments_val = "[" + ", ".join(u256_hex(u256_from_bytes_be(c_b)) for c_b in inner_commitments_b) + "]"

    # Last layer polynomial coefficients (QM31 list of one)
    last_layer_poly = fri["last_layer_poly"]
    coeffs_json = last_layer_poly["coeffs"]
    assert len(coeffs_json) == 1, "Expected only one coefficient"
    last_coeffs_qm31 = parse_qm31_from_json(coeffs_json[0])
    last_layer_val = qm31_value_str(last_coeffs_qm31)

    fri_commitments_val = f"({first_commitment_val}, {inner_commitments_val}, {last_layer_val})"

    # FRI decommitments: first + inner
    first_layer = fri["first_layer"]
    first_layer_decommitment_val = parse_fri_layer_decommitment(first_layer, n_queries)
    inner_layer_decommitments_vals = [parse_fri_layer_decommitment(layer, n_queries) for layer in inner_layers]
    inner_layers_block_val = "[" + ", ".join(inner_layer_decommitments_vals) + "]"
    fri_decommitments_val = f"({first_layer_decommitment_val}, {inner_layers_block_val})"

    # PoW nonce
    pow_nonce = int(data.get("proof_of_work", 0))

    # Derive explicit unfolded types (arrays everywhere except MerkleProof)
    types = build_types(
        cols=len(trace_oods_qm31),
        col_offsets=1,
        cp_parts=len(cp_oods_qm31),
        n_queries=n_queries,
        n_layers=n_layers,
    )

    # Build witness map
    witness: Dict[str, Dict[str, str]] = {
        "COMMITMENTS": {
            "value": commitments_val,
            "type": types["COMMITMENTS"],
        },
        "DECOMMITMENTS": {
            "value": decommitments_list_val,
            "type": types["DECOMMITMENTS"],
        },
        "OODS_EVALS": {
            "value": oods_evals_val,
            "type": types["OODS_EVALS"],
        },
        "FRI_COMMITMENTS": {
            "value": fri_commitments_val,
            "type": types["FRI_COMMITMENTS"],
        },
        "FRI_DECOMMITMENTS": {
            "value": fri_decommitments_val,
            "type": types["FRI_DECOMMITMENTS"],
        },
        "POW_NONCE": {
            "value": str(pow_nonce),
            "type": types["POW_NONCE"],
        },
    }

    return witness


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: generate_wit.py <proof.json>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]

    with open(path, "r") as f:
        data = json.load(f)

    witness = build_witness_from_json(data)

    print(json.dumps(witness, indent=4))


if __name__ == "__main__":
    main()
