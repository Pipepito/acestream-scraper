# Container storage

Open **Overview → Storage** to see data directories, detected mount destinations,
allocated file sizes and filesystem free space. No Docker socket or host privileges
are needed. Legacy environment variables also produce a deprecation notice here,
showing the replacement name without exposing either value.

## Read the report

- **Mounted storage**: the directory is on a mount visible inside the container.
  This may be a bind mount, Docker volume, tmpfs or another filesystem; it is not
  proof of durable storage. The original host path and Docker volume name cannot
  reliably be determined inside the container. Consult Compose or your container
  manager for those details.
- **Container filesystem**: the directory uses the container's root filesystem.
  In a normal Docker deployment, deleting/recreating the container can discard it.
- **Mount unknown**: `/proc/self/mountinfo` is unavailable, such as on native macOS.
  Configured paths and readable size/space data may still be shown.
- **Directory size**: allocated bytes in regular files, with hard links counted once
  within a directory scan. Symbolic links and nested mount contents are excluded.
  Sparse files may have much smaller allocated size than their apparent length.
- **At least … / Partial size**: a time, depth or entry limit was reached, or some
  entries could not be read. This is a lower bound, not a complete size.
- **Free space / Filesystem total**: space available to the app and total filesystem
  capacity. Directories on the same filesystem share this space; do not add their
  free-space figures together. Mounts or Docker Desktop may report a backing VM's
  filesystem rather than the host drive's capacity. Read-only mounts are labelled.
- **Unavailable** means missing or unreadable, never zero.

Configured locations include the SQLite database directories, logs, player output,
IPFS, ZeroNet, both engine states and WARP. Existing directory mounts elsewhere in
the container are discovered too, except `/dev`, `/proc`, `/sys` and their children.
Docker's injected individual files (such as `/etc/hosts`) are not directory mounts.
Unused sidecar directories may be missing when a service is disabled.

## Refresh and bounds

The report is cached for one minute. Refresh retrieves the current cached result
or starts a new scan after expiry. Scanning runs in a separate process with an
8-second deadline, at most 64 paths, a shared 4-second directory-scan budget,
1 second per directory, 100,000 entries per directory and depth 64. Disk activity
can change sizes while a scan is running. Nested configured paths can overlap;
the app deliberately does not sum directory sizes.

The read-only `/api/v1/system/storage` endpoint uses normal optional API-token
protection, accepts no path parameter, and does not export environment values,
mount source paths, database contents or file listings.
