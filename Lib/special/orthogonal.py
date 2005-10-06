## Automatically adapted for scipy Oct 05, 2005 by convertcode.py

#!/usr/bin/env python
#
# Author:  Travis Oliphant 2000
# Updated Sep. 2003 (fixed bugs --- tested to be accurate)

"""
A collection of functions to find the weights and abscissas for
Gaussian Quadrature.

These calculations are done by finding the eigenvalues of a
tridiagonal matrix whose entries are dependent on the coefficients
in the recursion formula for the orthogonal polynomials with the
corresponding weighting function over the interval.

Many recursion relations for orthogonal polynomials are given:

a1n f_n+1 (x) = (a2n + a3n x ) f_n (x) - a4n f_n-1 (x)

The recursion relation of interest is

P_n+1 (x) = (x - A_n) P_n (x) - B_n P_n-1 (x)

where P has a different normalization than f.

The coefficients can be found as:

A_n = -a2n / a3n

B_n = ( a4n / a3n sqrt(h_n-1 / h_n))**2

     where
             h_n = int_a^b w(x) f_n(x)^2
assume:
P_0(x) = 1
P_-1(x) == 0
             
See Numerical Recipies in C, page 156 and
Abramowitz and Stegun p. 774, 782

Functions:

  gen_roots_and_weights  -- Generic roots and weights.
  j_roots                -- Jacobi 
  js_roots               -- Shifted Jacobi
  la_roots               -- Generalized Laguerre
  h_roots                -- Hermite
  he_roots               -- Hermite (unit-variance)
  cg_roots               -- Ultraspherical (Gegenbauer)
  t_roots                -- Chebyshev of the first kind
  u_roots                -- Chebyshev of the second kind
  c_roots                -- Chebyshev of the first kind ([-2,2] interval)
  s_roots                -- Chebyshev of the second kind ([-2,2] interval)
  ts_roots               -- Shifted Chebyshev of the first kind.
  us_roots               -- Shifted Chebyshev of the second kind.
  p_roots                -- Legendre
  ps_roots               -- Shifted Legendre
  l_roots                -- Laguerre
"""

from __future__ import nested_scopes
from scipy.base import *
import _cephes as cephes
_gam = cephes.gamma

def poch(z,m):
    """Pochhammer symbol (z)_m = (z)(z+1)....(z+m-1) = gamma(z+m)/gamma(z)"""
    return _gam(z+m) / _gam(z)

class orthopoly1d(poly1d):
    def __init__(self, roots, weights=None, hn=1.0, kn=1.0, wfunc=None, limits=None, monic=0):
        poly1d.__init__(self, roots, r=1)
	equiv_weights = [weights[k] / wfunc(roots[k]) for k in range(len(roots))]
	self.__dict__['weights'] = array(zip(roots,weights,equiv_weights)) 
        self.__dict__['weight_func'] = wfunc
        self.__dict__['limits'] = limits
        mu = sqrt(hn)
        if monic:
            mu = mu / abs(kn)
            kn = 1.0
        self.__dict__['normcoef'] = mu
        self.__dict__['coeffs'] *= kn


_eigfunc_cache = None
def get_eig_func():
    global _eigfunc_cache
    if _eigfunc_cache is not None:
        return _eigfunc_cache
    try:
        import scipy.linalg
        eig = scipy.linalg.eig
    except ImportError:
        try:
            import linalg
            eig = linalg.eig
        except ImportError:
            try:
                from scipy.base import eigenvectors as eig
            except ImportError:
                raise ImportError, \
                      "You must have scipy.linalg or Numeric or numarray to" \
                      "use this function."
    _eigfunc_cache = eig
    return eig

def gen_roots_and_weights(n,an_func,sqrt_bn_func,mu):
    """[x,w] = gen_roots_and_weights(n,an_func,sqrt_bn_func,mu)

    Returns the roots (x) of an nth order orthogonal polynomail,
    and weights (w) to use in appropriate Gaussian quadrature with that
    orthogonal polynomial.

    The polynomials have the recurrence relation
          P_n+1(x) = (x - A_n) P_n(x) - B_n P_n-1(x)

    an_func(n)          should return A_n
    sqrt_bn_func(n)     should return sqrt(B_n)
    mu ( = h_0 )        is the integral of the weight over the orthogonal interval
    """
    eig = get_eig_func()
    nn = arange(1.0,n)
    sqrt_bn = sqrt_bn_func(nn)
    an = an_func(concatenate(([0],nn)))
    [x,v] = eig((diag(an)+diag(sqrt_bn,1)+diag(sqrt_bn,-1)))
    answer = []
    sortind = argsort(real(x))
    answer.append(take(x,sortind))
    answer.append(take(mu*v[0]**2,sortind))
    return answer    

