---
ctf_name: "THCon 2026"
challenge_name: "Exponope"
category: "crypto"           # web / pwn / rev / crypto / misc
difficulty: "easy"      # easy / medium / hard / insane
author: "minyoung13"
date: "2026-05-08"
points: 50
tags: [RSA, Low Exponent Attack]
---

# Exponope

## 문제 설명
> Aurélien Pouilles ( credit goes to Nathan Maillet for the original challenge). This challenge was created by a TLS-SEC student

> Our cryptography expert, Axel Vaughn just announced he's implemented a Secure way of encryption that is very efficient in order to lower the latency of our troops' telecommunications. To do so he lowered the exponent used to a tiny value and claims the security impact is negligible. He sent us the following file for proof. Can you try to crack it ?

- 첨부 파일 : 'vewy-much-mysterious-file-such-encryptationnly-encrypted.crypt'

## 풀이

### 분석

파일을 열면 매우 큰 크기의 16진수 N과 ciphertext가 제시되어 있다.

### 취약점

문제 설명에서 '지수 값을 매우 낮추었다'는 내용을 통해, Low Exponent Attack을 떠올릴 수 있었다.
c = m^e mod N으로 암호화하는 RSA 암호화 방식에서 e와 m이 충분히 작아 m^e < N 조건이 성립하면 c = m^e 가 되는, 즉 mod N이 무의미해지는 취약점이 발생한다.

### 익스플로잇

주어진 ciphertext에 대해 작은 지수 e 값을 가정하고 c의 e제곱근을 계산하였다.
e=5일 때 c가 정확한 5제곱수임을 확인할 수 있었고, 이를 통해 plaintext 복구에 성공하였다.
즉, c = m^5 이다.

```python
from sympy import integer_nthroot
from Crypto.Util.number import long_to_bytes

c = 0xfd7d893b965ca58d3e19e07e85f95b440b3e66245a14ad601c8aeae7b139b3d044ec05e9bd4e1ba9a9f2603d4d12bbd343068e55d454417a9ef0dd4d8c8deb717de0c538ca56524ce3e0adee6542d5b710ca6359510d05b9e04fd49adf8f2cf63a7eda6d69b6a59982311801e48c6a5a0154c5bc206dcf7315441d838859871a444cd81c4836b660f26a5e69a7702d8d

for e in [3,5,7,11,13,17]:
    m, exact = integer_nthroot(c, e)

    if exact:
        print(e, long_to_bytes(m))
```

## 플래그

```
flag{REDACTED}
```

## 배운 점

- 주어진 c 값이 커, 연산을 위해 sympy 라이브러리를 활용하였다. sympy의 integer_nthroot(x, n)을 사용하면 (root, exact(bool)) 튜플을 반환하며, root는 x의 n제곱근의 정수부분을, exact는 x가 정확한 n제곱수인지 여부를 의미한다. e.g. integer_nthroot(8, 3) = (2, True)
- e가 작으면 encryption에 드는 시간이 줄어드는 장점이 있지만, 작은 메시지를 패딩 없이 암호화할 경우 m^e < N 조건이 성립하여 공격이 가능해질 수 있다. 메시지에 패딩을 추가하여 크게 만들거나 큰 e 값을 사용해야 한다.