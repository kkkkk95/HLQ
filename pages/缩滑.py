import streamlit as st
import pandas as pd
from openpyxl import load_workbook
import time
import requests
from bs4 import BeautifulSoup
import re
import datetime
import os
import base64
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
matplotlib.use('Agg')
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
    def __init__(self,source_file,st,key):        
        self.source_file = source_file
        self.data34_path=os.path.abspath(r'data/代码.xlsx')
        self.data34=pd.read_excel(self.data34_path)
        self.st=st
        #设置机型数据
        self.wide = ['332','333','359','744','747','773','787']
        self.narrow = ['20N','21N','319','320','321','737','738','7M8','ARJ']
        #设置跑道数据
        self.west_runway = ['18R','36L']
        self.center_runway = ['18L','36R']  
        self.east_runway = ['1','19']
        #设置地区数据
        self.pos_pattern_rule={
            '澳洲':r'^(Y|NZ)[A-Z]{2}$',
            '日韩':r'^(RK|ZK|RJ|RO)[A-Z]{2}$',
            '美洲':r'^(C|K|P|S)[A-Z]{3}$',
            '欧洲':r'^(UUEE|E|L|G|U)[A-Z]{3}$',
            '华东':r'^(ZS)[A-Z]{2}$',
            '东北':r'^(ZY)[A-Z]{2}$',
            '中南':r'^(ZG|ZH|ZJ)[A-Z]{2}$',
            '新疆':r'^(ZW)[A-Z]{2}$',
            '西南':r'^(ZU|ZP)[A-Z]{2}$',
            '西北':r'^(ZL)[A-Z]{2}$',
            '华北':r'^(ZB)[A-Z]{2}$',
            '韩国':r'^(RK|ZK)[A-Z]{2}$',
            '日本':r'^(RJ|RO)[A-Z]{2}$',
            '地区':r'^(VH|VM|RC)[A-Z]{2}$',
            '东南亚':r'^(VT|V|O|RP|W)[A-Z]{2}$',
            '印度':r'^(VA|VE|VI|VO)[A-Z]{2}$',
            '台湾':r'^(RC)[A-Z]{2}$',
            '分流航班':r'^(ZBTJ|ZBHH|ZYTX|ZYTL|ZSPD|ZSQD|ZHCC|ZLXY|ZSNJ)$',
            '湖北':r'^(ZHYC|ZHXF|ZHHH|ZHSY|ZHSN)$',
            '高高原':r'^(ZUDC|ZUHY|ZUBD|ZUNZ|ZULZ|ZUZJ|ZURK|ZUKD|ZUGZ|ZUAL|ZPNL|ZPDQ|ZLYS|ZLXH|ZLHB|ZLGM|ZLGL|ZHSN)$',
            '短跑道':r'^(ZGHZ|ZGZJ|ZPJH|ZSFY|ZSJD|ZSSR|ZSWY|ZUMY|ZWYN|ZYTN|ZYCY|ZUDX)$'
        }
        #设置三字码四字码数据
        self.dicelse={
            'TFU':'ZUTF',
            'LLV':'ZBLL',
            'SQD':'ZSSR',
            'LFQ':'ZBLF',
            'WMT':'ZUMT',
            'UBN':'ZMCK',
            'DZH':'ZUDA',
            'WDS':'ZHSY',
            'HUZ':'ZGHZ',
            'WGN':'ZGSY',
            'KHN':'ZSCN',
            'BKK':'VTBS',
            'DLU':'ZPDL',
            'NNG':'ZGNN',
            'BHY':'ZGBH',
        }
        self.key=key
        self.df=self.reading()
    def reading(self):
        # 将第二行设置为标题
        df=pd.read_excel(self.source_file, header=0, skiprows=1)
        if bool(df['落地机场'][0]=='PEK') and self.key==3:
            df = df.merge(self.data34[['三字码', '四字码']], left_on='起飞机场', right_on='三字码', how='left')
            df.rename(columns={'四字码': '起飞机场四字码'}, inplace=True)
            # 保留指定列
            columns_to_keep = ['航班号', '飞机号', '机型', '起飞机场', '撤轮挡时间', 'ACARS滑出时间', 'ACARS起飞时间', 'ACARS落地时间','ACARS推入时间', '落地机场', '落地跑道', '起飞跑道','起飞机场四字码']
        else:
            # 保留指定列
            columns_to_keep = ['航班号', '飞机号', '机型', '起飞机场', '撤轮挡时间', 'ACARS滑出时间', 'ACARS起飞时间', 'ACARS落地时间','ACARS推入时间', '落地机场', '落地跑道', '起飞跑道']
        df = df.loc[:, columns_to_keep]
        df['机型'] = df['机型'].astype(str)
        df['起飞机场'] = df['起飞机场'].astype(str)
        df['落地跑道'] = df['落地跑道'].astype(str) 
        # 替换空值
        df['撤轮挡时间'].fillna(df['ACARS滑出时间'], inplace=True)
        # 将字符串转换为datetime类型
        df['ACARS起飞时间'] = pd.to_datetime(df['ACARS起飞时间'], format='%H:%M:%S')
        df['撤轮挡时间'] = pd.to_datetime(df['撤轮挡时间'], format='%H:%M:%S')
        df['ACARS推入时间'] = pd.to_datetime(df['ACARS推入时间'], format='%H:%M:%S')
        df['ACARS落地时间'] = pd.to_datetime(df['ACARS落地时间'], format='%H:%M:%S')
        # 计算滑行时间
        df['滑出时间'] = df['ACARS起飞时间'] - df['撤轮挡时间']
        df['滑出时间'] = abs(df['滑出时间'])
        df['滑入时间'] = df['ACARS推入时间'] - df['ACARS落地时间']
        df['滑入时间'] = abs(df['滑入时间'])
        
        return df
    def calculate_time(self,pos,minutes,key):
        # 创建字典存储结果
        dic = {}
        # 处理minutes
        time_format = datetime.timedelta(minutes=minutes)
        #key=0为滑出；key=1为滑入
        if key==0:
            for i in pos:
                # 筛选起飞机场等于i的行
                filtered_df = self.df[self.df['落地机场'] == i]
        
                # 删除滑出时间大于time_format的行
                filtered_df = filtered_df[filtered_df['滑出时间'] <= time_format]
                # 计算滑出时间的总和
                filtered_df['滑出时间'] = abs(filtered_df['滑出时间'])
                total_taxiout = filtered_df['滑出时间'].sum()
                
                # 计算滑出时间的平均值
                average_taxiout = str(total_taxiout / len(filtered_df)).split(" ")[-1]
                
                # 存储结果到字典
                dic[i] = average_taxiout
        else:
            for i in pos:
                # 筛选起飞机场等于i的行
                filtered_df = self.df[self.df['起飞机场'] == i]
                
                # 删除滑入时间大于time_format的行
                filtered_df = filtered_df[filtered_df['滑入时间'] <= time_format]
                # 计算滑入时间的总和
                filtered_df['滑入时间'] = abs(filtered_df['滑入时间'])
                total_taxiin = filtered_df['滑入时间'].sum()
                
                # 计算滑入时间的平均值
                average_taxiin = str(total_taxiin / len(filtered_df)).split(" ")[-1]
                
                # 存储结果到字典
                dic[i] = average_taxiin
        return dic
    def calculate_percent1(self,pos,minutes):
        filtered_df = self.df[(self.df['起飞机场'].isin(pos))]
        #平均滑入时间
        time_format = datetime.timedelta(minutes=minutes)
        filtered_df['滑入时间'] = abs(filtered_df['滑入时间'])
        filtered_df = filtered_df[filtered_df['滑入时间'] <= time_format]
        total_taxiin = filtered_df['滑入时间'].sum()
        average_taxiin = str(total_taxiin / len(filtered_df)).split(" ")[-1]

        #跑道占比
        df_all = self.reading()
        df=df_all[(df_all['起飞机场'].isin(pos))]
        sum_n=len(df)
        west = [len(df[df['落地跑道'].isin(self.west_runway)]),"{:.2f}%".format((len(df[df['落地跑道'].isin(self.west_runway)])/sum_n)*100)]
        centre = [len(df[df['落地跑道'].isin(self.center_runway)]),"{:.2f}%".format((len(df[df['落地跑道'].isin(self.center_runway)])/sum_n)*100)]
        east = [len(df[df['落地跑道'].isin(self.east_runway)]),"{:.2f}%".format((len(df[df['落地跑道'].isin(self.east_runway)])/sum_n)*100)]
        data={'西跑道':west,
            '中跑道':centre,
            '东跑道':east}
        
        return data,average_taxiin
    
    def calculate_percent2(self,minutes):
        # 初始化空的结果DataFrame
        result_df = pd.DataFrame(index=self.pos_pattern_rule.keys(),
                                columns=['总个数', '西跑道宽体机个数', '西跑道宽体机占比', '西跑道窄体机个数', '西跑道窄体机占比',
                                        '中跑道宽体机个数', '中跑道宽体机占比', '中跑道窄体机个数', '中跑道窄体机占比',
                                        '东跑道宽体机个数', '东跑道宽体机占比', '东跑道窄体机个数', '东跑道窄体机占比',
                                        '总平均滑入时间', '宽体机平均滑入时间', '窄体机平均滑入时间'])
        total=len(self.df['起飞机场四字码'])
        for region in self.pos_pattern_rule.keys():
            # 获取符合正则表达式的起飞机场四字码
            matching_airports = self.df[self.df['起飞机场四字码'].str.match(self.pos_pattern_rule[region]) & self.df['起飞机场四字码'].notna()]
            # 删除"落地跑道"列值为nan的数据行
            matching_airports = matching_airports[matching_airports['落地跑道'] != 'nan']
            # 去除所有滑入时间大于15分钟的数据
            time_format = datetime.timedelta(minutes=minutes)
            matching_airports = matching_airports[matching_airports['滑入时间'] <= time_format]
            #去除国际航班落地时间在0-6点的数据
            if region in ['澳洲','日韩','美洲','欧洲','韩国','日本','东南亚','印度']:
                matching_airports = matching_airports[matching_airports['ACARS落地时间'].dt.hour > 6]
            # 计算总个数
            total_count = len(matching_airports)
            if total_count!=0:
                # 计算西跑道宽体机个数和占比
                west_wide_count = len(matching_airports[(matching_airports['落地跑道'].isin(self.west_runway)) & (matching_airports['机型'].isin(self.wide))])
                west_narrow_count = len(matching_airports[(matching_airports['落地跑道'].isin(self.west_runway)) & (matching_airports['机型'].isin(self.narrow))])
                west_wide_percentage = "{:.2f}%".format((west_wide_count / total_count)*100)
                west_narrow_percentage = "{:.2f}%".format((west_narrow_count / total_count)*100)


                # 计算中跑道宽体机个数和占比
                center_wide_count = len(matching_airports[(matching_airports['落地跑道'].isin(self.center_runway)) & (matching_airports['机型'].isin(self.wide))])
                center_narrow_count = len(matching_airports[(matching_airports['落地跑道'].isin(self.center_runway)) & (matching_airports['机型'].isin(self.narrow))])
                center_wide_percentage = "{:.2f}%".format((center_wide_count / total_count)*100)
                center_narrow_percentage = "{:.2f}%".format((center_narrow_count / total_count)*100)


                # 计算东跑道宽体机个数和占比
                east_wide_count = len(matching_airports[(matching_airports['落地跑道'].isin(self.east_runway)) & (matching_airports['机型'].isin(self.wide))])
                east_narrow_count = len(matching_airports[(matching_airports['落地跑道'].isin(self.east_runway)) & (matching_airports['机型'].isin(self.narrow))])
                east_wide_percentage = "{:.2f}%".format((east_wide_count / total_count)*100)
                east_narrow_percentage = "{:.2f}%".format((east_narrow_count / total_count)*100)

                # 计算平均滑入时间
                # 计算总平均滑入时间
                total_taxiout = matching_airports['滑入时间'].sum()
                average_taxi_in_time = str(total_taxiout / len(matching_airports)).split(" ")[-1]
                # 计算宽体机平均滑入时间
                wide_total_taxi_in_time = matching_airports[matching_airports['机型'].isin(self.wide)]['滑入时间'].sum()
                wide_average_taxi_in_time = str(wide_total_taxi_in_time / len(matching_airports[matching_airports['机型'].isin(self.wide)])).split(" ")[-1]if len(matching_airports[matching_airports['机型'].isin(self.wide)]) !=0 else 0
                # 计算窄体机平均滑入时间
                narrow_total_taxi_in_time = matching_airports[matching_airports['机型'].isin(self.narrow)]['滑入时间'].sum()
                narrow_average_taxi_in_time = str(narrow_total_taxi_in_time / len(matching_airports[matching_airports['机型'].isin(self.narrow)])).split(" ")[-1] if len(matching_airports[matching_airports['机型'].isin(self.narrow)]) !=0 else 0
                # 更新结果DataFrame
                result_df.loc[region] = [total_count,
                                    west_wide_count, west_wide_percentage, west_narrow_count, west_narrow_percentage,
                                    center_wide_count, center_wide_percentage, center_narrow_count, center_narrow_percentage,
                                    east_wide_count, east_wide_percentage, east_narrow_count, east_narrow_percentage,
                                    average_taxi_in_time, wide_average_taxi_in_time, narrow_average_taxi_in_time]
            else:
                result_df.loc[region] = 0
        
    
            # 添加汇总行
            # 进行计算
            numall=result_df[0:-1]['总个数'].fillna(0).replace('nan', '0').astype(int).sum()
            numwestwide=result_df[0:-1]['西跑道宽体机个数'].fillna(0).replace('nan', '0').astype(int).sum()
            percentwestwide=(numwestwide/numall*100).round(2).astype(str) + '%'
            numwestnarrow=result_df[0:-1]['西跑道窄体机个数'].fillna(0).replace('nan', '0').astype(int).sum()
            percentwestnarrow=(numwestnarrow/numall*100).round(2).astype(str) + '%'

            numcenterwide=result_df[0:-1]['中跑道宽体机个数'].fillna(0).replace('nan', '0').astype(int).sum()
            percentcenterwide=(numcenterwide/numall*100).round(2).astype(str) + '%'
            numcenternarrow=result_df[0:-1]['中跑道窄体机个数'].fillna(0).replace('nan', '0').astype(int).sum()
            percentcenternarrow=(numcenternarrow/numall*100).round(2).astype(str) + '%'

            numeastwide=result_df[0:-1]['东跑道宽体机个数'].fillna(0).replace('nan', '0').astype(int).sum()
            percenteastwide=(numeastwide/numall*100).round(2).astype(str) + '%'
            numeastnarrow=result_df[0:-1]['东跑道窄体机个数'].fillna(0).replace('nan', '0').astype(int).sum()
            percenteastnarrow=(numeastnarrow/numall*100).round(2).astype(str) + '%'


            # 将值为0的timedelta替换为NaN
            result_df['总平均滑入时间'] = result_df['总平均滑入时间'].replace(pd.Timedelta(0), pd.NaT)
            result_df['宽体机平均滑入时间'] = result_df['宽体机平均滑入时间'].replace(pd.Timedelta(0), pd.NaT)
            result_df['窄体机平均滑入时间'] = result_df['窄体机平均滑入时间'].replace(pd.Timedelta(0), pd.NaT)

            # 转换为timedelta类型
            result_df['总平均滑入时间'] = pd.to_timedelta(result_df['总平均滑入时间'])
            result_df['宽体机平均滑入时间'] = pd.to_timedelta(result_df['宽体机平均滑入时间'])
            result_df['窄体机平均滑入时间'] = pd.to_timedelta(result_df['窄体机平均滑入时间'])

            # 计算平均滑入时间（以秒为单位）
            average_total_time = result_df['总平均滑入时间'].mean().total_seconds()
            average_wide_time = result_df['宽体机平均滑入时间'].mean().total_seconds()
            average_narrow_time = result_df['窄体机平均滑入时间'].mean().total_seconds()

            # 将平均滑入时间转换为Timedelta类型
            average_total_time = pd.to_timedelta(average_total_time, unit='seconds')
            average_wide_time = pd.to_timedelta(average_wide_time, unit='seconds')
            average_narrow_time = pd.to_timedelta(average_narrow_time, unit='seconds')

            # 将平均滑入时间转换为字符串格式
            average_total_time_str = str(average_total_time).split()[-1]
            average_wide_time_str = str(average_wide_time).split()[-1]
            average_narrow_time_str = str(average_narrow_time).split()[-1]

            # 将修改后的数据赋值给对应的列
            result_df.loc['汇总'] = [
                numall,
                numwestwide,
                percentwestwide,
                numwestnarrow,
                percentwestnarrow,
                numcenterwide,
                percentcenterwide,
                numcenternarrow,
                percentcenternarrow,
                numeastwide,
                percenteastwide,
                numeastnarrow,
                percenteastnarrow,
                average_total_time_str,
                average_wide_time_str,
                average_narrow_time_str
            ]
            result_df = result_df.astype(str)
            result_df['总平均滑入时间'] = result_df['总平均滑入时间'].str.extract(r'(\d{2}:\d{2}:\d{2})')
            result_df['宽体机平均滑入时间'] = result_df['宽体机平均滑入时间'].str.extract(r'(\d{2}:\d{2}:\d{2})')
            result_df['窄体机平均滑入时间'] = result_df['窄体机平均滑入时间'].str.extract(r'(\d{2}:\d{2}:\d{2})')
        return result_df



