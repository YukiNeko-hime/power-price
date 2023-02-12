# -*- coding: UTF-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import csv

SMALL_SIZE = 14
MEDIUM_SIZE = 16
BIGGER_SIZE = 18
HUGE_SIZE = 22

plt.rc('font', size=SMALL_SIZE)			# controls default text sizes
plt.rc('axes', titlesize=BIGGER_SIZE)		# fontsize of the axes title
plt.rc('axes', labelsize=BIGGER_SIZE)		# fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)		# fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)		# fontsize of the tick labels
plt.rc('legend', fontsize=MEDIUM_SIZE)	# legend fontsize
plt.rc('figure', titlesize=HUGE_SIZE)		# fontsize of the figure title


# margin and monthly base price of the contract (in cents)
margin = 0.37
base_price = 350.0


# some helper functions for string conversion
def price_to_str(price):
	# convert float to string, rounded and padded with zeros to two decimals
	s = str(round(price, 2))
	i = s.index('.')
	s = s.ljust(i+3,'0')
	s = s.replace('.',',')
	
	return s

def usage_to_str(usage):
	# convert float to string, rounded to integers
	r = round(usage, 0)
	s = str(int(r))
	
	return s


# load the usage data from Vattenfall report file
timestamp = []
usage = []
with open('report.csv', 'r', encoding='utf-16-le') as csvfile:
	data = csv.reader(csvfile, delimiter=';')
	
	for row in data:
		try:
			u = float(row[2].replace(',','.'))
			if u > 0:							# Vattenfall includes hours that don't yet have usage data, skip those
				usage.append(u)
				timestamp.append(row[0] + ':00')
		except:
			# Vattenfall includes a complicated header in the file, skip all rows that don't fit the measurement pattern
			pass


# load the price data obtained from sahko.tk as a csv file
price = []
with open('chart.csv','r') as csvfile:
	data = csv.reader(csvfile, delimiter=';')
	
	next(data)				# skip the header row
	
	# skip to the timestamp that matches with the first timestamp of the usage data
	row = next(data)
	while row:
		ts = row[0].strip('"')
		if ts == timestamp[0]:
			break
		
		row = next(data)
	
	# read the price data for the hours there is usage data
	while row:
		ts = row[0].strip('"')
		price.append(float(row[1].replace(',','.')))
		if ts == timestamp[-1]:
			break
		
		row = next(data)


# calculate the number of days in the month for which we have data
cur = np.datetime64(timestamp[0])
y = cur.astype('datetime64[Y]').astype(int) + 1970
m = cur.astype('datetime64[M]').astype(int) % 12 + 1
cur = str(y) + '-' + str(m).rjust(2,'0') + '-01'

# find out the next month
nm = m%12 + 1
if nm < m:
	ny = y+1		# current month is December, next month is January of the next year
else:
	ny = y
next = str(ny) + '-' + str(nm).rjust(2,'0') + '-01'

# calculate the number of days
days_in_month = np.datetime64(next) - np.datetime64(cur)
days_in_month = days_in_month.astype(float)

# calculate the daily base price for the month
daily_base_price = base_price/days_in_month


# calculate the cost for each hour based on the current contract
cost = []
i = 0
while i < len(timestamp):
	cost.append(usage[i]*(price[i] + margin))
	i += 1


# calculate the daily usage and cost from the hourly data
date = []
daily_cost = []
daily_usage = []
i = 0
while i < len(timestamp):
	d = timestamp[i].split(' ')[0]
	date.append(d.split('-')[-1].lstrip('0'))
	
	dc = 0
	du = 0
	while i < len(timestamp) and timestamp[i].split(' ')[0] == d:
		dc += cost[i]
		du += usage[i]
		i += 1
	
	daily_cost.append((dc + daily_base_price)/100)
	daily_usage.append(du)


# calculate the totals and average price for the month
total_usage = np.sum(daily_usage)
total_cost = np.sum(daily_cost)
total_cost_kwh = np.sum(cost)
average_price = total_cost_kwh/total_usage

# format strings for title
total_usage = usage_to_str(total_usage)
total_cost = price_to_str(total_cost)
average_price = price_to_str(average_price)

title = f'Sähkön kulutus ja hinta, kuukauden kertymä {total_usage} kWh ja {total_cost}€, keskihinta {average_price} snt/kWh'

# make some clever rounding to get better maximums for the axes
umax = np.ceil(max(daily_usage)/5)*5			# round up the maximum value of the month at 5 kWh increments
cmax = np.ceil(max(daily_cost)*5)/5			# round up the maximum value of the month at 0.2 euro increments

# plot the results with two y-axes, one for usage and one for price
fig, ax = plt.subplots()
ax.set_ylim(ymin=0, ymax=umax)
ax2=ax.twinx()
ax2.set_ylim(ymin=0, ymax=cmax)

ax.bar(date, daily_usage, label='kulutus')
ax2.plot(date, daily_cost, label='hinta', color='red')

plt.title(title)
ax.set_xlabel(u'päivä')
ax.set_ylabel(u'kWh')
ax2.set_ylabel(u'euroa')
ax.legend(loc='upper left')
ax2.legend(loc='upper right')

# output the result to a file
save_path = 'kulutus.png'
fig.set_size_inches(19.20, 10.80)
fig.savefig(save_path, dpi=100)
