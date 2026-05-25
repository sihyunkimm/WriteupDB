---
ctf_name: "0xV01D CTF 2026"
challenge_name: "Nujum Ledger"
category: "crypto"
difficulty: "easy"
author: "no-carve-only-pizza"
date: "2026-05-16"
points: 100
tags: [ECDSA, nonce reuse, AES-GCM]
---

# Nujum Ledger

## 문제 설명

> A ledger export contains signed production records and a sealed note. The archive is small, but the operator cleanup was incomplete.

제공 파일 `nujum.zip`에는 `transcript.json`과 `README_NOTE.txt`가 들어 있다. `README_NOTE.txt`에는 decoy flag가 적혀 있으므로 그대로 제출하면 안 된다.

## 풀이

### 분석

`transcript.json`에는 secp256k1 공개키, ECDSA 서명 3개, 그리고 AES-GCM으로 암호화된 flag blob이 들어 있다.

중요한 부분은 첫 두 서명의 `r` 값이 같다는 점이다.

```text
r1 = 0f9e421557283d32d785bce51a2760fde38f05ac34a0ed9bd24d6e99c8573524
r2 = 0f9e421557283d32d785bce51a2760fde38f05ac34a0ed9bd24d6e99c8573524
```

ECDSA에서 같은 개인키로 같은 nonce `k`를 재사용하면 같은 `r`이 나오고, 두 서명으로 `k`와 개인키 `d`를 복구할 수 있다.

### Nonce 재사용

ECDSA 서명식은 다음과 같다.

```text
s = k^-1 * (z + r*d) mod n
```

같은 `k`를 사용한 두 서명이 있으면 다음 식으로 nonce를 구할 수 있다.

```text
k = (z1 - z2) * (s1 - s2)^-1 mod n
```

그 뒤 개인키는 다음처럼 복구한다.

```text
d = (s1*k - z1) * r^-1 mod n
```

풀이 코드는 다음과 같다.

```python
import json
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.number import inverse

with open("transcript.json", "r") as f:
    data = json.load(f)

n = int(data["order_n"], 16)
sigs = data["signatures"]

r = int(sigs[0]["r"], 16)
s1 = int(sigs[0]["s"], 16)
s2 = int(sigs[1]["s"], 16)
z1 = int(sigs[0]["sha256"], 16)
z2 = int(sigs[1]["sha256"], 16)

k = ((z1 - z2) * inverse(s1 - s2, n)) % n
d = ((s1 * k - z1) * inverse(r, n)) % n
```

복구한 개인키는 다음 값이다.

```text
9728b0d524a5b91c12875559e1eef99fc45d98bacdd76e58b41a5397469bf454
```

### AES-GCM 복호화

`encrypted_flag`에는 `nonce`, `tag`, `ciphertext`, `aad`가 모두 제공되어 있다. 개인키를 32바이트 big-endian으로 바꾼 뒤 SHA-256을 적용하면 AES key가 된다.

```python
enc = data["encrypted_flag"]

key = hashlib.sha256(d.to_bytes(32, "big")).digest()
nonce = bytes.fromhex(enc["nonce"])
tag = bytes.fromhex(enc["tag"])
ct = bytes.fromhex(enc["ciphertext"])
aad = enc["aad"].encode()

cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
cipher.update(aad)
pt = cipher.decrypt_and_verify(ct, tag)

print(pt.decode())
```

실행 결과:

```text
0xV01D{nonce_reuse_turns_signatures_into_keys}
```

## 플래그

```text
0xV01D{nonce_reuse_turns_signatures_into_keys}
```

## 배운 점

ECDSA에서 nonce 재사용은 개인키 노출로 바로 이어진다. `r` 중복 여부는 서명 transcript를 볼 때 가장 먼저 확인해야 할 신호다.