# Jacobi Polynomials 1               P^(alpha,beta)_n(x)
def j_roots(n,alpha,beta,mu=0):
    """[x,w] = j_roots(n,alpha,beta)

    Returns the roots (x) of the nth order Jacobi polynomial, P^(alpha,beta)_n(x)
    and weights (w) to use in Gaussian Quadrature over [-1,1] with weighting
    function (1-x)**alpha (1+x)**beta with alpha,beta > -1.
    """
    if any(alpha <= -1) or any(beta <= -1):
        raise ValueError, "alpha and beta must be greater than -1."
    assert(n>0), "n must be positive."

    (p,q) = (alpha,beta)
    # from recurrence relations
    sbn_J = lambda k: 2.0/(2.0*k+p+q)*sqrt((k+p)*(k+q)/(2*k+q+p+1)) * \
                (where(k==1,1.0,sqrt(k*(k+p+q)/(2.0*k+p+q-1))))
    if any(p == q):  # XXX any or all???
        an_J = lambda k: 0.0*k
    else:
        an_J = lambda k: where(k==0,(q-p)/(p+q+2.0),
                               (q*q - p*p)/((2.0*k+p+q)*(2.0*k+p+q+2)))
    g = cephes.gamma
    mu0 = 2.0**(p+q+1)*g(p+1)*g(q+1)/(g(p+q+2))
    val = gen_roots_and_weights(n,an_J,sbn_J,mu0)
    if mu:
        return val + [mu0]
    else:
        return val

def jacobi(n,alpha,beta,monic=0):
    """Returns the nth order Jacobi polynomial, P^(alpha,beta)_n(x)
    orthogonal over [-1,1] with weighting function
    (1-x)**alpha (1+x)**beta with alpha,beta > -1.
    """
    assert(n>=0), "n must be nonnegative"
    wfunc = lambda x: (1-x)**alpha * (1+x)**beta
    if n==0: return orthopoly1d([],[],1.0,1.0,wfunc,(-1,1),monic)
    x,w,mu = j_roots(n,alpha,beta,mu=1)
    ab1 = alpha+beta+1.0
    hn = 2**ab1/(2*n+ab1)*_gam(n+alpha+1)
    hn *= _gam(n+beta+1.0) / _gam(n+1) / _gam(n+ab1)
    kn = _gam(2*n+ab1)/2.0**n / _gam(n+1) / _gam(n+ab1)
    # here kn = coefficient on x^n term
    p = orthopoly1d(x,w,hn,kn,wfunc,(-1,1),monic)
    return p

# Jacobi Polynomials shifted         G_n(p,q,x)
def js_roots(n,p1,q1,mu=0):
    """[x,w] = js_roots(n,p,q)

    Returns the roots (x) of the nth order shifted Jacobi polynomial, G_n(p,q,x),
    and weights (w) to use in Gaussian Quadrature over [0,1] with weighting
    function (1-x)**(p-q) x**(q-1) with p-q > -1 and q > 0.
    """
    # from recurrence relation
    if not ( any( (p1 - q1) > -1 ) and any( q1 > 0 ) ):
        raise ValueError, "(p - q) > -1 and q > 0 please."
    if (n <= 0):
        raise ValueError, "n must be positive."
    
    p,q = p1,q1

    sbn_Js = lambda k: sqrt(where(k==1,q*(p-q+1.0)/(p+2.0), \
                                  k*(k+q-1.0)*(k+p-1.0)*(k+p-q) \
                                  / ((2.0*k+p-2) * (2.0*k+p))))/(2*k+p-1.0)
    an_Js = lambda k: where(k==0,q/(p+1.0),(2.0*k*(k+p)+q*(p-1.0)) / ((2.0*k+p+1.0)*(2*k+p-1.0)))

    # could also use definition
    #  Gn(p,q,x) = constant_n * P^(p-q,q-1)_n(2x-1)
    #  so roots of Gn(p,q,x) are (roots of P^(p-q,q-1)_n + 1) / 2.0
    g = _gam
    # integral of weight over interval
    mu0 =  g(q)*g(p-q+1)/g(p+1)
    val = gen_roots_and_weights(n,an_Js,sbn_Js,mu0)
    if mu:
        return val + [mu0]
    else:
        return val
    # What code would look like using jacobi polynomial roots
    #if mu:
    #    [x,w,mut] = j_roots(n,p-q,q-1,mu=1)
    #    return [(x+1)/2.0,w,mu0]
    #else:
    #    [x,w] = j_roots(n,p-q,q-1,mu=0)
    #    return [(x+1)/2.0,w]    

