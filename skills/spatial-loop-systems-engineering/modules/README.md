# Domain modules

Modules are loaded only when their trigger matches. They interpret the portable
procedure for a concrete substrate and may not override the core evidence laws.

| Module | Trigger |
|---|---|
| [`linux-isolation-runtime.md`](linux-isolation-runtime.md) | Linux namespaces, cgroup v2, seccomp, capabilities, pidfd, container/sandbox runtime, KVM/microVM, TAP/veth, rootfs, snapshot/restore |

A module is design guidance, not runtime evidence. Consumer-specific kernel,
hardware, path, privilege, and receipt state remains outside this repository.
