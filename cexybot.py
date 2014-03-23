"""
Copyright (C) 2014 Jerry Teeple / Brian Jack

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be# useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


	Please consider donating to us to help see continued support 	and development. For (possibly slow) email support 
	jteeple @ gmail.com


		----Donation Addresses----	

  BTC  1D4dsP4ojMos5a5AggXx5DdiFMKXXPUDUg
  LTC  LgHGSjx6BHYqe6kC84wN2k2sqdXQsbQkcq
  DOGE DNSx8MSRmi1rQjUZwBiNQ7jisLLYY4RqSC
  FTC  6q4HRmiVqaCz3BBzEjfQfzp4ufCgnqVama
  AUR  ANL31J9na9qYvBNxqVUR98e5JJWVDqCEci
  NMC  N7MMZCUJ5QBmGZFWhXzeofhcvSACocBQeX
  IXC  xuNA3pakj4zVTvXUrXdvMcHiZReMenAXgq
  DVC  1PGGYrCDYRFjiKUJZxsQNMerv6WuFypmyx


"""

import cexapi
import time
from math import floor

api=cexapi.api('USERNAME','ApiKey','ApiSecret')


# sell when GHS balance reference higher by margin value in BTC
# buy  when GHS balance reference lower  by margin value in BTC
margin=.0000025

MINPRICE=.001
MAXPRICE=.03
MAXVOL=20

"""

Check market at regular interval

whenever prices rises by margin (or more) sell a chunk
remember all chunks sold
buyback any chunks sold at a price higher than current price by margin or more

!!!!!!!!!!!!!!!!!!!!!!!!!!!WARNING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

DO NOT ADJUST ANY SETTINGS BELOW THIS POINT UNLESS YOU KNOW WHAT YOU ARE DOING!! WE ARE NOT RESPONSIBLE FOR ANY SEVERE LOSSES YOU MAY SUFFER AS A RESULT OF YOU THINKING YOU KNOW BETTER!!!!!!!!!

YOU USE THIS UNDER YOUR OWN RISK AND WE BEAR NO RESPONSIBILITY FOR YOU BEING A DUMBASS. THIS SCRIPT WORKS AS INTENDED. MODIFICATIONS ARE YOUR OWN ISSUE!!

"""

def fmtNumber(n):
    """
    format number to form 0000.00000000
    """
    whole=str(int(n)).rjust(4,'0')
    frac=str(float(n)-float(int(n)))[2:].ljust(8,'0')
    return "%s.%s" % (whole,frac)    

quitting=False

openOrder=None

def trunc(n,places=100000000.0):
    return floor(places*float(n))/places

while not quitting:
    try:
        t=time.time()
        if openOrder is not None:
            # Delete open order if still standing
            print "(Delete previous order if still there)\n"
            api.cancel_order(openOrder)
            openOrder=None
        bal=api.balance()
        book=api.order_book('GHS/BTC')
        ticker=api.ticker()
    
        balGHS=bal['GHS']
        balBTC=bal['BTC']
        avlGHS=float(balGHS['available'])
        avlBTC=float(balBTC['available'])
        sells=book['asks']
        buys=book['bids']
        hibuy=(float(buys[0][1]),float(buys[0][0]))
        losell=(float(sells[0][1]),float(sells[0][0]))
        lastGHS=trunc(ticker['last'])
        priceGHS=trunc((hibuy[0]*hibuy[1]+losell[0]*losell[1])/(hibuy[0]+losell[0]))
        GHS2BTC=trunc(priceGHS*avlGHS)
    
        print "GHS price: %s BTC per 1.0 GHS (last: %s)\n" % (priceGHS,lastGHS)
        print "  Balance: %s GHS, %s BTC\n" % (fmtNumber(avlGHS),fmtNumber(avlBTC))
        print " BTC refs: %s BTC, %s BTC\n" % (fmtNumber(GHS2BTC),fmtNumber(avlBTC))
    
        # if swing<0 GHS reference worth less than BTC balance, more if >0
        swing=int((GHS2BTC-avlBTC)/margin)
        swamt=trunc(GHS2BTC-avlBTC)
        desc="balanced"
        if (swing<0):
            desc="GHS<BTC"
        if (swing>0):
            desc="GHS>BTC"
        ss='s'
        if abs(swing)==1:
            ss=''
        print "Swing value: %s (%s margin%s) swing=%f margin=%f\n" % (desc,abs(swing),ss,swamt,margin)
        
        if swing!=0:
            amt=trunc(abs(GHS2BTC-avlBTC)/2.0)
            vol=trunc(amt/priceGHS)
            sale=trunc(vol*priceGHS)
            print "Amount needed to balance: %f\n" % amt
            if swing>0:
                print "Selling %f GHS @%f/per (total %f BTC)\n" % (vol,priceGHS,sale)
                if vol<=MAXVOL and priceGHS>=MINPRICE:
                    order=api.place_order('sell',vol,priceGHS,'GHS/BTC')
                    openOrder=order['id']
                else:
                    print "*** SELL ORDER OUT OF BOUNDS ADJUST SETTINGS ***\n"
                    print "*** volume %f>%f or price %f<%f\n" % (vol,MAXVOL,priceGHS,MINPRICE)
                    print "*** CHECK LIMIT SETTINGS!! ***\n" 
            else:
                print "Buy %f GHS @%f/per (total %f BTC)\n" % (vol,priceGHS,sale)
                if vol<=MAXVOL and priceGHS<=MAXPRICE:
                    order=api.place_order('buy',vol,priceGHS,'GHS/BTC')
                    openOrder=order['id']
                else:
                    print "*** BUY ORDER OUT OF BOUNDS ADJUST SETTINGS ***\n"
                    print "*** volume %f>%f or price %f>%f\n" % (vol,MAXVOL,priceGHS,MAXPRICE)
                    print "*** CHECK LIMIT SETTINGS!!\n" 
        dt=time.time()-t
        rest=max(0,30-dt)
        print "%s/30 elapsed so sleep for %s" % (dt,rest)
        if rest>0:
            time.sleep(rest)
    except KeyboardInterrupt:
        print "*** QUITTING ***"
        quitting=True
    except Exception, e:
        print "*** BARFED!! SOMETHING FAILED!!!! (%s) ***\n" % str(e)
        time.sleep(1)

