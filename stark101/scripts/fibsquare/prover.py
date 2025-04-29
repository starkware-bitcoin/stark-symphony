###############################################################################
# Copyright 2025 StarkWare Industries Ltd.                                    #
#                                                                             #
# Licensed under the Apache License, Version 2.0 (the "License").             #
# You may not use this file except in compliance with the License.            #
# You may obtain a copy of the License at                                     #
#                                                                             #
# https://www.starkware.co/open-source-license/                               #
#                                                                             #
# Unless required by applicable law or agreed to in writing,                  #
# software distributed under the License is distributed on an "AS IS" BASIS,  #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.    #
# See the License for the specific language governing permissions             #
# and limitations under the License.                                          #
###############################################################################

from typing import List

from fibsquare.channel import Channel
from fibsquare.field import FieldElement
from fibsquare.merkle import MerkleTree
from fibsquare.polynomial import interpolate_poly, Polynomial, X


def generate_trace() -> List[FieldElement]:
    # FibonacciSq, 1023 elements
    t = [FieldElement(1), FieldElement(3141592)]
    while len(t) < 1023:
        t.append(t[-2] * t[-2] + t[-1] * t[-1])
    return t


def generate_subgroup(size: int) -> List[FieldElement]:
    assert (3 * 2 ** 30) % size == 0
    g = FieldElement.generator() ** ((3 * 2 ** 30) // size)
    return [g ** i for i in range(size)]


def generate_left_coset(size: int) -> List[FieldElement]:
    g = generate_subgroup(size)
    return [FieldElement.generator() * x for x in g]


def build_constraints(p: Polynomial, domain: List[FieldElement]) -> List[Polynomial]:
    p0 = (p - 1) / (X - 1)
    p1 = (p - 2338775057) / (X - domain[1022])

    p2_denom = (X**1024 - 1) / ((X - domain[1021]) * (X - domain[1022]) * (X - domain[1023]))
    p2_numer = p(domain[2] * X) - p(domain[1] * X)**2 - p**2
    p2 = p2_numer / p2_denom

    return [p0, p1, p2]


def build_composition_polynomial(constraints: List[Polynomial], channel: Channel) -> tuple[Polynomial, tuple[FieldElement, FieldElement, FieldElement]]:
    p0, p1, p2 = constraints
    a0 = channel.receive_random_field_element('composition polynomial coefficient #0')
    a1 = channel.receive_random_field_element('composition polynomial coefficient #1')
    a2 = channel.receive_random_field_element('composition polynomial coefficient #2')
    cp0 = p0.scalar_mul(a0)
    cp1 = p1.scalar_mul(a1)
    cp2 = p2.scalar_mul(a2)
    cp = cp0 + cp1 + cp2
    return cp, (a0, a1, a2)


def next_fri_domain(domain: List[FieldElement]) -> List[FieldElement]:
    return [x ** 2 for x in domain[:len(domain) // 2]]


def next_fri_polynomial(poly: Polynomial, alpha: FieldElement) -> Polynomial:
    odd_coefficients = poly.poly[1::2]
    even_coefficients = poly.poly[::2]
    odd = Polynomial(odd_coefficients).scalar_mul(alpha)
    even = Polynomial(even_coefficients)
    return odd + even


def next_fri_layer(prev_poly, prev_domain, beta: FieldElement) -> tuple:
    fri_poly = next_fri_polynomial(prev_poly, beta)
    fri_domain = next_fri_domain(prev_domain)
    fri_layer = [fri_poly.eval(x) for x in fri_domain]
    fri_mt = MerkleTree(fri_layer)
    return fri_poly, fri_domain, fri_layer, fri_mt


def decommit(channel: Channel, poly_ev: List[FieldElement], poly_mt: MerkleTree, idx: int, comment: str) -> tuple[FieldElement, list[bytes]]:
    auth_path = poly_mt.get_authentication_path(idx)
    channel.send(poly_ev[idx], comment)
    channel.send(auth_path, f'{comment} auth')
    return poly_ev[idx], auth_path


def prove(domain_size=1024, domain_ex_mult=8) -> tuple[list, dict]:
    channel = Channel()
    res = {}

    # Generate FibonacciSq Trace, multiplicative subgroup, and extended evaluation domain
    trace = generate_trace()
    domain = generate_subgroup(size=domain_size)
    domain_ex = generate_left_coset(size=domain_ex_mult * len(domain))  # 8x larger than the original domain

    # Interpolate polynomial and evaluate it on an extended domain
    p = interpolate_poly(domain[:-1], trace)
    p_ev = [p.eval(d) for d in domain_ex]
    p_mt = MerkleTree(p_ev)
    channel.send(p_mt.root, 'trace polynomial merkle root', mix=True)
    res['p_mt_root'] = int.from_bytes(p_mt.root, 'big')

    # Produce constraint polynomials and composition polynomial out of them, then evaluate on extended domain
    constraints = build_constraints(p, domain)
    cp, _ = build_composition_polynomial(constraints, channel)
    cp_ev = [cp.eval(d) for d in domain_ex]
    cp_mt = MerkleTree(cp_ev)
    channel.send(cp_mt.root, 'composition polynomial merkle root', mix=True)

    # FRI layer commitments
    fri_poly = cp
    fri_domain = domain_ex
    fri_layers = [cp_ev]
    fri_mts = [cp_mt]
    fri_betas = []

    while fri_poly.degree() > 0:
        beta = channel.receive_random_field_element(f'fri polynomial beta #{len(fri_layers)}')
        fri_poly, fri_domain, fri_layer, fri_mt = next_fri_layer(fri_poly, fri_domain, beta)
        if fri_poly.degree() > 0:
            # do not send for the last layer (free term)
            channel.send(fri_mt.root, f'fri layer merkle root #{len(fri_layers)}', mix=True)
        fri_layers.append(fri_layer)
        fri_mts.append(fri_mt)
        fri_betas.append(beta)

    channel.send(fri_poly.poly[0], 'last fri layer', mix=True)

    # Query
    idx = channel.receive_random_int(0, len(domain_ex) - 1, 'query')

    # Decommit on trace polynomial
    f_x, f_x_auth = decommit(channel, p_ev, p_mt, idx, 'f(x)')
    f_gx, f_gx_auth = decommit(channel, p_ev, p_mt, idx + domain_ex_mult, 'f(gx)')
    f_ggx, f_ggx_auth = decommit(channel, p_ev, p_mt, idx + 2 * domain_ex_mult, 'f(ggx)')
    res['evals'] = [
        [f_x.val, [int.from_bytes(x, 'big') for x in f_x_auth[::-1]]],
        [f_gx.val, [int.from_bytes(x, 'big') for x in f_gx_auth[::-1]]],
        [f_ggx.val, [int.from_bytes(x, 'big') for x in f_ggx_auth[::-1]]],
    ]

    # Decommit on FRI layers (including initial composition polynomial, excluding the last one)
    res['fri_layers'] = []
    for i in range(len(fri_layers) - 1):
        length = len(fri_layers[i])
        fri_idx = idx % length  # x
        sib_idx = (idx + length // 2) % length  # -x
        cpa_ev, cpa_auth = decommit(channel, fri_layers[i], fri_mts[i], fri_idx, f'cp_{i}')
        # print(f'>>>>>>>>> cpa_ev: {cpa_ev.val}, mt: {int.from_bytes(fri_mts[i].root, "big")}, cpa_idx: {fri_idx} <<<<<<<<')
        cpb_ev, cpb_auth = decommit(channel, fri_layers[i], fri_mts[i], sib_idx, f'cp_{i} sibling')
        res['fri_layers'].append([
            int.from_bytes(fri_mts[i].root, 'big'),
            fri_betas[i].val,
            cpa_ev.val,
            [int.from_bytes(x, 'big') for x in cpa_auth[::-1]],
            cpb_ev.val,
            [int.from_bytes(x, 'big') for x in cpb_auth[::-1]],
        ])

    res['fri_last_layer'] = fri_layers[-1][0].val

    # Decommit on last polynomial
    channel.send(fri_layers[-1][0], 'last FRI polynomial free term')
    return channel.proof, res
