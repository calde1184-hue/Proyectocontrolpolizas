# AGENTS.md

This is not a code repository. It is a document repository of insurance policy
PDFs under `Insumos_Control_Polizas/` plus a master client spreadsheet. There is
no source code, no package manager, no build, test, lint, or CI — do not invent
or run `npm`, `pip`, `make`, test, or deploy commands.

## Layout

- `Insumos_Control_Polizas/Maestro_Clientes.xlsx` — master client list
- `Insumos_Control_Polizas/polizas/` — PDF insurance policy documents

## Policy PDF naming

Files in `polizas/` follow `Poliza_<PREFIX>-<YEAR>-<SEQ>.pdf`:

- Prefixes: `AIS`, `PCS`, `SPC`
- Year: `2026`
- Sequence: 4 digits, zero-padded (e.g. `0001`)

Example: `Poliza_AIS-2026-0001.pdf`

If you add a PDF, use this exact pattern. Do not rename existing files.

## What to do here

- Read / reference the PDFs and the spreadsheet as needed.
- Do not look for `package.json`, `requirements.txt`, `Makefile`, CI workflows,
  test runners, or app entrypoints — none exist in this repo.

## Git

Commits are attributed to the global user: `calde1184-hue` /
`calde1184@gmail.com`.
