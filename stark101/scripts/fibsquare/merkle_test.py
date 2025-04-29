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


from hashlib import sha256
from random import randint

from fibsquare.field import FieldElement
from fibsquare.merkle import MerkleTree, verify_decommitment


def test_merkle_get_authentication_path():
    for _ in range(10):
        data_length = randint(0, 2000)
        data = [FieldElement.random_element() for _ in range(data_length)]
        m = MerkleTree(data)
        leaf_id = randint(0, data_length - 1)
        decommitment = m.get_authentication_path(leaf_id)
        # Check a correct decommitment.
        content = data[leaf_id]
        assert verify_decommitment(leaf_id, content, decommitment, m.root)
        # Check that altering the decommitment causes verification to fail.
        altered = decommitment[:]
        random_index = randint(0, len(altered) - 1)
        altered[random_index] = sha256(altered[random_index]).hexdigest().encode()
        assert not verify_decommitment(leaf_id, content, altered, m.root)
        # Check that altering the content causes verification to fail.
        other_content = data[randint(0, data_length - 1)]
        assert not verify_decommitment(
            leaf_id, other_content, decommitment, m.root) or other_content == content


def test_decommitment():
    root = (104500214297066916133126671825692285761566746556879834723302550549120383229768).to_bytes(32, 'big')
    leaf = FieldElement(2915689030)
    leaf_id = 365
    proof = [
        56974666195930694403713290580441264812544914556973432228768127355537336583012,
        68599396864515883651939550638527607595242626780681277342646949156789742939178,
        42301955221152678394190333573390831727995145343891343924222537015244996575494,
        94840054322059291530750321008166965053871351749658110562305809404250112199706,
        30418746830344061354082449665096536031982034761593207228745631004087660418979,
        100519484132498123993280827552597641444767528842124397297226835189343039225855,
        42453213914905194455440404069578264192574453344270898367924206751883339264593,
        86056786573167414412681166168252960406880608123124193289687215839010289393365,
        79218389783070783756683999973685334738468089983346892627711616664675847169649,
        60552900297880916965024681698561373284576136923986771043513996698868811233985,
        44367194844377689594601408886911285881450064458724818845992887113201531757121,
        68230051127233951163966464088993224369415563839403172920771929824688376897836,
        40002981752987147694309380063602322877192470823891740405244967830358421330165
    ]
    auth_path = [x.to_bytes(32, 'big') for x in proof]
    assert verify_decommitment(leaf_id, leaf, auth_path, root)
