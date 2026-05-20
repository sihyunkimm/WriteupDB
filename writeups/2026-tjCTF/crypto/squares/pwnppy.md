---
ctf_name: "tjCTF"
challenge_name: "squares"
category: "crypto"           # web / pwn / rev / crypto / misc
difficulty: "easy"      # easy / medium / hard / insane
author: "pwnppy"
date: "2026-05-17"
points: 238
tags: [crypto]
---

# squares

## 문제 설명

> A system defines a quadratic function over a finite field: 

> ```H(x) = x^T M x - 2c^T x (mod p)```

> The secret input x is a stationary point of H(x).
> Recover x and decode it to obtain the flag.

- **문제 분류**: Crypto

## 풀이

### 분석

정규표현식을 이용해 숫자 데이터만 순서대로 추출하면 다음과 같은 구조적 규칙을 발견할 수 있다.

* **첫 번째 숫자**: 모듈러스 값인 소수 $p = 257$
* **이후 2704개의 숫자**: $52 \times 52$ 크기의 정방행렬 $M$ ($52 \times 52 = 2704$)
* **마지막 52개의 숫자**: 결과 벡터 $c$

이 문제는 유한 필드(Finite Field) $GF(257)$ 상에서 정의된 선형 연립방정식인 $M \cdot x \equiv c \pmod p$를 만족하는 비밀 벡터 $x$를 구하는 문제이다. 

행렬의 크기가 52이므로 구하고자 하는 벡터 $x$의 길이 또한 52이며, 이 연산 결과 도출되는 정수들을 아스키(ASCII) 문자로 치환하면 플래그가 완성될 것임을 유추할 수 있다. 다만, 일반적인 실수 공간에서의 나눗셈 연산 대신 $\pmod p$ 상에서의 연산이 필요하므로 **확장 유클리드 호제법**을 통한 **모듈러 역원(Modular Inverse)**을 구해 가우스 소거법(Gaussian Elimination)을 수행한다.

### Exploit

```python
import numpy as np
import re

def solve_from_file(filename="out.txt"):
    # 1. 파일 읽기
    with open(filename, "r") as f:
        content = f.read()

    # 2. 정규식을 이용하여 모든 숫자(정수) 추출
    all_numbers = [int(x) for x in re.findall(r'\d+', content)]

    p = all_numbers[0]  # 첫 번째 숫자는 p = 257

    # 행렬 M은 52 * 52 = 2704개의 원소를 가짐
    M_flat = all_numbers[1:2705]
    M_mat = np.array(M_flat).reshape(52, 52)

    # 나머지 마지막 52개 숫자는 벡터 c
    c_vec = np.array(all_numbers[2705:])

    print(f"[+] File Parsing Done (p = {p})")
    print(f"[+] Matrix M size: {M_mat.shape}, Vector c size: {c_vec.shape}")

    # 3. 유한 필드 GF(p) 상에서의 가우스 소거법 풀이
    x_result = solve_modular_lin_eq(M_mat, c_vec, p)

    # 4. 정수 결과를 아스키(ASCII) 문자로 디코딩하여 플래그 추출
    flag = "".join([chr(int(val)) for val in x_result])

    print("\n" + "="*40)
    print(f"[+] Decoded Flag: {flag}")
    print("="*40)

def modular_inverse(a, m):
    # 확장 유클리드 호제법을 이용한 모듈러 역원 계산 
    g, x, y = ext_gcd(a, m)
    if g != 1:
        raise Exception('No inverse.')
    return x % m

def ext_gcd(a, b):
    if a == 0:
        return b, 0, 1
    g, x1, y1 = ext_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return g, x, y

def solve_modular_lin_eq(A, b, p):
    # M * x = c (mod p) 연립방정식 풀이 
    n = len(b)
    # Augmented Matrix 생성
    M = np.hstack((A.copy(), b.reshape(-1, 1))) % p

    for i in range(n):
        if M[i, i] == 0:
            for j in range(i + 1, n):
                if M[j, i] != 0:
                    M[[i, j]] = M[[j, i]]
                    break
            if M[i, i] == 0:
                raise ValueError("No unique sol.")

        # 주대각 성분을 1로 만들기
        inv = modular_inverse(int(M[i, i]), p)
        M[i] = (M[i] * inv) % p

        # 다른 행 성분 소거
        for j in range(n):
            if i != j:
                factor = M[j, i]
                M[j] = (M[j] - factor * M[i]) % p

    return M[:, -1]

if __name__ == "__main__":
    try:
        solve_from_file("out.txt")
    except FileNotFoundError:
        print("[-] Error: 'out.txt' not found.")
    except Exception as e:
        print(f"[-] Error: {e}")
```

## 플래그

```
tjctf{m4tr1c3s_4r3_4ll_y0u_n33d}
```

## 배운 점

* 일반적인 실수 연산 기반의 가우스 소거법과 달리, 모듈러 대수 환경($GF(p)$)에서는 연산 중간 과정에 모듈러 역원을 적용해야 한다.
* 정규표현식(`re.findall(r'\d+', ...)`)을 활용해 필요한 정수 시퀀스만 깔끔하게 정제하고 구조화하는 전처리 방법을 적용해볼 수 있다.