def sh_jacobi(n, p, q, monic=0):
    """Returns the nth order Jacobi polynomial, G_n(p,q,x)
    orthogonal over [0,1] with weighting function
    (1-x)**(p-q) (x)**(q-1) with p>q-1 and q > 0.
    """
    if (n<0):
        raise ValueError, "n must be nonnegative"
    wfunc = lambda x: (1.0-x)**(p-q) * (x)**(q-1.)
    if n==0: return orthopoly1d([],[],1.0,1.0,wfunc,(-1,1),monic)
    n1 = n  
    x,w,mu0 = js_roots(n1,p,q,mu=1)
    hn = _gam(n+1)*_gam(n+q)*_gam(n+p)*_gam(n+p-q+1)
    hn /= (2*n+p)*(_gam(2*n+p)**2)
    # kn = 1.0 in standard form so monic is redundant.  Kept for compatibility.
    kn = 1.0
    p = orthopoly1d(x,w,hn,kn,wfunc=wfunc,limits=(0,1),monic=monic)
    return p

# Generalized Laguerre               L^(alpha)_n(x)
def la_roots(n,alpha,mu=0):
    """[x,w] = la_roots(n,alpha)

    Returns the roots (x) of the nth order generalized (associated) Laguerre
    polynomial, L^(alpha)_n(x), and weights (w) to use in Gaussian quadrature over
    [0,inf] with weighting function exp(-x) x**alpha with alpha > -1.
    """
    if not all(alpha > -1):
        raise ValueError, "alpha > -1"
    assert(n>0), "n must be positive."
    (p,q) = (alpha,0.0)
    sbn_La = lambda k: -sqrt(k*(k + p))  # from recurrence relation
    an_La = lambda k: 2*k + p + 1                 
    mu0 = cephes.gamma(alpha+1)           # integral of weight over interval 
    val = gen_roots_and_weights(n,an_La,sbn_La,mu0)
    if mu:
        return val + [mu0]
    else:
        return val

def genlaguerre(n,alpha,monic=0):
    """Returns the nth order generalized (associated) Laguerre polynomial,
    L^(alpha)_n(x), orthogonal over [0,inf) with weighting function
    exp(-x) x**alpha with alpha > -1
    """
    if any(alpha <= -1):
        raise ValueError, "alpha must be > -1"
    assert(n>=0), "n must be nonnegative"
    if n==0: n1 = n+1
    else: n1 = n
    x,w,mu0 = la_roots(n1,alpha,mu=1)
    wfunc = lambda x: exp(-x) * x**alpha
    if n==0: x,w = [],[]
    hn = _gam(n+alpha+1)/_gam(n+1)
    kn = (-1)**n / _gam(n+1)
    p = orthopoly1d(x,w,hn,kn,wfunc,(0,inf),monic)
    return p

# Laguerre                      L_n(x)
def l_roots(n,mu=0):
    """[x,w] = l_roots(n)

    Returns the roots (x) of the nth order Laguerre polynomial, L_n(x),
    and weights (w) to use in Gaussian Quadrature over [0,inf] with weighting
    function exp(-x).
    """
    return la_roots(n,0.0,mu=mu)

def laguerre(n,monic=0):
    """Return the nth order Laguerre polynoimal, L_n(x), orthogonal over
    [0,inf) with weighting function exp(-x)
    """
    assert(n>=0), "n must be nonnegative"
    if n==0: n1 = n+1
    else: n1 = n
    x,w,mu0 = l_roots(n1,mu=1)
    if n==0: x,w = [],[]
    hn = 1.0
    kn = (-1)**n / _gam(n+1)
    p = orthopoly1d(x,w,hn,kn,lambda x: exp(-x),(0,inf),monic)
    return p 


