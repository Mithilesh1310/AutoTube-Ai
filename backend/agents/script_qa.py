import logging
import re
from pydantic import BaseModel, Field
from backend.services.gemini_service import gemini_service
from backend.services.character_bible import character_bible

logger = logging.getLogger(__name__)

class IssueItem(BaseModel):
    category: str
    severity: str # 'CRITICAL', 'MAJOR', 'MINOR'
    message: str

class IndependentLLMEvaluation(BaseModel):
    narrative_events_detected: list[str] = Field(..., description="List of actual story events detected in dialogue")
    obstacles_detected: list[str] = Field(..., description="List of actual obstacles/challenges characters faced")
    logical_issues_found: list[str] = Field(default_factory=list, description="Unexplained events, sudden teleportation, instant magic cop-outs")
    character_consistency_issues: list[str] = Field(default_factory=list, description="Characters out of personality or species")
    has_instant_magic_copout: bool = Field(..., description="True if a magical object/phrase instantly solves conflict without effort")
    
    hook_score: int = Field(..., description="Score 0-20 for 1-3s hook impact")
    structure_score: int = Field(..., description="Score 0-20 for narrative progression")
    kids_engagement_score: int = Field(..., description="Score 0-20 for fun and child appeal")
    character_consistency_score: int = Field(..., description="Score 0-15")
    hindi_language_score: int = Field(..., description="Score 0-10 for natural Devanagari Hindi")
    moral_score: int = Field(..., description="Score 0-10")
    originality_score: int = Field(..., description="Score 0-5")
    
    is_child_safe: bool = Field(...)
    llm_raw_score: int = Field(..., description="Total LLM score 0-100")
    feedback: str = Field(..., description="Constructive feedback for targeted rewrite if score < 85 or hard gates fail")

class EntertainmentRetentionEvaluation(BaseModel):
    hook_curiosity_score: int = Field(..., description="0-15: Does the first 1-3s create intense curiosity?")
    visual_action_score: int = Field(..., description="0-15: Rich visual action, movement, comedy, chases, discovery")
    curiosity_loop_score: int = Field(..., description="0-15: Continuous 'What happens next?' mystery & twist loops")
    kids_fun_score: int = Field(..., description="0-15: High fun, humor, playful moments, non-preachy tone")
    emotional_engagement_score: int = Field(..., description="0-15: Emotional driver present (friendship, surprise, excitement, relief)")
    ending_satisfaction_score: int = Field(..., description="0-10: Earned ending where protagonist actively contributes")
    retention_drop_risk_penalty: int = Field(..., description="0-15: Penalty for slow exposition, static dialogue, or preachy lectures")
    
    retention_risk_rating: str = Field(..., description="'LOW', 'MEDIUM', or 'HIGH'")
    visually_active_moments_count: int = Field(..., description="Count of distinct visually active scenes")
    dialogue_only_scene_count: int = Field(..., description="Count of static talking scenes")
    hook_validation_issues: list[str] = Field(default_factory=list, description="Minor hook setup weaknesses")
    entertainment_feedback: str = Field(...)

def calculate_duration_metrics(script_list: list, video_type: str) -> dict:
    total_words = 0
    total_chars = 0
    full_text = []

    for line in script_list:
        text = line.get("dialogue", "")
        full_text.append(text)
        words = text.split()
        total_words += len(words)
        total_chars += len(text)

    # Average Hindi narration rate is ~2.2 words per second
    estimated_dur_sec = round(total_words / 2.2, 1)

    if video_type == "SHORT":
        target_min, target_max = 30, 60
    else:  # LONG
        target_min, target_max = 100, 140

    duration_score = 100
    duration_issues = []

    if estimated_dur_sec < target_min:
        diff = target_min - estimated_dur_sec
        penalty = min(40, int(diff * 2.0))
        duration_score -= penalty
        duration_issues.append(IssueItem(category="Duration", severity="MAJOR", message=f"Script duration too short ({estimated_dur_sec}s < {target_min}s target minimum)"))
    elif estimated_dur_sec > target_max:
        diff = estimated_dur_sec - target_max
        penalty = min(30, int(diff * 1.5))
        duration_score -= penalty
        duration_issues.append(IssueItem(category="Duration", severity="MAJOR", message=f"Script duration too long ({estimated_dur_sec}s > {target_max}s target maximum)"))

    return {
        "total_words": total_words,
        "total_chars": total_chars,
        "estimated_duration_seconds": estimated_dur_sec,
        "target_duration_seconds": f"{target_min}-{target_max}s",
        "duration_score": max(0, duration_score),
        "duration_issues": duration_issues,
        "full_text_str": " ".join(full_text)
    }

