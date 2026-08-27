# Troubleshooting

Error messages, the container mechanics behind them, and the ground this was
verified on. Reach for this when a command fails; the rules that apply to every
run are the *Gotchas* in [`SKILL.md`](SKILL.md).

| Symptom | Cause / fix |
|---|---|
| `error getting credentials … docker-credential-*` | Only registry operations need credentials; the image is already local. See *No `docker pull`* below. |
| `Docker is not responding. Start the Docker daemon/Desktop.` | The daemon is not running. |
| `image … not found locally` | Pull it from an interactive terminal: `docker pull adeuxy/markitdown:latest`. |
| `no such script: X` (from `run`) | No file at that path on the host. Check the path you typed. |
| `X is outside both the current directory and PDFMD_TEMPLATES` | The file exists but no mount reaches it. Copy your extractor next to the PDF — which is where it belongs anyway, since its constants are this document's. |
| `container failed (exit 2)` | Your script rejected its arguments. The exact `docker run` line is echoed with a `$` prefix — copy it and debug directly. |
| `… exists and is not empty; pass --force to replace it` | `split` refusing to wipe a destination. Check it holds nothing hand-written, then re-run with `--force`. |
| `nothing to split: no heading at level N or above (… try --level M)` | `split` found nothing to cut on and tells you which levels the file actually has. Note the opposite mistake is silent: too high a `--level` cuts on every subsection and gives you dozens of one-paragraph files. |
| `(no text)` from `text` | Scanned PDF. See recipe 5. |
| `only N words, inconclusive` from `columns` | You sampled a cover or near-empty page. Try a content page. |
| Everything is slow on Apple Silicon / ARM | amd64 emulation. Small page ranges; full document once at the end. |

## No `docker pull`, on purpose

A pull is a *registry* operation, and if the host's `~/.docker/config.json` sets
a `credsStore` (Docker Desktop does by default on macOS and Windows), the CLI
shells out to a credential helper binary that is frequently absent from a
non-interactive shell's PATH, so the pull dies with
`error getting credentials - err: exec: "docker-credential-<store>": executable file not found`
even for a public image. **`docker run` against an already-local image never
touches the registry**, which is why everything else works. If `doctor` says the
image is missing, pull it from your own interactive terminal.

## Container mechanics

- **`--platform` is applied only when needed.** The default image is amd64-only;
  on an arm64 host the driver passes `--platform linux/amd64` to silence the
  per-run warning, on amd64 it passes nothing. `doctor` tells you which branch
  you are on.
- **Generated files belong to you, not root**, because the driver passes
  `--user <uid>:<gid>` where the host has POSIX ownership (Linux, macOS); on
  Windows it omits the flag and lets Docker Desktop handle it.
- **Mount layout**: five mounts — this skill at `/skill` and `PDFMD_TEMPLATES`
  at `/templates`, both **read-only**; the PDF's directory at `/pdf`, also
  read-only; the current directory at `/work`; the output directory at `/out`.
  The skill and the PDF may live anywhere, which is why you run the driver by
  absolute path and never copy it into a project. What `run` executes has to sit
  under `/work` or `/templates`.
- **Output paths**: `/tmp/pdfmd` on Linux, `/var/folders/.../T/pdfmd` on macOS,
  `%TEMP%\pdfmd` on Windows, via Python's `tempfile`. Set `PDFMD_OUT` for a
  stable location.
- **Any image works** if it has the libraries: `PDFMD_IMAGE=other/image
  python3 $D doctor` checks markitdown, pdfplumber, pypdfium2 and PIL up front.

## Where this was verified

macOS on arm64 with Docker Desktop (server 29.6.2), against three unrelated
PDFs — a 608-page two-column manual, an 87-page single-column book, and a
252-page single-column book set in one type family — each converted end to end
and split into a tree that passes `check`, plus a generated image-only PDF for
the scanned case. The Linux path differs only in the temp directory. The Windows
branches (no `--user`, `%TEMP%`) are handled in code but have not been
exercised.

The mount layout was exercised from a working directory holding no copy of the
skill, and `PDFMD_TEMPLATES` from a library root separate from both. `missing`,
`templates`, the ragged-right/justified report in `info`, and the header-band
fallback in `repeats` were verified on the 252-page book only; the other two
PDFs have not been re-run since those landed.