st.title("“缩滑”工作进展")
st.write('---------------------------------')
st.write("## 佳木斯和通辽航班移至T3航站楼进出港后的平均进出港时间")

def download_button(file_path, button_text):
    with open(os.path.abspath(file_path), 'rb') as f:
        bytes = f.read()
        b64 = base64.b64encode(bytes).decode()

    # 创建一个名为 "Download File" 的下载链接
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(file_path)}">{button_text}</a>'

    # 在 Streamlit 应用程序中使用按钮链接
    st.markdown(f'<div class="button-container">{href}</div>', unsafe_allow_html=True)

    # 添加 CSS 样式以将链接样式化为按钮
    st.markdown("""
        <style>
        .button-container {
            display: inline-block;
            margin-top: 1em;
        }
        .button-container a {
            background-color: #0072C6;
            border: none;
            color: white;
            padding: 0.5em 1em;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            font-weight: bold;
            border-radius: 4px;
            cursor: pointer;
        }
        .button-container a:hover {
            background-color: #005AA3;
        }
        </style>
    """, unsafe_allow_html=True)
# 用户输入机场三字码
airports1 = st.text_input("输入起飞机场三字码（多个机场以空格分开）",value='JMU TGO')
airport_list1 = airports1.split(' ')

# 用户输入忽略过大滑行时间
ignore_time = st.number_input("输入忽略过大滑行时间（分钟）", min_value=0, step=1, value=15)
is_button=0
source_file1=source_file2=None
col1, col2 = st.columns(2)
with col1:
    source_file1 = st.file_uploader("上传文件(PEK出港)：")
