# Deku Installer

Deku Installer is the installation and first-boot project for Deku Linux.

## Status

**Non-destructive plan-validation prototype.** No installable image or production installer is available. The current code parses and validates an installation plan; it does not discover physical disks, write partitions, format filesystems, mount a target root, install a bootloader, or install an operating system.

## Current prototype

The plan validator bounds raw JSON to 1 MiB before parsing and rejects duplicate JSON object keys, invalid UTF-8, excessive nesting, unsupported schema versions, boolean schema values, excessive action counts and duplicate boot-partition actions. It validates a plan only; no disk-writing or privileged operations are implemented.

Passing these tests proves that the plan meets the prototype's schema and consistency checks. It does not prove that a machine can be installed, that storage layouts are safe on real hardware, or that an image boots.

## Direction

Evaluate mature upstream installer technology before implementing low-level storage, bootloader and hardware handling from scratch. Fedora's Anaconda is a candidate for technical evaluation because it supports graphical, text and automated installation workflows; no Anaconda source code has been copied into this repository.

## Development principles

- Never run destructive disk operations without explicit confirmation and a tested plan.
- Separate UI, installation planning, storage operations, package deployment and boot configuration.
- Keep privileged operations narrow and auditable.
- Test in disposable virtual machines before hardware claims or release images.
- Track licenses, provenance, patches and upstream versions for any reused components.
- Do not advertise unsupported features or publish download links before artifacts exist.

## Run checks

With Python 3.12 or newer:

```sh
python -m unittest discover -s tests -v
PYTHONPATH=. python -m deku_installer.cli examples/dry-run-plan.json
```

The CLI validates the example plan only. It does not modify disks or install software.

## Planned milestones

1. Record architecture and upstream evaluation criteria.
2. Define a machine-readable installation plan and validation tests — prototype exists.
3. Add non-destructive device discovery and plan preview.
4. Integrate the chosen package deployment and boot configuration paths.
5. Build and test an installer image in virtual machines.
6. Consider hardware testing and release engineering only after repeatable VM results.
