# coding=utf-8
#
# The MIT License (MIT)
#
# Copyright (c) 2016-2017 yutiansut/QUANTAXIS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import csv
import datetime
import json
import os
import random
import re
import sys
import time

import apscheduler
import numpy as np
import pandas as pd
import pymongo
from QUANTAXIS import *
from QUANTAXIS import (QA_Market, QA_Portfolio, QA_QAMarket_bid, QA_Risk,
                       __version__)
from QUANTAXIS.QAARP.QAAccount import QA_Account
from QUANTAXIS.QABacktest.QAAnalysis import QA_backtest_analysis_start
from QUANTAXIS.QAFetch.QAQuery import (QA_fetch_index_day, QA_fetch_stock_day,
                                       QA_fetch_stock_info,
                                       QA_fetch_stocklist_day,
                                       QA_fetch_trade_date)
from QUANTAXIS.QASU.save_backtest import (QA_SU_save_account_message,
                                          QA_SU_save_account_to_csv)
from QUANTAXIS.QAUtil import (QA_Setting, QA_util_get_real_date,
                              QA_util_log_info)

from QUANTAXIS.QATask import QA_Queue
from tabulate import tabulate

import configparser
import queue
from functools import wraps, update_wrapper


class QA_Backtest_stock_day():
    '因为涉及很多不继承类的情况,所以先单列出来'
    account = QA_Account()
    market = QA_Market()
    bid = QA_QAMarket_bid()
    setting = QA_Setting()
    clients = setting.client
    user = setting.QA_setting_user_name
    market_data = []
    today = ''

    def __init__(self):

        self.account = QA_Account()
        self.market = QA_Market()
        self.bid = QA_QAMarket_bid()
        self.setting = QA_Setting()
        self.clients = self.setting.client
        self.user = self.setting.QA_setting_user_name
        self.market_data = []
        self.today = ''

    def __QA_backtest_init(self):
        """既然是被当做装饰器使用,就需要把变量设置放在装饰函数的前面,把函数放在装饰函数的后面"""

        # 设置回测的开始结束时间
        self.strategy_start_date = str('2017-01-05')
        self.strategy_end_date = str('2017-07-01')
        # 设置回测标的,是一个list对象,不过建议只用一个标的
        # gap是回测时,每日获取数据的前推日期(交易日)
        self.strategy_gap = int(60)
        # 设置全局的数据库地址,回测用户名,密码,并初始化
        self.setting.QA_util_sql_mongo_ip = str('127.0.0.1')
        self.setting.QA_setting_user_name = str('admin')
        self.setting.QA_setting_user_password = str('admin')
        self.setting.QA_setting_init()
        # 回测的名字
        self.strategy_name = str('example')
       # 股票的交易日历,真实回测的交易周期,和交易周期在交易日历中的id
        self.trade_list = QA_fetch_trade_date(
            self.setting.client.quantaxis.trade_date)
        self.benchmark_code = 'hs300'
        """
        这里会涉及一个区间的问题,开始时间是要向后推,而结束时间是要向前推,1代表向后推,-1代表向前推
        """
        self.start_real_date = QA_util_get_real_date(
            self.strategy_start_date, self.trade_list, 1)
        self.start_real_id = self.trade_list.index(self.start_real_date)
        self.end_real_date = QA_util_get_real_date(
            self.strategy_end_date, self.trade_list, -1)
        self.end_real_id = self.trade_list.index(self.end_real_date)
        self.strategy_stock_list = ['000001', '000002', '000004']
        self.account.init_assest = 1000000
        self.backtest_bid_model = 'market_price'
    def __QA_backtest_init_class(self):
        """
        这是模型内部的 初始化,主要是初始化一些账户和市场资产
        写成了私有函数
        @yutiansut
        2017/7/20
        """

        # 重新初始账户资产

        self.setting.QA_setting_init()
        self.account.init()

        # 重新初始化账户的cookie
        self.account.account_cookie = str(random.random())
        # 初始化股票池的市场数据
        self.market_data = QA_fetch_stocklist_day(
            self.strategy_stock_list, self.setting.client.quantaxis.stock_day,
            [self.trade_list[self.start_real_id - int(self.strategy_gap)],
             self.trade_list[self.end_real_id]])

    def __QA_backtest_start(self, *args, **kwargs):
        """
        这个是回测流程开始的入口
        """
        assert len(self.strategy_stock_list) > 0
        assert len(self.trade_list) > 0
        assert isinstance(self.start_real_date, str)
        assert isinstance(self.end_real_date, str)

        assert len(self.market_data) == len(self.strategy_stock_list)

        QA_util_log_info('QUANTAXIS Backtest Engine Initial Successfully')
        QA_util_log_info('Basical Info: \n' + tabulate(
            [[str(__version__), str(self.strategy_name)]], headers=('Version', 'Strategy_name')))
        QA_util_log_info('Stock_List: \n' +
                         tabulate([self.strategy_stock_list]))

        # 初始化报价模式
        self.__QA_backtest_set_bid_model(self)
        self.__messages = []


    



    def __QA_backtest_excute_bid(self,__code,__amount,__towards,__bid_model):
        """

        """

        self.__QA_backtest_set_bid_model()
        if self.bid.bid['bid_model'] == 'strategy':
            __bid_price = __result['price']
        else:
            __bid_price = self.bid.bid['price']

        __bid = self.bid.bid

        __bid['order_id'] = str(random.random())
        __bid['user'] = self.setting.QA_setting_user_name
        __bid['strategy'] = self.strategy_name
        __bid['code'] = __code
        __bid['date'] = __date
        __bid['price'] = __bid_price
        __bid['amount'], __bid['amount_model'] = self.__QA_bid_amount(
            __result['amount'], __amount)

        if __result == 1:
            # 这是买入的情况
            __bid['towards'] = 1
            __message = self.market.receive_bid(
                __bid, self.setting.client)

            if float(self.account.message['body']['account']['cash'][-1]) > \
                    float(__message['body']['bid']['price']) * \
                    float(__message['body']['bid']['amount']):
                    # 这里是买入资金充足的情况
                    # 不去考虑
                pass
            else:
                # 如果买入资金不充足,则按照可用资金去买入
                __message['body']['bid']['amount'] = int(float(
                    self.account.message['body']['account']['cash'][-1]) / float(
                        float(str(__message['body']['bid']['price'])[0:5]) * 100)) * 100

            if __message['body']['bid']['amount'] > 0:
                # 这个判断是为了 如果买入资金不充足,所以买入报了一个0量单的情况
                #如果买入量>0, 才判断为成功交易
                self.account.QA_account_receive_deal(__message)
        elif __result == 0:
            # 如果买入状态为0,则不进行任何买入操作
            pass

        # 下面是卖出操作,这里在卖出前需要考虑一个是否有仓位的问题:
        # 因为在股票中是不允许卖空操作的,所以这里是股票的交易引擎和期货的交易引擎的不同所在

        if __result == -1 and __hold == 1:
            __bid['towards'] = -1
            __message = self.market.receive_bid(
                __bid, self.setting.client)

            self.account.QA_account_receive_deal(__message)
    def __QA_backtest_set_bid_model(self):
    
        if self.backtest_bid_model == 'market_price':
            self.bid.bid['price'] = 'market_price'
            self.bid.bid['bid_model'] = 'auto'
        elif self.backtest_bid_model == 'close_price':
            self.bid.bid['price'] = 'close_price'
            self.bid.bid['bid_model'] = 'auto'
        elif self.backtest_bid_model == 'strategy':
            self.bid.bid['price'] = 0
            self.bid.bid['bid_model'] = 'strategy'
        else:
            QA_util_log_info('support bid model')
            sys.exit()
    def __check_state(self,bid_price,bid_amount):
        pass
    def __QA_bid_amount(self, __strategy_amount, __amount):
        if __strategy_amount == 'mean':
            return float(float(self.account.message['body']['account']['cash'][-1]) /
                         len(self.strategy_stock_list)), 'price'
        elif __strategy_amount == 'half':
            return __amount * 0.5, 'amount'
        elif __strategy_amount == 'all':
            return __amount, 'amount'

    def __QA_get_data_from_market(self, __id, stock_id):
        if __id > self.strategy_gap + 1:
            index_of_day = __id
            index_of_start = index_of_day - self.strategy_gap + 1
            return self.market_data[stock_id][index_of_start:index_of_day + 1]
        else:
            return 'not_enough_data'
    
    def __QA_data_handle(self, __id, __stock_id):
        "已经废弃"
        market_data = self.__QA_get_data_from_market(__id, __stock_id)
        __message = self.account.message

        return {'market': market_data, 'account': __message}
    def __backtest_every_day_trading(self, i, func, *arg, **kwargs):
        
        # 正在进行的交易日期
        __running_date = self.trade_list[i]
        QA_util_log_info(
            '=================daily hold list====================')
        QA_util_log_info('in the begining of ' + __running_date)
        QA_util_log_info(
            tabulate(self.account.message['body']['account']['hold']))
        for __j in range(0, len(self.strategy_stock_list)):
            if __running_date in [l[6] for l in self.market_data[__j]] and \
                    [l[6] for l in self.market_data[__j]].index(__running_date) \
                    > self.strategy_gap + 1:

                __data = self.__QA_data_handle(
                    [__l[6] for __l in self.market_data[__j]].index(__running_date), __j)
                __amount = 0
                for item in __data['account']['body']['account']['hold']:

                    if self.strategy_stock_list[__j] in item:
                        __amount = __amount + item[3]
                if __amount > 0:
                    __hold = 1
                else:
                    __hold = 0

                __result = func(self, *arg, **kwargs)

                if float(self.account.message['body']['account']['cash'][-1]) > 0:
                    self.QA_backtest_excute_bid(
                        __result, __running_date, __hold,
                        str(self.strategy_stock_list[__j])[0:6], __amount)

                else:
                    QA_util_log_info('not enough free money')
            else:
                pass
    def __end_of_trading(self, *arg, **kwargs):
        # 在回测的最后一天,平掉所有仓位(回测的最后一天是不买入的)
        # 回测最后一天的交易处理

        while len(self.account.hold) > 1:
            __hold_list = self.account.hold[1::]
            pre_del_id = []
            for item_ in range(0, len(__hold_list)):
                if __hold_list[item_][3] > 0:
                    __last_bid = self.bid.bid
                    __last_bid['amount'] = int(__hold_list[item_][3])
                    __last_bid['order_id'] = str(random.random())
                    __last_bid['price'] = 'close_price'
                    __last_bid['code'] = str(__hold_list[item_][1])
                    __last_bid['date'] = self.trade_list[self.end_real_id]
                    __last_bid['towards'] = -1
                    __last_bid['user'] = self.setting.QA_setting_user_name
                    __last_bid['strategy'] = self.strategy_name
                    __last_bid['bid_model'] = 'auto'
                    __last_bid['status'] = '0x01'
                    __last_bid['amount_model'] = 'amount'

                    __message = self.market.receive_bid(
                        __last_bid, self.setting.client)
                    _remains_day = 0
                    while __message['header']['status'] == 500:
                        # 停牌状态,这个时候按停牌的最后一天计算价值(假设平仓)

                        __last_bid['date'] = self.trade_list[self.end_real_id - _remains_day]
                        _remains_day += 1
                        __message = self.market.receive_bid(
                            __last_bid, self.setting.client)

                        # 直到市场不是为0状态位置,停止前推日期

                    self.__messages = self.account.QA_account_receive_deal(
                        __message)
                else:
                    pre_del_id.append(item_)
            pre_del_id.sort()
            pre_del_id.reverse()
            for item_x in pre_del_id:
                __hold_list.pop(item_x)
    def __end_of_backtest(self, *arg, **kwargs):
    
        # 开始分析
        QA_util_log_info('start analysis====\n' +
                         str(self.strategy_stock_list))
        QA_util_log_info('=' * 10 + 'Trade History' + '=' * 10)
        QA_util_log_info('\n' + tabulate(self.account.history,
                                         headers=('date', 'code', 'price', 'towards',
                                                  'amounts', 'order_id', 'trade_id', 'commission')))
        QA_util_log_info(tabulate(self.account.detail,
                                  headers=('date', 'code', 'price', 'amounts', 'order_id',
                                           'trade_id', 'sell_price', 'sell_order_id',
                                           'sell_trade_id', 'sell_date', 'left_amount',
                                           'commission')))
        __exist_time = int(self.end_real_id) - int(self.start_real_id) + 1
        self.__benchmark_data = QA_fetch_index_day(
            self.benchmark_code, self.start_real_date,
            self.end_real_date)
        if len(self.__messages) > 1:
            performace = QA_backtest_analysis_start(
                self.setting.client, self.strategy_stock_list, self.__messages,
                self.trade_list[self.start_real_id:self.end_real_id + 1],
                self.market_data, self.__benchmark_data)
            _backtest_mes = {
                'user': self.setting.QA_setting_user_name,
                'strategy': self.strategy_name,
                'stock_list': performace['code'],
                'start_time': self.strategy_start_date,
                'end_time': self.strategy_end_date,
                'account_cookie': self.account.account_cookie,
                'annualized_returns': performace['annualized_returns'],
                'benchmark_annualized_returns': performace['benchmark_annualized_returns'],
                'assets': performace['assets'],
                'benchmark_assets': performace['benchmark_assets'],
                'trade_date': performace['trade_date'],
                'total_date': performace['total_date'],
                'win_rate': performace['win_rate'],
                'alpha': performace['alpha'],
                'beta': performace['beta'],
                'sharpe': performace['sharpe'],
                'vol': performace['vol'],
                'benchmark_vol': performace['benchmark_vol'],
                'max_drop': performace['max_drop'],
                'exist': __exist_time,
                'time': datetime.datetime.now()
            }
            QA_SU_save_backtest_message(_backtest_mes, self.setting.client)
            QA_SU_save_account_message(self.__messages, self.setting.client)
            QA_SU_save_account_to_csv(self.__messages)
        # QA.QA_SU_save_backtest_message(analysis_message, self.setting.client)

    def QA_backtest_send_order(self,code,amount,towards,bid_model='strategy'):
        """
        2017/8/4
        委托函数
        在外部封装的一个报价接口,尽量满足和实盘一样的模式
        
        输入
        =============
        买入/卖出
        股票代码
        买入/卖出数量
        委托模式*
            0 限价委托； 上海限价委托/ 深圳限价委托
            1 市价委托(深圳对方最优价格)
            2 市价委托(深圳本方最优价格)
            3 市价委托(深圳即时成交剩余撤销)
            4 市价委托(上海五档即成剩撤/ 深圳五档即成剩撤)
            5 市价委托(深圳全额成交或撤销)
            6 市价委托(上海五档即成转限价)


        输出
        =============
        委托状态/委托id
        成交状态/成交id/成交量/成交价

        错误/错误id/
        """
        # step1 检查委托方式/剩余资金
        pass


    def QA_backtest_get_market_data(self, code, date):
        '这个函数封装了关于获取的方式'
        index_of_code = self.strategy_stock_list.index(code)
        if date in [l[6] for l in self.market_data[index_of_code]]:
            index_of_date = [l[6]
                             for l in self.market_data[index_of_code]].index(date)
        return self.__QA_get_data_from_market(self, index_of_date, index_of_code)

    @classmethod
    def load_strategy(__backtest_cls, func, *arg, **kwargs):
        '策略加载函数'

        # 首先判断是否能满足回测的要求`
        _info = {}
        _info['stock_list'] = __backtest_cls.strategy_stock_list
        __messages = {}
        __backtest_cls.__init_cash_per_stock = int(
            float(__backtest_cls.account.init_assest) / len(__backtest_cls.strategy_stock_list))

        # 策略的交易日循环
        for i in range(int(__backtest_cls.start_real_id), int(__backtest_cls.end_real_id) - 1, 1):
            __backtest_cls.running_date = __backtest_cls.trade_list[i]
            QA_util_log_info(
                '=================daily hold list====================')
            QA_util_log_info('in the begining of ' +
                             __backtest_cls.running_date)
            QA_util_log_info(
                tabulate(__backtest_cls.account.message['body']['account']['hold']))
            __backtest_cls.today = __backtest_cls.running_date

            func(*arg, **kwargs)

        # 最后一天
        __backtest_cls.__end_of_trading(__backtest_cls)



    @classmethod
    def backtest_init(__backtest_cls, func, *arg, **kwargs):
        def __init_backtest(__backtest_cls, *arg, **kwargs):
            __backtest_cls.__QA_backtest_init(__backtest_cls)
            func(*arg, **kwargs)
            __backtest_cls.__QA_backtest_init_class(__backtest_cls)
        return __init_backtest(__backtest_cls)
    @classmethod
    def before_backtest(__backtest_cls, func, *arg, **kwargs):
        func(*arg, **kwargs)
        __backtest_cls.__QA_backtest_start(__backtest_cls)

    @classmethod
    def end_backtest(__backtest_cls, func, *arg, **kwargs):
        # yield __backtest_cls.cash
        __backtest_cls.__end_of_backtest(__backtest_cls, func, *arg, **kwargs)
        return func(*arg, **kwargs)