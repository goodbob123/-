## Designed by 陳若婕 Chen Ruo-Jie，學號 B08902009
class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['ETH-USDT'],
            },
        }
        self.period = 30 * 60
        self.options = {}

        # user defined class attribute
        self.max_length = 500  #定義最大取樣長度
        self.VOL_TREND_DAYS_NEED = 3
        
        self.last_kd_cross_status = None
        self.last_ma_cross_status = None
        self.last_macd_cross_status = None
        self.last_rsi_cross_status = None
        self.high_price_trace = np.array([])
        self.low_price_trace = np.array([])
        self.close_price_trace = np.array([])
        self.volume_trace = np.array([])
        self.ma_20 = 20  #定義20個週期，用以計算是否20週期均線向上
        self.ma_10 = 10  #定義10個週期，用以計算長均線
        self.ma_5 = 5    #定義5個週期，用以計算短均線
        self.last_ma_20 = 0
        self.now_volume = 0
        self.last_volume = 0
        self.rsi_14 = 14
        self.rsi_short = 5
        self.rsi_long = 10
        self.MA_UP = 1
        self.MA_DOWN = 2
        self.MA20_UP = 1
        self.MA20_DOWN = 2
        self.VOL_DOUBLED_UP = 1
        self.VOL_DOUBLED_DOWN = 2
        self.VOL_SHRINKED_UP = 3
        self.VOL_SHRINKED_DOWN = 4
        self.TREND_UP = 1
        self.TREND_DOWN = 2
        self.RSI14_OVER_BUY = 1
        self.RSI14_OVER_SELL = 2
        self.RSI_UP = 1
        self.RSI_DOWN = 2
        self.K_UP = 1
        self.K_DOWN = 2
        self.MACD_UP = 1
        self.MACD_DOWN = 2


    # MA CROSS
    # check whether ma 5 is above ma 10, used for check ma cross
    def get_current_ma_cross(self):
        ma5 = talib.SMA(self.close_price_trace, self.ma_5)[-1]
        ma10 = talib.SMA(self.close_price_trace, self.ma_10)[-1]
        if np.isnan(ma5) or np.isnan(ma10):
            return None
        if ma5 > ma10:
            return self.MA_UP
        return self.MA_DOWN

    # MA 20 UP
    # check whether ma 20 is toward up status
    def get_current_ma_20(self):
        ma20 = talib.SMA(self.close_price_trace, self.ma_20)[-1]
        if np.isnan(ma20):
            return None
        if (ma20 > self.last_ma_20) and (self.last_ma_20 != 0):
            self.last_ma_20 = ma20
            return self.MA20_UP
        self.last_ma_20 = ma20
        return self.MA20_DOWN

    # RSI CROSS
    # check whether rsi short is above rsi long, used for check rsi cross
    def get_current_rsi_cross(self):
        s_rsi = talib.RSI(self.close_price_trace, self.rsi_short)[-1]
        l_rsi = talib.RSI(self.close_price_trace, self.rsi_long)[-1]
        if np.isnan(s_rsi) or np.isnan(l_rsi):
            return None
        if s_rsi > l_rsi:
            return self.RSI_UP
        return self.RSI_DOWN

    # RSI 14 OVER
    # check whether rsi 14 >= 70 or <= 30
    def get_current_rsi_14(self):
        rsi14 = talib.RSI(self.close_price_trace, self.rsi_14)[-1]
        if np.isnan(rsi14):
            return None
        if rsi14 >= 70:
            return self.RSI14_OVER_BUY
        if rsi14 <= 30:
            return self.RSI14_OVER_SELL
        return 0

    # KD CROSS
    # check whether k 9 is above d 9, used for check kd cross
    # Using default:fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0
    def get_current_kd_cross(self):
        slowk, slowd  = talib.STOCH(self.high_price_trace, self.low_price_trace, self.close_price_trace)
        if np.isnan(slowk[-1]) or np.isnan(slowd[-1]):
            return None, None
        if slowk[-1] > slowd[-1]:
            return self.K_UP, slowk[-1]
        return self.K_DOWN, slowk[-1]

    # MACD CROSS
    # Using default: fastperiod = 12, slowperiod = 26, signalperiod = 9
    # check whether MACD above MACD_SIGNAL
    def get_current_macd_cross(self):
        macd, signal, hist  = talib.MACD(self.close_price_trace)
        if np.isnan(macd[-1]) or np.isnan(signal[-1]):
            return None
        if macd[-1] > signal[-1]:
            return self.MACD_UP
        return self.MACD_DOWN
    
    # VOLUME STATUS
    # check whether volume is (increased and doubled) or (shrink under half)
    # 本週期成交量若為上週期一倍以上，表示量倍增，表示原盤整趨勢可能改變向上或向下
    # 本週期成交量若不及上週期一半，表示量急縮，上漲無量或下跌無量，原下跌或上漲趨勢可能可能反向改變
    def get_volume_increase_status(self):
        if self.last_volume == 0:
            self.last_volume = self.now_volume
            return None
        if (self.now_volume > (self.last_volume * 2)):
            self.last_volume = self.now_volume
            if (self.close_price_trace[-1]) > (self.close_price_trace[-2]):
               return self.VOL_DOUBLED_UP
            if (self.close_price_trace[-1]) < (self.close_price_trace[-2]):
               return self.VOL_DOUBLED_DOWN
        if (self.now_volume < (self.last_volume / 2)):
            self.last_volume = self.now_volume
            if (self.close_price_trace[-1]) > (self.close_price_trace[-2]):
               return self.VOL_SHRINKED_DOWN
            if (self.close_price_trace[-1]) < (self.close_price_trace[-2]):
               return self.VOL_SHRINKED_UP
        self.last_volume = self.now_volume
        return 0

    # VOLUME OVER AVERAGE 20%
    # 本週期成交量大於VOL_TREND_DAYS_NEED日之次均量的20%，表示趨勢可能改變向上或向下
    # VOL_TREND_DAYS_NEED均量就是VOL_TREND_DAYS_NEED*(24*60*60/self.period)次的均量)
    def get_volume_trend_change(self):
        vols_need = self.VOL_TREND_DAYS_NEED * (24 * 60 * 60 / self.period)
        vol_days_average = talib.SMA(self.volume_trace, vols_need)[-1]
        price_days_average = talib.SMA(self.close_price_trace, vols_need)[-1]
        if np.isnan(vol_days_average) or np.isnan(price_days_average):
            return None
        if self.volume_trace[-1] > (1.2 * vol_days_average):
            if (self.close_price_trace[-1]) > (self.close_price_trace[-2]):
               return self.TREND_UP
            if (self.close_price_trace[-1]) < (self.close_price_trace[-2]):
               return self.TREND_DOWN
        return 0


    # called every self.period
    def trade(self, information):
        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        high_price = information['candles'][exchange][pair][0]['high']
        low_price = information['candles'][exchange][pair][0]['low']
        close_price = information['candles'][exchange][pair][0]['close']
        close_volume = information['candles'][exchange][pair][0]['volume']

        # add latest high price into trace
        self.high_price_trace = np.append(self.high_price_trace, [float(high_price)])
        # add latest low price into trace
        self.low_price_trace = np.append(self.low_price_trace, [float(low_price)])
        # add latest close price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # add latest volume into trace
        self.volume_trace = np.append(self.volume_trace, [float(close_volume)])
        
        # only keep max length of max_length count elements
        self.high_price_trace = self.high_price_trace[-self.max_length:]
        self.low_price_trace = self.low_price_trace[-self.max_length:]
        self.close_price_trace = self.close_price_trace[-self.max_length:]
        self.volume_trace = self.volume_trace[-self.max_length:]

        ma_indicator = 1
        macd_indicator = 0
        rsi_indicator = 2
        kd_indicator = 2
        vol_indicator = 0
        kd_buy_weight = 0     #KD因素佔買權重:3(起始值為0)
        kd_sell_weight = 0    #KD因素佔賣權重:-3(起始值為0)
        ma_cross_buy_weight = 0     #MA均線因素佔買權重(起始值為0)
        ma_cross_sell_weight = 0    #MA均線因素佔賣權重(起始值為0)
        macd_cross_buy_weight = 0     #MACD因素佔買權重(起始值為0)
        macd_cross_sell_weight = 0    #MACD因素佔賣權重(起始值為0)        
        rsi_cross_buy_weight = 0    #RSI交叉因素佔買權重(起始值為0)
        rsi_cross_sell_weight = 0   #RSI交叉因素佔賣權重(起始值為0)
        rsi_value_buy_weight = 0    #RSI值因素佔買權重(起始值為0)
        rsi_value_sell_weight = 0   #RSI值因素佔賣權重(起始值為0)
        vol_trend_up_buy_weight = 0   #成交量大於均量，趨勢向上因素佔買權重:1(起始值為0)
        vol_trend_down_sell_weight = 0   #成交量小於均量，趨勢向下因素佔買權重:-1(起始值為0)
        vol_doubled_weight = 0   #價漲量增，趨勢向上，價跌量增，趨勢向下，此因素佔買賣權重:1(起始值為0，可能加1，也可能減1)
        vol_shrinked_weight = 0   #下跌無量，趨勢向上， 上漲無量，趨勢向下，此因素佔買賣權重:1(起始值為0，可能加1，也可能減1)
        sum_weight_factors = 0#綜合權重分數(起始值為0)
        strong_buy = 10   #強烈買進
        medium_buy = 5    #普通買進        
        little_buy = 2    #稍微買進
        strong_sell = -10 #強烈賣出
        medium_sell = -5  #普通賣出
        little_sell = -2  #稍微賣出
        action_amount = 0
        final_amount = 0      
       
        # calculate current ma cross status
        cur_ma_cross = self.get_current_ma_cross()
        # check whether ma 20 is toward up status
        cur_ma_20 = self.get_current_ma_20()
        # calculate current rsi cross status
        cur_rsi_cross = self.get_current_rsi_cross()
        # calculate current rsi_14 value
        cur_rsi_14 = self.get_current_rsi_14()
        # calculate current kd cross status
        cur_kd_cross, k_value = self.get_current_kd_cross()
        # calculate volume doubled or halfed
        self.now_volume = close_volume
        cur_vol_change = self.get_volume_increase_status()
        # calculate macd and macd_signal status
        cur_macd_cross = self.get_current_macd_cross()
        # calculate volume trend
        vol_trend = self.get_volume_trend_change()        

        Log('ASSET NOW==>' + 'USDT= ' + str(self['assets'][exchange]['USDT']) +',  ETH= ' + str(self['assets'][exchange]['ETH']))

        if cur_ma_cross is None:
            #Log('info: cur_ma_cross NONE，不交易')
            return []
        if cur_rsi_cross is None:
            #Log('info: cur_rsi_cross NONE，不交易')
            return []
        if cur_rsi_14 is None:
            #Log('info: cur_rsi_14 NONE，不交易')
            return []
        if cur_kd_cross is None:
            #Log('info: cur_kd_cross NONE，不交易')
            return []
        if cur_macd_cross is None:
            #Log('info: cur_macd_cross NONE，不交易')
            return []
        if vol_trend is None:
            #Log('info: vol_trend NONE，不交易')
            return []
        if cur_vol_change is None:
            #Log('info: cur_vol_change NONE，不交易')
            return []
        

        if self.last_ma_cross_status is None:
            self.last_ma_cross_status = cur_ma_cross
            #Log('info: self.last_ma_cross_status NONE，不交易')
            return []
        if self.last_rsi_cross_status is None:
            self.last_rsi_cross_status = cur_rsi_cross
            #Log('info: self.last_rsi_cross_status NONE，不交易')
            return []
        if self.last_kd_cross_status is None:
            #Log('info: self.last_kd_cross_status NONE，不交易')
            self.last_kd_cross_status = cur_kd_cross
            return []
        if self.last_macd_cross_status is None:
            #Log('info: self.last_macd_cross_status NONE，不交易')
            self.last_macd_cross_status = cur_macd_cross
            return []



        # 計算 Weight    

        # MA cross up, MA_5及MA_10黃金交叉，權重為 1，若 MA_20向上再加 1
        if cur_ma_cross == self.MA_UP and self.last_ma_cross_status == self.MA_DOWN:
            self.last_ma_cross_status = cur_ma_cross
            ma_cross_buy_weight = ma_cross_buy_weight + 1
            #Log('info: MA_5及MA_10黃金交叉，權重加 1')
            if cur_ma_20 == self.MA20_UP:
               ma_cross_buy_weight = ma_cross_buy_weight + 1
               #Log('info: MA_20向上，權重再加 1')
        # MA cross down, MA_5及MA_10死亡交叉，權重為 -1，若 MA_20向下再減 1
        elif cur_ma_cross == self.MA_DOWN and self.last_ma_cross_status == self.MA_UP:
            self.last_ma_cross_status = cur_ma_cross
            ma_cross_sell_weight = ma_cross_sell_weight - 1
            #Log('info: MA_5及MA_10死亡交叉，權重減 1')
            if cur_ma_20 == self.MA20_DOWN:
               ma_cross_sell_weight = ma_cross_sell_weight - 1
               #Log('info: MA_20向下，權重再減 1')            
        self.last_ma_cross_status = cur_ma_cross

        # MACD cross up, MACD line及 MACD_SIGNAL line黃金交叉，權重為 1
        if cur_macd_cross == self.MACD_UP and self.last_macd_cross_status == self.MACD_DOWN:
            self.last_macd_cross_status = cur_macd_cross
            macd_cross_buy_weight = macd_cross_buy_weight + 1
            #Log('info: MACD line及MACD_SIGNAL line黃金交叉，權重加 1')
        # MA cross down, MACD line及 MACD_SIGNAL line死亡交叉，權重為 -1
        elif cur_macd_cross == self.MACD_DOWN and self.last_macd_cross_status == self.MACD_UP:
            self.last_macd_cross_status = cur_macd_cross
            macd_cross_sell_weight = macd_cross_sell_weight - 1
            #Log('info: MACD line及MACD_SIGNAL line死亡交叉，權重減 1')
        self.last_macd_cross_status = cur_macd_cross

        # KD cross up, KD黃金交叉，權重為 1，若是低檔(K<=30)黃金交叉則再加 1
        if cur_kd_cross == self.K_UP and self.last_ma_cross_status == self.K_DOWN:
            self.last_kd_cross_status = cur_kd_cross
            kd_buy_weight = kd_buy_weight + 1
            #Log('info: KD黃金交叉，權重加 1')
            if (k_value <= 30):
               kd_buy_weight = kd_buy_weight + 1
               #Log('info: KD <=30，權重再加 1')
        # KD cross down, KD死亡交叉，權重為 -1，若是高檔(K>=70)死亡交叉則再減 1
        elif cur_kd_cross == self.K_DOWN and self.last_kd_cross_status == self.K_UP:
            self.last_kd_cross_status = cur_kd_cross
            kd_sell_weight = kd_sell_weight - 1
            #Log('info: KD死亡交叉，權重減 1')
            if (k_value >= 70):
               kd_sell_weight = kd_sell_weight - 1
               #Log('info: KD >=70，權重再減 1')
        self.last_kd_cross_status = cur_kd_cross

        # RSI cross up, RSI_5及RSI_10黃金交叉，權重為 1
        if cur_rsi_cross == self.RSI_UP and self.last_rsi_cross_status == self.RSI_DOWN:
            self.last_rsi_cross_status = cur_rsi_cross
            rsi_cross_buy_weight = rsi_cross_buy_weight + 1
            #Log('info: RSI_5及RSI_10黃金交叉，權重加 1')
        # RSI cross down, RSI_5及RSI_10死亡交叉，權重為 -1
        elif cur_rsi_cross == self.RSI_DOWN and self.last_rsi_cross_status == self.RSI_UP:
            self.last_rsi_cross_status = cur_rsi_cross
            rsi_cross_sell_weight = rsi_cross_sell_weight - 1
            #Log('info: RSI_5及RSI_10死亡交叉，權重減 1')
        self.last_rsi_cross_status = cur_rsi_cross

        # RSI_14 cross down, RSI_14若超賣，權重為 1，RSI_14若超買，權重為 -1
        if cur_rsi_14 == self.RSI14_OVER_SELL:
            rsi_value_buy_weight = rsi_value_buy_weight + 1
            #Log('info: RSI_14 超賣，權重加 1')
        elif cur_rsi_14 == self.RSI14_OVER_BUY:
            rsi_value_sell_weight = rsi_value_sell_weight - 1
            #Log('info: RSI_14 超買，權重減 1')
            
        # 成交量大於均量因素，趨勢向上，權重為 2，趨勢向下，權重為 -2
        if vol_trend == self.TREND_UP:
            vol_trend_up_buy_weight = vol_trend_up_buy_weight + 2
            #Log('info: 成交量大於均量20%，且趨勢向上，權重加 2')
        elif vol_trend == self.TREND_DOWN:
            vol_trend_down_sell_weight = vol_trend_down_sell_weight - 2
            #Log('info: 成交量大於均量20%，且趨勢向下，權重減 2')
        
        # 成交量倍增，表示原盤整趨勢可能改變向上或向下，價漲量增則權重為 1，價跌量增則權重為-1
        # 成交量若不及上次一半，表示量急縮，上漲無量則準備下跌，權重為 -1，下跌無量，則權重為 1
        if cur_vol_change == self.VOL_DOUBLED_UP:
            vol_doubled_weight = vol_doubled_weight + 1
            #Log('info: 價漲量增，趨勢向上，權重加 1')
        elif cur_vol_change == self.VOL_DOUBLED_DOWN:
            vol_doubled_weight = vol_doubled_weight - 1
            #Log('info: 價跌量增，趨勢向下，權重減 1')
        elif cur_vol_change == self.VOL_SHRINKED_UP:
            vol_shrinked_weight = vol_shrinked_weight + 1
            #Log('info: 下跌無量，趨勢向上，權重加 1')
        elif cur_vol_change == self.VOL_SHRINKED_DOWN:
            vol_shrinked_weight = vol_shrinked_weight - 1
            #Log('info: 上漲無量，趨勢向下，權重減 1')
        

        # 綜合各項權重，計算操作策略：強烈買進 或 普通買進 或 稍微買進 或 強烈賣出 或 普通賣出 或 稍微賣出
        macd_weight =  macd_indicator * (macd_cross_buy_weight + macd_cross_sell_weight)        
