仓储运营数据分析与异常监控系统｜正式展示版
========================================
本项目为个人独立实践，数据均为模拟生成，不属于京东或其他企业的内部真实业务数据。

你已创建的Conda环境：warehouse（Python 3.11）
启动方式：
1. 将本压缩包解压到 D:\warehouse_showcase （路径可以自行更改）。
2. 打开 Miniconda Prompt。
3. conda activate warehouse
4. cd /d "D:\warehouse_showcase"
5. python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
6. python -m streamlit run app.py
7. 在浏览器访问 http://localhost:8501
停止：在Miniconda Prompt中按 Ctrl+C。

展示建议：先看运营总览和仓库排名，再进入异常预警页调整阈值，最后打开数据与方法页展示SQL。

注意：旧项目的启动看板.bat 可能调用base环境，请使用上面的Conda命令启动。
