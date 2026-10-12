# Behavior Rebuild Kit

**Version 0.1.0**

An original agent skill and practical method for turning permitted product-behavior research into an independently authored implementation contract and reproducible acceptance evidence. Includes reusable templates and local record validators.

Use it to discover behavior, prepare a reviewed handoff, and verify outcomes or prioritize recovery work. It applies across products and technology stacks. It does not automate target access or certify legal clearance, independence, product parity, or readiness.

## What is included

- **One skill:** `skills/behavior-rebuild/`, with discover, handoff, and verify/recover modes.
- **Templates:** source/permission records, command and observation notes, acceptance/recovery planning, task ownership, session status, and quality gates.
- **Local tools:** strict record validation, evidence hashes, handoff checks, explicit run/candidate acceptance gates, and reports. Python 3.11+, standard library only; offline and read-only.
- **Original example:** Delimited Notebook, a fictional CSV workflow with synthetic inputs and a small executable demonstration.

## Install in Codex

Requires Python 3.11+. To clone this private repository, use GitHub CLI authenticated with an account that has access:

```sh
gh repo clone oabdelmaksoud/behavior-rebuild-kit
cd behavior-rebuild-kit
```

From the repository root, copy the complete skill folder. This Python standard-library command works with the same paths on macOS, Linux, and Windows; it uses `CODEX_HOME` when set, otherwise the `.codex` directory in your home folder. It refuses to overwrite an existing installation.

```sh
python3 -c "import os, shutil; from pathlib import Path; source = Path('skills/behavior-rebuild'); destination = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex') / 'skills' / 'behavior-rebuild'; shutil.copytree(source, destination); print(destination)"
```

If your Python 3.11+ executable is named `python`, substitute it for `python3`. Review an existing installation before replacing it. Start a new Codex turn after installation so the skill can be discovered, then invoke it in chat:

```text
$behavior-rebuild Discover the permitted behavior of this workflow. Record evidence, exclusions, and unknowns.
$behavior-rebuild Prepare a handoff from this approved evidence. Freeze the packet and arrange separate review.
$behavior-rebuild Verify/recover this implementation against its frozen contract. Report failures and rank repair work.
```

| Mode | Produces |
|---|---|
| Discover | Scoped observations, source-use decisions, unknowns, and exclusions. |
| Handoff | An original implementation contract, reviewed packet, file hashes, and exposure records. |
| Verify/recover | Explicit acceptance evidence, open gaps, and prioritized recovery work. |

Choose one mode for the task. The skill grants no authority for target access or publication. Read [SKILL.md](skills/behavior-rebuild/SKILL.md) for the method and [compatibility](docs/compatibility.md) for observed host coverage. The complete folder includes every required reference, template, and script; there is no plugin wrapper or package dependency to install.

## Try the example

From this repository's root, with Python 3.11 or later:

```sh
python3 skills/behavior-rebuild/scripts/validate.py examples/delimited-notebook --stage discover
python3 skills/behavior-rebuild/scripts/validate.py examples/delimited-notebook --stage handoff
python3 skills/behavior-rebuild/scripts/report.py examples/delimited-notebook
```

On systems where Python 3.11+ is named `python`, use that executable instead. The commands need no package installation. The static example has no executed acceptance run. A discovery or handoff pass must not be described as product acceptance.

Generate fresh demonstration evidence in a new output directory:

```sh
python3 examples/delimited-notebook/run_demo.py --output ../behavior-rebuild-demo
python3 skills/behavior-rebuild/scripts/validate.py ../behavior-rebuild-demo --stage acceptance --run runs/demo.json --candidate demo-v1
python3 skills/behavior-rebuild/scripts/report.py ../behavior-rebuild-demo --run runs/demo.json --candidate demo-v1
```

