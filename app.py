import html
import streamlit as st

from agent import analyze_dialogue, load_dataset_summary, load_knowledge, SIGNAL_TEXT

st.set_page_config(page_title="银龄盾｜对话核验助手", page_icon="🛡️", layout="centered")
st.markdown("""
<style>
  .stApp { background: #eaf6ff; }
  [data-testid="stMainBlockContainer"] { max-width: 900px; padding-top: 2.2rem; padding-bottom: 3rem; }
  [data-testid="stSidebar"] { background: #dff1ff; border-right: 1px solid #c9e3f7; }
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color: #29445f; font-size: .97rem; line-height: 1.65; }
  [data-testid="stSidebar"] h2 { color: #1e4f79; }
  div[data-testid="stTextArea"] textarea { border: 1px solid #bfd8eb; border-radius: 16px; background: #ffffff; line-height: 1.7; box-shadow: 0 4px 16px rgba(43,93,133,.06); }
  div[data-testid="stTextArea"] textarea:focus { border-color: #4c8ed9; box-shadow: 0 0 0 2px rgba(76,142,217,.14); }
  div.stButton > button[kind="primary"] { border: 0; border-radius: 12px; min-height: 3rem; background: linear-gradient(90deg,#2878c8,#3b9aa3); font-weight: 700; box-shadow: 0 5px 14px rgba(40,120,200,.18); }
  div.stButton > button[kind="primary"]:hover { border: 0; background: linear-gradient(90deg,#1f68b2,#2d858e); }
  div[data-testid="stExpander"] { border: 1px solid #d4e4f2; border-radius: 12px; background: #ffffff; }
  div[data-testid="stAlert"] { border-radius: 13px; }
  [data-testid="stSidebar"] [data-testid="stAlert"] { background: #fff9e8; border: 1px solid #f1dfaa; }
  [data-testid="stSidebar"] hr { border-color: #c5dfef; }
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong { color: #1e4f79; }
  code { color: #245b83 !important; }
</style>
<div style="display:flex;align-items:center;gap:16px;margin:0.2rem 0 0.4rem 0;">
  <div style="width:58px;height:58px;border-radius:18px;background:linear-gradient(145deg,#e6f4ff,#d8e8ff);display:flex;align-items:center;justify-content:center;font-size:36px;box-shadow:0 5px 16px rgba(44,105,180,.14);">🛡️</div>
  <div><div style="font-size:2.2rem;font-weight:750;line-height:1.2;color:#25364a;">银龄盾｜对话核验助手</div>
  <div style="font-size:1rem;color:#65758b;margin-top:5px;">让每一次核实更清楚、更安心</div></div>
</div>
""", unsafe_allow_html=True)
st.write("粘贴一段短信或聊天记录，看看其中是否出现需要暂停核实的风险信号。")
st.caption("本地规则原型，仅作风险提示；不会确认对方身份，也不会自动发送短信。")

summary = load_dataset_summary()
knowledge = load_knowledge()

with st.sidebar:
    st.header("使用提示")
    st.markdown("""
<div style="padding:15px 16px;margin:2px 0 14px;border-radius:16px;background:linear-gradient(135deg,#ffffff,#f2f9ff);border:1px solid #c8e1f4;box-shadow:0 4px 14px rgba(43,93,133,.06);">
<div style="font-size:1.08rem;font-weight:750;color:#1e4f79;margin-bottom:8px;">🧭 怎么使用</div>
<div>① 粘贴对话，尽量保留“对方：”和“我：”。</div>
<div>② 点击“开始核验”。</div>
<div>③ 查看建议、提醒依据和相关知识卡。</div>
<div>④ 需要时生成家属核实卡，由你决定是否分享。</div>
</div>
<div style="padding:15px 16px;margin:0 0 14px;border-radius:16px;background:linear-gradient(135deg,#ffffff,#f2f9ff);border:1px solid #c8e1f4;box-shadow:0 4px 14px rgba(43,93,133,.06);">
<div style="font-size:1.08rem;font-weight:750;color:#1e4f79;margin-bottom:8px;">📊 风险阶段</div>
<div><b>S0 普通说明</b>：暂未发现明显风险要求。</div>
<div><b>S1 身份待核</b>：先核实对方身份和业务。</div>
<div><b>S2 催促施压</b>：建议暂停并独立核实。</div>
<div><b>S3 外部操作</b>：如陌生链接、安装软件或共享屏幕。</div>
<div><b>S4 资金与认证</b>：如索要验证码、密码或要求转账。</div>
</div>
<div style="padding:15px 16px;margin:0 0 14px;border-radius:16px;background:linear-gradient(135deg,#ffffff,#f2f9ff);border:1px solid #c8e1f4;box-shadow:0 4px 14px rgba(43,93,133,.06);">
<div style="font-size:1.08rem;font-weight:750;color:#1e4f79;margin-bottom:8px;">🛡️ 页面功能</div>
<div>🔎 提醒依据：标出可疑原句、风险信号和出现阶段。</div>
<div>✅ 安全建议：提供清晰、可操作的核实步骤。</div>
<div>📚 相关知识卡：提供反诈资料和来源，方便查证。</div>
<div>👨‍👩‍👧 家属协同：生成核实卡，由用户自主决定是否分享。</div>
</div>
""", unsafe_allow_html=True)
    st.warning("不要输入真实验证码、密码、身份证号或银行卡号。")

