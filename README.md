# CRCR

CalendrCreatr for fast creation of beautiful calendars in svg format

#Usage
```
usage: calendrcreatr.py [-h] [-y YEAR] [-c CONFIG] [-t TEMPLATE]
                        [-s STYLESHEET] [-o OUTPUT]

Create a beautiful calendar in a heartbeat from a config file and a template.

optional arguments:
  -h, --help            show this help message and exit
  -y YEAR, --year YEAR  overwrite the year in the config file (default: None)
  -c CONFIG, --config CONFIG
                        path to the config file to read (default:
                        calendar.conf)
  -t TEMPLATE, --template TEMPLATE
                        path to the template file to read (default:
                        templates/calendar.svg)
  -s STYLESHEET, --stylesheet STYLESHEET
                        path to the stylesheet file to import into the svg
                        (default: templates/style.css)
  -o OUTPUT, --output OUTPUT
                        path to the write the output to (default:
                        outputCalendar.svg)
```

## How to print (e.g. for 2017)
```
./calendrcreatr.py -c calendar_2017.conf -o output-2017.svg
inkscape -f output-2017.svg -e output-2017.png -d 300
convert output-2017.png -colorspace cmyk output-2017.jpg
rm output-2017.png
```
Hand to your friendly printing agency, tell them the size (file is A0, usually you want something like A1, A2 or A3).

## License
This software is released under GPL v3