Choose a different output path if that directory already exists. The demonstration runner writes only its new output directory; the validator and reporter do not mutate inputs. The example tests its declared total/export and invalid-amount behavior. Crash recovery, cancellation, and receipt/idempotency guarantees are extension work, not accepted features of this demo.

The recorded demo reviewer identifies automated fixture checks. It is not a human approval or evidence of legal independence. Inspect the [example](examples/delimited-notebook/README.md) for its exact implementation and oracle scope.

## Use the skill

Start with the [templates](skills/behavior-rebuild/assets/templates). The starter `project.json` is intentionally incomplete and blocked until it contains meaningful scope and evidence. Keep raw restricted research outside the distributable packet. Use [record format](skills/behavior-rebuild/references/record-format.md) for exact fields; the format is bespoke versioned JSON, not JSON Schema.

Supply an explicit run and candidate for acceptance. Runs bind the exact `project.json` bytes, so editing the manifest invalidates that binding; retain historical records and produce a new run. Tools never select a newest run automatically. Add `--json` to either tool for structured output. Validator `--digest` prints manifest identity, not gate approval.

| Exit code | Meaning |
|---|---|
| 0 | Selected supported structural/recorded-evidence gate passed. |
| 1 | Well-formed records, but the selected gate is blocked or failed. |
| 2 | Invalid input, path, integrity, or invocation. |

## Method and trust boundary

Track documented, observed, reported, and unknown claims separately from proposed original design. Record explicit source-use decisions, including observation, handoff, and publication permission. A local handoff approval does not grant publication permission. Use separate research, implementation, and review contexts where required and disclose prior exposure.

Validate a trusted, quiescent local copy: another process must not replace files or path components during a check. The tools are not a sandbox for a concurrently hostile filesystem.

Hash checks establish file identity. They do not establish permission, truthful observation, or correct real-world outcomes. The [quality gate matrix](docs/quality-gates.md) explains what each check can support. Read the [method](docs/method.md) and [evidence boundary](docs/evidence-boundary.md) before applying the kit to a real product.

## Verified checks

- **36 tests passed on six CI combinations:** Linux, macOS, and Windows with Python 3.11 and 3.14. Every job also passed the demo, explicit acceptance gate, and release build. See the [completed CI run](https://github.com/oabdelmaksoud/behavior-rebuild-kit/actions/runs/38187814468) and [verification record](docs/release-verification.md) for the tested revision.
- **Installed-skill project trial:** 141/141 final comparisons and 80/80 independent review probes passed within a bounded sorting contract; negative controls blocked acceptance. See [project trial](docs/project-trial.md).
- **Native Codex:** bounded project-local and global installed trials completed. Claude native behavior remains unverified because authentication blocked its trial. See [compatibility](docs/compatibility.md).

## Development and release

```sh
python3 -m unittest discover -s tests -v
```

Build release archives into a new directory outside this repository:

```sh
python3 tools/build_release.py --output ../behavior-rebuild-release
```

The builder checks the tree against the explicit `release-files.txt` inventory, then creates `behavior-rebuild-kit-0.1.0.zip`, `behavior-rebuild-skill-0.1.0.zip`, and `SHA256SUMS`. Choose a different destination if it already exists. The skill archive contains the self-contained `behavior-rebuild/` folder; the kit archive includes the repository resources. Adding or removing a release file requires updating the inventory. Archives and hashes do not constitute publication approval.

A bounded real-command [project trial](docs/project-trial.md) exercised the installed skill with separate research, implementation, evaluation, and review contexts. See the dated [verification record](docs/release-verification.md) for observed checks.

See [contributing](CONTRIBUTING.md), [security](SECURITY.md), and the [publication checklist](docs/publication-checklist.md). Local preparation does not publish anything. Actual host/platform coverage must be stated from observed test results, not inferred from configured CI.

Original material is [MIT licensed](LICENSE). [NOTICE](NOTICE.md) attributes pinned Storytold inspiration and discloses source exposure. No Storytold implementation or proprietary target material is bundled.
