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


def recover_id():
    inv = [0] * 256
    for i, b in enumerate(sbox):
        inv[b] = i

    mid = [inv[b] for b in id_target]
    ids = []

    for c0 in range(0x20, 0x7f):
        cur = [c0]

        def dfs(i):
            if i == 16:
                if rol4(cur[-1]) ^ (cur[0] >> 5) == mid[-1]:
                    ids.append(bytes(cur))
                return
            high = rol4(cur[-1]) ^ mid[i - 1]
            for c in range(0x20, 0x7f):
                if c >> 5 == high:
                    cur.append(c)
                    dfs(i + 1)
                    cur.pop()

        dfs(1)

    if len(ids) != 1:
        raise RuntimeError(f"unexpected id candidate count: {len(ids)}")
    return ids[0]


def mix(i, t):
    return (t + sbox[(i ^ (~t & 0xff)) & 0xff]) & 0xff


def recover_password(user_id):
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

    def dfs(i, prev, remain, out):
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
                dfs(i + 1, t, remain, out + [p])
                remain[v] += 1

    dfs(0, 255, Counter(pw_target), [])

    if len(passwords) != 1:
        raise RuntimeError(f"unexpected password candidate count: {len(passwords)}")
    return passwords[0]


def decrypt_flag(user_id, password):
    out = bytearray(enc_flag)
    h1 = sha1(user_id + password).digest()
    h2 = sha1(h1).digest()
    for i in range(20):
        out[2 * i] ^= h1[i]
        out[2 * i + 1] ^= h2[i]
    return bytes(out)


def main():
    user_id = recover_id()
    password = recover_password(user_id)
    flag = decrypt_flag(user_id, password)

    print(user_id.decode())
    print(password.decode())
    print(flag.decode())


if __name__ == "__main__":
    main()
