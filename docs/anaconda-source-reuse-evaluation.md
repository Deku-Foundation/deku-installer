# Anaconda Source Reuse Evaluation

**Status:** research and decision record only; no Anaconda source has been copied into this repository.

## Upstream

- Repository: https://github.com/rhinstaller/anaconda
- The upstream project declares GPL-2.0 and is a mature installer for Fedora, RHEL and related distributions.
- It integrates storage, package installation, bootloader configuration, device discovery and automated installation services. It is not a generic UI package that can simply be rebranded without replacing distribution-specific interfaces.

## Proposed approach

Do not build a Fedora-based distribution. Evaluate Anaconda as an upstream source donor under a documented GPL-compatible fork/derivative strategy. Preserve upstream copyright/license notices and mark Deku modifications. Replace product identity, visual design, language/accessibility behavior, workflow and branding. Isolate distribution-specific services behind interfaces:

- Storage backend: enumerate block devices read-only, produce a dry-run partition plan, validate device identity/destructive effects, then apply only after explicit final confirmation.
- Package deployment backend: install a resolved Deku package plan; never assume DNF/RPM is present in the target.
- Boot backend: configure selected upstream boot components with verification and recovery.
- System profile backend: apply locale, keyboard, accounts, network and services from declarative profiles.
- Recovery backend: retain logs, failed-stage information and recovery path.

The UI must not perform privileged disk operations. A narrow privileged helper accepts typed, validated requests instead of arbitrary shell commands. It must re-check device identity, disk size, partition layout and free space at execution time because a validated plan can become stale.

## License implications

The current Deku Installer repository is MIT licensed. Do not copy Anaconda implementation files into this MIT-only codebase until maintainers explicitly select a GPL-compatible distribution license and audit the dependency/license tree. A substantial derivative of GPL-2.0 code cannot be redistributed under the existing MIT-only terms merely because its UI was rewritten. Keep imported source and modifications traceable to exact upstream commits.

Before copying:
1. Confirm the exact upstream license text and notices at the selected commit.
2. Inventory runtime/build dependencies, including blivet, DBus APIs, UI libraries and storage tooling; evaluate each license and platform coupling.
3. Record source-file origins, patch set, branding removals, generated assets and notice obligations.
4. Change the repository license only after maintainers agree on redistribution strategy; retain third-party attribution.
5. Pin upstream source, apply a small staged patch series and add regression tests before a broad redesign.
6. Assign an upstream security-update and rebase owner.

## Alternatives

- **GPL-compatible Anaconda derivative:** faster reuse of a proven workflow, but Python/upstream dependency coupling and recurring rebase work.
- **New Rust UI/coordinator with selected upstream storage APIs:** stronger product control and typed interfaces, but more integration work. Do not reimplement partitioning, filesystems, bootloaders or cryptographic primitives.
- **Hybrid:** reuse the upstream installer backend/storage orchestration and build a Deku frontend with adapter layers; keep process and license boundaries explicit.

The next step is a code/license audit and a minimal architecture prototype, not a wholesale copy or an ISO build. Compare dependency compatibility, licensing, testability, UI customization cost and long-term security maintenance.

## Acceptance checklist

- [ ] Exact upstream commit and license audited.
- [ ] Dependencies and asset licenses inventoried.
- [ ] GPL-compatible strategy approved before copying.
- [ ] UI/backend boundary documented.
- [ ] Dry-run storage preview and second-confirmation model specified.
- [ ] Disposable-VM tests cover UEFI, disk-full, interrupted operations and recovery.
- [ ] No test path can target a host physical disk by default.