# Hermite  1                         H_n(x)
def h_roots(n,mu=0):
    """[x,w] = h_roots(n)

    Returns the roots (x) of the nth order Hermite polynomial,
    H_n(x), and weights (w) to use in Gaussian Quadrature over
    [-inf,inf] with weighting function exp(-x**2).
    """
    assert(n>0), "n must be positive."
    sbn_H = lambda k: sqrt(k/2)  # from recurrence relation
    an_H = lambda k: 0*k                    
    mu0 = sqrt(pi)               # integral of weight over interval 
    val = gen_roots_and_weights(n,an_H,sbn_H,mu0)
    if mu:
        return val + [mu0]
    else:
        return val

def hermite(n,monic=0):
    """Return the nth order Hermite polynomial, H_n(x), orthogonal over
    (-inf,inf) with weighting function exp(-x**2)
    """
    assert(n>=0), "n must be nonnegative"
    if n==0: n1 = n+1
    else: n1 = n
    x,w,mu0 = h_roots(n1,mu=1)
    wfunc = lambda x: exp(-x*x)
    if n==0: x,w = [],[]
    hn = 2**n * _gam(n+1)*sqrt(pi)
    kn = 2**n
    p = orthopoly1d(x,w,hn,kn,wfunc,(-inf,inf),monic)
    return p
    
# Hermite  2                         He_n(x)
def he_roots(n,mu=0):
    """[x,w] = he_roots(n)

    Returns the roots (x) of the nth order Hermite polynomial,
    He_n(x), and weights (w) to use in Gaussian Quadrature over
    [-inf,inf] with weighting function exp(-(x/2)**2).
    """
    assert(n>0), "n must be positive."
    sbn_He = lambda k: sqrt(k)   # from recurrence relation
    an_He  = lambda k: 0*k                
    mu0 = sqrt(2*pi)             # integral of weight over interval 
    val = gen_roots_and_weights(n,an_He,sbn_He,mu0)
    if mu:
        return val + [mu0]
    else:
        return val

def hermitenorm(n,monic=0):
    """Return the nth order normalized Hermite polynomial, He_n(x), orthogonal
    over (-inf,inf) with weighting function exp(-(x/2)**2)
    """
    assert(n>=0), "n must be nonnegative"
    if n==0: n1 = n+1
    else: n1 = n
    x,w,mu0 = he_roots(n1,mu=1)
    wfunc = lambda x: exp(-x*x/4.0)
    if n==0: x,w = [],[]
    hn = sqrt(2*pi)*_gam(n+1)
    kn = 1.0
    p = orthopoly1d(x,w,hn,kn,wfunc=wfunc,limits=(-inf,inf),monic=monic)
    return p

## The remainder of the polynomials can be derived from the ones above.

# Ultraspherical (Gegenbauer)        C^(alpha)_n(x)
def cg_roots(n,alpha,mu=0):
    """[x,w] = cg_roots(n,alpha)

    Returns the roots (x) of the nth order Ultraspherical (Gegenbauer)
    polynomial, C^(alpha)_n(x), and weights (w) to use in Gaussian Quadrature
    over [-1,1] with weighting function (1-x**2)**(alpha-1/2) with alpha>-1/2.
    """
    return j_roots(n,alpha-0.5,alpha-0.5,mu=mu)

def gegenbauer(n,alpha,monic=0):
    """Return the nth order Gegenbauer (ultraspherical) polynomial,
    C^(alpha)_n(x), orthogonal over [-1,1] with weighting function
    (1-x**2)**(alpha-1/2) with alpha > -1/2
    """
    base = jacobi(n,alpha-0.5,alpha-0.5,monic=monic)
    if monic:
        return base
    #  Abrahmowitz and Stegan 22.5.20
    factor = _gam(2*alpha+n)*_gam(alpha+0.5) / _gam(2*alpha) / _gam(alpha+0.5+n)
    return base * factor

