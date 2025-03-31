# Polynomials over subgroups of the unit circle

> WARNING
> This is an informal explanation with a purpose of giving an intuition how the math behind the code works

We use polynomails for encoding the execution trace and for expressing the constraints on that trace, but there are also helper polynomials used for ALI (algebraic linking) and FRI protocol: vanishing polynomials, quotients, interpolants, etc. Very roughly, when we do arithmetization we reduce the problem of proving arbitrary computation to an equation $C(T(x))=V(x)*Q(x)$ where $C$ is compositional polynomial, $T$ is trace polynomial, $V$ is vanishing polynomial, and $Q$ is quotient (which is also a polynomial if prover is honest).

Some intuition that might be helpful for understanding how we can jump between the original trace domain (where we interpolate), extended domain (where we commit and query), and complex extension of the extended domain (where we doo out-of-domain sampling): once we move from numbers (polynomial evaluations) to coefficients (in monomial or other basis) we can no longer care (much) about the domain as long as the group structure and operations are preserved. Also the points from the extended domain are also points in its complex extension (just the imaginary part is zero).

## Vanishing polynomial

In STARKs we translate the problem of constraint satisfiability to a low-degree test (FRI). Instead of proving that a constraint polynomial $C(x)$ evaluates to zero on the trace domain (subgroup used to interpolate trace polynomials) we can instead prove that a quotient $Q(x)=\frac{C(x)}{V(x)}$ is a polynomial (as opposed to a rational function), or, with high probability, that $Q(x)$ is close to a low degree polynomial ("close" means that numbers add up in several random points that we check, and "low" means it has degree not larger than the domain size). Here $V(P)$ is __vanishing__ polynomial that evaluates to zero on the entire trace domain.

It works because vanishing polynomial can be reinterpreted as $V(x)=(x-x_0)(x-x_1)\dots(x-x_{n-1})$ where roots are points from the domain. Since our constraint polynomial $C(x)=0$ in those points it means they are also roots of $C(x)$ hence $C(x)=Q(x)*V(x)$ and $Q(x)=\frac{C(x)}{V(x)}$ is a polynomial. How do we avoid division by zero when evaluating quotients? Since we sample outside of the extension domain (where $V(x)$ vanishes) we never end up in such situation.

It should be noted that a constraint polynomial does not necessarily have to evaluate to zero on the entire domain, it can be just several points or almost all points (e.g. if you set up boundary constraints for specific trace rows). However in Stwo AIRs are flat/wide which means that constraints are applied to all trace rows in the same way.

### Polynomial that vanishes on a canonic coset

In Circle STARK the evaluation domain is a canonical (aka standard) coset — a subgroup of the unit circle with points from a finite field `M31`. Standard coset has a nice property that if you double all its points you'll get a standard coset half the size. The coset of size 2 consists of two points lying on y-axis (thanks to the symmetry and equal spacing): $\{(0, y), (0, -y)\}$, so if we wanted to construct a vanishing polynomial on that domain we would just take $V(x) = x$.

For a coset of size 4 we'd need to double all the points to reduce our case to the previous one. Happily, doubling the x-coordinate of a point is independent of y: $double(x) = 2*x^2 - 1$. Applying this operation (denoted by $pi$ in Stwo) recursively we can construct vanishing polynomials for cosets of arbitrary size. Therefore evaluating such a polynomial is just calculating $pi^{logsize - 1}(P.x)$ where $P$ is a point from a domain of size $2^{logsize}$.

### References

- https://vitalik.eth.limo/general/2024/07/23/circlestarks.html#vanishing-polynomials
- https://github.com/starkware-libs/stwo/blob/dev/crates/prover/src/core/constraints.rs

## DEEP quotients

Algebraic linking is not enough to catch a cheating prover which can provide inconsistent evaluations. So we do several more random queries (FRI queries) that allow us to assess whether the polynomials prover uses for evaluations are (close to) the ones he committed to.

In a univariate STARK DEEP quotient looks like $Q(b)=\frac{F(x)-y}{x-c}$ where $y=F(c)$ is the evaluation at the sampled point (out of domain). We prove that $Q$ is a polynomial (not a rational function) at a specific point. It cannot be $c$, because that would lead to 0/0, also we'd want to choose from the extended domain, so that the verifier can check that the polynomial evaluation in this point is actually the one prover committed to. 

Why does that work? If $Q(x)$ is a polynomial it means that $F(x)=Q(x)(x-c) + y$ and substituting $x=c$ gives $F(x)=y$. Note that the OODS point is from a complex extension while the random query is from the evaluation domain, so we operate in the former and treat queries as elements of the extension.

### Line between conjugate points

In univariate case it's simple to draw a line passes through only one point (polynomial evaluates to zero only in one point) $y=x-c$, but in the group of points on a cirlce it's not possible: you could take a tangent line that touches the circle in just one place, however that would put more strict conditions on the line polynomial (than just being zero at a point) making it unsuitable for quotienting purposes.

