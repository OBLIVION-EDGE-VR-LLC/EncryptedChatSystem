"""
DBA 1337_TECH, AUSTIN TEXAS © July 2021
Proof of Concept code, No liabilities or warranties expressed or implied.
"""


def modexp(x, y, n):
    result = 1
    while y != 0:
        if (y & 1) != 0:
            result = (result * x) % n
        y >>= 1
        x = (x * x) % n
    return result


def modexpRecursive(x, y, n):
    if y == 0:
        result = 1
        return
        # z = modexp(x, y >> 2, n)

    if y % 2 == 0:
        result = (z * z) % n
        return
    else:
        result = (x * z * z) % n
        return


def powCustom(x, y):
    result = 1
    while y != 0:
        if (y & 1) != 0:
            result *= x
        y >>= 1
        x *= x
    return result


"""Modular exponentiation
Provides a pure python implementation of modular exponentiation
modexp(b, e, m) computes b^e mod m using python's pow(b, e, m)
by range reducing b, e and m to natural numbers
For negative exponents, modexp uses the identity b^-e == (b^-1)^e mod m
The multiplicative inverse b^-1 mod m is computed using the Extended GCD
modexp always returns natural numbers. negative numbers are converted
to the additive inverses of their magnitudes using the identity -a mod m = m-a mod m
"""


def natural_mod(a, m):
    "mod returning natural number"

    assert isinstance(a, int) and isinstance(m, int)

    invert = False

    if m < 0:
        invert = True
        m = -m

    am = a % m
    if am < 0:
        am += m

    assert am >= 0 and m >= 0

    if invert:
        assert am <= m
        am = m - am

    return am


def congruent(a, b, m):
    "test for a = b mod m"

    return natural_mod(a, m) == natural_mod(b, m)


def natural_multiplicative_inverse(b, m):
    "modular multiplicative inverse returning natural number"

    assert isinstance(b, int) and isinstance(m, int)

    egcd = ExtendedGCD(b, m)
    mi = egcd.multiplicative_inverse
    mi_m = natural_mod(mi, m)

    return mi_m


def natural_additive_inverse(a, m):
    "modular additive inverse returning natural number"

    assert isinstance(a, int) and isinstance(m, int)

    ai = natural_mod(-a, m)

    return ai


def natural_pow(b, e, m, sign):
    "modular power for natural numbers returning natural number"

    assert isinstance(b, int) and isinstance(e, int)
    assert isinstance(m, int)
    assert sign == 1 or sign == -1
    assert b >= 0 and e >= 0 and m >= 0

    np = natural_mod(sign * pow(b, e, m), m)
    return np


def natural_modexp(b, e, m):
    "modular exponentiation returning natural number"

    assert isinstance(b, int) and isinstance(e, int) and isinstance(m, int)

    sign = 1

    if m < 0:
        sign = -sign
        m = -m

    if b < 0:
        b = natural_mod(b, m)

    if e < 0:
        e = - e
        b = natural_multiplicative_inverse(b, m)

    return natural_pow(b, e, m, sign)


def computed_method(f):
    def wrapped(self):
        self.compute()
        return f(self)

    return wrapped


class ExtendedGCD():
    def __init__(self, a, b):
        assert isinstance(a, int) and isinstance(b, int)
        self._a = a
        self._b = b
        self.computed = False

    @property
    def a(self):
        return self._a

    @property
    def b(self):
        return self._b

    @property
    @computed_method
    def bézout(self):
        return self._bézout

    @property
    @computed_method
    def gcd(self):
        return self._gcd

    @property
    @computed_method
    def quotient(self):
        return self._quotient

    @property
    def multiplicative_inverse(self):
        if self.gcd != 1:
            raise ValueError('gcd({}, {}) != 1, no multiplicative inverse exists'.format(self.a, self.b))
        return self.bézout[0]

    def compute(self):
        if not self.computed:
            r, prev_r = self.b, self.a
            s, prev_s = 0, 1
            t, prev_t = 1, 0

            while r != 0:
                q = prev_r // r
                prev_r, r = r, prev_r - q * r
                prev_s, s = s, prev_s - q * s
                prev_t, t = t, prev_t - q * t

            self._bézout = prev_s, prev_t
            self._gcd = prev_r
            self._quotient = s, t

            self.computed = True
