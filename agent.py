"""银龄盾本地对话风险提示逻辑（规则原型，不是诈骗定性模型）。"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
STAGE_ORDER = {f"S{i}": i for i in range(5)}
STAGE_LABEL = {"S0": "no_obvious_signal", "S1": "needs_verification", "S2": "needs_verification", "S3": "high_risk_signal", "S4": "high_risk_signal"}
LABEL_TEXT = {"no_obvious_signal": "暂未发现明显风险信号", "needs_verification": "需要进一步核实", "high_risk_signal": "发现高风险操作信号"}
STAGE_TEXT = {"S0": "普通业务说明", "S1": "身份或理由待核验", "S2": "催促或施压", "S3": "引导外部操作", "S4": "资金或认证风险动作"}
SIGNAL_TEXT = {
    "credential_request": "索要验证码或密码", "transfer_request": "要求转账或垫付",
    "unknown_link": "引导打开链接或安装软件", "screen_sharing": "要求屏幕共享或远程控制",
    "urgency_pressure": "催促或施压", "secrecy_request": "要求保密或阻止核实",
    "biometric_request": "要求人脸、指纹等认证",
}
PATTERNS = {
    "credential_request": r"(?:把|将|请|麻烦|提供|报给|发给|告诉|念给|输入|填写|提交).{0,12}(?:短信)?验证码|(?:短信)?验证码.{0,12}(?:告诉|发给|提供|报给|念给|发送|输入)|(?:支付密码|银行卡密码|登录密码|交易密码).{0,10}(?:告诉|发给|提供|输入|填写)",
    "transfer_request": r"转账|汇款|转入|垫付|保证金|手续费|解冻费|验证金|安全账户|刷流水",
    "unknown_link": r"(?:点击|打开|访问|扫描|扫码).{0,18}(?:链接|网址|二维码|网页)|(?:下载|安装).{0,14}(?:软件|应用|APP)",
    "screen_sharing": r"屏幕共享|共享屏幕|远程控制|远程协助|远程操作",
    "urgency_pressure": r"马上|立刻|立即|限时|必须现在|不然|否则|逾期|冻结|马上扣费",
    "secrecy_request": r"(?:不要|不许|不能|别).{0,10}(?:告诉|联系|咨询|告知).{0,8}(?:家人|家属|警方|警察|银行|官方客服)|保密",
    "biometric_request": r"人脸识别|刷脸|指纹验证|录入指纹",
}
NEGATION = re.compile(r"(?:不要|不必|不需要|无需|不应|不能|切勿|勿|别|严禁|禁止|未曾|没有|并未).{0,12}$")
SPEAKER = re.compile(r"^\s*(?:(\d+)\s*[.、)）]\s*)?(对方|客服|来电者|商家|平台客服|用户|老人|我|家属|本人)\s*[：:]\s*(.*)$")
USER_NAMES = {"用户", "老人", "我", "家属", "本人"}


def read_csv(filename: str) -> list[dict[str, str]]:
    path = DATA_DIR / filename
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_knowledge() -> list[dict[str, str]]:
    return read_csv("knowledge.csv")


def load_dataset_summary() -> dict[str, Any]:
    dialogues, turns, knowledge = read_csv("dialogues.csv"), read_csv("turns.csv"), load_knowledge()
    return {"dialogues": len(dialogues), "turns": len(turns), "knowledge": len(knowledge),
            "split_status": "尚未划分锁定测试集" if any(r.get("split") == "unassigned" for r in dialogues) else "请核对切分字段"}


def parse_dialogue(text: str) -> list[dict[str, Any]]:
    result = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        match = SPEAKER.match(line)
        if match:
            _, speaker, utterance = match.groups()
            role = "user" if speaker in USER_NAMES else "other"
        else:
            speaker, utterance, role = "对方", line, "other"
        if utterance.strip():
            result.append({"turn_no": len(result) + 1, "speaker": speaker, "role": role, "text": utterance.strip()})
    if not result and text.strip():
        result.append({"turn_no": 1, "speaker": "对方", "role": "other", "text": text.strip()})
    return result


def _active_match(pattern: re.Pattern[str], text: str) -> re.Match[str] | None:
    for match in pattern.finditer(text):
        if NEGATION.search(text[max(0, match.start() - 14):match.start()]):
            continue
        return match
    return None


def retrieve_knowledge(text: str, signals: set[str], knowledge: list[dict[str, str]], limit: int = 3) -> list[dict[str, str]]:
    query = set(re.findall(r"退款|理赔|快递|物流|订单|会员|扣费|客服|售后|转账|验证码|屏幕共享", text))
    scored = []
    for card in knowledge:
        if not card.get("url", "").strip():
            continue
        tags = set(re.split(r"[|,，;；]", card.get("risk_tags", "")))
        searchable = " ".join(card.get(k, "") for k in ("title", "scenario", "pattern_summary", "official_advice"))
        score = 4 * len(signals & tags) + sum(term in searchable for term in query)
        if score:
            scored.append((score, card))
    scored.sort(key=lambda x: x[0], reverse=True)
    output, seen = [], set()
    for _, card in scored:
        group = card.get("source_group_id") or card.get("source_id") or card.get("knowledge_id")
        if group not in seen:
            output.append(card)
            seen.add(group)
        if len(output) >= limit:
            break
    return output


def safe_actions(signals: set[str], stage: str) -> list[str]:
    actions = []
    advice = {
        "credential_request": "不要提供验证码或密码；如果已经提供，尽快通过官方渠道联系银行或平台。",
        "transfer_request": "先停止转账或垫付；如已转出，尽快联系银行并通过官方渠道求助。",
        "unknown_link": "不要继续点击陌生链接或安装对方推荐的软件，请自行打开官方 App 查询。",
        "screen_sharing": "拒绝或立即结束屏幕共享/远程控制，并关闭相关权限。",
        "biometric_request": "不要按陌生联系人的要求进行刷脸、指纹或远程认证。",
        "urgency_pressure": "先暂停，不要因限时或扣费威胁而跳过核实。",
        "secrecy_request": "先暂停并联系可信任家人或官方渠道核实。",
    }
    for key, message in advice.items():
        if key in signals:
            actions.append(message)
    if not actions:
        actions.append("暂未发现已收录的明显风险动作；仍建议通过官方 App 或自行查到的联系方式核实。" if stage == "S0" else "不要仅凭对方自称的身份相信其说法，请通过官方渠道核实。")
    return actions


def make_family_card(status: str, stage: str, evidence: list[dict[str, Any]], actions: list[str]) -> str:
    quote = evidence[0]["quote"][:100] if evidence else "目前没有提取到明确风险原句"
    return f"我收到一段可能需要核实的对话，系统提示：{LABEL_TEXT[status]}（{stage}：{STAGE_TEXT[stage]}）。\n相关原句：{quote}\n建议：{actions[0]}\n你能陪我通过官方渠道一起核实吗？这只是风险提示，不代表已经确认诈骗。"


def analyze_dialogue(text: str, knowledge: list[dict[str, str]] | None = None) -> dict[str, Any]:
    turns, overall, evidence = parse_dialogue(text), set(), []
    max_stage, first_risk, first_high = "S0", None, None
    turn_results = []
    compiled = {key: re.compile(value) for key, value in PATTERNS.items()}
    for turn in turns:
        found, stage = [], "S0"
        # User statements count only as completed actions, not as requests made by a scammer.
        content = turn["text"]
        if turn["role"] == "user" and not re.search(r"(?:我|本人).{0,8}(?:已经|刚才|已)?(?:提供|发给|告诉|输入|转账|汇款|点开|安装|开启|打开|刷脸)", content):
            matches = []
        else:
            matches = [(name, _active_match(pattern, content)) for name, pattern in compiled.items()]
            matches = [(name, match) for name, match in matches if match]
        for name, match in matches:
            found.append(name); overall.add(name)
            s = "S4" if name in {"credential_request", "transfer_request", "biometric_request"} else "S3" if name in {"unknown_link", "screen_sharing"} else "S2"
            if STAGE_ORDER[s] > STAGE_ORDER[stage]: stage = s
            evidence.append({"turn_no": turn["turn_no"], "speaker": turn["speaker"], "signal": name, "quote": content, "matched_phrase": match.group(0)})
        if turn["role"] == "other" and re.search(r"(?:我是|这里是|自称).{0,15}(?:客服|平台|售后|银行|快递)", content) and stage == "S0":
            stage = "S1"
            evidence.append({"turn_no": turn["turn_no"], "speaker": turn["speaker"], "signal": "identity_or_reason_needs_verification", "quote": content, "matched_phrase": content})
        if stage != "S0" and first_risk is None: first_risk = turn["turn_no"]
        if STAGE_ORDER[stage] >= 3 and first_high is None: first_high = turn["turn_no"]
        if STAGE_ORDER[stage] > STAGE_ORDER[max_stage]: max_stage = stage
        turn_results.append({**turn, "stage": stage, "signals": [x[0] for x in matches]})
    status = {"S0": "no_obvious_signal", "S1": "needs_verification", "S2": "needs_verification", "S3": "high_risk_signal", "S4": "high_risk_signal"}[max_stage]
    actions = safe_actions(overall, max_stage)
    return {"status": status, "status_text": LABEL_TEXT[status], "max_stage": max_stage, "stage_text": STAGE_TEXT[max_stage],
            "signals": sorted(overall), "signal_texts": [SIGNAL_TEXT[s] for s in sorted(overall)], "evidence": evidence,
            "turns": turn_results, "first_risk_turn": first_risk, "first_high_risk_turn": first_high,
            "actions": actions, "knowledge": retrieve_knowledge(text, overall, knowledge if knowledge is not None else load_knowledge()),
            "family_card": make_family_card(status, max_stage, evidence, actions)}
