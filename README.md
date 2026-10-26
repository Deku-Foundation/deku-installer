# Deku Installer

Deku Installer currently validates installation plans and calculates a partition-layout preview for Deku Linux. It does not discover physical disks, change partition tables, format filesystems or install an operating system.

## Status

**Non-destructive planner prototype.** It validates an installation plan and computes a deterministic partition layout preview, but it does not discover physical disks, write partition tables, format filesystems, mount a target root, install a bootloader or install an operating system.

## Current working code

- `deku_installer/plan.py` validates bounded plan JSON, rejects duplicate keys and unknown actions, requires a safe fixture-style device identifier, enforces layout/action consistency, and keeps destructive confirmation explicitly unset.
- `deku_installer/layout.py` computes a pure UEFI/GPT or BIOS/MBR preview with 1 MiB alignment, reserved leading/trailing space, fixed EFI/boot sizes, and a minimum 8 GiB root filesystem. It returns byte ranges and does not open device nodes or invoke external tools.
- `deku_installer/cli.py` prints the preview with exclusive end offsets and the explicit statement `writes_performed=false`.
- `tests/test_plan.py` and `tests/test_layout.py` exercise malformed plans, size limits, partition order, alignment, overlaps, small disks and non-destructive behavior.

## Run checks

With Python 3.12 or newer:

```sh
python -m unittest discover -s tests -v
PYTHONPATH=. python -m deku_installer.cli examples/dry-run-plan.json
```

The example target is a fixture, not a real block device. The preview is not an implementation recommendation for every disk layout, and it is not a guarantee that partitioning or boot will work on real hardware.

## Upstream installer reuse

See [the Anaconda source reuse and licensing evaluation](docs/anaconda-source-reuse-evaluation.md). No Anaconda code has been copied. The repo currently uses an MIT license; Anaconda is GPL-2.0. A source-derived installer must not be folded into this repo until the maintainers choose a GPL-compatible redistribution strategy and audit its dependencies and assets.

The design should reuse mature upstream storage and boot tooling rather than implement partitioning/filesystems/bootloaders from scratch. The Deku UI, profile flow, language/accessibility experience, backend contracts and recovery evidence can be differentiated while respecting the licenses and provenance of reused components.

## Safety gates before any disk-writing executor

1. Read-only device discovery, with size/model/serial and stable identity shown to the user.
2. Revalidate the device identity and the exact plan immediately before any destructive action.
3. Two-step confirmation for destructive writes; never infer the target disk from device order.
4. A narrow privileged helper that accepts typed validated operations—not arbitrary shell commands.
5. Disposable virtual-disk tests for UEFI and BIOS layouts, disk-full, interrupted operations, stale device plans and recovery.
6. An auditable operation journal and explicit handling of cases where automatic rollback is not safe.

No physical-disk writes should be implemented until these boundaries have test coverage.
