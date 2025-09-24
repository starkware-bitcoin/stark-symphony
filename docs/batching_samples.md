# OODS batching

Prior to computing [DEEP quotients](/@m-kus/stwo-deep-quotients) we need to apply some transformations to the sampled values provided by the prover. Initially we have the following nested structure:

```
* Preprocessed (constant) tree
    - Trace poly for column 0
        - Evaluation at OODS point
        - ...
* Trace tree
    - Trace poly for column 0
        - Evaluation at OODS point 
        - ...
    - Trace poly for column 1
        - Evaluation at OODS point
        - Evaluation at (OODS point + offset)
        - ...
    - ...
* Interaction trace tree
    - Trace poly for column 0 / virtual M31 col #0
        - ...
    - Trace poly for column 0 / virtual M31 col #1
    - ...
* Composition poly tree
    - Virtual M31 column #0
        - Evaluation at OODS point, re(re(f))
    - Virtual M31 column #1
        - Evaluation at OODS point, im(re(f))
    - Virtual M31 column #2
        - Evaluation at OODS point, re(im(f))
    - Virtual M31 column #3
        - Evaluation at OODS point, im(im(f))
```

For every commitment tree we have a set of columns (that can be of different length), for every column there can be multiple evaluations with different point offsets (masked points) depending on specific constraints for this column.

Note "virtual" `M31` columns of the interaction trace and four extra columns for the composition polynomial: we unpack the `QM31` value into four "coordinates". We do that to all `QM31` columns to make them homogenous and simplify the workflow. Why interaction trace and composition polynomial only? Because they rely on random coefficients from `QM31` so that the evaluations are always in `QM31` hence we won't be able to use the trick with complex conjugates in [DEEP quotients](/@m-kus/stwo-deep-quotients).


Now we do the following:
1. Combine masked points and sampled values (they must have the same structure)
2. Collapse the "tree" level to get a flat array of columns
3. Group columns by `log_size` (they would also share the same evaluation domain)
4. Inside each column set we group the evaluations by the point offset

In the result we get:

```
* Columns of log_size N
    - Samples with offset 0 <---- BATCH
        - Column 0 <---- SAMPLE
        - Column 1
        ...
    - Samples with offset -1
        - Column 1
    - ...
* Columns of log_size N-1
    - ...
* ...
```

where **batch** is a set of columns of the same length with evaluations at the same point offset, **sample** is a single evaluation at OODS point.

So essentially we have rearranged the samples: instead of grouping by the column index and commitment tree, we now group by the column length, point offset, and the column index.

This allows to compute denominator inverse once for every point and reduce the number of costly divisions.

## Simplicity version

In the simplified verifier all the columns have the same length. For simple circuits where all columns have length one there will be one batch per query.
