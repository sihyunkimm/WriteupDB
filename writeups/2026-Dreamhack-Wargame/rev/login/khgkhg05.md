---
ctf_name: "Dreamhack-Wargame"
challenge_name: "login"
category: "rev"           # web / pwn / rev / crypto / misc
difficulty: "medium"      # easy / medium / hard / insane
author: "khgkhg05"
date: "2026-05-25"
points:
tags: [ELF, C++, SHA1, SHA256, S-box]
---

# 문제명

login

## 문제 설명

> 주어진 `login` 바이너리에서 올바른 id와 password를 찾아 로그인에 성공하고 flag를 구한다.

- 문제 파일: `login`
- 파일 형식: 64-bit Linux ELF PIE
- 주요 라이브러리: C++ STL, OpenSSL `SHA1`, `SHA256`

## 풀이

### 분석

IDA로 `main()`을 확인하면 프로그램은 id와 password를 차례대로 입력받고, 세 개의 검증 함수를 통과한 경우에만 flag를 출력한다.

```c
cin >> id;
if (!id_check(id))
    cout << "id does not exist ;(";
else {
    cin >> password;
    if (!password_check(id, password))
        cout << "password does not match ;(";
    else if (!old_password_check(id, password))
        cout << "you entered old password ;(";
    else
        cout << decrypt_flag(id, password);
}
```

첫 번째 검증인 `id_check()`는 입력 id의 각 문자를 다음과 같이 변환한다.

```python
v = rol4(id[i]) ^ (id[(i + 1) % len(id)] >> 5)
out.append(sbox[v])
```

여기서 사용되는 256바이트 테이블은 AES S-box와 동일하다. 비교 대상 target은 16바이트이므로 id 길이도 16바이트로 볼 수 있다.

```text
68 f0 6e 0e 82 69 88 96 5a f7 83 1b 63 3f bf ca
```

AES S-box inverse를 적용하면 다음 중간값이 나온다.

```text
f7 17 45 d7 11 e4 97 35 46 26 41 44 00 25 f4 10
```

인접한 다음 문자의 상위 비트 조건을 printable ASCII 범위에서 맞추면 id는 하나로 정해진다.

```text
_Adm!nIsTr4T0r_!
```

두 번째 검증인 `password_check()`는 id, password, 16바이트 key를 xor하여 중간 배열을 만든다.

```python
t[i] = password[i] ^ id[i] ^ key[i]
```

이후 `t[i] < t[i + 1]`이면 실패하므로, 배열은 전체적으로 `t[i] >= t[i + 1]` 조건을 만족해야 한다. 그 다음 각 원소를 S-box로 다시 섞는다.

```python
mixed[i] = (t[i] + sbox[(i ^ (~t[i] & 0xff)) & 0xff]) & 0xff
```

마지막에는 `mixed` 배열을 정렬한 결과가 내장 target과 같은지 비교한다.

```text
22 30 33 38 61 68 74 7e 83 94 b3 bc d1 e0 eb fc
```

세 번째 검증은 `SHA256(id + password)`가 내장된 32바이트 값과 같은지 확인한다.

```text
fc f0 c9 ab 55 83 3f 2b 80 a5 61 8f 6c 42 1d 2d
e0 f8 7f 0a cc be 98 05 cf a4 3e de 93 e4 ee 97
```

검증을 모두 통과하면 `decrypt_flag()`에서 `SHA1(id + password)`와 `SHA1(SHA1(id + password))`를 이용해 40바이트 암호문을 xor 복호화한다.

```python
h1 = SHA1(id + password)
h2 = SHA1(h1)

for i in range(20):
    enc[2 * i] ^= h1[i]
    enc[2 * i + 1] ^= h2[i]
```

### 취약점

이 문제의 핵심은 검증 로직이 모두 바이너리 내부의 고정 테이블과 고정 target에 의존한다는 점이다.

- `id_check()`는 AES S-box를 사용하지만, S-box는 permutation이므로 inverse table로 target을 되돌릴 수 있다.
- `password_check()`는 정렬 전 값의 감소 조건과 정렬 후 target 비교를 동시에 사용하지만, password 길이가 16바이트라 충분히 역산할 수 있다.
- 마지막 SHA256 검증은 후보를 하나로 확정하는 필터 역할을 한다.
- flag 복호화 key도 최종 id/password에서 파생되므로, 검증값을 만족하는 입력을 찾으면 flag를 바로 복호화할 수 있다.

즉 암호학적 secret을 외부에 두지 않고 바이너리에 고정해 둔 check-and-decrypt 구조라서, 정적 분석만으로 올바른 입력과 flag를 복구할 수 있다.

### 익스플로잇

아래 스크립트는 S-box inverse로 id를 복구하고, password 후보를 DFS로 줄인 뒤 SHA256 검증을 통과하는 password를 찾는다. 마지막으로 SHA1 기반 xor 복호화를 수행한다.