#        rsi_weight  =  rsi_indicator  * (rsi_cross_buy_weight + rsi_cross_sell_weight + rsi_value_buy_weight + rsi_value_sell_weight)
        rsi_weight  =  rsi_indicator  * (rsi_value_buy_weight + rsi_value_sell_weight)
        vol_weight  =  vol_indicator  * (vol_trend_up_buy_weight + vol_trend_down_sell_weight + vol_doubled_weight + vol_shrinked_weight)
        kd_weight   =  kd_indicator   * (kd_buy_weight + kd_sell_weight)
        ma_weight   =  ma_indicator   * (ma_cross_buy_weight + ma_cross_sell_weight)
        
        sum_weight_factors = kd_weight + ma_weight + macd_weight + rsi_weight + vol_weight

        if sum_weight_factors >= 20:
            action_amount = strong_buy
        elif (sum_weight_factors >= 10) and (sum_weight_factors <= 19):
            action_amount = medium_buy
        elif (sum_weight_factors >= 4) and (sum_weight_factors <= 9):
            action_amount = little_buy
        elif (sum_weight_factors >= -9) and (sum_weight_factors <= -4):
            action_amount = little_sell
        elif (sum_weight_factors >= -19) and (sum_weight_factors <= -10):
            action_amount = medium_sell
        elif sum_weight_factors <= -20:
            action_amount = strong_sell
###########
        action_amount = sum_weight_factors
###########
        
        # 進行買賣， 並處理 USDT不足買 及 ETH不足賣 狀況
        eth_amount = self['assets'][exchange]['ETH']
        usdt_amount = self['assets'][exchange]['USDT']
        could_buy = int(usdt_amount / close_price)
    
        if action_amount > 0 and could_buy != 0:
            if usdt_amount >= (action_amount * close_price):
               buy_amount = action_amount
            if usdt_amount < (action_amount * close_price):
               buy_amount = could_buy
            final_amount = buy_amount           
        elif action_amount < 0 and eth_amount!= 0:
            if eth_amount >= (action_amount * -1):
               sell_amount = action_amount
            if eth_amount < (action_amount * -1):
               sell_amount = eth_amount * -1
            final_amount = sell_amount        

        if final_amount != 0:
            return [
                {
                    'exchange': exchange,
                    'amount': final_amount,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]

        return []            
