# Polynomials over subgroups of the unit circle

> WARNING
> This is an informal explanation with a purpose of giving an intuition why the math works

We use polynomails for encoding the execution trace and for expressing the constraints on that trace, but there are also helper polynomials used for ALI (algebraic linking) and FRI protocol: vanishing polynomials, quotients, interpolants, etc.

Some intuition that might be helpful for understanding how we can jump between the original trace domain (where we interpolate), extended domain (where we commit and query), and out of domain (where we sample): once we move from numbers (polynomial evaluations) to coefficients (monomial or other basis) we can no longer care (much) about the domain as long as the group structure and operations are preserved.

## Vanishing polynomial

In STARKs we translate the problem of constraint satisfiability to a low-degree test (FRI). Instead of proving that a constraint polynomial $C(x)$ evaluates to zero on the trace domain (subgroup used to interpolate trace polynomials) we can instead prove that a quotient $Q(x)=\frac{C(x)}{V(x)}$ is a polynomial (as opposed to a rational function), or, with high probability, that $Q(x)$ is close to a low degree polynomial ("close" means that numbers add up in several random points that we check, and "low" means it has degree not larger than the domain size). Here $V(P)$ is __vanishing__ polynomial that evaluates to zero on the entire trace domain.

It works because vanishing polynomial can be reinterpreted as $V(x)=(x-x_0)(x-x_1)\dots(x-x_{n-1})$ where roots are points from the domain. Since our constraint polynomial $C(x)=0$ in those points it means they are also roots of $C(x)$ hence $C(x)=Q(x)*V(x)$ and $Q(x)=\frac{C(x)}{V(x)}$ is a polynomial. How do we avoid division by zero when evaluating quotients? Since we sample outside of the extension domain (where $v(x)$ vanishes) we never end up in such situation.

It should be noted that a constraint polynomial does not necessarily have to evaluate to zero on the entire domain, it can be just several points or almost all points (e.g. if you set up boundary constraints for specific trace rows). However in Stwo AIRs are flat/wide which means that constraints are applied to all trace rows in the same way.

In Circle STARK the evaluation domain is a canonical (aka standard) coset — a subgroup of the unit circle with points from a finite field `M31`. Standard coset has a nice property that if you double all its points you'll get a standard coset half the size. The coset of size 2 consists of two points lying on y-axis (thanks to the symmetry and equal spacing): $\{(0, y), (0, -y)\}$, so if we wanted to construct a vanishing polynomial on that domain we would just take $V(x) = x$.

For a coset of size 4 we'd need to double all the points to reduce our case to the previous one. Happily, doubling the x-coordinate of a point is independent of y: $double(x) = 2*x^2 - 1$. Applying this operation (denoted by $pi$ in Stwo) recursively we can construct vanishing polynomials for cosets of arbitrary size. Therefore evaluating such a polynomial is just calculating $pi^{log\_size - 1}(P.x)$ where $P$ is a point from a domain of size $2^{log\_size}$.

### References

- https://vitalik.eth.limo/general/2024/07/23/circlestarks.html#vanishing-polynomials
- https://github.com/starkware-libs/stwo/blob/dev/crates/prover/src/core/constraints.rs

## DEEP quotients

ALI is not enough to catch a cheating prover which can provide inconsistent evaluations. So we do several more random queries (FRI queries) that allow us to assess whether the polynomials prover uses for evaluations are close to the ones he committed to.

In univariate STARK a DEEP quotient looks like $Q(X)=\frac{F(X)-y}{X-x}$ where $y=F(x)$ is evaluation at the sampled point (out of extended domain). We prove that $Q$ is a polynomial (not a rational function) at a specific point, and verifier can check that the polynomial evaluation in this point is actually the one prover committed to.

### Vanishing line


### Interpolant

### Batching


### References

- https://vitalik.eth.limo/general/2024/07/23/circlestarks.html#quotienting
- https://github.com/ethereum/research/blob/master/circlestark/line_functions.py
- https://github.com/starkware-libs/stwo/blob/dev/crates/prover/src/core/constraints.rs
