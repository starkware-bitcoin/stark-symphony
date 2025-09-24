# Stwo verifier workflow

1. **Stage I — Commit**
    - Read preprocessed tree commitment
    - Read trace commitment
    - Draw random coefficient for composition polynomial evaluation
    - Read composition polynomial commitment
2. **Stage II — Sample**
    - Draw random OODS point
    - Read trace & composition polynomial evaluations at OODS point
    - Evaluate composition polynomial at OODS point
    - Assert CP evaluations match
    - Draw random coefficient for DEEP quotients evaluation
3. **Stage III — FRI commit**
    - FRI commit first layer
        * Read commitment
        * Draw folding $\alpha$
    - FRI commit inner layers
        * Read commitment
        * Draw folding $\alpha$
    - FRI commit last layer
        * Read last polynomial coefficients
4. **Stage IV — Check PoW**
    - Read PoW nonce
    - Check proof of work
5. **Stage V — Decommit**
    - Generate queries (point indexes/positions)
        * Draw 32 random bytes
        * Generate positions for all columns
    - Check decommitments for trace & composition polynomial evaluations at queried points
6. **Stage VI — Link**
    - Compute DEEP quotients in queried positions
7. **Stage VII — FRI decommit**
    - FRI decommit first layer
    - FRI decommit inner layers
    - FRI decommit last layer
