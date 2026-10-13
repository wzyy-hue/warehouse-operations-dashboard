"""仓储运营数据分析与异常监控系统 | 个人模拟数据项目"""
import sqlite3
import pandas as pd
import streamlit as st
from data_setup import setup, DB

st.set_page_config(page_title="仓储运营数据分析系统", page_icon="📦", layout="wide")
setup()

SQL_DAILY = """
SELECT w.warehouse_name AS 仓库, o.order_date AS 日期,
       COUNT(*) AS 订单数,
       SUM(CASE WHEN o.shipped_date IS NOT NULL AND o.shipped_date <= o.promised_date THEN 1 ELSE 0 END) AS 按时发货数,
       ROUND(100.0 * SUM(CASE WHEN o.shipped_date IS NOT NULL AND o.shipped_date <= o.promised_date THEN 1 ELSE 0 END) / COUNT(*), 2) AS 按时发货率,
       ROUND(SUM(o.amount),2) AS 订单金额
FROM orders o JOIN warehouses w ON o.warehouse_id=w.warehouse_id
GROUP BY w.warehouse_id, w.warehouse_name, o.order_date
ORDER BY o.order_date, w.warehouse_name;
"""
SQL_RANK = """
WITH daily_employee AS (
 SELECT e.warehouse_id, e.employee_id, e.employee_name, o.order_date,
        COUNT(*) AS 已发货订单量
 FROM orders o JOIN employees e ON o.employee_id=e.employee_id
 WHERE o.shipped_date IS NOT NULL
 GROUP BY e.warehouse_id, e.employee_id, e.employee_name, o.order_date
)
SELECT w.warehouse_name AS 仓库, d.order_date AS 日期,
       d.employee_name AS 员工, d.已发货订单量,
       ROW_NUMBER() OVER (
         PARTITION BY d.warehouse_id, d.order_date
         ORDER BY d.已发货订单量 DESC, d.employee_id
       ) AS 当日排名
FROM daily_employee d JOIN warehouses w ON d.warehouse_id=w.warehouse_id
ORDER BY 日期 DESC, 仓库, 当日排名;
"""
SQL_INVENTORY = """
SELECT w.warehouse_name AS 仓库, p.product_name AS 商品,
       i.book_qty AS 账面库存, i.physical_qty AS 实盘库存,
       i.physical_qty - i.book_qty AS 库存差异
FROM inventory i JOIN warehouses w ON i.warehouse_id=w.warehouse_id
JOIN products p ON i.product_id=p.product_id
WHERE i.physical_qty != i.book_qty
ORDER BY ABS(i.physical_qty-i.book_qty) DESC;
"""
SQL_TREND = """
WITH daily AS (
 SELECT order_date AS 日期, COUNT(*) AS 订单数 FROM orders GROUP BY order_date
)
SELECT 日期, 订单数,
       LAG(订单数) OVER (ORDER BY 日期) AS 前一日订单数,
       订单数 - LAG(订单数) OVER (ORDER BY 日期) AS 较前日变化,
       SUM(订单数) OVER (ORDER BY 日期 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS 累计订单数
FROM daily ORDER BY 日期;
"""
# 预警计算先保留所有每日记录，阈值统一在界面层筛选，便于对比调整。
SQL_ALERT = """
WITH daily AS (
    SELECT warehouse_id, order_date, COUNT(*) AS order_count
    FROM orders GROUP BY warehouse_id, order_date
), daily_change AS (
    SELECT warehouse_id, order_date, order_count,
        LAG(order_count) OVER (
            PARTITION BY warehouse_id ORDER BY order_date
        ) AS prev_count
    FROM daily
)
SELECT w.warehouse_name AS 仓库, d.order_date AS 日期,
       d.order_count AS 当日订单量, d.prev_count AS 前日订单量,
       ROUND(100.0 * (d.order_count-d.prev_count) / NULLIF(d.prev_count,0),2) AS 变化率
FROM daily_change d JOIN warehouses w ON d.warehouse_id=w.warehouse_id
ORDER BY w.warehouse_name, d.order_date;
"""

def query(sql):
    with sqlite3.connect(DB) as con:
        return pd.read_sql_query(sql, con)

def download(df, filename, key):
    st.download_button("⬇ 导出CSV报表", df.to_csv(index=False).encode("utf-8-sig"),
                       file_name=filename, mime="text/csv", key=key)

st.title("📦 仓储运营数据分析系统")
st.caption("个人独立实践项目  ·  2026年9月  ·  模拟仓储业务数据（非京东或任何企业内部数据）")

all_daily = query(SQL_DAILY)
warehouses = ["全部仓库"] + sorted(all_daily["仓库"].unique().tolist())
selected = st.sidebar.selectbox("仓库筛选", warehouses)
st.sidebar.caption("分析对象：模拟订单、仓库、员工及库存数据")
subset = all_daily if selected == "全部仓库" else all_daily[all_daily["仓库"] == selected]
orders_n = int(subset["订单数"].sum())
on_time = int(subset["按时发货数"].sum())
revenue = float(subset["订单金额"].sum())
inventory = query(SQL_INVENTORY)
inv_view = inventory if selected == "全部仓库" else inventory[inventory["仓库"] == selected]

