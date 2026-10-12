# Security and evidence handling

The tools consume local, untrusted records. They must not execute record text, fetch URLs, invoke target software, install dependencies, or repair inputs. Run them against copies of research material when isolation is useful. Validation cannot detect every secret or establish that evidence is truthful or permitted.

Do not include credentials, account exports, personal content, proprietary product source, private endpoints, or restricted observation bundles in reports or issues. Excluded research belongs outside a distributed implementation packet.

For a suspected security defect, prepare a minimal synthetic reproduction and contact the repository maintainer through a private channel they explicitly provide. This project currently has no configured private reporting endpoint. Do not put sensitive exploit data in a public issue; if no private channel is available, report only a non-sensitive description and request one.

Record the affected release, expected boundary, observed behavior, platform/Python version, and a redacted reproduction. Review path handling, resource bounds, non-regular files, and input mutation before distributing a fix.
