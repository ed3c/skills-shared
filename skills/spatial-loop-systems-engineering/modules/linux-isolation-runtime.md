# Linux isolation runtime module

Load this module for Linux namespace/cgroup/seccomp sandboxes, container
runtimes, KVM/microVM supervisors, or microsandbox-like execution systems.

It is a worked domain interpretation of the portable Skill. It is not a
production sandbox implementation and does not certify isolation.

## 1. Select the isolation class before APIs

| Class | Kernel relationship | Typical reason to choose | Required proof surface |
|---|---|---|---|
| namespaces + cgroup + seccomp | shares the host kernel | lowest overhead and broad Linux compatibility | kernel attack surface, namespace/mount/credential closure, syscall policy |
| user-space kernel | mediates guest syscalls in user space | reduce direct host-kernel syscall exposure | compatibility, mediation completeness, host interfaces |
| KVM microVM | separate guest kernel | stronger kernel boundary and VM lifecycle | KVM/device model/jailer/snapshot/network lifecycle |
| WebAssembly/runtime isolate | no full Linux ABI by default | small capability surface and fast instantiation | host-call allowlist, runtime/compiler safety, workload compatibility |

Do not choose by a headline latency number. Bind threat model, workload ABI,
hardware availability, operational burden, and measured tail latency.

## 2. Linux-specific realm map

```text
HOST CONTROL REALM
  supervisor identity
  cgroup hierarchy/delegation
  namespace handles
  rootfs/image and snapshot store
  network devices/routes/firewall
  logs/metrics/receipts

ISOLATION REALM
  namespace PID 1 or guest init
  payload processes/threads
  mounted filesystem view
  bounded descriptors and sockets
  assigned CPU/memory/PID/I/O resources

EXTERNAL REALM
  network peers
  registries/object stores
  metadata/control services
  operator and recovery authority
```

Every FD, namespace handle, TAP/veth device, route, mount, cgroup, temporary
directory, snapshot, and process handle must have one lifecycle owner.

## 3. Process identity and lifecycle invariants

### Prefer stable process handles

Use pidfds where the target kernel/runtime supports them. A pidfd is pollable
and can be used with `waitid`, `pidfd_send_signal`, and `epoll`; signaling via a
pidfd avoids the PID-reuse race inherent in a raw numeric PID.

Raw PID use requires an explicit identity/reuse defense.

### `PR_SET_PDEATHSIG` is defense in depth

Do not treat parent-death signaling as the primary lifecycle proof:

- the relevant parent is the thread that created the child, not necessarily the
  lifetime of the whole supervisor process;
- no signal is delivered if the parent died before the child installed the
  setting, so the immediate parent identity check is still needed;
- credential-changing `execve` paths can clear the setting.

Combine stable process identity, a supervisor-owned cgroup/subtree, explicit
wait/reap, and an idempotent cleanup loop.

### Namespace PID 1 is special

The first process in a PID namespace must reap orphaned descendants and handle
signal semantics deliberately. Waiting for only the original payload child
does not prove the namespace contains no zombies or descendants.

A representative lifecycle is:

```text
ALLOCATE_BOUNDARIES
→ CREATE_CHILD_WITH_STABLE_HANDLE
→ ATTACH_RESOURCE_BOUNDARY
→ RELEASE_CHILD_BARRIER
→ CHILD_BECOMES_NAMESPACE_INIT
→ SET_MOUNTS/CREDENTIALS/SECCOMP
→ EXEC_PAYLOAD
→ FORWARD_SIGNAL_AND_REAP_SUBTREE
→ KILL/WAIT_EMPTY
→ RELEASE_EXTERNAL_RESOURCES
→ VERIFY_ZERO_LEAK
```

## 4. cgroup v2 invariants

Before use, probe:

```text
unified hierarchy mounted
required controllers available
controllers delegated/enabled at the intended parent
write permissions and ownership
kernel support for required files/events
```

Bind limits and observations separately:

- `memory.high` is a throttling/reclaim boundary, not a hard kill line;
- `memory.max` is the hard memory boundary, but observation must use cgroup
  events rather than assuming allocation fails at an exact instruction;
- `pids.max` bounds process creation;
- `cpu.max` and I/O controls require an explicit load and fairness contract;
- use `memory.events`, `cgroup.events`, and pressure metrics where applicable.

Cleanup is a state machine, not `remove_dir` in a destructor:

```text
stop admission
→ signal/kill the owned subtree
→ wait until the cgroup is unpopulated
→ verify event/process state
→ remove the cgroup
→ verify absence
```

Use `cgroup.kill` where admitted and supported, while preserving a fallback
contract. A failed directory removal is a reconciliation input, not a warning
to ignore.

## 5. Mount and rootfs invariants

A `chroot` alone is not the target boundary.

For a namespace-root design:

1. make mount propagation private (`MS_REC | MS_PRIVATE`) before restructuring;
2. ensure the new root is a mount point;
3. satisfy `pivot_root` preconditions in the correct user/mount namespace;
4. `chdir("/")` after the pivot;
5. detach and remove the old root;
6. mount a fresh `/proc` from the intended PID namespace with explicit
   `nosuid`, `nodev`, and `noexec` policy as required;
