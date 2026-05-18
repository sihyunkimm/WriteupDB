---
ctf_name: "2026-0xV01DCTF"
challenge_name: "FirstStep"
category: "crypto"           # web / pwn / rev / crypto / misc
difficulty: "easy"      # easy / medium / hard / insane
author: "ansihoo"
date: "2026-05-18"
points: 500
tags: [태그1, 태그2]
---

# 문제명
FirstStep

## 문제 설명

> Everyone walks through the same door to get here. The question is whether you know how to open it. Welcome.

Flag format: 0xV01D{...}

- cipher.txt (hex 인코딩된 암호문 파일)
## 풀이

### 분석

cipher.txt를 열면 `723a147273063915710e01720f711d16721d0116043f` 라는 16진수 문자열 하나가 들어있다. 바이트 수를 세면 총 22바이트이고, 플래그 형식인 `0xV01D{...}` 도 7글자로 시작하므로 known plaintext attack을 시도할 수 있다.

### 취약점

단일 바이트 XOR 암호화가 사용됐다. 동일한 키 바이트 하나를 전체 평문에 반복 적용한 방식으로, 플래그 형식처럼 평문의 일부를 알고 있으면 키를 즉시 복구할 수 있다.

### 익스플로잇

암호문의 첫 바이트 `0x72`와 예상 평문 첫 바이트 `0x30`('0')을 XOR하면 `0x42`('B')가 나온다. 나머지 바이트도 동일하게 확인하면 전부 `0x42`로 일치한다. 키가 단일 바이트 `0x42`임을 확인했으므로 전체 암호문을 복호화한다.

```python
ct = bytes.fromhex("723a147273063915710e01720f711d16721d0116043f")
key = 0x42
flag = ''.join(chr(b ^ key) for b in ct)
print(flag)
```

## 플래그

```
0xV01D{W3LC0M3_T0_CTF}
```

## 배운 점

단일 바이트 XOR은 플래그 형식처럼 평문의 일부만 알아도 키를 즉시 역산할 수 있어 암호화로서 의미가 없다. 실제로 안전한 암호화를 하려면 키 길이가 평문과 같고 재사용하지 않는 OTP(One-Time Pad)를 쓰거나, AES 같은 검증된 대칭 암호를 사용해야 한다. CTF 입문 문제에서 자주 등장하는 패턴이므로 암호문을 보면 길이와 반복 패턴부터 확인하는 습관을 들이는 게 좋다.
