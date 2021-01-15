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
            'Bitfinex': {
                'pairs': ['ETH-USDT'],
            },
        }
        self.period = 10 * 60
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.ma_long = 100
        self.ma_short = 10
        self.UP = 1
        self.DOWN = 2

        self.ma_month = 28
        self.wait_for_sell = 0;
        


    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if s_ma > l_ma:
            return self.UP
        return self.DOWN


    # called every self.period
    def trade(self, information):

        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        close_price = information['candles'][exchange][pair][0]['close']

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long:]
        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()

        Log('info: ' + str(information['candles'][exchange][pair][0]['time']) + ', ' + str(information['candles'][exchange][pair][0]['open']) + ', assets' + str(self['assets'][exchange]['ETH']))

        # cross down
        if cur_cross != None and  self.last_cross_status != None and self.last_type == 'buy' and cur_cross == self.DOWN and self.last_cross_status == self.UP:
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            
            return [
                {
                    'exchange': exchange,
                    'amount': -0,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]

        maMonth = talib.SMA(self.close_price_trace, self.ma_month)[-1]
        # condition1
        if ( self.last_type == 'buy'and close_price < maMonth):
            Log('buying, opt1:' + self['opt1'])
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            self.wait_for_sell +=1
            return [
                {
                    'exchange': exchange,
                    'amount': 10,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        
        if(self.last_type == 'sell' and close_price > maMonth *1.03):
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            amount = self.wait_for_sell
            self.wait_for_sell = 0;
            return [
                {
                    'exchange': exchange,
                    'amount': -amount,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
            
        # condition1 end
        if cur_cross is None:
            return []

        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []

        # cross up
        if self.last_type == 'sell' and cur_cross == self.UP and self.last_cross_status == self.DOWN:
            Log('buying, opt1:' + self['opt1'])
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': 10,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        

        
        self.last_cross_status = cur_cross
        return []