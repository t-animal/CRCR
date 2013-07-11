#!/usr/bin/env python3
import xml.dom.minidom
import datetime
import itertools
import sys

xml.dom.minidom.Element.addClass = lambda x,y: x.setAttribute("class", x.getAttribute("class")+" "+str(y))

jahr=datetime.date.today().year
stammtischwochen = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53]
ferienzeiträume = []
freietage = []
sondertage = []
filename = "kalender_prepared_hochformat.svg"
try:
	conf = open("calendar.conf", "r")
	configIterator = itertools.filterfalse(lambda l:l[0]=="#" or l[0] == '\n' or len(l)==0, conf)
	conf.readline =  lambda:next(configIterator)

	jahr = int(conf.readline())

	stammtischwochen = list(map(int, conf.readline().split(",")))
	ferienzeitraeume = [(tuple(map(int,b.split("."))),tuple(map(int,c.split(".")))) for b,c in [a.split("-") for a in conf.readline().split(",")]]
	freietage = [tuple(map(int,b.split("."))) for b in conf.readline().split(",")]
	while True:
		sondertage += [((int(w),int(x)), y, z) for (w,x,y,z) in [conf.readline().replace(".",",").split(","),]]
except StopIteration:
	pass
except Exception:
	print("Fehler beim Einlesen der config")


schaltjahr = jahr%4 == 0 and (jahr%100 == 1 or jahr%1000 == 0)
wochentagoffset = datetime.date(jahr, 1, 1).weekday()

monatslaenge = (31,28,31,30,31,30,31,31,30,31,30,31)
wochentage = ("montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag")

if(schaltjahr):
	monatslaenge[1] += 1

sondertage2 = dict((i, []) for i in range(1,367))
for (d,m),y,z in sondertage:
	sondertage2[sum(monatslaenge[:m-1])+d] += [(y,z)]
sondertage = sondertage2

freietage = [sum(monatslaenge[:m-1])+d for (d,m) in freietage]
freietage += [x for ((d1,m1),(d2,m2)) in ferienzeitraeume for x in range(sum(monatslaenge[:m1-1])+d1,sum(monatslaenge[:m2-1])+d2+1)]

try:
	image = xml.dom.minidom.parse(filename)
except IOError:
	print("Konnte Vorlage nicht öffnen. Dateiname?")
	sys.exit(1)

for rect in image.getElementsByTagName("rect"):
	if "day" in rect.getAttribute("class"):
		id = rect.getAttribute("id")
		
		try:
			month = int(id[0:id.find("-")])
			day = int(id[id.find("-")+1:])
			
			if not 0 < month < 13 or not 0 < day < 32:
				raise ValueError()
		except ValueError:
			print("Warning: Invalid id {}!".format(id))
			continue
		
		if day > monatslaenge[month-1]:
			rect.addClass("invisible")
			rect.nextSibling.nextSibling.addClass("invisible")
			continue
		
		tagImJahr = sum(monatslaenge[:month-1])+day
		wochentag = (tagImJahr + wochentagoffset)%7
		rect.setAttribute("weekday", wochentage[wochentag-1])
		
		offset = 0
		if wochentag == 1:
			offset = 15 #15=1/2 fontsize
			rect.parentNode.insertBefore(xml.dom.minidom.parseString("""<text id="{}-{}-woy" class="weekday" style="font-size:30px" x="{}" y="{}">{}</text>"""
					.format(month,
						day, 
						float(rect.getAttribute("x"))+2,
						float(rect.getAttribute("y"))+float(rect.getAttribute("height"))/2+10-offset,
						int(tagImJahr/7)+1)).firstChild, rect.nextSibling)
		
		if wochentag == 2 and int(tagImJahr/7+1) in stammtischwochen:
			rect.addClass("trunktable")
		
		if tagImJahr in freietage:
			rect.addClass("holiday")
		
		if wochentag == 0 or wochentag == 6:
			rect.addClass("weekend")
		
		if tagImJahr in sondertage:
			for i, sondertag in enumerate(sondertage[tagImJahr]):
				rect.addClass(sondertag[1])
				rect.parentNode.insertBefore(xml.dom.minidom.parseString("""<text id="{}-{}-special" class="specialdaytext" style="font-size:{}px;" x="{}" y="{}">{}</text>"""
						.format(month,
							day, 
							float(rect.getAttribute("height"))/(0.7+0.7*len(sondertage[tagImJahr])),
							float(rect.getAttribute("x"))+45,
							float(rect.getAttribute("y"))+float(rect.getAttribute("height"))/len(sondertage[tagImJahr])*(i+1)-0.3*(float(rect.getAttribute("height"))/(0.7+0.7*len(sondertage[tagImJahr]))),
							sondertag[0])).firstChild, rect.nextSibling)
			
		
		rect.parentNode.insertBefore(xml.dom.minidom.parseString("""<text id="{}-{}-weekday" style="font-size:30px;" x="{}" y="{}">{}</text>"""
					.format(month,
						day, 
						float(rect.getAttribute("x"))+2,
						float(rect.getAttribute("y"))+float(rect.getAttribute("height"))/2+10+offset,
						wochentage[wochentag-1][0:2])).firstChild, rect.nextSibling)
			

f = open('outputCalendar.svg','w')

image.writexml(f)
f.close()
