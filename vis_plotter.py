import matplotlib.pyplot as plt
import prettyplotlib as ppl
import itertools
import sklearn
import asyncio
import random
import math
import numpy as np
def data_gen():
    status = {True:'running', False:'sleeping'}
    return [{'battery':random.randint(0,5), 'status':status[random.random()>0.9]} for i in range(5)]

# The slices will be ordered and plotted counter-clockwise.
def add_pie(fig, ax, center, percent):
    sizes = [percent, 100-percent]
    colors = ['#F05F40', '#d9d9d9']
    ax.pie(sizes, colors=colors,wedgeprops = {'linewidth':0, 'zorder':1}, center = center, radius = 1, startangle = 10)
        #draw a circle at the center of pie to make it look like a donut
    centre_circle = plt.Circle(center,0.75,color='white', fc='white',linewidth=1.25)
    #fig = plt.gcf()
    ax.add_artist(centre_circle)
    # Set aspect ratio to be equal so that pie is drawn as a circle.
    ax.axis('equal')
    return fig, ax
def add_line(ax, list_of_pairs):
    #e.g. [(0,0),(1,0)]
    for i in list_of_pairs:
        xs = [j[0] for j in i]
        ys = [j[1] for j in i]
        ppl.plot(ax, xs,ys, color = '#252525', linewidth = 1.0, zorder=0)

def update(fig, ax, new_data, max_batt):
    ###centres is a list of centre coordinates
    ###new data is a list of corresponding update, {'battery': , 'status':}
    print(new_data)
    one = [(i[0], i[1]['battery']) for i in new_data if i[1]['_id']==0]
    two = [(i[0], i[1]['battery']) for i in new_data if i[1]['_id']==1]
    ppl.plot(ax, [i[1] for i in one], label = 'Sensor 1', linewidth=1.0 )
    ppl.plot(ax, [i[1] for i in two], label = 'Sensor 2', linewidth=1.0 )
    ax.set_ylim([0,5])
    ax.set_xlim([0,100])
    ax.set_ylabel('Battery')
#plt.show() 
def data_generator(single_series, num_sensors, max_batt):
	initial = [{'status':'running', 'battery':max_batt, '_id':i} for i in range(num_sensors)]
	for update in single_series:
		_id = update[1]['_id']
		initial[_id] = update[1]
		yield initial

def distance(xy1, xy2):
    x = (xy2[0]-xy1[0])**2
    y = (xy2[1]-xy1[1])**2
    return math.sqrt(x+y)
def safe(candidate, existing_one, radius):
    return distance(candidate, existing_one)>=radius+2
def safe_vs_all(candidate, all_existing, radius):
    return all([safe(candidate, i, radius) for i in all_existing])
def gen_centre(x, y):
    #generate random within [0,x], [0,y]
    candidate = (random.gauss(x/2,1 ), random.gauss(y/2, 1))
    return candidate
def gen_safe_centre(radius, x, y, existing):
    #generate random within [0,x], [0,y]
    while True:
        candidate = gen_centre(x,y)
        if safe_vs_all(candidate, existing, radius):
            return candidate
def gen_centres(radius, x, y, number):
    existing = [(0,0)]
    while len(existing)<number:
        existing.append(gen_safe_centre(radius, x,y, existing))
    return existing
if __name__ == '__main__':
    num_sensors = 3 #one more than there is a record for
    num_records = int((num_sensors-1)/2)
    print('num records', num_records)
    centres = gen_centres(1, 10,10, num_sensors)
    all_data = [sklearn.externals.joblib.load('data/batt_0')]
    all_data = [i[400:450] for i in all_data]
    merged = sorted(list(itertools.chain(*all_data)))
    streamer = data_generator(merged, num_sensors, 5)
    updater = []
    for index, new_data in enumerate(streamer):
        fig, ax = plt.subplots(1)
        updater.append(new_data)
        update(fig, ax, updater, 5)
        fig.savefig('plot/line%d'%index, format = 'png', dpi=450)