# Chebyshev of the first kind: T_n(x)  = n! sqrt(pi) / _gam(n+1./2)* P^(-1/2,-1/2)_n(x)
#  Computed anew.
def t_roots(n,mu=0):
    """[x,w] = t_roots(n)

    Returns the roots (x) of the nth order Chebyshev (of the first kind)
    polynomial, T_n(x), and weights (w) to use in Gaussian Quadrature
    over [-1,1] with weighting function (1-x**2)**(-1/2).
    """
    assert(n>0), "n must be positive."
    # from recurrence relation
    sbn_J = lambda k: where(k==1,sqrt(2)/2.0,0.5)
    an_J = lambda k: 0.0*k
    g = cephes.gamma
    mu0 = pi
    val = gen_roots_and_weights(n,an_J,sbn_J,mu0)
    if mu:
        return val + [mu0]
    else:
        return val

def chebyt(n,monic=0):
    """Return nth order Chebyshev polynomial of first kind, Tn(x).  Orthogonal
    over [-1,1] with weight function (1-x**2)**(-1/2).
    """
    assert(n>=0), "n must be nonnegative"
    wfunc = lambda x: 1.0/sqrt(1-x*x)
    if n==0: return orthopoly1d([],[],pi,1.0,wfunc,(-1,1),monic)
    n1 = n
    x,w,mu = t_roots(n1,mu=1)
    hn = pi/2
    kn = 2**(n-1)
    p = orthopoly1d(x,w,hn,kn,wfunc,(-1,1),monic)
    return p
    
    return jacobi(n,-0.5,-0.5,monic=monic)

# Chebyshev of the second kind
#    U_n(x) = (n+1)! sqrt(pi) / (2*_gam(n+3./2)) * P^(1/2,1/2)_n(x)
def u_roots(n,mu=0):
    """[x,w] = u_roots(n)

    Returns the roots (x) of the nth order Chebyshev (of the second kind)
    polynomial, U_n(x), and weights (w) to use in Gaussian Quadrature
    over [-1,1] with weighting function (1-x**2)**1/2.
    """
    return j_roots(n,0.5,0.5,mu=mu)

def chebyu(n,monic=0):
    """Return nth order Chebyshev polynomial of second kind, Un(x).  Orthogonal
    over [-1,1] with weight function (1-x**2)**(1/2).
    """
    base = jacobi(n,0.5,0.5,monic=monic)
    if monic:
        return base
    factor = sqrt(pi)/2.0*_gam(n+2) / _gam(n+1.5)
    return base * factor

# Chebyshev of the first kind        C_n(x)
def c_roots(n,mu=0):
    """[x,w] = c_roots(n)

    Returns the roots (x) of the nth order Chebyshev (of the first kind)
    polynomial, C_n(x), and weights (w) to use in Gaussian Quadrature
    over [-2,2] with weighting function (1-(x/2)**2)**(-1/2).
    """
    if mu:
        [x,w,mu0] = j_roots(n,-0.5,-0.5,mu=1)
        return [x*2,w,mu0]
    else:
        [x,w] = j_roots(n,-0.5,-0.5,mu=0)
        return [x*2,w]

def chebyc(n,monic=0):
    """Return nth order Chebyshev polynomial of first kind, Cn(x).  Orthogonal
    over [-2,2] with weight function (1-(x/2)**2)**(-1/2).
    """
    assert(n>=0), "n must be nonnegative"
    if n==0: n1 = n+1
    else: n1 = n
    x,w,mu0 = c_roots(n1,mu=1)
    if n==0: x,w = [],[]
    hn = 4*pi * ((n==0)+1)
    kn = 1.0
    p = orthopoly1d(x,w,hn,kn,wfunc=lambda x: 1.0/sqrt(1-x*x/4.0),limits=(-2,2),monic=monic)
    if not monic:
        p = p * 2.0/p(2)
    return p

# Chebyshev of the second kind       S_n(x)
def s_roots(n,mu=0):
    """[x,w] = s_roots(n)

    Returns the roots (x) of the nth order Chebyshev (of the second kind)
    polynomial, S_n(x), and weights (w) to use in Gaussian Quadrature
    over [-2,2] with weighting function (1-(x/2)**2)**1/2.
    """
    if mu:
        [x,w,mu0] = j_roots(n,0.5,0.5,mu=1)
        return [x*2,w,mu0]
    else:
        [x,w] = j_roots(n,0.5,0.5,mu=0)
        return [x*2,w]