7. apply read-only, device, suid, exec, propagation, and overlay/write-layer
   policies to every relevant mount;
8. verify the resulting mount table from both host and isolated views.

Open descriptors or namespace handles that still reference the old root are
escape/retention vectors and belong in the FD/handle ledger.

## 6. Credentials, capabilities, and syscall policy

Do not say “drop capabilities” without naming all sets and ordering.

Bind:

```text
user-namespace UID/GID mapping
supplementary groups
real/effective/saved UID and GID
permitted/effective/inheritable capability sets
capability bounding set
ambient capabilities
securebits
no_new_privs
seccomp installation and synchronization behavior
```

Dropping only the effective set is insufficient. `no_new_privs` prevents
`execve` from granting new privilege, but it is not a universal sandbox.
Seccomp requires the correct privilege or `no_new_privs`, persists across
fork/exec, and needs explicit policy for multi-thread synchronization.

Build syscall policy from the workload ABI and negative tests. A denylist
created from memory is not a policy proof.

## 7. File-descriptor invariants

Default to an explicit inherited-FD allowlist.

Use `close_range`/`CLOSE_RANGE_CLOEXEC` and, where needed,
`CLOSE_RANGE_UNSHARE`, or an equivalent bounded mechanism. Account for:

```text
shared FD tables
descriptors opened between enumeration and exec
SCM_RIGHTS descriptor transfer
epoll/io_uring registrations
namespace/rootfs handles
logging/control sockets
```

`FD_CLOEXEC` on selected descriptors does not prove all other inherited
descriptors are closed.

## 8. Network invariants

For each netns, TAP/veth, route, nftables/iptables rule, forwarding setting, DNS
path, and address lease, declare owner and teardown.

Threat-model at least:

```text
host loopback and management interfaces
cloud metadata endpoints
DNS rebinding and resolver trust
IPv4 and IPv6 parity
egress allow/deny policy
spoofing and source validation
half-created interfaces/routes
supervisor death during network setup
```

A network namespace without egress/firewall policy is separation of view, not a
complete network security policy.

## 9. Snapshot, warm pool, and performance invariants

Snapshot/restore compatibility depends on the exact VM/runtime implementation,
CPU model/architecture, device state, kernel/userspace version, and network or
vsock state. Treat a snapshot as a versioned artifact with compatibility and
rollback metadata.

A warm-pool claim must define:

```text
what is already allocated
what is restored versus freshly initialized
tenant-data scrubbing boundary
pool replenishment loop
stale-image/snapshot invalidation
memory accounting
cold and warm percentile definitions
failure behavior when the pool is empty
```

Measure the exact hardware, firmware, kernel, mitigations, VMM/runtime build,
rootfs, workload, concurrency, and percentile. Project or vendor latency
numbers are comparison inputs, not acceptance evidence.

## 10. Teardown oracle

A completed run should be able to prove, for its exact subject:

```text
no live or zombie descendant processes
owned cgroup unpopulated and removed
no leaked pidfds or inherited FDs
no mounted old root or leaked mount namespace
no TAP/veth, route, firewall, or address lease left behind
no temporary rootfs/snapshot/shared-memory artifact left behind
no admission path still accepting work
terminal receipt binds exit/signal/OOM/timeout cause
```

Some checks require a privileged host observer. If that observer is unavailable,
the state is `NOT_EXERCISED`.

## 11. Corrections to common prototype patterns

| Prototype shortcut | Why it is insufficient | Required contract |
|---|---|---|
| `exec` plus `chroot` | shares host kernel view and leaves mount/credential/FD paths unclosed | namespace/mount/rootfs/credential/syscall/FD invariants |
| `PR_SET_PDEATHSIG` alone | parent-thread and installation-race semantics; no subtree cleanup proof | pidfd/wait + cgroup lifecycle + parent-death defense |
| one `waitpid` | does not prove PID-namespace descendants are reaped | PID 1/subreaper behavior and subtree-empty oracle |
| delete cgroup in `Drop` | directory may remain populated or cleanup may be interrupted | kill/wait-empty/remove/verify reconciliation |
| drop one capability | capability sets and bounding/ambient state can retain authority | complete credential/capability ledger |
| `memory.max` means exact deterministic kill point | memory reclaim/OOM behavior is observed through events and workload behavior | event-bound OOM/backpressure oracle |
| marketing cold-start number | environment, percentile, workload, and warm state are unbound | complete performance measurement contract |
| mock-only “escape test” | no kernel, privilege, exploit, or teardown path executed | privileged/chaos/security lanes with negative controls |

## 12. Primary implementation references

Re-verify versions and semantics at implementation time:

- Linux man-pages: `pid_namespaces(7)`, `PR_SET_PDEATHSIG(2)`,
  `pidfd_open(2)`, `pidfd_send_signal(2)`, `close_range(2)`, `capabilities(7)`,
  `seccomp(2)`, `pivot_root(2)`, `mount_namespaces(7)`.
- Linux kernel documentation: cgroup v2 and `no_new_privs`.
- The selected VMM/runtime's official source and snapshot/jailer documentation.
- The exact target kernel configuration and hardware capability probes.

Source review does not replace execution on the target environment.
