#!/usr/bin/python
# -*- coding:utf-8 -*-

import time
import datetime
import ADS1256
import RPi.GPIO as GPIO
import sqlite3
import signal
import sys

sensitivity = 75.4

# 创建数据库连接，将数据库保存在u盘
# 数据库名dftcpv
conn = sqlite3.connect('/mnt/udisk/dftcpv.db')
c = conn.cursor()

# 创建表 dftcpv_irradiance_data
# 存储两种数据： 获取时间 Get_time 并作为主键，辐射照度irradiance
c.execute('''
    CREATE TABLE IF NOT EXISTS dftcpv_irradiance_data (
        Get_time DATETIME PRIMARY KEY,
        Irradiance REAL
    )
''')

# 定义一个处理中断信号的函数来中断读取
def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    GPIO.cleanup()
    conn.close()
    sys.exit(0)

# 设置中断信号处理函数
signal.signal(signal.SIGINT, signal_handler)

try:
    ADC = ADS1256.ADS1256()
    ADC.ADS1256_init()

    data_to_insert = []  # 创建一个空列表来收集数据

    # 1s读一次数据（辐射度）
    while(1):
        Irradiance = 0  # 辐射照度初始化
        #reference = 30532  # 通道电压的被减值？
        Get_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ADC_Value = ADC.ADS1256_GetAll()

        # 通道6、7的值（单位是微伏）
        ADC_6_value = int((ADC_Value[6]*5.0/0x7fffff)*1e+06)
        ADC_7_value = int((ADC_Value[7]*5.0/0x7fffff)*1e+06)

        # 计算辐射照度
        Irradiance = abs(ADC_7_value-ADC_6_value)/sensitivity

        # 将数据添加到列表
        data_to_insert.append((Get_time, Irradiance))

        # 每60秒将数据统一插入到数据库
        if int(time.time()) % 60 == 0 and data_to_insert:
            c.executemany("INSERT INTO dftcpv_irradiance_data VALUES (?, ?)", data_to_insert)
            conn.commit()
            data_to_insert = []  # 清空列表

        time.sleep(1)  # 每1秒钟执行一次

except:
    GPIO.cleanup()
finally:
    # 关闭数据库连接
    conn.close()

print ("\r\nProgram end     ")
exit()