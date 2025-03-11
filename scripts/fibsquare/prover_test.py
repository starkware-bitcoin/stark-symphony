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

import math

from fibsquare.channel import Channel
from fibsquare.prover import prove
from fibsquare.field import FieldElement
from fibsquare.merkle import verify_decommitment


def receive_and_verify_field_element(channel: Channel, idx: int, mt_root: bytes, comment: str = '') -> FieldElement:
    elt = channel.receive(comment)
    auth = channel.receive(f'{comment} auth')
    verify_decommitment(idx, elt, auth, mt_root)
    return elt


def test_prover(domain_size=1024, domain_ex_mult=8):
    print("\n===================== Prover log =====================")
    proof, _ = prove(domain_size=domain_size, domain_ex_mult=domain_ex_mult)

    print("\n==================== Verifier log ====================")
    channel = Channel(proof)

    # Restore commitments
    p_mt_root = channel.receive('p_mt_root', mix=True)
    # print(f">>>>>>>>> channel state: {int.from_bytes(channel.state, 'big')} <<<<<<<<")
    cp_alpha = [channel.send_random_field_element(f'cp_alpha_{i}') for i in range(3)]

    fri_mt_roots = []
    fri_beta = []
    num_fri_layers = int(math.log2(domain_size)) + 1

    for i in range(num_fri_layers):
        # print(f">>>>>>>>> channel state: {int.from_bytes(channel.state, 'big')} <<<<<<<<")
        fri_mt_roots.append(channel.receive(f'cp_{i}_mt_root', mix=True))
        if i < num_fri_layers - 1:
            fri_beta.append(channel.receive_random_field_element(f'cp_{i+1}_beta'))

    # print(f">>>>>>>>> channel state: {int.from_bytes(channel.state, 'big')} <<<<<<<<")

    fri_last = channel.receive('last fri layer', mix=True)

    # print(f">>>>>>>>> fri_last: {fri_last.val} <<<<<<<<")
    # print(f">>>>>>>>> channel state: {int.from_bytes(channel.state, 'big')} <<<<<<<<")
    idx = channel.send_random_int(0, domain_size * domain_ex_mult - 1, 'query')
    #print(f">>>>>>>>> new channel state: {int.from_bytes(channel.state, 'big')} <<<<<<<<")

    # Receive and authenticate trace polynomial evaluations
    f_x = receive_and_verify_field_element(channel, idx, p_mt_root, 'f(x)')
    f_gx = receive_and_verify_field_element(channel, idx + domain_ex_mult, p_mt_root, 'f(gx)')
    f_ggx = receive_and_verify_field_element(channel, idx + 2 * domain_ex_mult, p_mt_root, 'f(ggx)')

    # Receive and authenticate FRI layers
    cp = []
    fri_domain_size = domain_size * domain_ex_mult

    for i in range(num_fri_layers - 1):
        fri_idx = idx % fri_domain_size
        fri_sib = (idx + fri_domain_size // 2) % fri_domain_size
        # print(f">>>>>>>>> fri_idx: {fri_idx}, fri_sib: {fri_sib}, domain_size: {fri_domain_size}, idx: {idx} <<<<<<<<")
        cp.append(receive_and_verify_field_element(channel, fri_idx, fri_mt_roots[i], f'cp_{i}'))
        cp.append(receive_and_verify_field_element(channel, fri_sib, fri_mt_roots[i], f'cp_{i} sibling'))
        fri_domain_size >>= 1

    cp.append(channel.receive('last fri layer'))

    # Check the composition polynomial correctness
    g = FieldElement.generator() ** ((3 * 2 ** 30) // domain_size)
    points = [g ** i for i in {1021, 1022, 1023}]

    h = FieldElement.generator() ** ((3 * 2 ** 30) // (domain_size * domain_ex_mult))
    x = FieldElement.generator() * (h ** idx)
    # print(f">>>>>>>>> x: {x}, h: {h}, g: {FieldElement.generator()}, e: {h ** idx} <<<<<<<<")

    p0 = (f_x - 1) / (x - 1)
    p1 = (f_x - 2338775057) / (x - points[1])
    p2 = (f_ggx - f_gx**2 - f_x**2) * (x - points[0]) * (x - points[1]) * (x - points[2]) / (x**1024 - 1)
    assert cp[0] == (cp_alpha[0] * p0 + cp_alpha[1] * p1 + cp_alpha[2] * p2), 'Composition polynomial invalid'
    # print(f">>>>>>>>> cp[0]: {cp[0]}, p0: {p0}, p1: {p1}, p2: {p2} <<<<<<<<")

    # Check that polynomial is of low degree
    fri_x = x

    for i in range(0, num_fri_layers - 1):
        op1 = (cp[2 * i] + cp[2 * i + 1]) / FieldElement(2)
        op2 = (cp[2 * i] - cp[2 * i + 1]) / (FieldElement(2) * fri_x)
        rhs = op1 + fri_beta[i] * op2
        # print(f">>>>>>>>> rhs: {rhs}, x: {fri_x}, beta: {fri_beta[i]}, cpa: {cp[2 * i]}, cpb: {cp[2 * i + 1]} <<<<<<<<")
        assert cp[2 * (i + 1)] == rhs, f'FRI layer #{i} invalid'
        fri_x = fri_x**2
