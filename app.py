import html
import streamlit.components.v1 as components

import streamlit as st

from agent import SIGNAL_TEXT, analyze_dialogue, load_dataset_summary, load_knowledge

st.set_page_config(page_title="银龄盾｜对话核验助手", page_icon="🛡️", layout="wide")
st.markdown("""
<style>
  :root { --ink:#17324d; --muted:#587087; --line:#d7e4ec; --blue:#1e6da1; --teal:#18857e; }
  .stApp { background:linear-gradient(145deg,#eaf4f8 0%,#f5f8f6 54%,#edf3f8 100%); color:var(--ink); }
  header[data-testid="stHeader"] { background:transparent; }
  [data-testid="stMainBlockContainer"] { max-width:1220px; padding-top:2.2rem; padding-bottom:3rem; }
  [data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] { font-size:1.16rem; line-height:1.75; color:#29445b; }
  [data-testid="stMainBlockContainer"] h2, [data-testid="stMainBlockContainer"] h3 { color:#173f63; letter-spacing:.01em; }
  [data-testid="stSidebar"] { background:#edf5f8; border-right:1px solid #d3e2e9; }
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color:#29445f; font-size:1.08rem; line-height:1.8; }
  [data-testid="stSidebar"] h2 { color:#1e4f79; }
  div[data-testid="stTextArea"] textarea { border:2px solid #c6d9e4; border-radius:16px; background:#fff; line-height:1.8; font-size:1.22rem; color:#17324d; padding:16px 18px; box-shadow:0 8px 24px rgba(35,75,100,.06); }
  div[data-testid="stTextArea"] textarea:focus { border-color:#3486b1; box-shadow:0 0 0 3px rgba(52,134,177,.16); }
  div.stButton > button[kind="primary"] { border:0; border-radius:14px; min-height:3.35rem; background:linear-gradient(100deg,#1e6da1,#18857e); color:#fff; font-size:1.2rem; font-weight:750; box-shadow:0 8px 20px rgba(30,109,161,.18); }
  div.stButton > button[kind="primary"]:hover { border:0; background:linear-gradient(100deg,#185b89,#126e69); color:#fff; }
  div.stButton > button:not([kind="primary"]), .stLinkButton a { border-radius:12px; min-height:2.8rem; font-size:1.05rem; }
  div[data-testid="stExpander"] { border:1px solid #d4e4ec; border-radius:14px; background:#fff; box-shadow:0 4px 14px rgba(35,75,100,.04); }
  div[data-testid="stExpander"] summary { font-size:1.08rem; font-weight:650; }
  div[data-testid="stVerticalBlockBorderWrapper"] { border:1px solid #d7e4ec; border-radius:21px; background:rgba(255,255,255,.94); box-shadow:0 12px 30px rgba(35,75,100,.055); padding:10px 15px; }
  div[data-testid="stAlert"] { border-radius:15px; font-size:1.12rem; padding:14px 18px; }
  [data-testid="stSidebar"] [data-testid="stAlert"] { background:#fff8e8; border:1px solid #eddda9; }
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong { color:#1e4f79; }
  [data-testid="stSidebar"] hr { border-color:#d5e3e9; }
  [data-testid="stSidebar"] h2 { font-size:1.55rem; }
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] div[style*="border-radius:17px"] { background:linear-gradient(145deg,#f9fcff,#eaf5ff)!important; border-color:#c6deef!important; box-shadow:0 7px 20px rgba(40,99,140,.06)!important; }
  [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] div[style*="border-radius:17px"] div { margin-bottom:3px; }
  .risk-banner { padding:18px 22px; margin:10px 0 12px; border-radius:15px; font-size:1.24rem; line-height:1.6; font-weight:700; }
  .risk-high { background:#fff0f1; border:1px solid #f3c5c8; color:#87313b; }
  .risk-check { background:#fff6df; border:1px solid #ecd38b; color:#76520a; }
  .risk-clear { background:#eaf4ff; border:1px solid #cbdff1; color:#24577d; }
  @media (max-width:700px) { [data-testid="stMainBlockContainer"] { padding:1.2rem 1rem 2rem; } }
</style>
<div style="display:flex;align-items:center;gap:17px;margin:.2rem 0 .5rem;padding:6px 0 14px;">
  <div style="width:62px;height:62px;border-radius:19px;background:linear-gradient(145deg,#e6f4ff,#d8e8ff);display:flex;align-items:center;justify-content:center;box-shadow:0 8px 20px rgba(30,109,161,.13);">
    <svg width="42" height="48" viewBox="0 0 48 54" role="img" aria-label="蓝色盾牌"><defs><linearGradient id="shieldBlue" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3189e8"/><stop offset="1" stop-color="#25b6dc"/></linearGradient></defs><path d="M24 3 43 9v15c0 12-7.8 21.2-19 27C12.8 45.2 5 36 5 24V9z" fill="#d5e9ff" stroke="#647eaa" stroke-width="2.5" stroke-linejoin="round"/><path d="M24 7 39 12v12c0 9.8-5.8 17.3-15 22V7z" fill="url(#shieldBlue)"/><path d="M24 7v39c-9.2-4.7-15-12.2-15-22V12z" fill="#3489ee"/></svg>
  </div>
  <div><div style="font-size:2.25rem;font-weight:780;line-height:1.2;color:#17324d;">银龄盾 <span style="font-weight:450;color:#49677f;">｜对话核验助手</span></div>
  <div style="font-size:1.08rem;color:#587087;margin-top:6px;">看清风险信号，再决定下一步</div></div>
</div>
""", unsafe_allow_html=True)
st.markdown("<div style='padding:15px 20px;margin:0 0 18px;border:1px solid #d2e2ea;background:rgba(255,255,255,.72);border-radius:16px;color:#36536b;font-size:1.12rem;'><b style='color:#17324d;'>遇到不确定的电话、短信或聊天，先停一停。</b><br>粘贴对话，我们会把需要留意的原句、风险原因和核实办法说清楚。</div>", unsafe_allow_html=True)
st.caption("本地规则与知识卡检索原型，仅作风险提示；不会确认对方身份，也不会自动发送短信。")

