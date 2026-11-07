import streamlit as st

from agent import analyze_dialogue, load_dataset_summary, load_knowledge

st.set_page_config(page_title="银龄盾｜对话核验助手", page_icon="🛡️", layout="centered")
st.title("🛡️ 银龄盾｜老年消费对话核验助手")
st.write("粘贴一段短信或聊天记录，查看对话中是否出现需要暂停核实的风险信号。")
st.caption("本地规则与知识卡检索原型；输出仅作风险提示，不会确认对方身份，也不会自动发送短信。")

summary = load_dataset_summary()
knowledge = load_knowledge()

with st.sidebar:
    st.header("使用提示")
    st.markdown("1. 粘贴对话，尽量保留‘对方：’和‘我：’。\n2. 点击开始核验。\n3. 查看触发原句、建议和相关资料。")
    st.warning("不要输入真实验证码、密码、身份证号或银行卡号。")
    st.caption(f"项目数据：{summary['dialogues']} 段对话、{summary['turns']} 轮、{summary['knowledge']} 张知识卡。")
    if summary["missing_files"]:
        st.error("有数据文件未读取到。请确认以下文件已提交到 GitHub 仓库的 data/ 文件夹：\n\n" + "\n".join(f"- `{p}`" for p in summary["missing_files"]))
    else:
        st.success("三类CSV已找到并读取。")

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
    # Put the overall risk status before the detailed evidence, as requested.
    if result["status"] == "high_risk_signal":
        st.error(f"{result['status_text']}｜{result['max_stage']}：{result['stage_text']}")
    elif result["status"] == "needs_verification":
        st.warning(f"{result['status_text']}｜{result['max_stage']}：{result['stage_text']}")
    else:
        st.info(f"{result['status_text']}｜{result['max_stage']}：{result['stage_text']}")
    st.caption("阶段描述的是对话中出现的行为，不代表已确认诈骗；未发现信号也不代表绝对安全。")

    for alert in result.get("context_alerts", []):
        st.warning(f"**潜在线索提醒：{alert['title']}**\n\n{alert['message']}")

    st.subheader("提醒依据")
    if result["evidence"]:
        for item in result["evidence"]:
            label = item["signal"] if item["signal"] != "identity_or_reason_needs_verification" else "身份或理由需要核实"
            st.write(f"第 {item['turn_no']} 轮 · {item['speaker']} · {label}")
            st.code(item["quote"], language=None)
    else:
        st.write("没有提取到明确触发规则的原句。")
    if result["signal_texts"]:
        st.write("识别信号：" + "、".join(result["signal_texts"]))
    if result["first_risk_turn"]:
        st.write(f"首次出现需核实信号：第 {result['first_risk_turn']} 轮。")
    if result["first_high_risk_turn"]:
        st.write(f"首次出现 S3/S4 高风险操作：第 {result['first_high_risk_turn']} 轮。")

    st.subheader("建议")
    for action in result["actions"]:
        st.markdown(f"- {action}")

    st.subheader("相关知识卡")
    if result["knowledge"]:
        for card in result["knowledge"]:
            title = card.get("title", "核实资料")
            publisher = card.get("publisher", "来源待核")
            with st.expander(f"{title}｜{publisher}"):
                if card.get("_match_reason"):
                    st.caption("匹配依据：" + card["_match_reason"])
                if card.get("scenario"):
                    st.write("**相关情景：**" + card["scenario"])
                if card.get("pattern_summary"):
                    st.write(card["pattern_summary"])
                if card.get("official_advice"):
                    st.write("**资料建议：**" + card["official_advice"])
                st.caption(f"发布日期：{card.get('publish_date') or '未注明'}；知识卡编号：{card.get('knowledge_id', '')}")
                if card.get("url", "").strip():
                    st.link_button("打开来源网页", card["url"])
                else:
                    st.caption("本条知识卡没有来源链接，请通过官方渠道再次核实。")
    else:
        st.info("当前知识卡没有找到足够相关的资料。请不要按陌生卡片或链接操作，可自行打开官方 App 或请家人协助核实。")

    st.subheader("家属协同（可选）")
    if st.button("生成家属核实卡"):
        st.session_state.show_family = True
    if st.session_state.get("show_family"):
        st.text_area("检查后可自行复制给家人；系统不会自动发送", value=result["family_card"], height=140)

with st.expander("数据与系统说明"):
    st.markdown(f"""
- 已读取：{summary['dialogues']} 段对话、{summary['turns']} 轮标注、{summary['knowledge']} 张知识卡。
- 文件预期位置：`data/dialogues.csv`、`data/turns.csv`、`data/knowledge.csv`。
- 数据切分：{summary['split_status']}；没有锁定测试集时不报告准确率。
- 当前对话分析由本地规则和知识卡检索完成，不调用外部大模型，也没有用标签训练模型。
- 输入内容不会被本程序写入CSV。请勿输入真实敏感信息。
""")
