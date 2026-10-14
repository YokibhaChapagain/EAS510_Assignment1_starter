"""EAS 510 - Project 1 - Phase 2: the V2 rule set.

Rules 1-3 are kept exactly as in `rules.py`. Your job is to ADD Rule 4 that
targets the systematic weakness you diagnosed from results_v1_hard.txt.

Constraint: the rules' `out_of` weights must still sum to 100 so the Final
Score stays on a /100 scale (the format validator enforces "Final Score:
<s>/100" equals the sum of the block's rule scores).

Example split that keeps the original spirit: Rules 1-3 -> 25/25/40 and
Rule 4 -> 10 (or trim the losers more aggressively).
"""

import cv2
import rules

#: Import the original rules and append your new one.
RULES = (
    "rule1_metadata",
    "rule2_histogram",
    "rule3_v2",
    "rule4_multiscale"
)

def rule3_v2(target, input_path):
    """Same Rule 3 logic, but weight is out of 30."""

    out = rules.rule3_template(target, input_path)
    out["out_of"] = 30
    if out["fired"]:
        out["score"] = int(round(30 * out["metric"]))
    else:
        out["score"] = 0

    return out

def rule4_multiscale(target, input_path):
    """Try template matching at multiple scales to handle resized suspects"""

    out = {
        "rule": 4,
        "name": "Multiscale",
        "fired": False,
        "score": 0,
        "out_of": 10,
        "note": "Best scale match 0.00",
        "metric": 0.0,
    }

    try:
      src = cv2.imread(target["path"])
      nd = cv2.imread(input_path)

      if src is None or nd is None:
        return out

      #Convert both to grayscale
      src_g = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
      nd_g = cv2.cvtColor(nd, cv2.COLOR_BGR2GRAY)

      #Downscale for speed
      src_h, src_w = src_g.shape[:2]
      if max(src_h, src_w) > 512:
        base_scale = 512 / max(src_h, src_w)

        src_g = cv2.resize(
          src_g,
          (
              int(src_w * base_scale),
              int(src_h * base_scale)
          )
        )

        nd_h, nd_w = nd_g.shape[:2]

        nd_g = cv2.resize(
          nd_g,
          (
            int(nd_w * base_scale),
            int(nd_h * base_scale)
          )
        )

      #Different suspect sizes
      scales = [0.75, 0.85, 1.0, 1.15, 1.33]
      best_metric = 0.0
      best_scale = None

      for scale in scales:
          new_w = int(nd_g.shape[1] * scale)
          new_h = int(nd_g.shape[0] * scale)

          #To avoid invalid sizes
          if new_w < 1 or new_h < 1:
            continue

          if(
              new_w > src_g.shape[1]
              or new_h > src_g.shape[0]
          ):
              continue

          #Resize suspect to this scale
          template = cv2.resize(
              nd_g,
              (new_w, new_h)
          )

          #Compare with original
          res = cv2.matchTemplate(
              src_g,
              template,
              cv2.TM_CCOEFF_NORMED
          )

          metric = float(res.max())

          if metric > best_metric:
              best_metric = metric
              best_scale = scale
      best_metric = max(0.0, min(1.0, best_metric))

      out["metric"] = round(best_metric, 3)

      if best_scale is not None:
        out["note"] = (
            f"Scale {best_scale:.2f}"
            f"match {out['metric']: .2f}"
        ) 

      if out["metric"] >= 0.55:
          out["fired"] = True
          out["score"] = int(
              round(out["out_of"] * out["metric"])
          )

    except Exception:
      pass

    return out