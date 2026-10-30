# Radeon OpenCL workflow

This branch runs Radeon GPUs through Futhark's existing `opencl` backend.
Compiler builds use the standard Cabal project. Machine-specific workloads,
host integration, diagnostics, benchmarks, and preserved measurements remain
in the independent `futhark_radeon` kit; it can use this compiler or an upstream
release through `FUTRAD`.

## Build and run

Requirements: the upstream Haskell toolchain described in `HACKING.md`, Python
3.9+, Make, a C compiler, and a copy of the Radeon kit. GPU execution also needs
OpenCL and a visible GPU. On the validated Intel iMac, use Apple's OpenCL;
ROCm, HIP, and CUDA are not required.

From this compiler checkout:

```sh
cabal build exe:futhark -j4 --ghc-options=-j4
cabal list-bin exe:futhark
python3 tools/radeon/verify.py --kit ../futhark_radeon --skip-build
```

Omit `--skip-build` to build and validate in one command. Use `--cpu-only` when
OpenCL is unavailable, `--device` for another GPU name, and `--help` for all
options. The kit path is explicit; no particular sibling layout is required.
If Cabal's cached package index predates `cabal.project`'s pinned snapshot,
run `cabal update` and retry. Do not change the snapshot merely to bypass that
error. The helper does not install the compiler or publish any data.

Use the same executable for all other kit features:

```sh
compiler=$(cabal -v0 list-bin exe:futhark)
make -C ../futhark_radeon hybrid FUTRAD="$compiler"
make -C ../futhark_radeon resident FUTRAD="$compiler"
make -C ../futhark_radeon bench FUTRAD="$compiler"
make -C ../futhark_radeon baseline FUTRAD="$compiler"
```

Run these sequentially and save measurements locally. The kit's default compiler
is unchanged; each command selects the executable explicitly. The default hybrid
split is an example, not a routing rule for every workload.

## Device visibility and diagnostics

Select the Radeon by name, for example `--device='AMD Radeon Pro 5500 XT'` on a
generated program. Through `futhark test` or `bench`, use
`--pass-option='--device=AMD Radeon Pro 5500 XT'`. Device numbering varies by
listing and visibility; do not assume a fixed index.

A sandbox can expose the OpenCL CPU while hiding the GPU. Missing-device errors
suggest checking the name and retrying outside restricted environments
`(sandbox limitation?)`; this is a possible cause, not proof of a sandbox.
Successful CPU execution is not evidence of Radeon execution.

## Keeping up with upstream

`origin` is the personal fork; `upstream` is `https://github.com/diku-dk/futhark.git`.
Keep local commits on `radeon-opencl`, with `master` reserved for upstream code.
Before updating, finish or preserve local edits and record the current revision.

```sh
git fetch upstream --tags
git switch radeon-opencl
git merge upstream/master
python3 tools/radeon/verify.py --kit ../futhark_radeon
```

To adopt a specific release, merge its tag instead of `upstream/master`. A branch
already based on newer development code cannot be downgraded by merging an older
tag; use a separate worktree for that comparison. Merging preserves shared
history. Rebasing is also possible for an unpublished branch, but avoid rewriting
history others are using. Resolve conflicts, inspect the resulting diff, and
validate before using the updated compiler for real workloads. Nothing here
pushes changes or submits reports automatically.

Keep generic diagnostic improvements separate from workflow documentation and
fork-only policy. This fork omits the compiler's upstream-report invitation while
retaining error details and failure status. `AGENTS.md` additionally forbids
publishing project data without explicit user authorization.