with col2:
    source_file2 = st.file_uploader("上传文件(PEK进港)：")
if st.button('生成处理结果（滑行时间）', key="taxitime"):
    with st.spinner('正在处理数据，请稍等...'):
        if  source_file1 and source_file2 is not None:
            analyze1=ana(source_file1,st,1)
            df1=analyze1.df
            analyze2=ana(source_file2,st,1)
            df2=analyze2.df
            dicout=analyze1.calculate_time(airport_list1,ignore_time,0)
            dicin=analyze2.calculate_time(airport_list1,ignore_time,1)
            dic = {}
            for key in dicin:
                if key in dicout:
                    dic[key] = [dicout[key], dicin[key]]
            df=pd.DataFrame.from_dict(dic, orient='index', columns=['平均滑出时间','平均滑入时间'])
            is_button=1
            
        else:
            st.warning('未检测到文件')
if is_button==1:
    st.write(df)
    is_button=0 


st.write('---------------------------------') 
st.write("## 成都两场、昆明、重庆航班首都机场使用跑道数据")
# 用户输入机场三字码
airports2 = st.text_input("输入起飞机场三字码（多个机场以空格分开）",value='CTU TFU CKG KMG')
airport_list2 = airports2.split(' ')
if st.button('生成处理结果（跑道占比）'):
    with st.spinner('正在处理数据，请稍等...'):
        if source_file2 is not None:
            analyze2=ana(source_file2,st,2)
            df2=analyze2.df
            data,average_taxiin=analyze2.calculate_percent1(airport_list2,ignore_time)
            df = pd.DataFrame(data, index=['数量', '百分比'])
            col1, col2 = st.columns(2)
            with col1:
                st.bar_chart(df.loc['数量'])
                st.write('当月平均滑入时长：'+average_taxiin)
            with col2:
                st.write(df)
            
        else:
            st.warning('未检测到文件')