def chebys(n,monic=0):
    """Return nth order Chebyshev polynomial of second kind, Sn(x).  Orthogonal
    over [-2,2] with weight function (1-(x/)**2)**(1/2).
    """
    assert(n>=0), "n must be nonnegative"
    if n==0: n1 = n+1
    else: n1 = n
    x,w,mu0 = s_roots(n1,mu=1)
    if n==0: x,w = [],[]
    hn = pi
    kn = 1.0
    p = orthopoly1d(x,w,hn,kn,wfunc=lambda x: sqrt(1-x*x/4.0),limits=(-2,2),monic=monic)
    if not monic:
        p = p * (n+1.0)/p(2)
    return p

# Shifted Chebyshev of the first kind     T^*_n(x)
def ts_roots(n,mu=0):
    """[x,w] = ts_roots(n)

    Returns the roots (x) of the nth order shifted Chebyshev (of the first kind)
    polynomial, T^*_n(x), and weights (w) to use in Gaussian Quadrature
    over [0,1] with weighting function (x-x**2)**(-1/2).
    """
    return js_roots(n,0.0,0.5,mu=mu)

def sh_chebyt(n,monic=0):
    """Return nth order shifted Chebyshev polynomial of first kind, Tn(x).
    Orthogonal over [0,1] with weight function (x-x**2)**(-1/2).
    """
    base = sh_jacobi(n,0.0,0.5,monic=monic)
    if monic: return base
    if n > 0:
        factor = 4**n / 2.0
    else:
        factor = 1.0
    return base * factor
    

# Shifted Chebyshev of the second kind    U^*_n(x)
def us_roots(n,mu=0):
    """[x,w] = us_roots(n)

    Returns the roots (x) of the nth order shifted Chebyshev (of the second kind)
    polynomial, U^*_n(x), and weights (w) to use in Gaussian Quadrature
    over [0,1] with weighting function (x-x**2)**1/2.
    """
    return js_roots(n,2.0,1.5,mu=mu)

def sh_chebyu(n,monic=0):
    """Return nth order shifted Chebyshev polynomial of second kind, Un(x).
    Orthogonal over [0,1] with weight function (x-x**2)**(1/2).
    """
    base = sh_jacobi(n,2.0,1.5,monic=monic)
    if monic: return base
    factor = 4**n
    return base * factor

# Legendre 
def p_roots(n,mu=0):
    """[x,w] = p_roots(n)

    Returns the roots (x) of the nth order Legendre polynomial, P_n(x),
    and weights (w) to use in Gaussian Quadrature over [-1,1] with weighting
    function 1.
    """
    return j_roots(n,0.0,0.0,mu=mu)

def legendre(n,monic=0):
    """Returns the nth order Legendre polynomial, P_n(x), orthogonal over
    [-1,1] with weight function 1.
    """
    assert(n>=0), "n must be nonnegative"
    if n==0: n1 = n+1
    else: n1 = n
    x,w,mu0 = p_roots(n1,mu=1)
    if n==0: x,w = [],[]
    hn = 2.0/(2*n+1)
    kn = _gam(2*n+1)/_gam(n+1)**2 / 2.0**n
    p = orthopoly1d(x,w,hn,kn,wfunc=lambda x: 1.0,limits=(-1,1),monic=monic)
    return p

# Shifted Legendre              P^*_n(x)
def ps_roots(n,mu=0):
    """[x,w] = ps_roots(n)

    Returns the roots (x) of the nth order shifted Legendre polynomial, P^*_n(x),
    and weights (w) to use in Gaussian Quadrature over [0,1] with weighting
    function 1.
    """
    return js_roots(n,1.0,1.0,mu=mu)

def sh_legendre(n,monic=0):
    """Returns the nth order shifted Legendre polynomial, P^*_n(x), orthogonal
    over [0,1] with weighting function 1.
    """
    assert(n>=0), "n must be nonnegative"
    wfunc = lambda x: 0.0*x + 1.0
    if n==0: return orthopoly1d([],[],1.0,1.0,wfunc,(0,1),monic)
    x,w,mu0 = ps_roots(n,mu=1)
    hn = 1.0/(2*n+1.0)
    kn = _gam(2*n+1)/_gam(n+1)**2
    p = orthopoly1d(x,w,hn,kn,wfunc,limits=(0,1),monic=monic)
    return p 