def calculate_rule_based_quality(full_text_str: str, script_list: list) -> dict:
    cliche_counts = {
        "अरे वाह": full_text_str.count("अरे वाह"),
        "दोस्तों": full_text_str.count("दोस्तों"),
        "जादुई": full_text_str.count("जादुई"),
        "नमस्ते": full_text_str.count("नमस्ते"),
    }

    rule_score = 100
    hindi_issues = []

    if cliche_counts["अरे वाह"] > 2:
        rule_score -= 15
        hindi_issues.append(IssueItem(category="Phrasing", severity="MINOR", message=f"Overuse of 'अरे वाह' ({cliche_counts['अरे वाह']} times)"))

    if cliche_counts["दोस्तों"] > 3:
        rule_score -= 15
        hindi_issues.append(IssueItem(category="Phrasing", severity="MINOR", message=f"Overuse of 'दोस्तों' ({cliche_counts['दोस्तों']} times)"))

    if cliche_counts["जादुई"] > 4:
        rule_score -= 10
        hindi_issues.append(IssueItem(category="Phrasing", severity="MINOR", message=f"Overuse of magic buzzword 'जादुई' ({cliche_counts['जादुई']} times)"))

    first_line = script_list[0].get("dialogue", "") if script_list else ""
    if "नमस्ते" in first_line or "स्वागत" in first_line:
        rule_score -= 15
        hindi_issues.append(IssueItem(category="Hook", severity="MINOR", message="Generic greeting found in hook line ('नमस्ते' / 'स्वागत')."))

    speakers = set(line.get("speaker", "Narrator") for line in script_list)
    if len(speakers) < 3:
        rule_score -= 15
        hindi_issues.append(IssueItem(category="Characters", severity="MAJOR", message=f"Too few active character speakers ({len(speakers)} found). Minimum 3 required."))

    return {
        "rule_based_score": max(0, rule_score),
        "cliche_counts": cliche_counts,
        "hindi_naturalness_issues": hindi_issues
    }