```python
from collections import Counter
from hashlib import sha1, sha256

sbox = bytes.fromhex(
    "637c777bf26b6fc53001672bfed7ab76ca82c97dfa5947f0add4a2af9ca472c0"
    "b7fd9326363ff7cc34a5e5f171d8311504c723c31896059a071280e2eb27b275"
    "09832c1a1b6e5aa0523bd6b329e32f8453d100ed20fcb15b6acbbe394a4c58cf"
    "d0efaafb434d338545f9027f503c9fa851a3408f929d38f5bcb6da2110fff3d2"
    "cd0c13ec5f974417c4a77e3d645d197360814fdc222a908846eeb814de5e0bdb"
    "e0323a0a4906245cc2d3ac629195e479e7c8376d8dd54ea96c56f4ea657aae08"
    "ba78252e1ca6b4c6e8dd741f4bbd8b8a703eb5664803f60e613557b986c11d9e"
    "e1f8981169d98e949b1e87e9ce5528df8ca1890dbfe6426841992d0fb054bb16"
)

id_target = bytes.fromhex("68f06e0e826988965af7831b633fbfca")
pw_target = bytes.fromhex("223033386168747e8394b3bcd1e0ebfc")
pw_key = bytes.fromhex("f88ee7dfa299ce9afd64644d4d17406d")
sha_target = bytes.fromhex("fcf0c9ab55833f2b80a5618f6c421d2de0f87f0accbe9805cfa43ede93e4ee97")
enc_flag = bytearray.fromhex(
    "c87763be4e65a5d60daf8953c24653308c9def79b064ac5c8960e189b650d5f0"
    "595c6b23c580ed0d"
)

def rol4(x):
    return ((x << 4) & 0xff) | (x >> 4)

inv = [0] * 256
for i, b in enumerate(sbox):
    inv[b] = i

mid = [inv[b] for b in id_target]
ids = []

for c0 in range(0x20, 0x7f):
    cur = [c0]

    def dfs_id(i):
        if i == 16:
            if rol4(cur[-1]) ^ (cur[0] >> 5) == mid[-1]:
                ids.append(bytes(cur))
            return
        high = rol4(cur[-1]) ^ mid[i - 1]
        for c in range(0x20, 0x7f):
            if c >> 5 == high:
                cur.append(c)
                dfs_id(i + 1)
                cur.pop()

    dfs_id(1)

user_id = ids[0]

def mix(i, t):
    return (t + sbox[(i ^ (~t & 0xff)) & 0xff]) & 0xff

possible = []
for i in range(16):
    cand = []
    for t in range(256):
        v = mix(i, t)
        if v in pw_target:
            p = t ^ user_id[i] ^ pw_key[i]
            if 0x20 <= p < 0x7f:
                cand.append((t, v, p))
    possible.append(cand)

passwords = []

def dfs_pw(i, prev, remain, out):
    if i == 16:
        password = bytes(out)
        if not remain and sha256(user_id + password).digest() == sha_target:
            passwords.append(password)
        return
    for t, v, p in possible[i]:
        if t <= prev and remain[v] > 0:
            remain[v] -= 1
            if remain[v] == 0:
                del remain[v]
            dfs_pw(i + 1, t, remain, out + [p])
            remain[v] += 1

dfs_pw(0, 255, Counter(pw_target), [])
password = passwords[0]

h1 = sha1(user_id + password).digest()
h2 = sha1(h1).digest()
for i in range(20):
    enc_flag[2 * i] ^= h1[i]
    enc_flag[2 * i + 1] ^= h2[i]

print(user_id.decode())
print(password.decode())
print(enc_flag.decode())
```

실행 결과는 다음과 같다.

```text
_Adm!nIsTr4T0r_!
^-^p4S$w0r1D._.@
DH{REDACTED}
```

실제 바이너리에 위 id와 password를 입력하면 로그인에 성공하고 flag가 출력된다.

```text
Welcome! Enter your id / password
id : password : Long time no see, here is your flag: DH{REDACTED}
```

## 플래그

```text
DH{REDACTED}
```

## 추가 파일

| 파일 | 설명 |
|------|------|
| `login` | 문제에서 제공된 원본 ELF 바이너리 |
| `solve.py` | id/password 복구와 flag 복호화를 재현하는 풀이 스크립트 |

## 배운 점

S-box처럼 암호 알고리즘에서 쓰이는 테이블이 등장해도, 입력 검증에 permutation 형태로 사용되면 inverse table을 만들어 비교값을 되돌릴 수 있다.

또한 정렬된 결과와 단조 조건이 함께 있는 검증 로직은 복잡해 보이지만, 길이가 짧고 target이 고정되어 있다면 각 위치별 후보를 만든 뒤 DFS와 hash 검증으로 충분히 풀 수 있다.

마지막으로 flag 복호화가 성공 입력에서 파생되는 key에만 의존한다면, 입력 검증 루틴을 먼저 정확히 역산하는 것이 곧 flag 복호화로 이어진다.
