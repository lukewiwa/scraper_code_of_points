import lxml.etree as ET
import re
import itertools
import csv
import string
import time

parser = ET.XMLParser(  remove_blank_text = True,
                        ns_clean = True,
                        encoding = 'utf-8',
                        recover = True,
                        )
tree = ET.parse('CoP_MAG_2017-2020_ICI-e.xml', parser)
root = tree.getroot()

# draw up the grid which all the skills sit in
xCoords= [(10, 70, 'A'),
          (100, 350, 'B'),
          (400, 550, 'C'),
          (600, 750, 'D'),
          (800, 950, 'E'),
          (1000, 1250, 'F'),
          ]
yCoords = [(90, 265),
           (272, 455),
           (465, 647),
           (657, 840),
           ]
xyCoords = list(itertools.product(xCoords,yCoords))

# Other important information like element groups and titles
elemGroupCoord = [(20, 44), (60, 90)]
elemGroup = {'I' : 1,
             'II' : 2,
             'III' : 3,
             'IV' : 4,
             'V' : 5
             }
appNameCoord = [(450, 500), (90, 110)]

pages = root.xpath("page")

# The regex patterns needed for all functions
RomNumRegex = r'([MDCLXVI]+)'
numRegex = r'([0-9]+)(?=\.)'
GHRegex = r'\b(G|H)\b'
vaultRegex = r'([0-9]\.[0-9])'
appRegex = r'(?<=section\s[0-9][0-9]:)\s*('\
            'floor exercise|'\
            'pommel horse|'\
            'rings|'\
            'vault|'\
            'parallel bars|'\
            'Horizontal Bar|'\
            ')'

# a function to get the path to all elements in a grid box
def elementPath(xyCoord):
    x1 = xyCoord[0][0]
    x2 = xyCoord[0][1]
    y1 = xyCoord[1][0]
    y2 = xyCoord[1][1]
    path = '*[@left > "{}" and '\
            '@left < "{}" and '\
            '@top > "{}" and '\
            '@top < "{}"]'\
            .format(x1, x2, y1, y2)
    return path

def getGH(element):
    GH = False
    for item in element:
        bold = item.xpath('b/text()')
        if bold:
            pattern = GHRegex
            GH = re.search(pattern, bold[0])
            if GH:
                GH = GH.group(0)
                break
    return GH

def getName(element):
    name = ''
    for item in element:
        italics = item.xpath('i/text()')
        bold = item.xpath('b/text()')
        if italics:
            name += italics[0]
        if bold and len(bold[0]) > 3:
            name += bold[0]
    name = name.strip()
    return name

def getNumber(element):
    number = ''
    for item in element:
        pattern = numRegex
        itemTxt = str(item.text)
        result = re.search(pattern, itemTxt)
        if result:
            number = int(result.group(0))
            break
    return number

def getElemGroup(page):
    path = elementPath(elemGroupCoord)
    try:
        EGdescription = page.xpath("{}/b/text()".format(path))[0]
        pattern = RomNumRegex
        EG = re.search(pattern, EGdescription)
        EG = EG.group(0)
        if EG in elemGroup:
            return elemGroup[EG]
    except (AttributeError, IndexError):
        return False

def getApp(page):
    path = elementPath(appNameCoord)
    try:
        appSection = page.xpath("{}/b/text()".format(path))[0]
        pattern = appRegex
        appName = re.search(pattern, appSection, flags=re.I)
        if appName:
            appName = appName.group(0)
            appName = appName.strip()
            return appName
    except (IndexError, AttributeError):
        return False

def getVault(element):
    vaultVal = ''
    for item in element:
        try:
            bold = item.xpath('b/text()')
            if bold:
                pattern = vaultRegex
                vaultVal = re.search(pattern, bold[0])
                if vaultVal:
                    vaultVal = vaultVal.group(0)
                    break
        except IndexError:
            continue
    return vaultVal

def get_img(element):
    image = ''
    for item in element:
        if item.tag == 'image':
            itemdict = dict(item.items())
            image = itemdict['src']
            break
    return image

def getSkills():
    appName = ''
    for i, page in enumerate(pages):
        print('processing page {}'.format(i))
        if not getElemGroup(page) and not getApp(page):
            continue
        elif getApp(page):
            appName = getApp(page)
            continue
        else:
            EG = getElemGroup(page)
        for xy in xyCoords:
            path = elementPath(xy)
            elem = page.xpath(path)
            if getGH(elem):
                value = getGH(elem)
            elif getVault(elem):
                value = getVault(elem)
            else:
                value = xy[0][2]
            if getName(elem):
                image = get_img(elem)
                number = getNumber(elem)
                name = getName(elem)
                yield        ({'app' : appName,
                               'value' : value,
                               'EG' : EG,
                               'number' : number,
                               'description' : name,
                               'image_path' : image,
                               })


if __name__ == "__main__":
    skills = getSkills()

    with open('skills.csv', 'w', encoding='utf-8') as csvfile:
        fieldnames = ['app', 'value', 'EG', 'number', 'description', 'image_path']
        write = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator='\n')
        write.writeheader()
        write.writerows(skills)