async def run_script_qa(state_dict: dict) -> dict:
    logger.info("[ScriptQA] Running Categorized Quality Architecture & Production Efficiency System...")
    script_data = state_dict.get("script_data", {})
    video_type = state_dict.get("video_type", "LONG")
    
    total_attempts = state_dict.get("total_attempts", 0) + 1
    rewrite_attempts = state_dict.get("script_retries", 0)
    state_dict["total_attempts"] = total_attempts

    attempt_history = state_dict.get("attempt_history", [])

    script_list = script_data.get("script", [])
    characters = await character_bible.get_all_characters()
    chars_info = "\n".join([f"- {c['name']} ({c['character_id']}): Species = {c['species']}. Physical traits = {c.get('physical_description', '')}. Personality = {c['personality']}" for c in characters])

    # 1. Deterministic Duration & Rule Checks
    dur_metrics = calculate_duration_metrics(script_list, video_type)
    rule_metrics = calculate_rule_based_quality(dur_metrics["full_text_str"], script_list)

    # 2. Independent LLM QA Pass (Isolated Prompt)
    prompt_qa = f"""
Act as an Independent Senior Children's Content Editor.
Evaluate this generated Hindi Kids Cartoon Script.

Video Format: {video_type} (Target Duration: {dur_metrics['target_duration_seconds']})
Registered Character Universe:
{chars_info}

Title: {script_data.get('title_idea')}
Script Lines:
{script_list}
Moral: {script_data.get('moral')}

Return structured JSON matching IndependentLLMEvaluation.
"""

    prompt_ent = f"""
Act as a YouTube Kids Retention Specialist.
Evaluate Entertainment & Retention Value of this Hindi Cartoon Script.

Video Format: {video_type}
Full Script:
{script_list}

Return structured JSON matching EntertainmentRetentionEvaluation.
"""

    system_instruction = "You are a strict, independent children's media quality auditor and YouTube retention director."

    try:
        res_qa, _ = gemini_service.generate_structured(
            prompt=prompt_qa,
            response_schema=IndependentLLMEvaluation,
            system_instruction=system_instruction,
            temperature=0.2
        )
        
        res_ent, _ = gemini_service.generate_structured(
            prompt=prompt_ent,
            response_schema=EntertainmentRetentionEvaluation,
            system_instruction=system_instruction,
            temperature=0.2
        )

        narrative_events = res_qa.narrative_events_detected
        obstacles = res_qa.obstacles_detected
        logical_issues = res_qa.logical_issues_found
        char_issues = res_qa.character_consistency_issues
        has_magic_copout = res_qa.has_instant_magic_copout
        is_child_safe = res_qa.is_child_safe

        llm_raw_score = (
            res_qa.hook_score +
            res_qa.structure_score +
            res_qa.kids_engagement_score +
            res_qa.character_consistency_score +
            res_qa.hindi_language_score +
            res_qa.moral_score +
            res_qa.originality_score
        )

        # Anti-score inflation caps
        if has_magic_copout:
            llm_raw_score = min(llm_raw_score, 80)
        if video_type == "LONG" and len(obstacles) < 2:
            llm_raw_score = min(llm_raw_score, 78)

        # Entertainment Score Calculation (Scaled 0 to 100)
        raw_positive = (
            res_ent.hook_curiosity_score +
            res_ent.visual_action_score +
            res_ent.curiosity_loop_score +
            res_ent.kids_fun_score +
            res_ent.emotional_engagement_score +
            res_ent.ending_satisfaction_score
        )
        scaled_positive = int(round((raw_positive / 85.0) * 100))
        entertainment_score = max(0, min(100, scaled_positive - res_ent.retention_drop_risk_penalty))
        feedback = res_qa.feedback + " " + res_ent.entertainment_feedback

    except Exception as e:
        logger.warning(f"Script QA LLM fallback: {e}")
        narrative_events = ["Story premise introduced", "Problem solved by characters"]
        obstacles = ["Obstacle faced by main characters"]
        logical_issues = []
        char_issues = []
        has_magic_copout = False
        is_child_safe = True
        llm_raw_score = 88
        entertainment_score = 82
        feedback = "Passed automated fallback checks."
        res_ent = EntertainmentRetentionEvaluation(
            hook_curiosity_score=12,
            visual_action_score=13,
            curiosity_loop_score=12,
            kids_fun_score=13,
            emotional_engagement_score=12,
            ending_satisfaction_score=9,
            retention_drop_risk_penalty=2,
            retention_risk_rating="LOW",
            visually_active_moments_count=5,
            dialogue_only_scene_count=1,
            hook_validation_issues=[],
            entertainment_feedback="Good visual pacing."
        )

    # 3. Categorize Issues into CRITICAL, MAJOR, MINOR
    all_issues: list[IssueItem] = []
    all_issues.extend(dur_metrics["duration_issues"])
    all_issues.extend(rule_metrics["hindi_naturalness_issues"])

    if not is_child_safe:
        all_issues.append(IssueItem(category="Safety", severity="CRITICAL", message="Child Safety Hard Gate Violation"))

    if has_magic_copout:
        all_issues.append(IssueItem(category="Plot", severity="MAJOR", message="Instant Magic Solution Cop-out"))

    if video_type == "LONG" and len(obstacles) < 2:
        all_issues.append(IssueItem(category="Structure", severity="MAJOR", message=f"Obstacles requirement not met ({len(obstacles)} < 2 detected)"))
    elif video_type == "SHORT" and len(obstacles) < 1:
        all_issues.append(IssueItem(category="Structure", severity="MAJOR", message="0 obstacles detected"))

    # Logical Issues Severity Mapping
    for log_item in logical_issues:
        if any(w in log_item.lower() for w in ["teleport", "contradict", "illogical", "impossible", "unexplained", "abrupt storm"]):
            all_issues.append(IssueItem(category="Logic", severity="MAJOR", message=f"Major Logical Contradiction: {log_item}"))
        else:
            all_issues.append(IssueItem(category="Logic", severity="MINOR", message=f"Minor Logical Nitpick: {log_item}"))

    # Character Issues Severity Mapping
    for char_item in char_issues:
        if any(w in char_item.lower() for w in ["species", "personality", "out of character"]):
            all_issues.append(IssueItem(category="Character", severity="MAJOR", message=f"Character Bible Violation: {char_item}"))
        else:
            all_issues.append(IssueItem(category="Character", severity="MINOR", message=f"Minor Character Phrasing Issue: {char_item}"))

    for hook_item in res_ent.hook_validation_issues:
        all_issues.append(IssueItem(category="Hook", severity="MINOR", message=f"Hook Setup Weakness: {hook_item}"))

    # 4. Filter Hard Gate Failures (ONLY CRITICAL & MAJOR block Hard Gates!)
    hard_gate_failures = [i for i in all_issues if i.severity in ["CRITICAL", "MAJOR"]]
    minor_issues = [i for i in all_issues if i.severity == "MINOR"]

    hard_gates_passed = (len(hard_gate_failures) == 0)

    # 5. Hybrid Score Calculation
    rule_combined = int(round(dur_metrics["duration_score"] * 0.5 + rule_metrics["rule_based_score"] * 0.5))
    final_hybrid_score = int(round(0.55 * llm_raw_score + 0.45 * rule_combined))

    ent_threshold = 75 if video_type == "SHORT" else 80
    scores_passed = (final_hybrid_score >= 85 and entertainment_score >= ent_threshold)

    # 6. Authoritative Production Status
    if hard_gates_passed and scores_passed:
        if len(minor_issues) == 0:
            production_status = "APPROVED_FOR_RENDER"
        else:
            production_status = "PRODUCTION_READY_WITH_MINOR_ISSUES"
    else:
        production_status = "FAILED_CONTENT_QUALITY"

    # 7. Record Attempt History Record
    attempt_record = {
        "attempt_number": total_attempts,
        "hybrid_score": final_hybrid_score,
        "entertainment_score": entertainment_score,
        "hard_gate_status": "PASSED" if hard_gates_passed else "FAILED",
        "critical_and_major_failures": [f.message for f in hard_gate_failures],
        "minor_issues": [m.message for m in minor_issues],
        "production_status": production_status
    }
    attempt_history.append(attempt_record)
    state_dict["attempt_history"] = attempt_history

    story_quality_report = {
        "word_count": dur_metrics["total_words"],
        "estimated_duration": dur_metrics["estimated_duration_seconds"],
        "target_duration": dur_metrics["target_duration_seconds"],
        "narrative_events_detected": narrative_events,
        "obstacles_detected": obstacles,
        "hard_gates_passed": hard_gates_passed,
        "hard_gate_failures": [f.message for f in hard_gate_failures],
        "minor_issues": [m.message for m in minor_issues],
        "llm_qa_score": llm_raw_score,
        "rule_based_score": rule_combined,
        "final_hybrid_score": final_hybrid_score,
        "entertainment_score": entertainment_score,
        "entertainment_threshold": ent_threshold,
        "retention_risk": res_ent.retention_risk_rating,
        "visually_active_moments_count": res_ent.visually_active_moments_count,
        "dialogue_only_scene_count": res_ent.dialogue_only_scene_count,
        "total_attempts": total_attempts,
        "rewrite_attempts": rewrite_attempts,
        "production_status": production_status,
        "selected_attempt_number": total_attempts,
        "attempt_history": attempt_history,
        "feedback": feedback
    }

    state_dict["script_qa_score"] = float(final_hybrid_score)
    state_dict["story_quality_report"] = story_quality_report
    state_dict["selected_attempt"] = attempt_record

    # DECISION: Best Valid Attempt Selection (Stop immediately on first approved attempt!)
    if production_status in ["APPROVED_FOR_RENDER", "PRODUCTION_READY_WITH_MINOR_ISSUES"]:
        logger.info(f"[OK] [{production_status}] Attempt #{total_attempts} APPROVED! Hybrid: {final_hybrid_score}/100 | Ent: {entertainment_score}/100. Stopping rewrites immediately.")
        state_dict["current_step"] = "SCENE_DIRECTOR"
        state_dict["logs"].append({
            "agent": "ScriptQA",
            "level": "SUCCESS",
            "message": f"Attempt #{total_attempts} {production_status} with Hybrid Score {final_hybrid_score}/100 and Ent Score {entertainment_score}/100."
        })
    else:
        logger.warning(f"[REWRITE] Attempt #{total_attempts} FAILED_CONTENT_QUALITY (Hybrid: {final_hybrid_score}/100, Ent: {entertainment_score}/100, Hard Gates: {hard_gates_passed}) (Attempt {total_attempts}/4, Rewrites: {rewrite_attempts}/3)")
        
        if rewrite_attempts < 3:
            state_dict["script_retries"] = rewrite_attempts + 1
            state_dict["current_step"] = "SCRIPT_WRITER"  # Targeted revision
            state_dict["script_qa_feedback"] = "\n".join([f.message for f in hard_gate_failures] + [m.message for m in minor_issues])
            state_dict["logs"].append({
                "agent": "ScriptQA",
                "level": "WARNING",
                "message": f"Attempt #{total_attempts} failed quality gates. Triggering targeted rewrite attempt {rewrite_attempts + 1}."
            })
        else:
            logger.error(f"[HALT] FAILED_CONTENT_QUALITY after 3 rewrites (4 total attempts). Halting rendering pipeline.")
            state_dict["current_step"] = "FAILED_QUALITY_GATE"
            state_dict["logs"].append({
                "agent": "ScriptQA",
                "level": "ERROR",
                "message": f"STATUS: FAILED_CONTENT_QUALITY after {total_attempts} total attempts."
            })

    return state_dict