summary = load_dataset_summary()
knowledge = load_knowledge()

with st.sidebar:
    st.header("🧭 使用提示")
    st.markdown("""
<div style="padding:16px 17px;margin:2px 0 14px;border-radius:17px;background:linear-gradient(145deg,#fff,#f5fafc);border:1px solid #d4e3e9;box-shadow:0 6px 18px rgba(35,75,100,.05);">
<div style="font-size:1.08rem;font-weight:750;color:#1e4f79;margin-bottom:8px;">🧭 怎么使用</div>
<div>① 粘贴对话，尽量保留“对方：”和“我：”。</div><div>② 点击“开始核验”。</div>
<div>③ 查看安全建议、提醒依据和相关资料。</div><div>④ 需要时生成家属核实卡，由您决定是否分享。</div></div>
<div style="padding:16px 17px;margin:0 0 14px;border-radius:17px;background:linear-gradient(145deg,#fff,#f5fafc);border:1px solid #d4e3e9;box-shadow:0 6px 18px rgba(35,75,100,.05);">
<div style="font-size:1.08rem;font-weight:750;color:#1e4f79;margin-bottom:8px;">📊 风险阶段</div>
<div><b>S0 普通说明</b>：暂未发现明显风险要求。</div><div><b>S1 身份待核</b>：先核实身份和业务。</div>
<div><b>S2 催促施压</b>：建议暂停并独立核实。</div><div><b>S3 外部操作</b>：如陌生链接、安装软件或共享屏幕。</div>
<div><b>S4 资金与认证</b>：如索要验证码、密码或要求转账。</div></div>
<div style="padding:16px 17px;margin:0 0 14px;border-radius:17px;background:linear-gradient(145deg,#fff,#f5fafc);border:1px solid #d4e3e9;box-shadow:0 6px 18px rgba(35,75,100,.05);">
<div style="font-size:1.08rem;font-weight:750;color:#1e4f79;margin-bottom:8px;">🛡️ 页面功能</div>
<div>🔎 提醒依据：标出可疑原句、信号和出现阶段。</div><div>✅ 安全建议：提供清晰、可操作的核实步骤。</div>
<div>📚 相关知识卡：提供反诈资料和来源，方便查证。</div><div>👨‍👩‍👧 家属协同：生成核实卡，由您自主决定是否分享。</div></div>
""", unsafe_allow_html=True)
    st.warning("请勿输入真实验证码、密码、身份证号或银行卡号。")
    if summary["missing_files"]:
        st.error("有数据文件未读取到，请确认 CSV 与 app.py 同在仓库根目录，或放在 data/ 文件夹中：" + "、".join(summary["missing_files"]))

with st.container(border=True):
    st.markdown("## 💬 把需要核实的内容放在这里")
    st.caption("可以粘贴短信，也可以粘贴聊天记录。保留“对方”和“我”的顺序会更容易看懂。")
    text = st.text_area(
        "对话内容", height=190, label_visibility="collapsed",
        placeholder="对方：我是平台客服，您的会员今天会自动扣费。\n我：需要怎么处理？\n对方：请开启屏幕共享，我指导您取消。",
    )
    st.caption("🔒 请勿粘贴真实验证码、密码、身份证号或银行卡号。")
    submitted = st.button("开始核验", type="primary", use_container_width=True)

if submitted:
    if not text.strip():
        st.warning("请先粘贴一段对话。")
    else:
        st.session_state.result = analyze_dialogue(text, knowledge)
        st.session_state.show_family = False

