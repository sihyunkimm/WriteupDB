---
ctf_name: "Dreamhack-Wargame"
challenge_name: "ptrace-block"
category: "rev"           # web / pwn / rev / crypto / misc
difficulty: "medium"      # easy / medium / hard / insane
author: "khgkhg05"
date: "2026-05-12"
points:
tags: [ptrace, AES-CBC, init_array]
---

# 문제명

ptrace-block

## 문제 설명

> 제작자가 입력한 내용이 어떤 내용이었는지 맞춰주세요!
> 해당 문자열은 DH{..}이며, printable ascii입니다.

주어진 파일은 `prob`와 `out.txt`이다.
`prob`는 사용자 입력을 받아 암호화한 뒤 `out.txt`에 저장하는 프로그램이고, 제공된 `out.txt`를 역산하여 제작자가 입력했던 문자열을 구하는 문제이다.

## 풀이

### 분석

`prob`는 64-bit ELF 바이너리이며, 문자열과 import를 확인하면 다음과 같은 함수들이 사용된다.

```text
AES_set_encrypt_key
AES_cbc_encrypt
ptrace
srand
rand
time
```

`main()` 함수에서는 사용자 입력을 받고, 256바이트를 암호화한 뒤 `./out.txt`에 저장한다.

```c
scanf("%255s", input);
sub_13F1(input, output, 0x100);
fd = open("./out.txt", 1);
write(fd, output, 0x100);
```

실제 AES-CBC 암호화는 `sub_13F1()`에서 수행된다.
이 함수는 전역 `key`를 이용해 AES-128 key schedule을 만들고, IV를 16바이트 `0x00`으로 둔 뒤 CBC 암호화를 수행한다.

```c
AES_set_encrypt_key(key, 128, &aes_key);
AES_cbc_encrypt(input, output, len, &aes_key, iv, AES_ENCRYPT);
```

중요한 점은 전역 `key`가 `main()` 전에 이미 변형된다는 것이다.
`.init_array`에는 다음 함수들이 등록되어 있다.

```text
0x12c0
0x12c9
0x1392
```

이 중 `0x12c9`, `0x1392`가 key 변형에 영향을 준다.

### `init_array 분석`

초기 key는 `.data`에 다음과 같이 저장되어 있다.

```text
41 28 19 4e a5 7c a1 41 13 cf 88 ac 2a f0 b7 da
```

먼저 `sub_12C9()`는 다음과 같은 형태이다.

```c
v0 = time(nullptr);
srand(v0);
v2 = 1;

for (i = 0; i <= 4095; ++i)
{
    v1 = ptrace(PTRACE_TRACEME, 0, 0, 0);
    v2 *= v1 * rand();
}

for (j = 0; j <= 14; ++j)
    key[j + 1] += key[j] + v2;
```

정상 실행에서 첫 번째 `ptrace(PTRACE_TRACEME)` 호출은 성공하며 `0`을 반환한다.
따라서 첫 루프에서 `v2`는 바로 `0`이 된다.
이후 루프에서 어떤 값이 곱해지더라도 `v2`는 계속 `0`이다.

그러므로 실제 key 변형은 다음과 같이 해석할 수 있다.

```c
for (j = 0; j <= 14; ++j)
    key[j + 1] += key[j];
```

이를 적용하면 중간 key는 다음과 같다.

```text
41 69 82 d0 75 f1 92 d3 e6 b5 3d e9 13 03 ba 94
```

다음으로 `sub_1392()`에서는 `rand()`를 이용해 key 전체에 같은 값을 XOR한다.

```c
v0 = rand();
srand(v0);
result = rand();
v3 = result;

for (i = 0; i <= 15; ++i)
    key[i] ^= v3;
```

`v3`는 `char` 타입이므로 `rand()` 전체가 아니라 하위 1바이트만 key에 영향을 준다.
즉 가능한 값은 `0x00`부터 `0xff`까지 256개뿐이다.

### 핵심 아이디어

`sub_1392()`의 `v3`는 실행 시간 기반 `rand()` 상태에 따라 달라질 수 있으므로 정적으로 바로 알기 어렵다.
하지만 제공된 `out.txt`는 이미 특정 실행에서 만들어진 결과이다.

따라서 중간 key에 대해 가능한 `v3` 256개를 모두 적용해 최종 key 후보를 만들고, AES-CBC로 `out.txt`를 복호화한다.
복호화 결과가 `DH{`로 시작하고 printable ascii이면 올바른 후보로 볼 수 있다.

단순히 문자열 형태만 확인하지 않고, 찾은 flag를 다시 `prob`의 원래 연산처럼 256바이트로 맞춘 뒤 암호화하여 `out.txt`와 같은지도 검증하였다.

### Solve

풀이 코드는 다음과 같다.

```python
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


BASE_KEY = bytes.fromhex("41 28 19 4e a5 7c a1 41 13 cf 88 ac 2a f0 b7 da")
IV = b"\x00" * 16


def enc(key: bytes, pt: bytes) -> bytes:
    e = Cipher(algorithms.AES(key), modes.CBC(IV)).encryptor()
    return e.update(pt) + e.finalize()


def dec(key: bytes, ct: bytes) -> bytes:
    d = Cipher(algorithms.AES(key), modes.CBC(IV)).decryptor()
    return d.update(ct) + d.finalize()


def mk_key() -> bytes:
    key = bytearray(BASE_KEY)

    for j in range(15):
        key[j + 1] = (key[j + 1] + key[j]) & 0xff

    return bytes(key)


def pad(s: bytes) -> bytes:
    if len(s) > 256:
        raise ValueError("input is longer than prob's 256-byte buffer")
    return s + b"\x00" * (256 - len(s))


def is_flag(pt: bytes) -> bool:
    if not pt.startswith(b"DH{"):
        return False

    end = pt.find(b"\x00")
    if end == -1:
        end = len(pt)

    s = pt[:end]
    return s.endswith(b"}") and all(0x20 <= c <= 0x7e for c in s)


def main():
    ct = Path("out.txt").read_bytes()
    mid = mk_key()

    for v3 in range(256):
        key = bytes(b ^ v3 for b in mid)
        pt = dec(key, ct)

        if not is_flag(pt):
            continue

        end = pt.find(b"\x00")
        flag = pt[:end]

        if enc(key, pad(flag)) == ct:
            print(flag.decode())
            return

    raise RuntimeError("flag candidate not found")


if __name__ == "__main__":
    main()
```

실행 결과 `v3 = 0x4b`일 때 올바른 flag가 복호화된다.

이때 최종 AES key는 다음과 같다.

```text
0a 22 c9 9b 3e ba d9 98 ad fe 76 a2 58 48 f1 df
```

## 플래그

```text
DH{REDACTED}
```

## 배운 점

`.init_array`에 등록된 함수는 `main()`보다 먼저 실행되므로, 전역 변수가 런타임에 바뀌는지 반드시 확인해야 한다.
`ptrace(PTRACE_TRACEME)`는 anti-debug 용도로 자주 사용되며, 정상 실행과 디버깅 실행에서 반환값 차이가 생길 수 있다.
또한 `rand()` 값 자체를 알 수 없더라도, 실제 연산에 사용되는 값이 1바이트로 잘려 있다면 전체 경우의 수를 brute force하여 충분히 복구할 수 있다.
