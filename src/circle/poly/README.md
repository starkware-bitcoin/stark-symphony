# Polynomials over subgroups of the unit circle

> WARNING
> Formulas and explanations can be imprecise and informal.

Intuitively, the goal of arithemtization is to move from execution trace (which is a bunch of numbers) to more sophisticated objects which allow us to ensure prover's consistency over the entire protocol duration. Such objects are polynomials: once we obtain them we no longer care (much) about the original domain and can play in any other algebraic group as long as the operations and group structure are preserved.

## Vanishing polynomial

In STARKs we apply ALI (algebraic linking) technique to reduce the problem of constraint satisfiability to a low-degree test (FRI) on single-point quotients. In simpler words, instead of proving that a constraint polynomial $F(P)$ evaluates to zero on the entire trace we can instead prove that a quotient $Q(P)=\frac{F(P)}{V(P)}$ is a polynomial (as opposed to a fraction), or, with high probability, that $Q(x)$ is close to a low degree polynomial ("close" means that numbers add up in several random points that we check, and "low" means it has degree not larger than the domain size). Here $V(P)$ is __vanishing__ polynomial that evaluates to zero at all points $P$ in the extended domain — where we commit to the trace polynomial evaluations.

It works because vanishing polynomial can be reinterpreted as $v(x)=(x-x_0)(x-x_1)\dots(x-x_{n-1})$ where roots are points from the domain. Since our constraint polynomial $f(x)=0$ in those points it means they are also roots of $f(x)$ hence $f(x)=h(x)*v(x)$ and $h(x)=\frac{f(x)}{v(x)}$ is a polynomial. How do we avoid division by zero when evaluating quotients? Since we sample outside of the extension domain (where $v(x)$ vanishes) we never end up in such situation. 

In Circle STARK the evaluation domain is a canonical (aka standard) coset — a subgroup of the unit circle with points from a finite field `M31`. Standard coset has a nice property that if you double all its points you'll get a standard coset half the size. The coset of size 2 consists of two points lying on y-axis (thanks to the symmetry and equal spacing): $\{(0, y), (0, -y)\}$, so if we wanted to construct a vanishing polynomial on that domain we would just take $V(x) = x$.

For a coset of size 4 we'd need to double all the points to reduce our case to the previous one. Happily, doubling the x-coordinate of a point is independent of y: $double(x) = 2*x^2 - 1$. Applying this operation (denoted by $pi$ in Stwo) recursively we can construct vanishing polynomials for cosets of arbitrary size. Therefore evaluating such a polynomial is just calculating $pi^{log\_size - 1}(P.x)$ where $P$ is a point from a domain of size $2^{log\_size}$.

### References

- https://vitalik.eth.limo/general/2024/07/23/circlestarks.html#vanishing-polynomials
- https://github.com/starkware-libs/stwo/blob/dev/crates/prover/src/core/constraints.rs

## DEEP quotients

ALI is not enough to catch a cheating prover which can provide inconsistent evaluations. So we do several more random queries (FRI queries) that allow us to assess whether the polynomials prover uses for evaluations are close to the ones he committed to.

In univariate STARK a DEEP quotient looks like $Q(X)=\frac{F(X)-y}{X-x}$ where $y=F(x)$ is evaluation at the sampled point (out of extended domain). We prove that $Q$ is a polynomial (not a fraction) in all queried points which are from the extended domain, and verifier can check that the polynomial evaluations in these points are actually the ones prover committed to.

### Vanishing line


### Interpolant

### Batching


### References

- https://vitalik.eth.limo/general/2024/07/23/circlestarks.html#quotienting
- https://github.com/ethereum/research/blob/master/circlestark/line_functions.py
- https://github.com/starkware-libs/stwo/blob/dev/crates/prover/src/core/constraints.rs
