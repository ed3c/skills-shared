# Forgejo-only private-lineage mode

This mode closes a boundary that the normal dual-forge procedure intentionally does not cover. The normal procedure moves one admitted Git lineage between GitHub and Forgejo. This mode keeps a private lineage local and permits only a checked, abstract requirements packet to cross into a separately authored fresh-root repository.

The directory is nested under `dual-forge-repository-loop` so the two modes remain explicitly related but mechanically non-interchangeable. Nothing here authorizes local mutation from a connector-only runtime.

## Components

- `audit_git_history.py` — local all-history and worktree denied-material inventory;
- `configure_forgejo_only.sh` and `check_forgejo_only.py` — exact one-remote sealing and replay;
- `pre-push.local-only-guard` — exact destination and alternate-object refusal;
- `build_private_fingerprints.py` and `check_cleanroom_packet.py` — one-way clean-room boundary;
- `create_fresh_root_snapshot.sh` and `assert_no_shared_lineage.sh` — public root production and lineage separation;
- `check_provider_retention.py` — explicit provider surface disposition without overclaiming erasure;
- `check_retirement_inventory.py` — local clones, worktrees, mirrors, bundles, caches, forks, and credentials retired against an exact observed head.