st.write('---------------------------------') 
st.write("## 按地区和款窄体机分类跑道使用数据对比")

if st.button('生成处理结果（各地区数据）'):
    with st.spinner('正在处理数据，请稍等...'):
        if source_file2 is not None:
            analyze2=ana(source_file2,st,3)
            df2=analyze2.df
            df=analyze2.calculate_percent2(ignore_time)
            
            is_button=1 
        else:
            st.warning('未检测到文件')

if is_button==1:
    st.session_state.df3 = df
    result=df.to_excel(os.path.abspath(r'result.xlsx'))
    download_button(os.path.abspath(r'result.xlsx'), 'download')
st.write(st.session_state.df3)



st.write('---------------------------------') 
st.write('## 柱状图制作')
st.write('### 数据导入:')
col1,col2=st.columns(2)

with col2:
    datadic_selfmake={}
    st.write('输入额外数据以制作柱状图')
    month = st.text_input("输入时间段名称（以空格分开）",value='7月 8月')
    month_list = month.split(' ')
    for month in month_list:
        datastr=st.text_input("输入{}数据（西/中/东跑道占比，以空格分开）".format(month),value='32.1 41.5 26.4')
        datadic_selfmake[month]=[float(num) for num in datastr.split()]
        j=0
        for x in datadic_selfmake[month]:
            x=float(x)
            j=j+x
        if 98<j<102:
            st.success('Done')
        else:
            st.warning('请检查数值')
    if st.button('输入数据',key='button0'):
        data=pd.DataFrame(datadic_selfmake, index=['西跑道','中跑道','东跑道'])
        st.write(data.transpose())
        st.session_state.recorddic.update(datadic_selfmake)
