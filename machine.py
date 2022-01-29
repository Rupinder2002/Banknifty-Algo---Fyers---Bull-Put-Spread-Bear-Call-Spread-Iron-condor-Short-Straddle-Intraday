from bot import bot

b = bot()
print('Select Option')
print(' ')
print(' ')
print('1. Find the option strategy and strike prices.')
print(' ')
print(' ')
print('2. Monitor Existing Options Trade')
print(' ')
print(' ')
print('3. Record Previous Week HLC')
print(' ')
print(' ')
print('4. Intraday Short Straddle Strategy')
print(' ')
print(' ')
print('5. Monitor Intraday Equity Trade')
print(' ')
print(' ')
option = int(input('Enter Option Number: '))
if option ==1:
    b.initFyers()
    b.getWeekHLC()
    b.initMarketFeed(2)
elif option==2:
    b.initMarketFeed(1)
    b.monitorTrade()
elif option==3:
    hlc = str(input('Enter Weekly high,low,close separated by comma: '))
    data = hlc.split(",")
    b.recordHLC(data)
elif option ==4:
    b.initFyers()
    b.initMarketFeed(3)
elif option==5:
    b.initFyers()
    b.monitorIntraday()