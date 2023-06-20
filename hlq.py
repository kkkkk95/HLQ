from pyclbr import Class
import streamlit as st
import pandas as pd
from openpyxl import load_workbook
import time
import re
import os
import base64
# 设置网页标题，以及使用宽屏模式
st.set_page_config(
    page_title="GZ",
    layout="wide"

)
# 隐藏右边的菜单以及页脚
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

class analyze:
    def __init__(self,source_file):
        self.source_file = source_file
    def reading(self):
        df=pd.read_excel(self.source_file)
        # 保留指定列
        columns_to_keep = ['航班号', '航班执行日期', '飞机号', '实际起飞机场', '实际落地机场', '离港停机位', '进港停机位', '计划起飞时间','计划落地时间', '撤轮挡时间', '实际起飞时间', '实际落地时间', '上轮档时间', '班表落地时间', '标准机型']
        df = df[columns_to_keep]
        # 去除撤轮挡时间为空的行
        df = df[df['撤轮挡时间'].notnull()]
        # 将相关列转换为时间格式
        time_cols = ['计划起飞时间', '计划落地时间', '撤轮挡时间', '实际起飞时间', '实际落地时间', '上轮档时间', '班表落地时间']
        df[time_cols] = df[time_cols].apply(pd.to_datetime, errors='coerce')
        return df
    def calculate_turnaround_time1(self,group):
        group = group.sort_values('计划起飞时间')  # 按计划起飞时间排序
        group['过站时间'] = group['撤轮挡时间'].shift(-1) - group['上轮档时间']  # 计算过站时间
        return group
    def calculate_turnaround_time2(self,group):
        group = group.sort_values('计划起飞时间')  # 按计划起飞时间排序
        group['过站时间'] = group['计划起飞时间'].shift(-1) - group['计划落地时间']  # 计算过站时间
        
        return group
    def run(self,n):
        self.df=self.reading()
        if n==1:
            grouped =self.df.groupby('飞机号',group_keys=True, as_index=False).apply(self.calculate_turnaround_time1)
        elif n==2:
            grouped =self.df.groupby('飞机号',group_keys=True, as_index=False).apply(self.calculate_turnaround_time2)
        # 按照飞机号和计划起飞时间排序
        grouped = grouped.sort_values(['飞机号', '计划起飞时间'])
        condition = ((grouped['过站时间'] >= pd.Timedelta(hours=3)) & 
                    (grouped['过站时间'] <= pd.Timedelta(hours=4)) & 
                    (grouped['实际落地机场'] == 'PEK'))

        # 保留符合条件的行数据和下一行数据
        filtered = grouped[condition | condition.shift(1)].reset_index(drop=True)
        
        filtered['过站时间'] = pd.to_datetime(filtered['过站时间'].dt.total_seconds(), unit='s').dt.strftime('%H:%M')
        # 将飞机号相同的行数据在一起
        filtered = filtered.groupby('飞机号').apply(lambda x: x.reset_index(drop=True))
        return filtered

# 定义下载函数
def download_csv(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="data.csv">下载 CSV 文件</a>'
    return href
st.header("过站时间数据处理")
st.write("上传需要处理的excel")
source_file = st.file_uploader("上传文件：")
if st.button('生成处理结果（out-in）', key="generate_result"):
    if source_file:
        with st.spinner('正在处理数据，请稍等...'):
            result=analyze(source_file)
            filtered=result.run(1)
            st.write(filtered)
            # 在 Streamlit 中创建下载按钮
            st.markdown(download_csv(filtered), unsafe_allow_html=True)
if st.button('生成处理结果（off-on）'):
    if source_file:
        with st.spinner('正在处理数据，请稍等...'):
            result=analyze(source_file)
            filtered=result.run(2)
            st.write(filtered)
            # 在 Streamlit 中创建下载按钮
            st.markdown(download_csv(filtered), unsafe_allow_html=True)


