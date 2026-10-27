#!/usr/bin/env python3
"""Read-only preflight checks for auto-recommended Skill tasks.

The tool reports structural and filesystem facts. It does not decide whether
summary/rationale claims are semantically supported; that remains manual.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ACTIONS = {"create", "update", "rename"}
WRITE_TOOLS = {
    "Write",
    "Edit",
    "MultiEdit",
    "NotebookEdit",
    "apply_ops",
    "apply_patch",
    "create_file",
    "replace_string_in_file",
}
SKILL_NAME_RE = re.compile(r"^[a-z0-9-]+$")
DELIVERY_RE = re.compile(r"(提交|commit|push|推送|发布|交付|merge|合并)", re.I)
RISK_PATTERNS = [
    (re.compile(r"ignore\s+(the\s+)?(user|permission|confirmation|scope|instruction)", re.I), "ignore_instruction"),
    (re.compile(r"bypass|auto[- ]?approve|without\s+(confirmation|approval)|do\s+not\s+ask|no\s+need\s+to\s+ask", re.I), "skip_confirmation"),
    (re.compile(r"skip\s+(the\s+)?(confirmation|approval)", re.I), "skip_confirmation"),
    (re.compile(r"skip\s+(the\s+)?(validation|qa|verification|wait|test)", re.I), "skip_validation"),
    (re.compile(r"\b(rm\s+-rf|delete|overwrite|force[- ]push|--force|--yes)\b", re.I), "destructive_or_forced"),
    (re.compile(r"忽略.{0,12}(确认|验证|等待|权限|范围)"), "zh_ignore"),
    (re.compile(r"(无需|不必|跳过).{0,8}(确认|审批|批准)"), "zh_skip_confirmation"),
    (re.compile(r"(无需|不必|跳过).{0,8}(验证|校验|等待|QA|测试)"), "zh_skip_validation"),
    (re.compile(r"(直接|强制).{0,6}(覆盖|写入|删除)"), "zh_forced_write"),
    (re.compile(r"(扩大|更改|改变).{0,6}(文件范围|权限|确认流程)"), "zh_scope_change"),
]
PROHIBITION_RE = re.compile(r"(不执行|不要|不得|禁止|切勿|严禁|勿|忽略|do\s+not|don't|never|avoid)", re.I)
CLAUSE_BREAK_RE = re.compile(r"[。；;！!？?\n]")


def configure_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


def ascii_json(value):
    return json.dumps(value, ensure_ascii=True)


def die_usage(message):
    print("ERROR=" + ascii_json(message))
    print("RESULT FAIL")
    print("EXIT=2")
    return 2


def load_json(path, label):
    if path == "-":
        raw = sys.stdin.read()
        source = "stdin"
    else:
        try:
            raw = Path(path).read_text(encoding="utf-8-sig")
        except OSError as exc:
            raise ValueError(f"cannot read {label} {path}: {exc}")
        except UnicodeDecodeError as exc:
            raise ValueError(f"{label} {path} is not valid UTF-8: {exc}")
        source = path
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} {source} is not valid JSON: {exc}")
    if not isinstance(data, dict):
        raise ValueError(f"{label} {source} must be a JSON object")
    return data


def frontmatter_name(path):
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return None
    match = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*(\r?\n|$)", text, re.S)
    if not match:
        return None
    for line in match.group(1).splitlines():
        if line.startswith("name:"):
            return line[5:].strip().strip('"').strip("'")
    return None


def prohibited_context(text, start):
    clause_start = 0
    for match in CLAUSE_BREAK_RE.finditer(text, 0, start):
        clause_start = match.end()
    return PROHIBITION_RE.search(text, clause_start, start) is not None


def message_text(message):
    text = message.get("text") if isinstance(message, dict) else None
    return text if isinstance(text, str) else ""


def tool_list(message):
    tools = message.get("tools") if isinstance(message, dict) else None
    return tools if isinstance(tools, list) else []


def summarize_session(data):
    messages = data.get("messages")
    if not isinstance(messages, list):
        raise ValueError("session snapshot has no messages array")

    failed_assistant = 0
    failed_empty_assistant = 0
    successful_writes = 0
    failed_writes = 0
    write_names = []
    bash_calls = 0
    mcp_calls = 0
    user_resends = 0

    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        status = message.get("status")
        tools = tool_list(message)

        if role == "assistant" and status == "failed":
            failed_assistant += 1
            if not message_text(message).strip() and not tools:
                failed_empty_assistant += 1
                previous_user = None
                for back in range(index - 1, -1, -1):
                    candidate = messages[back]
                    if isinstance(candidate, dict) and candidate.get("role") == "user":
                        previous_user = message_text(candidate).strip()
                        break
                next_user = None
                for forward in range(index + 1, len(messages)):
                    candidate = messages[forward]
                    if isinstance(candidate, dict) and candidate.get("role") == "user":
                        next_user = message_text(candidate).strip()
                        break
                if previous_user is not None and next_user == previous_user:
                    user_resends += 1

        for tool in tools:
            if not isinstance(tool, dict):
                continue
            name = tool.get("name")
            tool_status = tool.get("status")
            if name in WRITE_TOOLS:
                if tool_status == "completed":
                    successful_writes += 1
                    write_names.append(name)
                elif tool_status == "failed":
                    failed_writes += 1
            if name == "Bash":
                bash_calls += 1
            if name == "mcp_call":
                mcp_calls += 1

    final_user = None
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            final_user = message
            break
    final_assistant = None
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "assistant":
            final_assistant = message
            break

    final_user_text = message_text(final_user)
    final_assistant_text = message_text(final_assistant)
    delivery_incomplete = bool(
        final_user_text
        and DELIVERY_RE.search(final_user_text)
        and final_assistant is not None
        and final_assistant.get("status") == "failed"
        and not final_assistant_text.strip()
    )

    return {
        "session_id": data.get("sessionId"),
        "title": data.get("title"),
        "revision": data.get("revision"),
        "runtime_state": data.get("runtimeState"),
        "active_turn": data.get("activeTurnId"),
        "has_more_before": data.get("hasMoreBefore"),
        "messages": len(messages),
        "failed_assistant": failed_assistant,
        "failed_empty_assistant": failed_empty_assistant,
        "user_resends": user_resends,
        "successful_writes": successful_writes,
        "failed_writes": failed_writes,
        "write_tools": ",".join(write_names) if write_names else "none",
        "bash_calls": bash_calls,
        "mcp_calls": mcp_calls,
        "final_user": final_user_text,
        "final_user_status": final_user.get("status") if final_user else None,
        "final_assistant_status": final_assistant.get("status") if final_assistant else None,
        "final_assistant_chars": len(final_assistant_text),
        "delivery_incomplete": delivery_incomplete,
        "zero_write": successful_writes == 0,
    }


def print_value(key, value):
    if isinstance(value, bool):
        print(f"{key}={'true' if value else 'false'}")
    elif value is None:
        print(f"{key}=none")
    elif isinstance(value, str):
        print(f"{key}={ascii_json(value)}")
    else:
        print(f"{key}={value}")


def main():
    configure_stdout()
    parser = argparse.ArgumentParser(
        description="Read-only preflight checks for a Skill recommendation JSON and session snapshot."
    )
    parser.add_argument("--recommendation-json", default="-", help="recommendation JSON path or - for stdin")
    parser.add_argument("--session", required=True, help="read_chat_session snapshot JSON path")
    parser.add_argument("--target-dir", required=True, help="target Skill directory")
    parser.add_argument("--skills-root", action="append", default=[], help="allowed Skill root (repeatable)")
    args = parser.parse_args()

    try:
        recommendation = load_json(args.recommendation_json, "recommendation")
        session = load_json(args.session, "session")
        session_summary = summarize_session(session)
    except ValueError as exc:
        return die_usage(str(exc))

    fields = {key: recommendation.get(key) for key in ("skillName", "action", "summary", "rationale")}
    missing = [
        key
        for key, value in fields.items()
        if not isinstance(value, str) or not value.strip()
    ]
    name = fields["skillName"] if isinstance(fields["skillName"], str) else ""
    action = fields["action"] if isinstance(fields["action"], str) else ""

    target = Path(args.target_dir).expanduser()
    target_exists = target.exists()
    target_skill_md = target / "SKILL.md"
    target_skill_exists = target_skill_md.is_file()
    target_name = target.name
    name_match = bool(name) and target_name == name
    name_match_case_insensitive = bool(name) and target_name.lower() == name.lower()

    action_conflict = "NONE"
    if action == "create" and target_exists:
        action_conflict = "CREATE_TARGET_EXISTS"
    elif action == "update" and not target_exists:
        action_conflict = "UPDATE_TARGET_ABSENT"
    elif action == "rename":
        action_conflict = "RENAME_MANUAL"
    elif action not in ACTIONS:
        action_conflict = "UNSUPPORTED_ACTION"

    frontmatter = frontmatter_name(target_skill_md) if target_skill_exists else None
    if frontmatter is None:
        frontmatter_match = "unknown"
    else:
        frontmatter_match = "true" if frontmatter == name else "false"

    roots = [Path(root).expanduser() for root in args.skills_root]
    scope = "NO_ROOTS"
    duplicates = []
    if roots:
        scope = "OUTSIDE"
        for root in roots:
            try:
                target.resolve().relative_to(root.resolve())
                scope = "INSIDE"
            except (OSError, ValueError):
                pass
            duplicate = root / name if name else None
            if duplicate and duplicate.exists():
                try:
                    same = duplicate.resolve() == target.resolve()
                except OSError:
                    same = False
                if not same:
                    duplicates.append(str(duplicate))

    risk_hits = []
    for field in ("summary", "rationale"):
        text = fields[field] if isinstance(fields[field], str) else ""
        for pattern, label in RISK_PATTERNS:
            for match in pattern.finditer(text):
                if prohibited_context(text, match.start()):
                    continue
                risk_hits.append(f"{field}:{label}")
                break
    risk_hits = list(dict.fromkeys(risk_hits))

    invalid_frontmatter = bool(target_skill_exists and frontmatter is None)
    fail = bool(
        missing
        or not SKILL_NAME_RE.match(name)
        or action_conflict != "NONE"
        or not name_match
        or frontmatter_match == "false"
        or invalid_frontmatter
        or (target_exists and not target_skill_exists)
        or (roots and scope != "INSIDE")
    )

    print_value("REC_NAME", name)
    print_value("REC_ACTION", action)
    print_value("REC_SUMMARY_CHARS", len(fields["summary"]) if isinstance(fields["summary"], str) else 0)
    print_value("REC_RATIONALE_CHARS", len(fields["rationale"]) if isinstance(fields["rationale"], str) else 0)
    print_value("MISSING_FIELDS", ",".join(missing) if missing else "none")
    print_value("NAME_PATTERN", "ok" if SKILL_NAME_RE.match(name) else "invalid")
    print_value("TARGET", str(target))
    print_value("TARGET_EXISTS", target_exists)
    print_value("TARGET_SKILL_MD", target_skill_exists)
    print_value("TARGET_NAME", target_name)
    print_value("NAME_MATCH", name_match)
    print_value("NAME_MATCH_CASE_INSENSITIVE", name_match_case_insensitive)
    print_value("FRONTMATTER_NAME", frontmatter if frontmatter is not None else "none")
    print_value("FRONTMATTER_MATCH", frontmatter_match)
    print_value("ACTION_CONFLICT", action_conflict)
    print_value("SCOPE", scope)
    print_value("DUPLICATE_ROOTS", ";".join(duplicates) if duplicates else "none")
    print_value("INSTRUCTION_RISK", ";".join(risk_hits) if risk_hits else "none")

    print_value("SESSION_ID", session_summary["session_id"])
    print_value("SESSION_TITLE", session_summary["title"])
    print_value("SESSION_REVISION", session_summary["revision"])
    print_value("SESSION_RUNTIME_STATE", session_summary["runtime_state"])
    print_value("SESSION_ACTIVE_TURN", session_summary["active_turn"])
    print_value("SESSION_HAS_MORE_BEFORE", session_summary["has_more_before"])
    print_value("SESSION_MESSAGES", session_summary["messages"])
    print_value("SESSION_FAILED_ASSISTANT", session_summary["failed_assistant"])
    print_value("SESSION_FAILED_EMPTY_ASSISTANT", session_summary["failed_empty_assistant"])
    print_value("SESSION_USER_RESENDS", session_summary["user_resends"])
    print_value("SESSION_SUCCESSFUL_WRITES", session_summary["successful_writes"])
    print_value("SESSION_FAILED_WRITES", session_summary["failed_writes"])
    print_value("SESSION_WRITE_TOOLS", session_summary["write_tools"])
    print_value("SESSION_BASH_CALLS", session_summary["bash_calls"])
    print_value("SESSION_MCP_CALLS", session_summary["mcp_calls"])
    print_value("SESSION_FINAL_USER", session_summary["final_user"])
    print_value("SESSION_FINAL_USER_STATUS", session_summary["final_user_status"])
    print_value("SESSION_FINAL_ASSISTANT_STATUS", session_summary["final_assistant_status"])
    print_value("SESSION_FINAL_ASSISTANT_CHARS", session_summary["final_assistant_chars"])
    print_value("SESSION_DELIVERY_INCOMPLETE", session_summary["delivery_incomplete"])
    print_value("SESSION_ZERO_WRITE", session_summary["zero_write"])
    print_value("SEMANTIC_CHECK", "MANUAL")
    print(f"RESULT {'FAIL' if fail else 'PASS'}")
    print(f"EXIT={1 if fail else 0}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
