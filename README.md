# Deku Installer

Deku Installer is the installation and first-boot project for Deku Linux.

## Status

**Early design stage.** No installable image or production installer is available yet. This repository currently defines the project's scope and evaluation plan; it does not modify disks or install an operating system.

## Direction

Build an installer that is reliable, accessible, testable, and tailored to Deku Linux. Evaluate mature upstream installer technology before implementing low-level storage, bootloader, and hardware handling from scratch. Fedora's Anaconda is a candidate for technical evaluation because it supports graphical, text, and automated installation workflows; no Anaconda source code has been copied into this repository.

## Development principles

- Never run destructive disk operations without explicit confirmation and a tested plan.
- Separate UI, installation planning, storage operations, package deployment, and boot configuration.
- Keep privileged operations narrow and auditable.
- Test in disposable virtual machines before hardware claims or release images.
- Track licenses, provenance, patches, and upstream versions for any reused components.
- Do not advertise unsupported features or publish download links before artifacts exist.

## Planned milestones

1. Record architecture and upstream evaluation criteria.
2. Define a machine-readable installation plan and validation tests.
3. Prototype non-destructive discovery and plan-only behavior.
4. Integrate the chosen package deployment and boot configuration paths.
5. Build and test an installer image in virtual machines.
6. Consider hardware testing and release engineering only after repeatable VM results.

## Documentation

Architecture, upstream evaluation, and safety requirements will be added incrementally. All implementation claims must be backed by tests and reproducible build records.