k1,k2,k3,k4 = st.columns(4)
k1.metric("订单总量", f"{orders_n:,}")
k2.metric("按时发货率", f"{100*on_time/orders_n:.1f}%" if orders_n else "—")
k3.metric("订单金额", f"¥{revenue:,.0f}")
k4.metric("库存差异记录", f"{len(inv_view)}")

t1,t2,t3,t4,t5 = st.tabs(["📊 运营总览", "🏅 仓库作业分析", "📦 库存监控", "🚨 异常预警", "🗂 数据与方法"])

with t1:
    st.subheader("每日订单趋势")
    plotted = subset.groupby("日期",as_index=False)["订单数"].sum().set_index("日期")
    st.line_chart(plotted)
    st.subheader("仓储运营日报")
    st.dataframe(subset, use_container_width=True, hide_index=True)
    download(subset, "warehouse_daily_report.csv", "daily_download")

with t2:
    st.subheader("员工每日已发货订单量排名")
    st.caption("此指标衡量模拟订单处理数量；未包含工时、拣货件数，不能等同真实作业效率。")
    rank = query(SQL_RANK)
    rank = rank if selected == "全部仓库" else rank[rank["仓库"] == selected]
    st.dataframe(rank, use_container_width=True, hide_index=True)
    download(rank, "employee_order_ranking.csv", "rank_download")

with t3:
    st.subheader("账实库存差异")
    st.caption("库存差异 = 实盘库存 − 账面库存；正值为实盘更多，负值为实盘更少。")
    st.dataframe(inv_view, use_container_width=True, hide_index=True)
    download(inv_view, "inventory_discrepancies.csv", "inventory_download")

with t4:
    st.subheader("订单量异常预警")
    st.caption("按仓库比较相邻有记录日期的订单量变化；当日无订单的日期未补零。")
    col1,col2 = st.columns(2)
    with col1:
        threshold = st.slider("订单量下降阈值（%）", 10, 80, 20, step=5)
    with col2:
        minimum = st.slider("上一记录日最低订单量（单）", 0, 50, 0, step=5)
    raw_alerts = query(SQL_ALERT)
    if selected != "全部仓库":
        raw_alerts = raw_alerts[raw_alerts["仓库"] == selected]
    alerts = raw_alerts[
        (raw_alerts["变化率"] < -float(threshold)) &
        (raw_alerts["前日订单量"] >= minimum)
    ].sort_values(["变化率", "日期"]).reset_index(drop=True)
    st.metric("符合当前条件的异常记录", len(alerts))
    st.dataframe(alerts, use_container_width=True, hide_index=True)
    download(alerts, "warehouse_alerts_filtered.csv", "alerts_download")
    if not alerts.empty:
        counts = alerts["仓库"].value_counts().rename_axis("仓库").reset_index(name="异常次数")
        st.subheader("异常次数分布")
        st.bar_chart(counts.set_index("仓库")["异常次数"])
        most = counts.iloc[0]
        worst = alerts.iloc[0]
        st.subheader("分析摘要")
        st.write(f"当前筛选下共识别 **{len(alerts)} 条**订单量下降记录，**{most['仓库']}** 触发次数最多（{int(most['异常次数'])}次）。")
        st.write(f"最大降幅发生在 **{worst['仓库']} / {worst['日期']}**：由 {int(worst['前日订单量'])} 单降至 {int(worst['当日订单量'])} 单（{worst['变化率']:.2f}%）。")
        st.info("分析建议：结合订单基数、历史日均订单、订单需求、库存记录及人员排班核实原因；百分比下降不等同仓库作业效率下降。")
    else:
        st.info("当前筛选条件下无匹配记录，可调整阈值或更换仓库。")
    with st.expander("查看异常识别SQL"):
        st.code(SQL_ALERT, language="sql")

with t5:
    st.subheader("数据来源与指标口径")
    st.write("数据来自项目脚本自动生成的模拟订单、员工、仓库、商品及库存记录，用于展示查询、分析和可视化方法。")
    st.markdown("**按时发货率**：已发货且发货日期不晚于承诺日期的订单数 / 全部创建订单数；未发货按非按时计。")
    st.markdown("**库存差异**：实盘数量 − 账面数量。")
    st.markdown("**异常下降**：同仓库有订单记录的相邻日期订单量变化百分比低于负阈值，且满足上一记录日最低订单量条件。")
    st.caption("局限：模拟数据、未补齐零订单日期、未纳入完整作业工时与现场流程；规则不代表企业正式考核标准。")
    with st.expander("订单汇总SQL · JOIN / GROUP BY / CASE WHEN"):
        st.code(SQL_DAILY, language="sql")
    with st.expander("员工排名SQL · ROW_NUMBER"):
        st.code(SQL_RANK, language="sql")
    with st.expander("趋势分析SQL · LAG / SUM OVER"):
        st.code(SQL_TREND, language="sql")
        st.dataframe(query(SQL_TREND), use_container_width=True, hide_index=True)
    with st.expander("库存差异SQL"):
        st.code(SQL_INVENTORY, language="sql")
