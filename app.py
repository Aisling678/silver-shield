import streamlit as st

from agent import analyze_dialogue, load_dataset_summary, load_knowledge

st.set_page_config(page_title="银龄盾｜对话核验助手", page_icon="🛡️", layout="centered")
st.title("🛡️ 银龄盾｜对话核验助手")
st.write("粘贴一段短信或聊天记录，看看其中是否出现需要暂停核实的风险信号。")
st.caption("本地规则原型，仅作风险提示；不会确认对方身份，也不会自动发送短信。")

summary = load_dataset_summary()
knowledge = load_knowledge()

with st.sidebar:
    st.header("使用提示")
    st.markdown("1. 粘贴对话，并尽量保留‘对方：’和‘我：’。\n2. 点击开始核验。\n3. 查看触发原句、建议和可选家属核实卡。")
    st.warning("不要输入真实验证码、密码、身份证号或银行卡号。")
    st.caption(f"项目数据：{summary['dialogues']} 段对话、{summary['turns']} 轮、{summary['knowledge']} 张知识卡。")
    if summary.get("missing_files"):
        st.error("未找到这些CSV：" + "、".join(summary["missing_files"]) + "。请确认它们与 app.py 同在仓库根目录，或放在 data/ 文件夹中。")
    else:
        st.success("对话、轮次和知识卡CSV均已读取。")

text = st.text_area("粘贴对话", height=220, placeholder="对方：我是平台客服，您的会员今天会自动扣费。\n我：需要怎么处理？\n对方：请开启屏幕共享，我指导您取消。")
if st.button("开始核验", type="primary", use_container_width=True):
    if not text.strip():
        st.warning("请先粘贴一段对话。")
    else:
        st.session_state.result = analyze_dialogue(text, knowledge)
        st.session_state.show_family = False

result = st.session_state.get("result")
if result:
    st.divider()
    st.subheader("提醒依据")
    if result["status"] == "high_risk_signal": st.error(f"{result['status_text']}｜{result['max_stage']}：{result['stage_text']}")
    elif result["status"] == "needs_verification": st.warning(f"{result['status_text']}｜{result['max_stage']}：{result['stage_text']}")
    else: st.info(f"{result['status_text']}｜{result['max_stage']}：{result['stage_text']}")
    st.caption("阶段描述的是对话中出现的行为，不代表已确认诈骗；未发现信号也不代表绝对安全。")

    if result["evidence"]:
        for item in result["evidence"]:
            label = item["signal"] if item["signal"] != "identity_or_reason_needs_verification" else "身份或理由需要核实"
            st.write(f"第 {item['turn_no']} 轮 · {item['speaker']} · {label}")
            st.code(item["quote"], language=None)
    else: st.write("没有提取到明确触发规则的原句。")
    if result["signal_texts"]: st.write("识别信号：" + "、".join(result["signal_texts"]))
    if result["first_risk_turn"]: st.write(f"首次出现需核实信号：第 {result['first_risk_turn']} 轮。")
    if result["first_high_risk_turn"]: st.write(f"首次出现 S3/S4 高风险操作：第 {result['first_high_risk_turn']} 轮。")

    st.subheader("建议")
    for action in result["actions"]: st.markdown(f"- {action}")

    st.subheader("相关知识卡")
    if result["knowledge"]:
        for card in result["knowledge"]:
            with st.expander(f"{card.get('title', '核实资料')}｜{card.get('publisher', '来源待核')}"):
                st.write(card.get("pattern_summary", ""))
                if card.get("official_advice"): st.write("**资料建议：**" + card["official_advice"])
                st.caption(f"发布日期：{card.get('publish_date') or '未注明'}；知识卡编号：{card.get('knowledge_id', '')}")
                if card.get("url", "").strip(): st.link_button("打开来源网页", card["url"])
    else: st.info("没有找到匹配且带来源链接的知识卡，请自行通过官方渠道核实。")

    st.subheader("家属协同（可选）")
    if st.button("生成家属核实卡"): st.session_state.show_family = True
    if st.session_state.get("show_family"):
        st.text_area("检查后可自行复制给家人；系统不会自动发送", value=result["family_card"], height=140)

with st.expander("数据和系统说明"):
    st.markdown(f"""
- 当前加载 {summary['dialogues']} 段对话、{summary['turns']} 轮标注和 {summary['knowledge']} 张知识卡。
- 当前版本用本地规则识别风险信号，并检索知识卡；没有用这些标签训练模型，也不调用外部大模型。
- 数据状态：{summary['split_status']}，所以不报告准确率。
- 输入不会被此程序写入 CSV；请仍避免输入真实敏感信息。
""")
