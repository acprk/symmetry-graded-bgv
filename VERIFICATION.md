# Measurement discipline, and a worked example of it catching a real mistake

Every number in this paper that comes from a ciphertext experiment was produced under four
rules. This document states them, says why each one exists, and then walks through one
complete case where the discipline caught an error before it reached the paper — because a
verification document that only lists rules nobody ever needed is not evidence they work.

## The four rules

**1. An arm counts as exercising an evaluator only if the evaluator announces itself at
*evaluation* time, not merely when a plan is built.**
Our composed evaluator does two things offline: it builds a plan (folds the polynomial,
searches for a norm form, encodes constants), and later, if invoked, evaluates that plan on
a ciphertext. These are separated in code, and a run can build a plan that is *never
executed* if the calling code takes a different branch — printing a misleading "the
evaluator ran" line even though it did not touch a single ciphertext. Every experiment
script in `experiments/` therefore `grep`s the log for the specific string each evaluator
prints *inside its online branch* (e.g. `HELIB_COMPOSED_EVAL active:`) before any number
from that log is used. A log without that line is discarded, not averaged in.

**2. Every bootstrapping run must end with the library's own all-slot decryption check,
and a run that fails it is reported as a failure, never silently dropped.**
HElib's driver decrypts the bootstrapped ciphertext and compares every slot against the
expected plaintext at the end of each run; the string `### bts finished, everything ok ###`
(or, on failure, an uncaught `helib::LogicError`) is in every log in `results/raw_logs/`.

**3. Ratios that must be compared across arms are measured back-to-back, in one session,
on one machine, sharing ring / modulus chain / key / support.**
The shared 104-core server's load varies by up to 2x across sessions. Within one session,
the *accompanying linear transform* (SlotToCoeff/CoeffToSlot) is untouched by any of our
changes and performs identical work in every arm of a case, so its wall-clock time is a
free load barometer: we report it alongside every extraction time and normalise by it
(`extract / linear`) wherever an absolute ratio is claimed across two runs. Raw times from
different sessions are never compared directly.

**4. The plaintext-constant cache is a measurement hazard, not a feature.**
HElib caches encoded plaintext constants keyed by content; the *first* run of a given
configuration pays the encoding cost inside the timed region, and every subsequent run does
not. The same order-six configuration measured 135.8s cold and 83.2s warm on one ring — a
63% difference invisible to rule 3's load normalisation, since the linear transform's time is
unaffected by this particular cache. Both halves of that pair are shipped: `results/raw_logs/`
holds the cold run in `O6_smoke.log` (`extract = 135.763812`) and the warm one in
`O6_backtoback.log` (`extract = 83.242292`), same evaluator, same ring, same chain. Every number
quoted in the paper is warm-cache.

## A worked example: how rule 1 caught a wrong result

While assembling the end-to-end table for the Mersenne prime case (`p = 8191`), an early run
of the composed evaluator reported a norm form found (`c=346, degC=44`) and a plausible
speedup (1.23x) over the baseline. Rule 1 requires checking for the online-branch
announcement before trusting that number:

```bash
grep -c "HELIB_COMPOSED_EVAL active" results/raw_logs/<that run's log>
# -> 0
```

The count was **zero**. The plan-building code had run (hence the printed norm form), but
the online branch that actually evaluates it never executed, because at this prime the
order-four filter — which the composed branch's plan builder assumed as its precondition —
does not exist (`p = 8191 \equiv 7 \pmod{12}`, a Mersenne prime; Corollary "Fermat primes
are Gaussian, Mersenne primes are Eisenstein"). All three arms of that run were silently
executing the *same* baseline computation, and the measured "1.23x" was pure session-to-session
noise, not a real speedup. This was caught, retracted, and replaced with the correct
experiment: the composed evaluator was extended to operate on the order-six filter's
orbit-closed box (which *does* exist at every Mersenne prime), re-measured, and re-verified
under all four rules. The number that replaced the retracted 1.23x is the Case IV row of
Table 4, 3.60x.

The general lesson, and the reason rule 1 is stated the way it is: **a number that looks
plausible is not evidence that the code path producing it executed.** Every script here
checks the activation string first and the arithmetic second, in that order.

## Reproducing the check yourself

```bash
cd results/raw_logs
grep -c "HELIB_COMPOSED_EVAL active" O6_backtoback.log       # -> 2 (both passes of the Case IV
                                                              #    back-to-back run)
grep -c "HELIB_AUX_ORDER4_EVAL enabled" v_rerun_bsgs.log     # -> 1 (the order-four arm at set V;
                                                              #    last row of Table 13)
grep -c "everything ok" O6_backtoback.log v_rerun_bsgs.log CASE4_clean.log
#   -> O6_backtoback.log:6 (2 passes x 3 arms), v_rerun_bsgs.log:3 (3 arms),
#      CASE4_clean.log:6 (2 passes x 3 arms) -- one match per arm, as expected.
grep -c "thin results not match" zhao_thin24.log             # -> 2 (both cases abort on the
                                                              #    obstructed aux-radix path)
```

If any of these counts is lower than the number of arms you expect a table's row to cover,
that row's log is incomplete and should not be cited — this is exactly the check that would
have caught the Case IV mistake above before it was written down.
