# Pre-Registered Statistical Comparison Protocol: Design A vs Design C

Status: registered before any statistical interpretation of the fixed
walk-forward results.

This protocol is descriptive and conservative. It does not change either
strategy, the fold definitions, or the execution model.

## A. Pre-registered protocol

### What is compared

For every identical OOS fold, compare **Design C minus Design A**. Both designs
use the same approved data, historical SET50 membership, features, rebalance
schedule, portfolio rules, transaction costs, and execution assumptions. Only
the approved selection rule differs.

### Primary metric

The primary metric is **fold-level net return difference**:

`net return(C) - net return(A)`

Net return is selected because it is the realized investor outcome after
commission, VAT, slippage, fills, and cash constraints. A fold is the unit of
comparison because each walk-forward fold is a complete held-out experiment and
the engine resets capital at each fold. We will report the five differences,
their arithmetic mean, median, and sign pattern without weighting the longer
folds more heavily.

### Secondary descriptive metrics

The following are descriptive only: gross return, volatility, maximum drawdown,
turnover, commission, VAT, total fees, slippage, fills, non-fills, and positive
fold frequency. Differences are reported as C minus A where meaningful. They
must not be searched to find a favorable result.

### Unit and dependence

The primary observations are the five paired fold returns, not every daily
snapshot. Daily observations within a fold are serially dependent, and the
expanding research windows make folds related as historical samples. Therefore
daily rows must not be treated as independent replicates, and the five fold
differences are not assumed to be independent in a strong statistical sense.

### Statistical test decision

No formal inferential test will be used for this dataset. With only five folds,
there is insufficient information for a reliable conventional large-sample
test. Even an exact two-sided sign test cannot reach a 5% result with five
observations (its smallest attainable two-sided p-value is 0.0625). The primary
analysis is therefore a paired descriptive comparison.

If a later, separately approved study has a materially larger pre-specified
number of independent evaluation blocks, an exact paired sign/permutation test
may be considered with a two-sided alpha of 0.05. That future possibility does
not authorize testing the current five folds.

### Multiple testing

Only net-return difference is the primary comparison. Secondary metrics are
context, not alternative hypotheses. We will not test many metrics, thresholds,
fold definitions, or subsets and select the most favorable outcome.

### Significance threshold

No significance threshold is applied to the current five-fold result because no
inferential test is justified. The future-study threshold described above is
fixed at two-sided alpha = 0.05 and cannot be changed after observing results.

### Effect size

The primary effect size is the arithmetic mean of the five fold net-return
differences, accompanied by the median, each fold's difference, and the
compounded independent-fold return difference as a clearly labeled descriptive
quantity. No confidence interval is claimed for the current sample.

### Interpretation rules

- C is descriptively favorable only if its pre-registered primary difference is
  positive in aggregate and the direction is not driven solely by the short
  terminal fold.
- A is descriptively favorable under the corresponding negative result.
- Mixed signs, a near-zero mean, or dependence on one fold is inconclusive.
- Statistical significance, if available in a future larger study, would not by
  itself establish practical superiority; costs, drawdown, turnover, and data
  integrity must remain acceptable.
- For the current study, no observed return difference may be called evidence of
  superiority.

## B. Descriptive comparison of the existing results

The fixed results contain five folds. C beats A in folds 1, 2, and 4, loses in
fold 3, and ties in fold 5. Mean net returns are approximately -3.56% for A
and -3.39% for C; compounded independent-fold returns are approximately -20.07%
and -19.12%, respectively. Both have two positive folds out of five. These are
descriptive observations only and do not establish that C is better.

## C. Inferential result

No inferential result is reported. The available sample is too small and too
dependent for a defensible statistical claim.

## D. Limitations

- Only five OOS folds are available.
- The final fold contains only 18 observed rows and is not comparable in length
  to the other folds.
- Daily observations would be serially dependent and are not used as independent
  tests.
- Expanding research windows create dependence between folds.
- Transaction costs and conservative IOC fills materially affect realized net
  returns and are part of the fixed comparison.
- The historical SET50 universe is limited and includes membership/boundary data
  constraints.
- Statistical power is low; a small observed difference can easily be noise.

## E. Research conclusion

The correct conclusion from this protocol and the current results is:

> **insufficient evidence to establish superiority**

The next human decision is whether to approve a separately pre-specified,
larger OOS evaluation design (without changing strategy rules), or to stop the
A/C comparison and document it as inconclusive. No feature or parameter
optimization should begin on the basis of these five folds.
