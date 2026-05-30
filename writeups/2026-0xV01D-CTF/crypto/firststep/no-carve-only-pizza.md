---
ctf_name: "0xV01D CTF 2026"
challenge_name: "FirstStep"
category: "crypto"
difficulty: "easy"
author: "no-carve-only-pizza"
date: "2026-05-17"
points: 100
tags: [XOR, known plaintext]
---

# FirstStep

## 문제 설명

> Everyone walks through the same door to get here.
> The question is whether you know how to open it.
> Welcome.
>
> Flag format: 0xV01D{...}

제공 파일은 `beginner.zip`이고, 압축을 풀면 `cipher.txt` 하나가 나온다.

## 풀이

### 분석

`cipher.txt`에는 hex 문자열 하나가 들어 있다.

```text
723a147273063915710e01720f711d16721d0116043f
```

문제에서 플래그 형식이 `0xV01D{...}`라고 알려져 있으므로, 암호문 앞부분과 알려진 평문 prefix를 XOR해 키를 확인할 수 있다.

```text
0x72 ^ '0' = 0x42
0x3a ^ 'x' = 0x42
0x14 ^ 'V' = 0x42
0x72 ^ '0' = 0x42
0x73 ^ '1' = 0x42
0x06 ^ 'D' = 0x42
0x39 ^ '{' = 0x42
```

앞의 7바이트가 모두 같은 값 `0x42`를 만들기 때문에, 전체 암호문이 1바이트 XOR key `0x42`로 암호화되었다고 볼 수 있다.

### 복호화

```python
from pathlib import Path

cipher_hex = Path("cipher.txt").read_text().strip()
ct = bytes.fromhex(cipher_hex)
pt = bytes(b ^ 0x42 for b in ct)

print(pt.decode())
```

실행 결과:

```text
0xV01D{W3LC0M3_T0_CTF}
```

## 플래그

```text
0xV01D{W3LC0M3_T0_CTF}
```

## 배운 점

플래그 형식처럼 알려진 평문이 있으면 단순 XOR 암호는 첫 몇 바이트만으로도 키를 바로 복구할 수 있다.
