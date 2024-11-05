# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.6.x   | yes       |
| < 0.6   | no        |

## Reporting a vulnerability

Please do not open a public issue for security problems. Email the maintainer
or use GitHub's private vulnerability reporting on this repository.

Include: the command run, a minimal transcript or sealed file that triggers
the problem, and what the tool should have reported instead.

The one thing the hash chain does NOT provide is a signature: anyone who can
edit a sealed file can re-seal it. If your report is about tamper-evidence
boundaries, that limitation is documented in the README on purpose.

We aim to acknowledge reports within a few days and to ship a fix or a
documented limitation in the next release.
