"""Issue matching logic for comparing detected issues to ground truth."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from benchmark.schema import (
    BenchmarkResult,
    DetectedIssue,
    GroundTruth,
    GroundTruthIssue,
    MatchResult,
)


# Map Flamboyance event types to ground truth types
TYPE_ALIASES = {
    # Flamboyance types -> ground truth types
    "dead_end": ["dead_end", "hidden_element"],
    "broken_image": ["broken_image"],
    "slow_load": ["slow_load"],
    "rage_click": ["dead_end", "hidden_element", "random_failure"],
    "form_abandonment": ["form_error", "random_failure"],
    "unmet_goal": ["dead_end", "random_failure", "hidden_element"],
    "mobile_tap_target": ["mobile_tap_target"],
    "horizontal_scroll": ["mobile_tap_target"],
    "js_error": ["random_failure"],
    "network_error": ["random_failure"],
    "low_contrast": ["form_error"],
    "missing_label": ["misleading_affordance"],
}


def normalize_type(event_type: str) -> list[str]:
    """Get all ground truth types that could match this event type."""
    event_type = event_type.lower().replace("-", "_")
    return TYPE_ALIASES.get(event_type, [event_type])


def url_matches(detected_url: str, pattern: str) -> bool:
    """Check if a detected URL matches a ground truth URL pattern."""
    if not pattern:
        return True
    if not detected_url:
        return False
    
    # Normalize URLs
    detected_url = detected_url.lower().rstrip("/")
    pattern = pattern.lower().rstrip("/")
    
    # Check if pattern is in the URL path
    return pattern in detected_url


def text_similarity(text1: str, text2: str) -> float:
    """Compute similarity between two text strings."""
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def keyword_match_score(description: str, keywords: list[str]) -> float:
    """Score how many keywords appear in the description."""
    if not keywords:
        return 0.5  # Neutral if no keywords defined
    
    description_lower = description.lower()
    matches = sum(1 for kw in keywords if kw.lower() in description_lower)
    return matches / len(keywords)


def match_issue(
    detected: DetectedIssue,
    ground_truth_issues: list[GroundTruthIssue],
    already_matched: set[str],
) -> tuple[GroundTruthIssue | None, float]:
    """Find the best matching ground truth issue for a detected issue.
    
    Returns (matched_issue, score) or (None, 0) if no match.
    """
    best_match = None
    best_score = 0.0
    
    detected_types = normalize_type(detected.type)
    
    for gt in ground_truth_issues:
        # Skip already matched issues
        if gt.id in already_matched:
            continue
        
        # Type must match (with aliases)
        if gt.type not in detected_types:
            continue
        
        # URL must match pattern
        if not url_matches(detected.url, gt.url_pattern):
            continue
        
        # Compute match score based on description similarity and keywords
        desc_score = text_similarity(detected.description, gt.description)
        keyword_score = keyword_match_score(detected.description, gt.keywords)
        
        # Combined score (weighted)
        score = 0.4 * desc_score + 0.6 * keyword_score
        
        # Boost score if type matches exactly
        if detected.type.lower() == gt.type.lower():
            score += 0.2
        
        if score > best_score:
            best_score = score
            best_match = gt
    
    # Require minimum score for a match
    if best_score < 0.3:
        return None, 0.0
    
    return best_match, best_score


def compute_metrics(
    detected_issues: list[DetectedIssue],
    ground_truth: GroundTruth,
) -> BenchmarkResult:
    """Compute precision/recall metrics by matching detected issues to ground truth."""
    
    matches: list[MatchResult] = []
    matched_gt_ids: set[str] = set()
    
    # Match each detected issue to ground truth
    for detected in detected_issues:
        gt_match, score = match_issue(
            detected, ground_truth.issues, matched_gt_ids
        )
        
        if gt_match:
            matched_gt_ids.add(gt_match.id)
            matches.append(MatchResult(
                detected=detected,
                ground_truth=gt_match,
                matched=True,
                match_score=score,
            ))
        else:
            matches.append(MatchResult(
                detected=detected,
                ground_truth=None,
                matched=False,
                match_score=0.0,
            ))
    
    # Count metrics
    true_positives = len([m for m in matches if m.matched])
    false_positives = len([m for m in matches if not m.matched])
    false_negatives = len(ground_truth.issues) - true_positives
    
    return BenchmarkResult(
        app=ground_truth.app,
        tool="flamboyance",
        run_id="",
        detected_issues=detected_issues,
        ground_truth=ground_truth,
        matches=matches,
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
    )
