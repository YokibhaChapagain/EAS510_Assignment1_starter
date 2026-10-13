"""EAS 510 - Project 1: Rule functions for the Digital Forensics Apprentice.

Each rule compares one suspect image against one registered original and
returns a dict:

    {
        "rule": 1,
        "name": "Metadata",
        "fired": bool,          # True if the rule found supporting evidence
        "score": int,           # points awarded out of "out_of"
        "out_of": int,
        "note": "Size ratio 0.85",   # short human-readable metric
        "metric": 0.85,              # raw similarity measure in [0, 1]
    }

The points budgets are fixed by the assignment: Rule 1 = 30, Rule 2 = 30,
Rule 3 = 40. The detector sums them into a 0-100 confidence score.

These starter implementations are deliberately WEAK baselines (they hinge on
simple thresholds). Improving them is the assignment.

Reads are cached per path so one suspect against many originals does not
re-decode images needlessly.
"""

import os
from functools import lru_cache

import numpy as np
import cv2
from PIL import Image

#: Rule names used by SimpleDetector.evaluate() (V1).
RULES = ("rule1_metadata", "rule2_histogram", "rule3_template")


@lru_cache(maxsize=256)
def _arr(path):
    return cv2.imread(path)


@lru_cache(maxsize=256)
def _hist(path):
    img = _arr(path)
    if img is None:
        return None
    hists = []

    for i in range(3):
        hist = cv2.calcHist([img], [i], None, [32], [0, 256])
        cv2.normalize(hist, hist)
        hists.append(hist)
    return hists


def _downscale(img, max_dim=512):
    """Fit an image into `max_dim` before expensive cv2 work."""
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
    return img


@lru_cache(maxsize=256)
def _gray(path):
    img = _arr(path)
    if img is None:
        return None
    return _downscale(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))


@lru_cache(maxsize=256)
def _size(path):
    try:
        with Image.open(path) as img:
            return img.size
    except Exception:
        return None

#Detect JPEG/PNG from the file's actual header bytes
@lru_cache(maxsize=256)
def _file_type(path):
  try:
    with open(path, "rb") as f:
      header = f.read(8)

    if header.startswith(b"\xff\xd8"):
      return "jpeg"
    
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
      return "png"

    return "other"

  except Exception:
    return "unknown"

def rule1_metadata(target, input_path):
    """File size + dimensions. Compression and crops leave size fingerprints."""
    out = {"rule": 1, "name": "Metadata", "fired": False, "score": 0,
           "out_of": 30, "note": "Size ratio 0.00", "metric": 0.0}
    try:
        #File size similarity
        src_size = os.path.getsize(target["path"])
        in_size = os.path.getsize(input_path)
        size_ratio = min(src_size, in_size) / max(src_size, in_size)

        #Dimension similarity
        src_w, src_h = _size(target["path"]) or (0, 0)
        in_w, in_h = _size(input_path) or (0, 0)
        src_area = max(1,  src_w * src_h )
        in_area = max(1,in_w * in_h)
        area_ratio = min(src_area, in_area)/ max(src_area, in_area)

        #Actual file type
        src_type = _file_type(target["path"])
        in_type = _file_type(input_path)
        same_dimensions = (
          src_w == in_w and
          src_h == in_h and
          src_w > 0 and
          src_h > 0
        )
        format_changed = (
          src_type in {"jpeg", "png"} and
          in_type in {"jpeg", "png"} and
          src_type != in_type
        )
        metric = 0.5 * size_ratio + 0.5 * area_ratio

        if format_changed and same_dimensions:
          metric += 0.10
        metric = max(0.0, min(1.0,metric))
        out["metric"] = round(metric, 3)
        out["note"] = f"Size ratio {out['metric']:.2f}"
        if out["metric"] >= 0.6:
            out["fired"] = True
            out["score"] = int(round(out["out_of"] * out["metric"]))
    except Exception:
        pass
    return out


def rule2_histogram(target, input_path):
    """Color histogram correlation. Robust to crops and spatial changes."""
    out = {"rule": 2, "name": "Histogram", "fired": False, "score": 0,
           "out_of": 30, "note": "Correlation 0.00", "metric": 0.0}
    try:
        hs, hi = _hist(target["path"]), _hist(input_path)
        if hs is None or hi is None:
            return out

        correlations = []
        for src_hist, in_hist in zip(hs, hi):
            corr = cv2.compareHist(
              src_hist, 
              in_hist,
              cv2.HISTCMP_CORREL
            )
            correlations.append(corr)

        #Average similarities
        metric = float(np.mean(correlations))
        out["metric"] = round(max(0.0, min(1.0, metric)), 3)
        out["note"] = f"Correlation {out['metric']:.2f}"
        if out["metric"] >= 0.5:
            out["fired"] = True
            out["score"] = int(round(out["out_of"] * out["metric"]))
    except Exception:
        pass
    return out


def rule3_template(target, input_path):
    """Template matching. Detects when the suspect is contained in the original.

    cv2.matchTemplate needs the template (suspect) smaller than the target
    (original); on rotated/resized suspects this rule degrades fast. Fixing
    that becomes Rule 4 territory.
    """
    out = {"rule": 3, "name": "Template", "fired": False, "score": 0,
           "out_of": 40, "note": "Match score 0.00", "metric": 0.0}
    try:
        src = _arr(target["path"])
        nd = _arr(input_path)
        
        if src is None or nd is None:
            return out
        
        #Convert both to grayscale
        src_g = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
        nd_g = cv2.cvtColor(nd, cv2.COLOR_BGR2GRAY)

        src_h, src_w =  src_g.shape[:2]
        max_dim = 512

        #Downscale both using same scale factor
        if max(src_h, src_w) > max_dim:
          scale = max_dim / max(src_h, src_w)

          #Resize original
          new_src_w = int(src_w * scale)
          new_src_h = int(src_h * scale)

          src_g = cv2.resize(
            src_g,
            (new_src_w, new_src_h)
          )

          #Resize suspect with same scale
          nd_h, nd_w = nd_g.shape[:2]

          new_nd_w = int(nd_w * scale)
          new_nd_h = int(nd_h * scale)

          nd_g = cv2.resize(
            nd_g,
            (new_nd_w, new_nd_h)
          )
        
        if (
            nd_g.shape[0] > src_g.shape[0]
            or nd_g.shape[1] > src_g.shape[1]
        ):
            return out

       #Template matching
        res = cv2.matchTemplate(src_g, nd_g, cv2.TM_CCOEFF_NORMED)
        metric = float(res.max())
        out["metric"] = round(max(0.0, min(1.0, metric)), 3)
        out["note"] = f"Match score {out['metric']:.2f}"
        if out["metric"] >= 0.4:
            out["fired"] = True
            out["score"] = int(round(out["out_of"] * out["metric"]))
    except Exception:
        pass
    return out