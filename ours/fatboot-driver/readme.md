## Building

This driver builds against the patched HElib produced by `../apply_all.sh`; see
`../README.md` for the two-layer patch this artifact actually ships and the exact build
commands (`HELIB_ZZX_CACHE_DIR` replaces the upstream driver's hard-coded save-path, so no
manual path substitution is needed).

## Running
If the building is successful, it will produce a binary file `build/fatboot`.
Running `build/fatboot -h` will display the following help message
```
Usage: build/fatboot [i=<arg>] [h=<arg>] [t=<arg>] [newbts=<arg>] [newks=<arg>] [thick=<arg>] [repeat=<arg>]
  i      index of the chosen parameter set [ default=0 ]
  h      hwt of encapsulated key [ default=0 ]
  t      parameter t used in new bts [ default=0 ]
  newbts if new bts is used [ default=0 ]
  newks  if new ks is used [ default=1 ]
  thick  if thick bts is used [ default=0 ]
  repeat number of tests [ default=5 ]
```
+ Five parameter sets are available (given in Table 3 of the paper with ID I, II, III, IV and V). By setting the argument `i` to an integer in 0 to 4, the corresponding parameter set is chosen.
+ The Hamming weight of the encapsulated secret key needs to be assigned through the argument `h`. Again, please refer to Table 3 for the values of `h` with 80 or 128 bits of security.
+ Argument `t` controls the $t$ in our paper, i.e., $t=v_p(\Delta)$. Setting `t=0` tells the program to decide a positive $t$ that is as small as possible (type-A parameters), while setting `t=-1` uses $\Delta=\Delta_0$, i.e., $t=0$ (type-B parameters). Setting `t` to any positive integer will also set $t$ to the same value.
+ Set `newbts=1` if you want to test our optimized digit removal. Set `newbts=0` to test the native implementation of HElib.
+ Set `thick=1` to test general bootstrapping. Set `thick=0` to test thin bootstrapping.
+ Argument `repeat` indicates the number of tests to run. The performance data will be averaged over these tests. 

## Custom parameters: `(p, m, B)` nobody hand-tuned

`custom=1 cp=<p> cm1=<m1> cm2=<m2> cbits=<bits>` runs the same evaluator at a plaintext prime and
cyclotomic index of your choosing, instead of the five indexed sets above. Unlike the indexed
sets, `gens`/`ords` are **not** supplied: they are left empty and HElib's own generator search
(`findGenerators`, `NumbTh.cpp`) derives them from `mvec={cm1,cm2}` automatically. This exercises
the other half of `selector/select.py`'s promise (`(p,m,B) -> (r*,d,A)` predicts the filter; this
mode is what tests whether HElib can actually bootstrap on that `m` at all).

This is a genuinely harder problem than picking `(r,d)`: most `(m1,m2)` pairs a plain
number-theoretic search turns up (e.g. by requiring a specific residue-order pattern for a target
slot degree `d`) do **not** yield a working thin-bootstrapping context, for reasons below the
`select.py`/`(r,d)` layer entirely, in HElib's own linear-transform/hypercube machinery. Concretely
tried and failed here, so you don't have to re-discover them: a factor with trivial local order
(`p \equiv 1 \pmod{m_i}`) throws `ThinEvalMap: case not handled: bad inertPrefix`; a very large,
unstructured factor makes the generator search itself impractically slow; too few slots
(`\varphi(m)/d` in the low hundreds) throws `Invalid argument: sig and reps have inconsistent
dimension`; and even a combination that builds, encrypts, and runs the full recryption to
completion can still fail the final all-slot decryption check (`thin results not match`) --
observed once, at `p=3019`, `m=71*1051=74621`, `B=17` (`select.py` predicts `r*=6`, `d=105`,
speedup `5.68x`), where the run completed (`extract=233.07s`, `total=313.84s`) but many slots
decrypted incorrectly, with unusually high `KS-noise-ratio` warnings (17-32, vs.\ typically 1-3 on
the paper's working sets) suggesting the modulus chain's bit budget was undersized for this
specific ring rather than an evaluator bug -- not yet root-caused. Reusing a second factor already
proven to work in one of the five indexed sets (as done here, reusing `1051` from Case IV) improves
the odds of clearing the earlier failures, but does not guarantee correctness on its own; deriving
a working `(m1,m2)` for an arbitrary new prime currently still needs this kind of trial and error,
same as it did for the five hand-tuned sets above (see their own comments in this file's `.cpp` for
the "suspect primary m=X rejected; alternate m=Y" pattern this mode inherits).
