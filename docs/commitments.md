# Commitments

## Trace polynomials

In STARK protocols, the execution trace is first interpolated to create trace polynomials, which are then extended to evaluation domains larger than the original trace domain by a blowup factor. The trace table is interpolated to an evaluation domain that is larger by a factor `blowup`, and it is also offset by a cofactor to ensure the evaluation domain and trace evaluation domain remain disjoint. This initial extension creates the foundation for polynomial commitment, where each trace column becomes a polynomial of degree approximately equal to the trace length.

## Composition polynomial

The composition polynomial represents a fundamentally different mathematical object with significantly higher degree requirements. When constraints are applied to trace polynomials, the resulting composition polynomial combines multiple constraint polynomials through random linear combinations. The construction follows the pattern: CP(x) = Σ αⱼ · pⱼ(x), where each pⱼ(x) represents individual constraint polynomials and αⱼ are random coefficients provided by the verifier.

Critically, individual constraint polynomials often involve products and compositions of trace polynomial evaluations. For example, in the Fibonacci constraint f(g²x) - f(gx)² - f(x)² = 0, the composition involves squared terms that effectively double the polynomial degree. When such constraints are converted to polynomial form by dividing by vanishing polynomials, the numerator's degree can become substantially larger than the original trace polynomial degrees.

The degree bound for the composition polynomial, denoted as dCP, is determined by the constraint polynomial with the highest degree among all constraints. This degree bound must accommodate not only the individual constraint degrees but also the degree adjustments necessary to align all constraints properly. The adjustment degrees dᵢ = target_degree - deg Cᵢ ensure that the final polynomial represents a sum of all constraint polynomials aligned on both the lowest and highest coefficients.

## Commitment stages

1. Constant (ak preprocessed) trace
2. Main trace
3. Interaction trace
4. Composition polynomial
