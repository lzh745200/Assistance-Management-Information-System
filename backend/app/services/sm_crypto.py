"""国密密码模块 — SM4 对称加密 + 审计链.

SM4: 128-bit block cipher, 32 rounds, Chinese national standard (GB/T 32907-2016).
审计链: SHA-256 链式审计日志，防篡改可验证.
"""
import hashlib
import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ── SM4 S-box (国家标准) ──
_SBOX = [
    0xd6, 0x90, 0xe9, 0xfe, 0xcc, 0xe1, 0x3d, 0xb7, 0x16, 0xb6, 0x14, 0xc2, 0x28, 0xfb, 0x2c, 0x05,
    0x2b, 0x67, 0x9a, 0x76, 0x2a, 0xbe, 0x04, 0xc3, 0xaa, 0x44, 0x13, 0x26, 0x49, 0x86, 0x06, 0x99,
    0x9c, 0x42, 0x50, 0xf4, 0x91, 0xef, 0x98, 0x7a, 0x33, 0x54, 0x0b, 0x43, 0xed, 0xcf, 0xac, 0x62,
    0xe4, 0xb3, 0x1c, 0xa9, 0xc9, 0x08, 0xe8, 0x95, 0x80, 0xdf, 0x94, 0xfa, 0x75, 0x8f, 0x3f, 0xa6,
    0x47, 0x07, 0xa7, 0xfc, 0xf3, 0x73, 0x17, 0xba, 0x83, 0x59, 0x3c, 0x19, 0xe6, 0x85, 0x4f, 0xa8,
    0x68, 0x6b, 0x81, 0xb2, 0x71, 0x64, 0xda, 0x8b, 0xf8, 0xeb, 0x0f, 0x4b, 0x70, 0x56, 0x9d, 0x35,
    0x1e, 0x24, 0x0e, 0x5e, 0x63, 0x58, 0xd1, 0xa2, 0x25, 0x22, 0x7c, 0x3b, 0x01, 0x21, 0x78, 0x87,
    0xd4, 0x00, 0x46, 0x57, 0x9f, 0xd3, 0x27, 0x52, 0x4c, 0x36, 0x02, 0xe7, 0xa0, 0xc4, 0xc8, 0x9e,
    0xea, 0xbf, 0x8a, 0xd2, 0x40, 0xc7, 0x38, 0xb5, 0xa3, 0xf7, 0xf2, 0xce, 0xf9, 0x61, 0x15, 0xa1,
    0xe0, 0xae, 0x5d, 0xa4, 0x9b, 0x34, 0x1a, 0x55, 0xad, 0x93, 0x32, 0x30, 0xf5, 0x8c, 0xb1, 0xe3,
    0x1d, 0xf6, 0xe2, 0x2e, 0x82, 0x66, 0xca, 0x60, 0xc0, 0x29, 0x23, 0xab, 0x0d, 0x53, 0x4e, 0x6f,
    0xd5, 0xdb, 0x37, 0x45, 0xde, 0xfd, 0x8e, 0x2f, 0x03, 0xff, 0x6a, 0x72, 0x6d, 0x6c, 0x5b, 0x51,
    0x8d, 0x1b, 0xaf, 0x92, 0xbb, 0xdd, 0xbc, 0x7f, 0x11, 0xd9, 0x5c, 0x41, 0x1f, 0x10, 0x5a, 0xd8,
    0x0a, 0xc1, 0x31, 0x88, 0xa5, 0xcd, 0x7b, 0xbd, 0x2d, 0x74, 0xd0, 0x12, 0xb8, 0xe5, 0xb4, 0xb0,
    0x89, 0x69, 0x97, 0x4a, 0x0c, 0x96, 0x77, 0x7e, 0x65, 0xb9, 0xf1, 0x09, 0xc5, 0x6e, 0xc6, 0x84,
    0x18, 0xf0, 0x7d, 0xec, 0x3a, 0xdc, 0x4d, 0x20, 0x79, 0xee, 0x5f, 0x3e, 0xd7, 0xcb, 0x39, 0x48,
]
_FK = [0xa3b1bac6, 0x56aa3350, 0x677d9197, 0xb27022dc]
_CK = [
    0x00070e15, 0x1c232a31, 0x383f464d, 0x545b6269, 0x70777e85, 0x8c939aa1, 0xa8afb6bd, 0xc4cbd2d9,
    0xe0e7eef5, 0xfc030a11, 0x181f262d, 0x343b4249, 0x50575e65, 0x6c737a81, 0x888f969d, 0xa4abb2b9,
    0xc0c7ced5, 0xdce3eaf1, 0xf8ff060d, 0x141b2229, 0x30373e45, 0x4c535a61, 0x686f767d, 0x848b9299,
    0xa0a7aeb5, 0xbcc3cad1, 0xd8dfe6ed, 0xf4fb0209, 0x10171e25, 0x2c333a41, 0x484f565d, 0x646b7279,
]


def _rotl(x, n):
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF


def _sbox(x):
    return (_SBOX[(x >> 24) & 0xFF] << 24) | (_SBOX[(x >> 16) & 0xFF] << 16) | \
           (_SBOX[(x >> 8) & 0xFF] << 8) | _SBOX[x & 0xFF]


def _lt(x):
    return x ^ _rotl(x, 2) ^ _rotl(x, 10) ^ _rotl(x, 18) ^ _rotl(x, 24)


