from pyclbr import Class
import streamlit as st
import pandas as pd
from openpyxl import load_workbook
import time
import re
import os
import base64
import datetime

# 设置网页标题，以及使用宽屏模式
st.set_page_config(
    page_title="TAXI_TIME",
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

class ana:
    def __init__(self,source_file):
        self.source_file = source_file
    def reading(self):
        # 将第二行设置为标题
        df=pd.read_excel(self.source_file, header=0, skiprows=1)
        # 保留指定列
        columns_to_keep = ['航班号', '飞机号', '机型', '起飞机场', '撤轮挡时间', 'ACARS滑出时间', 'ACARS起飞时间', 'ACARS落地时间','ACARS推入时间', '落地机场', '落地跑道', '起飞跑道']
        df = df.loc[:, columns_to_keep] 
         # 替换空值
        df.loc[:, '撤轮挡时间'].fillna(df['ACARS滑出时间'], inplace=True)
        # 将相关列转换为时间格式
        time_format = "%H:%M:%S"
        time_cols = ['撤轮挡时间', 'ACARS滑出时间', 'ACARS起飞时间', 'ACARS落地时间', 'ACARS推入时间']
        for col in time_cols:
            df.loc[:, col] = pd.to_datetime(df[col], format=time_format, errors='coerce')
        return df
    def calculate_time(self,pos,minutes):
        df = self.reading()
        # 创建字典存储结果
        dic = {}
        # 处理minutes
        time_format = datetime.timedelta(minutes=minutes)
        
        for i in pos:
            # 筛选起飞机场等于i的行
            filtered_df = df[df['起飞机场'] == i]
            
            # 将滑入时间和滑出时间转换为datetime类型
            filtered_df.loc[:, 'ACARS起飞时间'] = pd.to_datetime(filtered_df['ACARS起飞时间'])
            filtered_df.loc[:, '撤轮挡时间'] = pd.to_datetime(filtered_df['撤轮挡时间'])
            
            # 计算滑出时间和滑入时间的时间间隔
            filtered_df.loc[:, '滑出时间'] = filtered_df['ACARS起飞时间'] - filtered_df['撤轮挡时间']
            filtered_df.loc[:, '滑入时间'] = filtered_df['ACARS推入时间'] - filtered_df['ACARS落地时间']
            
            # 删除滑入时间和滑出时间大于time_format的行
            filtered_df = filtered_df[(filtered_df['滑出时间'] <= time_format) & (filtered_df['滑入时间'] <= time_format)]
            # 计算滑出时间和滑入时间的总和
            total_taxiout = filtered_df['滑出时间'].sum()
            total_taxiin = filtered_df['滑入时间'].sum()
            
            # 计算滑出时间和滑入时间的平均值
            average_taxiout = str(total_taxiout / len(filtered_df)).split(" ")[-1]
            average_taxiin = str(total_taxiin / len(filtered_df)).split(" ")[-1]
            
            
            # 存储结果到字典
            dic[i] = [average_taxiout, average_taxiin]
        
        return dic
    def calculate_percent(self,pos):
        df_all = self.reading()
        df=df_all[(df_all['起飞机场'].isin(pos))]
        #设置机型数据
        wide = ['332','333','359','744','747','773','787']
        narrow = ['20N','21N','319','320','321','737','738','7M8','ARJ']
        #设置跑道数据
        west_runway = ['18R','36L']
        center_runway = ['18L','36R']  
        east_runway = ['1','19']
        #调整dataframe类型
        df['机型'] = df['机型'].astype(str)
        df['落地跑道'] = df['落地跑道'].astype(str)
        west_narrow = len(df[(df['机型'].isin(narrow)) & (df['落地跑道'].isin(west_runway))])
        west_wide = len(df[(df['机型'].isin(wide)) & (df['落地跑道'].isin(west_runway))])

        center_narrow = len(df[(df['机型'].isin(narrow)) & (df['落地跑道'].isin(center_runway))])  
        center_wide = len(df[(df['机型'].isin(wide)) & (df['落地跑道'].isin(center_runway))])

        east_narrow = len(df[(df['机型'].isin(narrow)) & (df['落地跑道'].isin(east_runway))])
        east_wide = len(df[(df['机型'].isin(wide)) & (df['落地跑道'].isin(east_runway))])
        data={'西跑道':[west_narrow,west_wide ],
            '中跑道':[ center_narrow, center_wide],
            '东跑道': [east_narrow,east_wide]}
        
        return data

# 定义下载函数
def download_csv(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="data.csv">下载 CSV 文件</a>'
    return href


st.title("“缩滑”工作进展")
st.write('---------------------------------')
st.write("佳木斯和通辽航班移至T3航站楼进出港后的平均进出港时间")
source_file = st.file_uploader("上传文件：")

 # 用户输入机场三字码
airports1 = st.text_input("输入起飞机场三字码（多个机场以空格分开）",value='JMU TGO')
airport_list1 = airports1.split()

# 用户输入忽略过大滑行时间
ignore_time = st.number_input("输入忽略过大滑行时间（分钟）", min_value=0, step=1, value=999)

if st.button('生成处理结果（滑行时间）'):
    with st.spinner('正在处理数据，请稍等...'):
        if source_file is not None:
            taxiwork=ana(source_file)
            dic=taxiwork.calculate_time(airport_list1,ignore_time)
            df=pd.DataFrame.from_dict(dic, orient='index', columns=['平均滑出时间', '平均滑入时间'])
            st.write(df)
        else:
            st.write('未检测到文件')
st.write('---------------------------------') 
st.write("成都两场、昆明、重庆航班首都机场使用跑道数据")
# 用户输入机场三字码
airports2 = st.text_input("输入起飞机场三字码（多个机场以空格分开）",value='CTU TFU CKG KMG')
airport_list2 = airports2.split()
if st.button('生成处理结果（跑道占比）'):
    with st.spinner('正在处理数据，请稍等...'):
        if source_file is not None:
            percent=ana(source_file)
            data=percent.calculate_percent(airport_list2)
            df = pd.DataFrame(data,['窄体机','宽体机'])
            df = df.transpose()
            st.write(df)
            st.bar_chart(df)
        else:
            st.write('未检测到文件')