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
from typing import List, Union

from stark101.field import FieldElement


def message_repr(message: Union[bytes, FieldElement, List[bytes]]) -> str:
    if isinstance(message, bytes):
        return message.hex()
    elif isinstance(message, FieldElement):
        return str(message)
    elif isinstance(message, list):
        return " ".join(x.hex() for x in message)
    raise NotImplementedError(message)


def message_bytes(message: Union[bytes, FieldElement]) -> bytes:
    if isinstance(message, FieldElement):
        return message.to_bytes()
    elif isinstance(message, bytes):
        return message
    raise NotImplementedError(message)


class Channel(object):
    """
    A Channel instance can be used by a prover or a verifier to preserve the semantics of an
    interactive proof system, while under the hood it is in fact non-interactive, and uses Sha256
    to generate randomness when this is required.
    It allows writing string-form data to it, and reading either random integers of random
    FieldElements from it.
    """

    def __init__(self, proof=None):
        self.state = b''
        self.proof = proof or []

    def mix(self, data: Union[bytes, FieldElement]):
        data = message_bytes(data)
        self.state = sha256(self.state + data).digest()

    def send(self, data: Union[bytes, int, List[bytes]], comment: str = '', mix=False):
        if mix:
            self.mix(data)
        self.proof.append(data)
        print(f'send: {message_repr(data)} ({comment})')

    def receive(self, comment: str = '', mix=False) -> Union[bytes, FieldElement, List[bytes]]:
        data = self.proof.pop(0)
        if mix:
            self.mix(data)
        print(f'recv: {message_repr(data)} ({comment})')
        return data

    def random_int(self, min, max, action: str, comment: str = '') -> int:
        """
        Emulates a random integer sent by the verifier in the range [min, max] (including min and
        max).
        """

        # Note that when the range is close to 2^256 this does not emit a uniform distribution,
        # even if sha256 is uniformly distributed.
        # It is, however, close enough for this tutorial's purposes.
        num = min + (int.from_bytes(self.state, 'big') % (max - min + 1))
        self.state = sha256(self.state).digest()
        print(f'{action}: {num} ({comment})')
        return num

    def receive_random_int(self, min, max, comment: str = '') -> int:
        return self.random_int(min, max, action='recv', comment=comment)

    def receive_random_field_element(self, comment: str = '') -> FieldElement:
        return FieldElement(self.random_int(0, FieldElement.k_modulus - 1, action='recv', comment=comment))

    def send_random_int(self, min, max, comment: str = '') -> int:
        return self.random_int(min, max, action='send', comment=comment)

    def send_random_field_element(self, comment: str = '') -> FieldElement:
        return FieldElement(self.random_int(0, FieldElement.k_modulus - 1, action='send', comment=comment))
