#!/usr/bin/env python3
import argparse
import xml.dom.minidom
import datetime
import itertools
import sys



parser = argparse.ArgumentParser(description="Create a beautiful calendar in a heartbeat from a config file and a template.",  formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-y", "--year", dest="year", type=int, help="overwrite the year in the config file")
parser.add_argument("-c", "--config", dest="config", default="calendar.conf", help="path to the config file to read")
parser.add_argument("-t", "--template", dest="template", default="templates/calendar.svg", help="path to the template file to read")
parser.add_argument("-s", "--stylesheet", dest="stylesheet", default="templates/style.css", help="path to the stylesheet file to import into the svg")
parser.add_argument("-o", "--output", dest="output", default="outputCalendar.svg", help="path to the write the output to")

args = parser.parse_args()



xml.dom.minidom.Element.addClass = lambda x,y: x.setAttribute("class", x.getAttribute("class")+" "+str(y))

#default werte setzen
jahr=datetime.date.today().year
stammtischwochen = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53]
ferienzeiträume = []
freietage = []
sondertage = []


#config lesen
try:
	conf = open(args.config, "r")
	configIterator = itertools.filterfalse(lambda l:l[0]=="#" or l[0] == '\n' or len(l)==0, conf)
	conf.readline =  lambda:next(configIterator)

	#zeile fuer zeile einlesen, adaequat splitten und zu int konvertieren
	jahr = int(conf.readline())
	if not args.year == None:
		jahr = args.year
	stammtischwochen = list(map(int, conf.readline().split(",")))
	ferienzeitraeume = [(tuple(map(int,von.split("."))),tuple(map(int,bis.split(".")))) for von, bis in [zeitraum.split("-") for zeitraum in conf.readline().split(",")]]
	freietage = [tuple(map(int,b.split("."))) for b in conf.readline().split(",")]

	#ab hier nur noch sondertage, bis StopIteration
	while True:
		sondertage += [((int(tag),int(monat)), titel, klasse) for (tag,monat,titel,klasse) in [conf.readline().replace(".",",").split(","),]]
except StopIteration:
	pass
except Exception as e:
	print("Fehler beim Einlesen der config")
	print(e)
	sys.exit()


#einige hilfsstrukturen initialisieren
monatslaenge = [31,28,31,30,31,30,31,31,30,31,30,31]
wochentage = ("montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag")
wochentagoffset = datetime.date(jahr, 1, 1).weekday()
kalenderwochenoffset = 1 if wochentagoffset >= 3 else 0 #erste woche mit donnerstag ist die erste woche

#im schaltjahr februar +1 Tag
if ((jahr%4 == 0 and not jahr%100 == 0) or jahr%400 == 0):
	monatslaenge[1] += 1


#dict mit 1 Eintrag pro Tag, mit offset im jahr als key und tuple(titel, klasse) als value
sondertage2 = dict((i, []) for i in range(1,367))#367: 365 Tage+Schalttag
for (d,m),titel,klasse in sondertage:
	sondertage2[sum(monatslaenge[:m-1])+d] += [(titel,klasse)]
sondertage = sondertage2

#einzelne freien tage eintragen
freietage = [sum(monatslaenge[:m-1])+d for (d,m) in freietage] if not freietage[0]==(0,0) else []
#pro ferienzeitraum, jeden freien tag (range(anfang, ende+1)) eintragn
freietage += [x for ((d1,m1),(d2,m2)) in ferienzeitraeume for x in range(sum(monatslaenge[:m1-1])+d1,sum(monatslaenge[:m2-1])+d2+1)] if not ferienzeitraeume[0] == ((0,0),(0,0)) else []

#vorlage oeffnen
try:
	image = xml.dom.minidom.parse(args.template)
except IOError:
	print("Konnte Vorlage nicht öffnen. Dateiname?")
	sys.exit(1)

#css eintragen
try:
	image.getElementsByTagName("style")[0].firstChild.replaceWholeText(open(args.stylesheet).read())
except IOError:
	print("Konnte CSS nicht oeffnen. Huh?!")
	sys.exit()

#jahr eintragen
textElement = [t for t in image.getElementsByTagName("text") if t.getAttribute("id") == "title"]
textElement[0].firstChild.replaceWholeText("FSI-Kalender {}".format(jahr))