st.markdown("### 💬 粘贴需要核实的对话")
st.caption("保留说话人和对话顺序，有助于系统逐轮分析。")
text = st.text_area("对话内容", height=220, label_visibility="collapsed", placeholder="对方：我是平台客服，您的会员今天会自动扣费。\n我：需要怎么处理？\n对方：请开启屏幕共享，我指导您取消。")
if st.button("开始核验", type="primary", use_container_width=True):
    if not text.strip():
        st.warning("请先粘贴一段对话。")
    else:
        st.session_state.result = analyze_dialogue(text, knowledge)
        st.session_state.show_family = False

result = st.session_state.get("result")
if result:
    st.divider()
    if result["status"] == "high_risk_signal": st.error(f"{result['status_text']}｜{result['max_stage']}：{result['stage_text']}")
    elif result["status"] == "needs_verification": st.warning(f"{result['status_text']}｜{result['max_stage']}：{result['stage_text']}")
    else: st.info(f"{result['status_text']}｜{result['max_stage']}：{result['stage_text']}")
    st.caption("阶段描述的是对话中出现的行为，不代表已确认诈骗；未发现信号也不代表绝对安全。")

    st.subheader("🧭 安全建议")
    for action in result["actions"]:
        st.markdown(f"<div style='padding:12px 16px;margin:8px 0;border-radius:12px;background:#eef8f4;border:1px solid #d5eee2;color:#244d3d;'>✅ {action}</div>", unsafe_allow_html=True)

    st.subheader("🔎 提醒依据")

    if result["evidence"]:
        for item in result["evidence"]:
            label = SIGNAL_TEXT.get(item["signal"], "身份或理由需要核实" if item["signal"] == "identity_or_reason_needs_verification" else item["signal"])
            st.markdown(f"**第 {item['turn_no']} 轮**　·　{item['speaker']}　·　`{label}`")
            safe_quote = html.escape(item["quote"])
            st.markdown(f"<div style='padding:14px 17px;margin:6px 0 15px;border-radius:12px;background:#f4f7fb;border-left:4px solid #75a9d4;color:#334155;line-height:1.8;'>{safe_quote}</div>", unsafe_allow_html=True)
    else: st.write("没有提取到明确触发规则的原句。")
    if result["signal_texts"]: st.write("识别信号：" + "、".join(result["signal_texts"]))
    if result["first_risk_turn"]: st.write(f"首次出现需核实信号：第 {result['first_risk_turn']} 轮。")
    if result["first_high_risk_turn"]: st.write(f"首次出现 S3/S4 高风险操作：第 {result['first_high_risk_turn']} 轮。")

    st.subheader("📚 相关知识卡")
    if result["knowledge"]:
        for card in result["knowledge"]:
            with st.expander(f"{card.get('title', '核实资料')}｜{card.get('publisher', '来源待核')}"):
                st.write(card.get("pattern_summary", ""))
                if card.get("official_advice"): st.write("**资料建议：**" + card["official_advice"])
                st.caption(f"发布日期：{card.get('publish_date') or '未注明'}；知识卡编号：{card.get('knowledge_id', '')}")
                if card.get("url", "").strip(): st.link_button("打开来源网页", card["url"])
    else: st.info("没有找到匹配且带来源链接的知识卡，请自行通过官方渠道核实。")

    st.subheader("👨‍👩‍👧 家属协同（可选）")
    if st.button("生成家属核实卡"): st.session_state.show_family = True
    if st.session_state.get("show_family"):
        st.text_area("检查后可自行复制给家人；系统不会自动发送", value=result["family_card"], height=140)

