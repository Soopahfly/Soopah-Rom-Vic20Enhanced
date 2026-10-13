# Building ROMs

## GitHub Actions

1. Open [Build VIC-20 ROMs](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/actions/workflows/build-roms.yml).
2. Select **Run workflow**, normally on main.
3. Set the three switches, or enable **Build all eight combinations**.
4. Run the workflow and wait for successful completion.
5. Download the run's **vic20-pal-roms** artifact.

Manual runs need suitable repository access. Other users can download existing
public artifacts while signed in, or fork the repository and run their own
Actions. Artifacts expire after 90 days. Main-branch and pull-request builds
automatically produce all eight combinations.

The additional **universal_experimental** switch builds the experimental PAL/NTSC
pair as a separate `vic20-universal-8k-experimental` artifact. Automatic builds
also test that pair. It currently includes the fixes, rainbow and V2.26 heading;
the three stable switches do not change the experimental image. Read
[Universal Experimental](https://github.com/Soopahfly/Soopah-Rom-Vic20Enhanced/wiki/Universal-Experimental)
before installing it. Stable PAL artifacts and all eight combinations are unchanged.

## Options

| Switch | On | Off |
| --- | --- | --- |
| Fixes | Six KERNAL fixes and both BASIC changes | Original behaviour, including bugs |
| Rainbow | Left-hand stepped rainbow and aligned layout | Stock layout |
| Heading | `CBM BASIC V2.26` | `CBM BASIC V2` wording |

BASIC/KERNAL fixes stay together because their helper code shares ROM space.
The heading is cosmetic and does not enable fixes. Rainbow builds remove framing
asterisks and align the heading and memory count at column six. READY is on
row six and typing starts on row seven, below the stripes (zero-based).
With both screen choices disabled, the complete original heading/layout remain.

## All Combinations

| Folder | Fixes | Rainbow | Heading |
| --- | --- | --- | --- |
| fixes-off_rainbow-off_banner-off | Off | Off | Stock |
| fixes-on_rainbow-off_banner-off | On | Off | Stock |
| fixes-off_rainbow-on_banner-off | Off | On | Stock |
| fixes-on_rainbow-on_banner-off | On | On | Stock |
| fixes-off_rainbow-off_banner-on | Off | Off | V2.26 |
| fixes-on_rainbow-off_banner-on | On | Off | V2.26 |
| fixes-off_rainbow-on_banner-on | Off | On | V2.26 |
| fixes-on_rainbow-on_banner-on | On | On | V2.26 |

Stock behaviour with rainbow: fixes off, rainbow on, either heading.
Fixes with a completely stock screen: fixes on, rainbow off, heading off.
Everything off reproduces the production ROMs byte-for-byte.

## Files And Local Builds

Each folder contains `basic.901486-01.bin` (8 KB), `kernal.901486-07.bin`
(8 KB), `vic20-combined.bin` (16 KB, BASIC first), `manifest.json`,
`SHA256SUMS` and `README.txt`. Manifests record options, source commit,
sizes and hashes. The combined image is not an 8 KB chip replacement.
A separate verification artifact contains the test reports. Upload requires
successful tests.

Install Node.js, Python, cc65 and `requirements-test.txt`.

```sh
node scripts/build-variants.mjs --all
python tests/test_variants.py
```

Single choice:

```sh
node scripts/build-variants.mjs --fixes=true --rainbow=false --banner=false
python tests/test_variants.py
```

Outputs go to `dist/`. Tests exercise all combinations even when one download is
requested. `build/` holds the canonical assembled image; `roms/` holds the
default all-enabled release.

Variants start from production references and copy reviewed feature ranges from
freshly assembled commented source. Overlapping ranges and unexpected changes
fail the build. Stock and default reproduction are checked.
