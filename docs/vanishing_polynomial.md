# Vanishing polynomial

In STARKs we translate the problem of constraint satisfiability to a low-degree test (FRI). Instead of proving that a constraint polynomial $C(x)$ evaluates to zero on the trace domain (subgroup used to interpolate trace polynomials) we can instead prove that a quotient $Q(x)=\frac{C(x)}{V(x)}$ is a polynomial (as opposed to a rational function), or, with high probability, that $Q(x)$ is close to a low degree polynomial ("close" means that numbers add up in several random points that we check, and "low" means it has degree not larger than the domain size). Here $V(P)$ is __vanishing__ polynomial that evaluates to zero on the entire trace domain.

It works because vanishing polynomial can be reinterpreted as $V(x)=(x-x_0)(x-x_1)\dots(x-x_{n-1})$ where roots are points from the domain. Since our constraint polynomial $C(x)=0$ in those points it means they are also roots of $C(x)$ hence $C(x)=Q(x)*V(x)$ and $Q(x)=\frac{C(x)}{V(x)}$ is a polynomial. How do we avoid division by zero when evaluating quotients? Since we sample outside of the extension domain (where $V(x)$ vanishes) we never end up in such situation.

It should be noted that a constraint polynomial does not necessarily have to evaluate to zero on the entire domain, it can be just several points or almost all points (e.g. if you set up boundary constraints for specific trace rows). However in Stwo AIRs are flat/wide which means that constraints are applied to all trace rows in the same way.

## Polynomial that vanishes on a canonic coset

In Circle STARK the evaluation domain is a canonical (aka standard) coset — a subgroup of the unit circle with points from a finite field `M31`. Standard coset has a nice property that if you double all its points you'll get a standard coset half the size. The coset of size 2 consists of two points lying on y-axis (thanks to the symmetry and equal spacing): $\{(0, y), (0, -y)\}$, so if we wanted to construct a vanishing polynomial on that domain we would just take $V(x) = x$.

For a coset of size 4 we'd need to double all the points to reduce our case to the previous one. Happily, doubling the x-coordinate of a point is independent of y: $double(x) = 2*x^2 - 1$. Applying this operation (denoted by $pi$ in Stwo) recursively we can construct vanishing polynomials for cosets of arbitrary size. Therefore evaluating such a polynomial is just calculating $pi^{logsize - 1}(P.x)$ where $P$ is a point from a domain of size $2^{logsize}$.

## References

- https://vitalik.eth.limo/general/2024/07/23/circlestarks.html#vanishing-polynomials
- https://github.com/starkware-libs/stwo/blob/dev/crates/prover/src/core/constraints.rs