There are two approaches how to address that:
1. Separate real and imaginary parts of the quotient and take their random linear combination
2. Choose a dummy second point on the circle and draw the line — Stwo does this

How do we pick that second point? We exploit the fact that we query from the extended domain (standard coset over M31 points) while all calculations are done in QM31, so if we chose the dummy point to be the complex conjugate of the query point they would collapse! Indeed, since obtaining complex conjugate of a point is flippping imaginary part of its coordinates, -0 is still 0.

Why does conjugate point also lie on the circle? We leverage the fact that the complex conjugate of a function is generally a function of the complex conjugates of its arguments, i.e. $x^2+y^2=1 \Rightarrow \overline x^2 + \overline y^2 = \overline 1 = 1$.

#### Coefficients

The line between conjugate points is actually used twice in quotient construction: for vanishing polynomial and for _interpolant_. Let's first see how we compute and normalize the line coefficients without using the fact that $P_2 = conj(P_1)$

let $P_1=(x_1,y_1), P_2=(x_2, y_2)$ be our points, then we have a system:

$$a*x_1+b*y_1+c=0$$
$$a*x_2+b*y_2+c=0$$

Substract expressions and divide summands:

$$\frac{a}{b}=\frac{y_2-y_1}{x_1-x_2}$$
$$c=-(a*x_1+b*y_1)$$

Notice that we have a family of lines so we can pick the one that suits us best. Typically we'd want to set one of the coefficients to a constant to optimize computations, in other words __normalize__ the coefficients of the line polynomial. We will be using different norms so let's pick the following coefficients for now and divide later:

$$a=y_2-y_1$$
$$b=x_1-x_2$$

Then:

$$c=-(y_2-y_1)*x_1-(x_1-x_2)*y_1=x_2*y_1-x_1*y_2$$

Now let's use the relation between $P_1$ and $P_2$:

$$x_2=re(x_1)-u*im(x_1)$$
$$y_2=re(y_1)-u*im(y_1)$$

Substituting:

$$a=-2u*im(y_1)$$
$$b=2u*im(x_1)$$
$$c=(re(x_1)-u*im(x_1))(re(y_1)+u*im(y_1))-(re(x_1)+u*im(x_1))(re(y_1)-u*im(y_1))$$
$$c=2u*(re(x_1)*im(y_1)-im(x_1)*re(y_1))$$

It's clear now that dividing all coefficients by $a$,$b$, or $c$ would allow us to get rid of imaginary unit $u$.

### Line vanishing at one point

For the DEEP quotient denominator we pick a line $L(x,y)=x+b*y+c$ normalizing all coefficients by $a$. Let's expand:

$$a=1$$
$$b=-\frac{im(P.x)}{im(P.y)}$$
$$c=\frac{im(P.x)*re(P.y)-re(P.x)*im(P.y)}{im(P.y)}=-b*re(P.y)-re(P.x)$$

Here $P$ is the OODS point, $P\in(QM31, QM31)$.  
In Stwo codebase $-b$ is denoted as `d`, and $c$ is `cross_term`.

### Interpolant

Similarly to univariate case $Q=\frac{F-y}{X-x}$ where $y=F(x)$, we need a function $I$ that outputs either $F(P_1)$ or $F(P_2)$. The simplest polynomial that would do the job is a line passing through сonjugate points $(P_1.y, F(P_1)), (P_2.y, F(P_2))$. In order to get the line coefficients we need to do interpolation (hence interpolant).

Why can we omit $P.x$? Point coordinates are bound by the circle equation (i.e. we can express x via y) and in this particular case we don't need to evaluate a polynomial at a point, we just need to distinct between two cases $P_1$ or $P_2$ and just y coordinate would suffice.

Let's compute the line coefficients, this time we use $b$ as a norm:

$$b=-1$$
$$a=\frac{im(F(P))}{im(P.y)}$$
$$c=-a*re(P.y)+re(F(P))$$

where $P$ is the OODS point, $F(P)$ is the target polynomial evaluation at that point.  
Then our interpolator and quotient numerator would look like:

$$I(R)=a*R.y+c$$
$$F(R)-I(R)=F(R)-a*R.y-c$$

where $R$ is a query point, $F(R)$ is the evaluation of the target (trace or composition) polynomial at that point (on the extended domain).

#### Non-normalized randomized coefficients

In a more recent Stwo implementation line coefficients are not normalized and additionally multiplied by a random number $\alpha^i$ where $i$ is different for every quotient:

$$a=\alpha^i * (\overline {F(P)} - F(P))$$
$$b=\alpha^i * (P.y - \overline {P.y})$$
$$c=\alpha^i * -(a*P.y+b*F(P))$$

And then the nominator would be:

$$b*F(R)-(a*R.y+c)$$

### Batching




### References

- https://vitalik.eth.limo/general/2024/07/23/circlestarks.html#quotienting
- https://github.com/ethereum/research/blob/master/circlestark/line_functions.py
- https://github.com/starkware-libs/stwo/blob/dev/crates/prover/src/core/constraints.rs
