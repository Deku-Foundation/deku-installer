# Upstream Installer Evaluation

## Candidate: Anaconda

Anaconda is a mature installer used by Fedora and other distributions. Its documented capabilities include graphical, text, and automated installation, remote installation sources, and advanced storage workflows. It is a candidate for a time-boxed technical evaluation, not an automatic architectural commitment.

- Upstream: https://github.com/rhinstaller/anaconda
- Project documentation: https://anaconda-installer.readthedocs.io/
- Fedora overview: https://fedoraproject.org/wiki/Anaconda
- Fedora package metadata lists Anaconda as GPL-2.0-or-later.
- The separate Anaconda Web UI has its own licensing and dependency set; evaluate each component and dependency individually.

## Evaluation questions

- Can Anaconda's install class, packaging hooks, and runtime configuration support a Deku base image without assuming RPM/DNF semantics throughout the stack?
- Which storage, bootloader, and hardware support can be reused as-is, and which pieces are coupled to Fedora/RHEL?
- Can package deployment be cleanly adapted to Deku's future package metadata and transaction interface?
- What is the maintenance cost of tracking upstream releases and carrying a minimal patch set?
- Are the installer UI and accessibility requirements satisfied, including keyboard navigation, screen-reader behavior, localization, and low-resolution displays?
- Can the resulting image be built reproducibly and tested safely in disposable VMs?

## Decision gates

1. Build a dependency and integration map from a pinned upstream revision.
2. Prototype a non-production install class or adapter without changing target disks.
3. Demonstrate that package deployment can be replaced behind a narrow interface.
4. Run upstream tests and a VM installation test using a clearly identified disposable disk.
5. Record maintenance burden, licensing notices, dependency licenses, and patch ownership.

## Reuse and project identity

Deku may reuse compatible upstream components when technical, security, and license reviews support the decision. Product naming and visual identity remain Deku-owned. Technical provenance, copyright notices, license texts, and required attribution must still be preserved in source distributions and documentation; independent branding does not waive license obligations.

## Current status

No Anaconda code has been imported, no upstream repository has been forked, and no installer image has been built or boot-tested by this repository. This document records an evaluation path only.