def _lt2(x):
    return x ^ _rotl(x, 13) ^ _rotl(x, 23)


def _key_expansion(mk):
    k = [0] * 36
    for i in range(4):
        k[i] = struct_unpack_uint32(mk[i * 4:(i + 1) * 4]) ^ _FK[i]
    rk = [0] * 32
    for i in range(32):
        k[i + 4] = k[i] ^ _lt2(_sbox(k[i + 1] ^ k[i + 2] ^ k[i + 3] ^ _CK[i]))
        rk[i] = k[i + 4]
    return rk


def struct_unpack_uint32(b):
    return int.from_bytes(b, 'big')


def struct_pack_uint32(n):
    return n.to_bytes(4, 'big')


class SM4Cipher:
    """SM4 国密分组密码."""

    def __init__(self, key: bytes):
        if len(key) != 16:
            raise ValueError("SM4 密钥长度必须为 16 字节（128 位）")
        self._rk = _key_expansion(key)

    def _process_block(self, x):
        for i in range(32):
            x.append(x[i + 1] ^ x[i + 2] ^ x[i + 3] ^ _lt(_sbox(x[i] ^ self._rk[i])))
        return [x[35], x[34], x[33], x[32]]

    def _pkcs7_pad(self, data: bytes) -> bytes:
        pad_len = 16 - (len(data) % 16)
        return data + bytes([pad_len] * pad_len)

    def _pkcs7_unpad(self, data: bytes) -> bytes:
        pad_len = data[-1]
        if pad_len > 16 or pad_len == 0:
            return data
        return data[:-pad_len]

    def encrypt_ecb(self, plaintext: bytes) -> bytes:
        pt = self._pkcs7_pad(plaintext)
        result = b""
        for i in range(0, len(pt), 16):
            block = pt[i:i + 16]
            x = [struct_unpack_uint32(block[j * 4:(j + 1) * 4]) for j in range(4)]
            y = self._process_block(x)
            result += b"".join(struct_pack_uint32(v) for v in y)
        return result

    def decrypt_ecb(self, ciphertext: bytes) -> bytes:
        rk_rev = list(reversed(self._rk))
        orig_rk = self._rk
        self._rk = rk_rev
        result = b""
        for i in range(0, len(ciphertext), 16):
            block = ciphertext[i:i + 16]
            x = [struct_unpack_uint32(block[j * 4:(j + 1) * 4]) for j in range(4)]
            y = self._process_block(x)
            result += b"".join(struct_pack_uint32(v) for v in y)
        self._rk = orig_rk
        return self._pkcs7_unpad(result)

    def encrypt_cbc(self, plaintext: bytes, iv: bytes) -> bytes:
        pt = self._pkcs7_pad(plaintext)
        result = b""
        prev = iv
        for i in range(0, len(pt), 16):
            block = pt[i:i + 16]
            xored = bytes(a ^ b for a, b in zip(block, prev))
            x = [struct_unpack_uint32(xored[j * 4:(j + 1) * 4]) for j in range(4)]
            y = self._process_block(x)
            ct_block = b"".join(struct_pack_uint32(v) for v in y)
            result += ct_block
            prev = ct_block
        return result

    def decrypt_cbc(self, ciphertext: bytes, iv: bytes) -> bytes:
        rk_rev = list(reversed(self._rk))
        orig_rk = self._rk
        self._rk = rk_rev
        result = bytearray()
        prev = iv
        for i in range(0, len(ciphertext), 16):
            block = ciphertext[i:i + 16]
            x = [struct_unpack_uint32(block[j * 4:(j + 1) * 4]) for j in range(4)]
            y = self._process_block(x)
            pt_block = b"".join(struct_pack_uint32(v) for v in y)
            pt_xored = bytes(a ^ b for a, b in zip(pt_block, prev))
            result.extend(pt_xored)
            prev = block
        self._rk = orig_rk
        return self._pkcs7_unpad(bytes(result))


# ── 审计链 ──

class AuditChain:
    """SHA-256 链式审计日志 — 每个条目包含前一哈希，防篡改."""

    def __init__(self):
        self.entries: List[Dict[str, Any]] = []
        self._prev_hash = "0" * 64

    def add_entry(self, event_type: str, data: Dict) -> Dict[str, Any]:
        seq = len(self.entries) + 1
        payload = f"{seq}|{event_type}|{json.dumps(data, sort_keys=True)}|{self._prev_hash}"
        hash_val = hashlib.sha256(payload.encode()).hexdigest()
        entry = {
            "sequence": seq,
            "event_type": event_type,
            "data": data,
            "prev_hash": self._prev_hash,
            "hash": hash_val,
        }
        self.entries.append(entry)
        self._prev_hash = hash_val
        return entry

    def verify(self) -> bool:
        prev = "0" * 64
        for e in self.entries:
            payload = f"{e['sequence']}|{e['event_type']}|{json.dumps(e['data'], sort_keys=True)}|{prev}"
            expected = hashlib.sha256(payload.encode()).hexdigest()
            if e["hash"] != expected or e["prev_hash"] != prev:
                return False
            prev = e["hash"]
        return True

    def to_json(self) -> str:
        return json.dumps(self.entries, ensure_ascii=False, indent=2)

    @staticmethod
    def from_json(json_str: str) -> "AuditChain":
        chain = AuditChain()
        chain.entries = json.loads(json_str)
        if chain.entries:
            chain._prev_hash = chain.entries[-1]["hash"]
        return chain