result = st.session_state.get("result")
if result:
    st.divider()
    with st.container(border=True):
        st.markdown("## 📋 核验结果")
        if result["status"] == "high_risk_signal":
            banner_class = "risk-high"
            banner_text = f"发现高风险操作信号｜{result['max_stage']}：{result['stage_text']}"
        elif result["status"] == "needs_verification":
            banner_class = "risk-check"
            banner_text = f"建议先暂停，核实后再操作｜{result['max_stage']}：{result['stage_text']}"
        else:
            banner_class = "risk-clear"
            banner_text = f"暂未发现明显风险信号｜{result['max_stage']}：{result['stage_text']}"
        st.markdown(f"<div class='risk-banner {banner_class}'>{html.escape(banner_text)}</div>", unsafe_allow_html=True)
        st.caption("阶段描述的是对话中出现的行为，不代表已确认诈骗；未发现信号也不代表绝对安全。")
    
        for alert in result.get("context_alerts", []):
            st.markdown(f"<div style='padding:20px 23px;margin:18px 0 22px;border-radius:18px;background:#fff8e2;border:1px solid #efd27a;color:#6b4b05;font-size:1.18rem;line-height:1.8;'><div style='font-size:1.32rem;font-weight:750;margin-bottom:8px;'>⚠️ 潜在线索提醒：{html.escape(alert['title'])}</div>{html.escape(alert['message'])}</div>", unsafe_allow_html=True)
    
        st.subheader("✅ 现在可以这样做")
        for action in result["actions"]:
            st.markdown(f"<div style='padding:15px 18px;margin:9px 0;border-radius:14px;background:linear-gradient(120deg,#f2faf6,#f8fcfa);border:1px solid #d3e9de;border-left:5px solid #5c9b7b;color:#244d3d;font-size:1.16rem;line-height:1.75;box-shadow:0 4px 12px rgba(35,75,100,.035);'>✓ {html.escape(action)}</div>", unsafe_allow_html=True)
    
        st.subheader("🔎 提醒依据")
        if result["evidence"]:
            for item in result["evidence"]:
                label = SIGNAL_TEXT.get(item["signal"], "身份或理由需要核实" if item["signal"] == "identity_or_reason_needs_verification" else item["signal"])
                st.markdown(f"**第 {item['turn_no']} 轮**　·　{item['speaker']}　·　**{label}**")
                st.markdown(f"<div style='padding:15px 18px;margin:7px 0 16px;border-radius:0 14px 14px 0;background:#f6f9fa;border-left:5px solid #67a2bc;color:#263f54;font-size:1.16rem;line-height:1.8;'>{html.escape(item['quote'])}</div>", unsafe_allow_html=True)
        else:
            st.write("没有提取到明确触发规则的原句。")
        if result["signal_texts"]:
            st.write("识别信号：" + "、".join(result["signal_texts"]))
        if result["first_risk_turn"]:
            st.write(f"首次出现需核实信号：第 {result['first_risk_turn']} 轮。")
        if result["first_high_risk_turn"]:
            st.write(f"首次出现 S3/S4 高风险操作：第 {result['first_high_risk_turn']} 轮。")
    
        st.subheader("📚 相关知识卡")
        if result["knowledge"]:
            for card in result["knowledge"]:
                with st.expander(f"{card.get('title', '核实资料')}｜{card.get('publisher', '来源待核')}"):
                    if card.get("_match_reason"):
                        st.caption("匹配依据：" + card["_match_reason"])
                    if card.get("scenario"):
                        st.markdown("**相关情景：** " + card["scenario"].replace("**", ""))
                    if card.get("pattern_summary"):
                        st.markdown(card["pattern_summary"].replace("**", ""))
                    if card.get("official_advice"):
                        st.markdown("**资料建议：** " + card["official_advice"].replace("**", ""))
                    st.caption(f"发布日期：{card.get('publish_date') or '未注明'}；知识卡编号：{card.get('knowledge_id', '')}")
                    if card.get("url", "").strip():
                        st.link_button("打开来源网页", card["url"])
                    else:
                        st.caption("本条知识卡没有来源链接，请通过官方渠道再次核实。")
        else:
            st.info("没有找到足够相关的知识卡。请勿按陌生卡片或链接操作，可自行打开官方 App 或请家人协助核实。")
    
        st.subheader("👨‍👩‍👧 家属协同（可选）")
        if st.button("生成家属核实卡"):
            st.session_state.show_family = True
        if st.session_state.get("show_family"):
            st.text_area("请检查后再自行复制给家人；系统不会自动发送", value=result["family_card"], height=140, key="family_card_text")
            copy_text = html.escape(result["family_card"], quote=True)
            components.html(f"""
<button id="family-copy-button" onclick="copyFamilyCard()"
 style="padding:13px 23px;border:0;border-radius:12px;background:linear-gradient(100deg,#1e6da1,#18857e);color:#fff;font-size:18px;font-weight:700;cursor:pointer;">
📋 一键复制给家人</button><textarea id="family-copy-source" style="position:fixed;left:-10000px;top:0">{copy_text}</textarea>
<script>
async function copyFamilyCard() {{
  const source = document.getElementById('family-copy-source');
  const button = document.getElementById('family-copy-button');
  try {{
    await navigator.clipboard.writeText(source.value);
    button.innerText = '✓ 已复制，可粘贴发送';
  }} catch (error) {{
    source.focus(); source.select();
    const copied = document.execCommand('copy');
    button.innerText = copied ? '✓ 已复制，可粘贴发送' : '请手动选择上方内容复制';
  }}
}}
</script>
""", height=58)
