# Code signing policy

## Status

The project is applying for the SignPath Foundation open-source code-signing program. V2.3.2 and earlier releases are unsigned. This policy becomes the active release-signing policy after the application is approved.

Free code signing provided by [SignPath.io](https://signpath.io/), certificate by [SignPath Foundation](https://signpath.org/).

## Team roles

- Committer and reviewer: [Tsukira1229](https://github.com/Tsukira1229)
- Signing approver: [Tsukira1229](https://github.com/Tsukira1229)

Changes from contributors without commit access must be reviewed before they are merged. Every signing request requires manual approval by the signing approver.

## Signed artifacts

Only `JapaneseStrokeMouseWriter.exe`, built by the public GitHub Actions workflow from this repository, will be signed with the project's certificate. Bundled third-party executables and libraries will not be re-signed with the project's certificate.

## Privacy

See the project [privacy statement](PRIVACY.md). This program will not transfer any information to other networked systems unless specifically requested by the user or the person installing or operating it.
