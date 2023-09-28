#!/usr/bin/python
# -*- coding:utf-8 -*-

import time
import datetime
import ADS1256
import RPi.GPIO as GPIO
import sqlite3
import signal
import sys
import logging

# 日志记录故障设置
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s  %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S',
                   filename='/home/dftc/PV/dftcpv_database/dftcpv_main_smp.log')

# 创建数据库连接，将数据库保存在u盘
# 数据库名dftcpv_smp
conn = sqlite3.connect('/home/dftc/PV/dftcpv_database/dftcpv_smp.db')
c = conn.cursor()

# 创建表 dftcpv_smp_irradiance_data
# 存储两种数据： 获取时间 Get_time 并作为主键，辐射照度irradiance
c.execute('''
    CREATE TABLE IF NOT EXISTS dftcpv_smp_irradiance_data (
        Get_time DATETIME PRIMARY KEY,
        Irradiance REAL
    )
''')

try:
    ADC = ADS1256.ADS1256()
    ADC.ADS1256_init()

    data_to_insert = []  # 创建一个空列表来收集数据

    # 5mins读一次数据（辐射度）
    while(1):
        Irradiance = 0  # 辐射照度初始化
        Get_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        ADC_Value = ADC.ADS1256_GetAll()

        # 通道6、7的值（单位是伏）
        ADC_6_value = ADC_Value[6]*5.0/0x7fffff
        ADC_7_value = ADC_Value[7]*5.0/0x7fffff #0-1V

        # 计算辐射照度W/m^2
        Irradiance = abs(ADC_7_value-ADC_6_value)*2000-200
        #print((Get_time,Irradiance))
        #print("\r",(ADC_6_value,ADC_7_value,Get_time,Irradiance),end="",flush=True)

        # 将数据添加到列表
        data_to_insert.append((Get_time, Irradiance))

        # 每1小时将数据统一插入到数据库
        if int(time.time()) % 3600 == 0 and data_to_insert:
            c.executemany("INSERT INTO dftcpv_smp_irradiance_data VALUES (?, ?)", data_to_insert)
            conn.commit()
            data_to_insert = []  # 清空列表

        time.sleep(300)  # 每5分钟执行一次

# 日志记录程序执行遇到的所有异常
except:
    logging.error('There are something wrong', exc_info=True)
    GPIO.cleanup()    

finally:
    # 关闭数据库连接
    conn.close()

print ("\r\nProgram end     ")
exit()