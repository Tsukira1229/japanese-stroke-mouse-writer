# Code signing policy

## Status

The project applied for the SignPath Foundation open-source code-signing program, but the application was not approved. Current releases, including V2.7.0, are unsigned.

The project does not currently have an active Authenticode signing workflow, signing certificate, signing request process, or planned signed release. If code signing is introduced in the future, this policy will be updated before any signed artifact is published.

## Team roles

- Committer and reviewer: [Tsukira1229](https://github.com/Tsukira1229)
- Release approver: [Tsukira1229](https://github.com/Tsukira1229)

Changes from contributors without commit access must be reviewed before they are merged. Release artifacts are built from the repository source and published with a SHA-256 checksum.

## Unsigned artifacts

Portable ZIP releases contain an unsigned `JapaneseStrokeMouseWriter.exe`. Windows SmartScreen may display an unknown-publisher warning. Users should download releases from the project GitHub repository and verify the provided SHA-256 checksum when possible.

## Privacy

See the project [privacy statement](PRIVACY.md). This program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it.
