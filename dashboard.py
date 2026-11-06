import streamlit as st
import akshare as ak
import time
import requests
from datetime import datetime

API_KEY = "ark-dc14af2d-9248-4246-b758-3e854c0d2afc-7d011"
MODEL_ID = "doubao-seed-2-1-lite-260915"
ARK_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

WHITE_LIST = {
    "光伏设备", "贵金属", "能源金属", "电池", "互联网电商", "消费电子",
    "通信服务", "风电设备", "其他电子", "IT服务", "教育", "家居用品",
    "电网设备", "环保设备", "半导体", "电子化学品", "文化传媒", "其他电源设备",
    "软件开发", "医疗服务", "包装印刷", "橡胶制品", "化学制品", "工程机械",
    "光学光电子", "纺织制造", "小金属", "塑料制品", "生物制品", "建筑装饰",
    "房地产", "建筑材料", "化学纤维", "农化制品", "医疗器械", "化学原料",
    "非金属材料", "工业金属", "其他社会服务", "小家电", "饮料制造", "金属新材料",
    "专用设备", "计算机设备", "白酒", "造纸", "化学制药", "食品加工制造",
    "通用设备", "贸易", "零售", "农产品加工", "综合", "服装家纺", "汽车服务及其他",
    "轨交设备", "美容护理", "厨卫电器", "汽车零部件",
    "机场航运", "影视院线", "自动化设备", "白色家电", "养殖业", "通信设备",
    "物流", "电力", "旅游及景区", "军工装备", "黑色家电", "种植业与林业",
    "军工电子", "石油加工贸易", "中药", "电机", "游戏", "多元金融",
    "汽车整车", "燃气", "医药商业", "钢铁", "保险", "元件",
    "证券", "公路铁路运输", "港口航运", "油气开采及服务", "银行", "煤炭开采加工"
}

st.set_page_config(page_title="A股盯盘大屏", layout="wide", page_icon="📈")
st.title("🔥 群总的短线暴富盯盘实时大屏")

if "history" not in st.session_state:
    st.session_state.history = []
if "ai_cache" not in st.session_state:
    st.session_state.ai_cache = {}

main_container = st.empty()

while True:
    now_ts = datetime.now().strftime("%H:%M:%S")
    now_hm = datetime.now().strftime("%H:%M")
    try:
        # 拉板块数据
        df_board = ak.stock_board_industry_name_em()
        res = {}
        for _, row in df_board.iterrows():
            b_name = row["板块名称"]
            if b_name in WHITE_LIST:
                res[b_name] = float(row["涨跌幅"])
        rise_top3 = sorted(res.items(), key=lambda x:x[1], reverse=True)[:3]
        fall_top3 = sorted(res.items(), key=lambda x:x[1])[:3]

        # 拉连板数据
        today = datetime.now().strftime("%Y%m%d")
        zt_df = ak.stock_zt_pool_em(date=today)
        industry_col = None
        for possible in ["所属板块", "所属行业", "行业"]:
            if possible in zt_df.columns:
                industry_col = possible
                break
        ladder_df = zt_df[zt_df["连板数"]>=2].sort_values("连板数", ascending=False)
        ladder_group = {}
        for _,r in ladder_df.iterrows():
            lb = int(r["连板数"])
            stock = f"{r['名称']}（{r[industry_col] if industry_col else ''}）"
            if lb not in ladder_group:
                ladder_group[lb] = []
            ladder_group[lb].append(stock)
        max_lb = int(ladder_df["连板数"].max()) if len(ladder_df)>0 else 0
        total_zt = len(zt_df)

        # 存半小时快照
        if now_hm in ["09:30","10:00","10:30","11:00","11:30","13:00","13:30","14:00","14:30","15:00"]:
            last_record_time = st.session_state.history[-1]["time"] if st.session_state.history else ""
            if last_record_time != now_hm:
                st.session_state.history.append({"time": now_hm, "rise": rise_top3})
    except Exception as e:
        st.error(f"数据拉取失败：{e}")
        time.sleep(10)
        continue

    with main_container.container():
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("当前时间", now_ts)
        c2.metric("今日涨停总数", total_zt)
        c3.metric("市场最高连板", f"{max_lb}板")
        c4.metric("监控状态", "✅ 运行中")

        st.divider()
        col_rise, col_fall = st.columns(2)
        with col_rise:
            st.markdown("### 🟢 实时涨幅前三")
            for i,(name,pct) in enumerate(rise_top3):
                st.markdown(f"**{i+1}. {name}：{pct:.2f}%**")
        with col_fall:
            st.markdown("### 🔴 实时跌幅前三")
            for i,(name,pct) in enumerate(fall_top3):
                st.markdown(f"**{i+1}. {name}：{pct:.2f}%**")

        st.divider()
        st.markdown("### 🧱 连板梯队")
        ladder_cols = st.columns(len(ladder_group))
        for idx, (lb_num, stocks) in enumerate(sorted(ladder_group.items(), reverse=True)):
            with ladder_cols[idx]:
                st.markdown(f"**{lb_num}板**")
                for s in stocks:
                    st.code(s)

        st.divider()
        st.markdown("### 🕒 当日半小时涨跌榜时间线（9:30-15:00）")
        for record in st.session_state.history:
            rise_str = " | ".join([f"{n}:{p:.1f}%" for n,p in record["rise"]])
            st.markdown(f"**{record['time']}** → 📈 {rise_str}")

    time.sleep(10)