with col1:
    
    st.write('记录当前数据（按地区和款窄体机分类跑道使用数据对比）')
    month = st.text_input("输入时间段名称",value='7月')
    pos=st.text_input("输入地区分类",value='东南亚')
    if st.button('记录数据',key='button1'):
        if st.session_state.df3 is not None and not st.session_state.df3.empty:
            zongjie = st.session_state.df3.loc[pos]
            float_west_wide=float(zongjie['西跑道宽体机占比'][0:-1].replace('nan', '0'))
            float_west_narrow=float(zongjie['西跑道窄体机占比'][0:-1].replace('nan', '0'))
            float_center_wide=float(zongjie['中跑道宽体机占比'][0:-1].replace('nan', '0'))
            float_center_narrow=float(zongjie['中跑道窄体机占比'][0:-1].replace('nan', '0'))
            float_east_wide=float(zongjie['东跑道宽体机占比'][0:-1].replace('nan', '0'))
            float_east_narrow=float(zongjie['东跑道窄体机占比'][0:-1].replace('nan', '0'))
            st.session_state.recorddic[month+pos]=[float_west_wide+float_west_narrow,float_center_wide+float_center_narrow,float_east_wide+float_east_narrow]
            st.write(pd.DataFrame({'西跑道':float_west_wide+float_west_narrow,
                                   '中跑道':float_center_wide+float_center_narrow,
                                   '东跑道':float_east_wide+float_east_narrow},index=[month+pos]))
            st.success('记录当前数据成功')
        else:
            st.warning('未检测到有效数据')
st.write('---------------------')
st.write('### 结果输出:')
# 绘制柱状图
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False
fig, ax = plt.subplots(figsize=(4,2), dpi=100)
datadic=st.session_state.recorddic
months = list(datadic.keys())
runways = ['西跑道', '中跑道', '东跑道']
data = np.array(list(datadic.values()))
st.write(pd.DataFrame(datadic,index=runways).transpose())

# 绘制柱状图
fig, ax = plt.subplots()
width = 0.2  # 柱子的宽度
x = np.arange(len(runways))

for i in range(len(months)):
    ax.bar(x + i * width, data[i], width, label=months[i])

# 添加数值标签
for i in range(len(months)):
    for j in range(len(runways)):
        ax.text(x[j] + i * width, data[i][j], str(data[i][j]), ha='center', va='bottom')

# 设置图例和轴标签
ax.set_xticks(x + width * (len(months) - 1) / 2)
ax.set_xticklabels(runways)
ax.legend(months)
ax.set_xlabel('跑道')
ax.set_ylabel('百分比：%')
ax.set_title('首都机场落地跑道占比柱状图')

# 显示图形
st.pyplot(plt)