#jedes rect anschauen
for rect in image.getElementsByTagName("rect"):
	if "day" in rect.getAttribute("class"):
		id = rect.getAttribute("id")

		#tag und monat ausblenden
		try:
			month = int(id[0:id.find("-")])
			day = int(id[id.find("-")+1:])

			if not 0 < month < 13 or not 0 < day < 32:
				raise ValueError()
		except ValueError:
			print("Warning: Invalid id {}!".format(id))
			continue

		#tage, die es im monat nicht gibt, ausblenden
		if day > monatslaenge[month-1]:
			rect.addClass("invisible")
			rect.nextSibling.nextSibling.addClass("invisible")
			continue

		tagImJahr = sum(monatslaenge[:month-1])+day
		wochentag = (tagImJahr + wochentagoffset)%7
		rect.setAttribute("weekday", wochentage[wochentag-1])

		#wochennummer einfuegen
		offset = 0
		if wochentag == 1:
			offset = 15 #15=1/2 fontsize
			rect.parentNode.insertBefore(xml.dom.minidom.parseString("""<text id="{}-{}-woy" class="weekday" style="font-size:30px" x="{}" y="{}">{}</text>"""
					.format(month,
						day,
						float(rect.getAttribute("x"))+2,
						float(rect.getAttribute("y"))+float(rect.getAttribute("height"))/2+10-offset,
						int(tagImJahr/7)+1+kalenderwochenoffset)).firstChild, rect.nextSibling)

		#stammtischwochen
		if wochentag == 2 and int(tagImJahr/7+1) in stammtischwochen:
			rect.addClass("trunktable")

		#ferien und feiertage faerben
		if tagImJahr in freietage:
			rect.addClass("holiday")

		if wochentag == 0 or wochentag == 6:
			rect.addClass("weekend")

		#besondere tage (geburtstage, ccc) kennzeichnen
		if tagImJahr in sondertage:
			specialDayRect = xml.dom.minidom.parseString("""<rect id="{}-{}-specialRect" class="specialdayrect" x="{}" y="{}" width="5" height="{}"></rect>"""
												.format(month, day, float(rect.getAttribute("x"))-5, rect.getAttribute("y"), rect.getAttribute("height"))).firstChild
			#pro eintrag an diesem tag klasse setzen, bezeichnung einfuegen
			for i, sondertag in enumerate(sondertage[tagImJahr]):
				specialDayRect.setAttribute("class", specialDayRect.getAttribute("class") + " " + sondertag[1])
				specialDayText = xml.dom.minidom.parseString("""<text id="{}-{}-special" class="specialdaytext {}" style="font-size:{}px;" x="{}" y="{}">{}</text>"""
						.format(month, day, sondertag[1],
							#textgroesse haengt von anzahl der eintraege ab
							float(rect.getAttribute("height"))/(0.7+0.7*len(sondertage[tagImJahr])),
							float(rect.getAttribute("x"))+45+(10 if len(sondertage[tagImJahr])>1 else 0),
							#y mit magischer formel bestimmen, die auch die anzahl der eintraege mit einbezieht
							float(rect.getAttribute("y"))+float(rect.getAttribute("height"))/len(sondertage[tagImJahr])*(i+1)-0.3*(float(rect.getAttribute("height"))/(0.7+0.7*len(sondertage[tagImJahr]))),
							sondertag[0])).firstChild

				rect.addClass(sondertag[1])
				rect.parentNode.insertBefore(specialDayText, rect.nextSibling)

			if not len(sondertage[tagImJahr]) == 0:
				rect.parentNode.insertBefore(specialDayRect, rect.nextSibling)


		#wochentag einfuegen
		rect.parentNode.insertBefore(xml.dom.minidom.parseString("""<text id="{}-{}-weekday" style="font-size:30px;" x="{}" y="{}">{}</text>"""
					.format(month,
						day,
						float(rect.getAttribute("x"))+2,
						float(rect.getAttribute("y"))+float(rect.getAttribute("height"))/2+10+offset,
						wochentage[wochentag-1][0:2])).firstChild, rect.nextSibling)


f = open(args.output,'w')

image.writexml(f)
f.close()

print("Warning: When printing, convert to cmyk first (inkscape->png; convert mycal.png -colorspace cmyk mycal.jpg)")
