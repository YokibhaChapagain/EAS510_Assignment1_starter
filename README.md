# EAS 510 - Assignment 1: Digital Forensics Apprentice

A rule-based expert system that matches modified images back to their originals.

This is the **starter repository** for Project 1. Two repositories matter:

| Repository | Role |
|------------|------|
| `delveccj/EAS510_Assignment1_starter` (this repo) | Your **code** lives here. You will fork it, work in your fork, and push your final submission here. |
| `delveccj/EAS510_Assignment1` | The **dataset** (read-only). Clone it for the images; never commit it to your fork. |

## Setup on your Codio box.

```bash
# 1. Fork this repo on GitHub, then in your box:
git clone https://github.com/YOUR-USERNAME/EAS510_Assignment1_starter.git
cd EAS510_Assignment1_starter

# 2. Clone the read-only dataset as a sibling folder (images live there):
cd ~/workspace
git clone https://github.com/delveccj/EAS510_Assignment1.git

# 3. Install dependencies:
cd ~/workspace/EAS510_Assignment1_starter
python3 -m pip install -r requirements.txt

# 4. Point this box at YOUR fork (run once):
./setup_git.sh
```

## Repository layout

```
forensics_detective.py   SimpleDetector: register targets + find_best_match
rules.py                 Rule functions (Rule 1: Metadata, Rule 2: Histogram, Rule 3: Template)
test_system.py           Runs the detector over the data folders and writes results_*.txt
scripts/check_output_format.py   Validates a results file against the required format
setup_git.sh, submit.sh  One-time setup + commit/push helper ("backup button")
```

## The task in one paragraph

Implement three interpretable rules (metadata, color histogram, template matching)
that combine into a 0-100 confidence score. Run your system on `modified_images/`
and `random/` and save the full output as `results_v1.txt`. In Phase 2, run on
`hard/`, diagnose a systematic failure, add a **Rule 4**, and save
`results_v1_hard.txt` and `results_v2.txt`. Full instructions are in the Codio guide
and in the assignment PDF in UBLearns.

## Running

```bash
# Phase 1 (easy + random) -> results_v1.txt
python3 test_system.py --modified --random --output results_v1.txt

# Phase 1 on hard cases -> results_v1_hard.txt
python3 test_system.py --hard --output results_v1_hard.txt

# Phase 2 (everything) -> results_v2.txt
python3 test_system.py --modified --hard --random --output results_v2.txt

# Validate any results file against the required format:
python3 scripts/check_output_format.py results_v1.txt
```

The data folders are resolved from a sibling clone of `EAS510_Assignment1`.
If your data is elsewhere, pass `--data-dir /path/to/EAS510_Assignment1`.

## Output format (do not alter)

```
Processing: modified_image_01.jpg
Rule 1 (Metadata): FIRED - Size ratio 0.85 -> 20/30 points
Rule 2 (Histogram): FIRED - Correlation 0.92 -> 25/30 points
Rule 3 (Template): FIRED - Match score 0.76 -> 30/40 points
Final Score: 75/100 -> MATCH to original_03.jpg
```

## Backup doctrine

Your Codio box can be reset at any time. **Your fork on GitHub is the only safe
copy.** After every milestone run `./submit.sh "describe what you did"`. A box
restart never touches GitHub.

## License

Apache 2.0. See `LICENSE`.

## Observed weakness in V1: what failed and why
V1 performed well on the easier set, matching 57 out of 60 modified images while keeping all 15 random images rejected.
On the hard set, only 47 of 60 images were matched. A repeated pattern appeared in resized and crop-plus-resize cases. 
In 10 of those 13 rejected hard cases, Rule 3 contributed 0 points,while Rule 1 and 2 often still provided useful evidence. 
This shows that the main V1 weakness was template matching under scale changes, since cv2.matchTemplate() is sensitive to 
changes in the size of the suspect image.

## Design decision for V2: what Rule 4 is and why you chose it
Rule 4 uses multi-scale template matching by testing the suspect image at several different sizes and keeping the best match score.
This was chosen because many of V1 hard-case failures involved resizing or crop-plus-resize transformations, where normal template
matching often gave zero points. The V2 weighting was changed to 30/30/30/10 so that 10 points were moved from Rule 3, which showed 
repeated weakness, to the new scale-aware Rule 4.

## Effect of the change: accuracy before/after on easy vs hard
The easy-set performance stayed the same at 57/60 matched, while the hard-set result improved from 47/60 in V1 to 49/60 in V2. 
Rule 4 fired on 39 of the 60 hard images, showing that it was contributing evidence on many of the harder transformations. 
The random set still had 0 false accepts out of 15, so the added scale flexibility did not reduce rejection of unrelated images. 

## Trade-offs: what new costs or risks did Rule 4 introduce
Multi-scale matching requires several template comparisons instead of one, so it adds computation and introduces new choices
such as which scales to test and what threshold to use. Testing a denser set of scales actually reduced the hard-set result 
from 49 to 48 matches, so the simpler scale set was kept. V2 still rejected 11 hard cases, especially crop-plus-resize combinations,
and testing more scales could increase the chance of accidental matches, although the random set still produced zero false accepts.