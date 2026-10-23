# Deku Installer Architecture (Draft)

## Scope

The installer prepares a Deku Linux target from a trusted installation environment. The first milestone is deliberately non-destructive: validate an installation plan and explain the proposed actions without touching disks.

## Components

- **Interface**: graphical and text interfaces consume the same plan model; UI code does not perform privileged storage operations.
- **Discovery**: read-only hardware, firmware, network, and block-device discovery.
- **Planner**: converts user choices into a deterministic plan and reports conflicts before execution.
- **Validator**: checks schema, supported actions, target identity, and explicit confirmation requirements.
- **Executor**: future privileged component, isolated behind a narrow API; not implemented in the current prototype.
- **Deployment**: future integration with Deku package/repository metadata and base-system artifacts.
- **Boot setup**: future bootloader and initramfs integration with explicit EFI/BIOS handling.
- **Audit log**: records plan, decisions, artifact digests, and errors without logging secrets.

## Safety invariants

1. Planning and validation must never write to disks or change firmware settings.
2. A plan must identify the target device and include an explicit destructive-operation confirmation gate.
3. Unknown action types and unknown schema versions fail closed.
4. Execution must re-discover and re-validate the target immediately before any destructive action.
5. Never infer the target disk from device ordering alone; require an explicit selection and show size/model/serial where available.
6. Partitioning, formatting, bootloader installation, and system deployment are separate steps with auditable results.
7. Interrupted execution must leave a recoverable journal; rollback guarantees must be stated per filesystem and operation rather than assumed.
8. Tests use fixtures or disposable virtual machines, never a developer's host disk.

## Initial implementation boundary

The first code milestone validates a JSON plan only. It does not scan real devices, mount filesystems, download packages, partition disks, install a bootloader, or run as root. This narrow scope makes it possible to test schema and safety rules before privileged code exists.

## Proposed implementation sequence

1. Plan schema and validator with unit tests.
2. Read-only discovery abstraction and fake-device tests.
3. UI wireframe and accessibility review.
4. Package deployment adapter after the Deku package format and base artifact are defined.
5. Storage backend prototype in a disposable VM, with interruption and recovery tests.
6. Reproducible installer image and boot tests under UEFI and BIOS where supported.

## Plan validator v1 limits

The plan-only validator currently requires an explicit fixture-style device identifier, a supported UEFI/GPT or BIOS/MBR layout, a fixed allowlist of partition actions, an unconfirmed destructive-operation gate, and at least 8 GiB reserved for the root filesystem in addition to any declared EFI/boot partitions. These are prototype validation rules, not final partitioning recommendations. No disk is touched.
