# Builder : Sam
# Build Time: 2021-11-20
# Description： Small cap quantitative trading strategy

def initialize(context):
    run_daily(period,time='every_bar')
​
    # 获取上证指数和深证综指的成分股代码并连接，即为全A股市场所有股票的股票代码
    g.total_stocks = get_index_stocks('000001.XSHG') + get_index_stocks('399106.XSHE')
    
    # 设定好要交易的股票数量
    g.stocks_num = 10
    
    # 记录策略进行天数
    g.days = 0
    
    # 设定交易周期
    g.period = 7
    
    # 设定止盈
    g.profit_line = 1
    
    # 设定止损
    g.loss_line = -1
​
#                           退市        ST      停牌        涨停
def stockfilter(stock_list, del_delist, del_st, del_paused, del_hl):
​
    current_data = get_current_data()
​
    if del_delist:  # 删除退市
        stock_list = [stock for stock in stock_list if not '退' in current_data[stock].name]
        print('删除退市股票')
​
    if del_st:  # 删除ST
        stock_list = [stock for stock in stock_list if not current_data[stock].is_st]
        print('删除ST股票')
​
    if del_paused: # 删除停牌
        stock_list = [stock for stock in stock_list if not current_data[stock].paused]
        print('删除停牌股票')
​
    if del_hl:  # 删除涨停
        stock_list = [stock for stock in stock_list if not current_data[stock].day_open >= current_data[stock].high_limit]
        print('删除涨停股票')
        
    return stock_list
    
# 代码：找出市值排名最小的前stocksnum只股票作为要买入的股票
def period(context):
​
    # 记录交易周期
    if g.days % g.period == 0:
​
        # 删除所有已经退市/ST/停牌/涨停的股票
        g.security = stockfilter(g.total_stocks, True, True, True, True)
​
        # 选出在剩余股票中选出的市值排名最小的前stocks_num只股票
        # query()填写需要查询的对象,可以是整张表,也可以是表中的多个字段或计算出的结果
        result = query(valuation.code  # valuation是内置市值数据对象, code: 股票代码
                    # filter填写过滤条件,多个过滤条件可以用逗号隔开,或者用and,or这样的语法
                    ).filter(
                        # in_ 判断某个字段的值是否在列表之中(一般用于查询多个标的)
                        valuation.code.in_(g.security)
                    # order_by 填写排序条件
                    ).order_by(
                        valuation.market_cap.asc()  # desc()降序排列; asc()升序排列
                    # limit 限制返回的个数
                    ).limit(g.stocks_num)
​
        # get_fundamentals  查询财务数据
        target = get_fundamentals(result)

        # 选取股票的代码并转为list
        buylist = list(target['code'])

        # 判断当下账户中是否存在股票
        if context.portfolio.positions == {}:

            # 买入要买入的股票，买入金额为可用资金的share分之一
            # 将资金分成share份
            share = len(buylist)
            position_per_stk = context.portfolio.cash/share
            # 用position_per_stk大小的share份资金去买buylist中share个的股票
            for stock in buylist:
                order_value(stock, position_per_stk)
            print('买入成功')

        # 若当下账户中已存在股票
        else:
            for stock in context.portfolio.positions:

                # 若已持有的股票的市值已经不够小而不在买入的buylist中，则全部卖出这部分股票
                if stock not in buylist: # 如果stock不在buylist
                    order_target(stock, 0) # 调整stock的持仓为0，即卖出
                    print("股票" + stock + "不在购买清单中，因此全部卖出")
                # 若已持有的股票在即将买入的buglist中，但已经到达设定的止盈或止损位，则清仓这部分股票

                # 若已持有的股票在买入的buylist中
                else:
                    cost=context.portfolio.positions[stock].avg_cost    #查询目前账户内每只股票的成本价
                    price=context.portfolio.positions[stock].price      #查询目前账户内每只股票的现价
                    if (price/cost - 1) > g.profit_line: #如果stock大于止盈线
                        order_target(stock, 0) #调整stock的持仓为0，即卖出
                        print("股票" + stock + "在buylist中，但已经触发止盈，因此全部卖出")
                    elif (price/cost - 1) < g.loss_line:    #如果stock小于止损线
                        order_target(stock, 0) #调整stock的持仓为0，即卖出
                        print("股票" + stock + "在buylist中，但已经触发止损，因此全部卖出")
                    else:   #如果stock既没有大于止盈也没有小于止损，因此不做操作
                        print("股票" + stock + "在buylist中，但因未到达止盈/止损，因此不做仓位调整")
                    # 将以上三种情况的stock从buylist中移除，以免进行重复操作
                    buylist.remove(stock)

            # 买入要买入的股票，买入金额为可用资金的share分之一
            # 将资金分成share份
            share = len(buylist)
            position_per_stk = context.portfolio.cash/share
            # 用position_per_stk大小的share份资金去买buylist中share个的股票
            for stock in buylist:
                order_value(stock, position_per_stk)
            print('买入成功')
​
    # 交易日加一
    g.days = g.days + 1