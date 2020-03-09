import asyncio
import re
import itertools
import csv
import argparse
import lxml.etree as ET


class Code:
    # initiate parser
    parser = ET.XMLParser(
        remove_blank_text=True, ns_clean=True, encoding="utf-8", recover=True,
    )

    # Important grid co ordinates
    x_coords = [
        (10, 70, "A"),
        (100, 350, "B"),
        (400, 550, "C"),
        (600, 750, "D"),
        (800, 950, "E"),
        (1000, 1250, "F"),
    ]
    y_coords = [
        (90, 265),
        (272, 455),
        (465, 647),
        (657, 840),
    ]
    xy_coords = tuple(itertools.product(x_coords, y_coords))

    # Other important information like element groups and titles
    elemGroupCoord = [(20, 44), (60, 90)]
    elemGroup = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
    apparatusCoord = [(450, 500), (90, 110)]

    # The regex patterns needed for all functions
    RomNumRegex = r"([MDCLXVI]+)"
    numRegex = r"([0-9]+)(?=\.)"
    GHRegex = r"\b(G|H)\b"
    vaultRegex = r"([0-9]\.[0-9])"
    appRegex = (
        r"(?<=section\s[0-9][0-9]:)\s*("
        "floor exercise|"
        "pommel horse|"
        "rings|"
        "vault|"
        "parallel bars|"
        "Horizontal Bar|"
        ")"
    )

    # Initialise Object
    def __init__(self, xml):
        self.xml = xml
        self.tree = ET.parse(self.xml, self.parser)
        self.root = self.tree.getroot()
        self.pages = self.root.xpath("page")

    # a function to get the path to all elements in a grid box
    async def element_path(self, xyCoord):
        x1, x2, *_ = xyCoord[0]
        y1, y2, *_ = xyCoord[1]
        path = (
            '*[@left > "{}" and '
            '@left < "{}" and '
            '@top > "{}" and '
            '@top < "{}"]'.format(x1, x2, y1, y2)
        )
        return path

    async def get_GH(self, element):
        GH = None
        for item in element:
            bold = item.xpath("b/text()")
            if bold:
                pattern = self.GHRegex
                GH = re.search(pattern, bold[0])
                if GH:
                    GH = GH.group(0)
                    break
        return GH

    async def get_name(self, element):
        name = ""
        for item in element:
            italics = item.xpath("i/text()")
            bold = item.xpath("b/text()")
            if italics:
                name += italics[0]
            if bold and len(bold[0]) > 3:
                name += bold[0]
        name = name.strip()
        return name

    async def get_number(self, element):
        number = ""
        for item in element:
            pattern = self.numRegex
            itemTxt = str(item.text)
            result = re.search(pattern, itemTxt)
            if result:
                number = int(result.group(0))
                break
        return number

    async def get_elem_group(self, page):
        path = await self.element_path(self.elemGroupCoord)
        try:
            EGdescription = page.xpath(f"{path}/b/text()")[0]
            pattern = self.RomNumRegex
            EG = re.search(pattern, EGdescription)
            EG = EG.group(0)
            if EG in self.elemGroup:
                return self.elemGroup[EG]
        except (AttributeError, IndexError):
            return False

    async def get_apparatus(self, page):
        path = await self.element_path(self.apparatusCoord)
        try:
            appSection = page.xpath("{}/b/text()".format(path))[0]
            pattern = self.appRegex
            apparatus = re.search(pattern, appSection, flags=re.I)
            if apparatus:
                apparatus = apparatus.group(0)
                apparatus = apparatus.strip()
                return apparatus
        except (IndexError, AttributeError):
            return False

    async def get_vault(self, element):
        vaultVal = ""
        for item in element:
            try:
                bold = item.xpath("b/text()")
                if bold:
                    pattern = self.vaultRegex
                    vaultVal = re.search(pattern, bold[0])
                    if vaultVal:
                        vaultVal = vaultVal.group(0)
                        break
            except IndexError:
                continue
        return vaultVal

    async def get_img(self, element):
        image = ""
        for item in element:
            if item.tag == "image":
                itemdict = dict(item.items())
                image = itemdict["src"]
                break
        return image

    async def get_skills(self):
        current_apparatus = ""
        for i, page in enumerate(self.pages):
            print("processing page {}".format(i))
            EG, page_apparatus = await asyncio.gather(
                self.get_elem_group(page), self.get_apparatus(page)
            )
            if not EG and not page_apparatus:
                continue
            elif page_apparatus:
                current_apparatus = page_apparatus
                continue

            for xy in self.xy_coords:
                path = await self.element_path(xy)
                elem = page.xpath(path)
                if value := await self.get_GH(elem):
                    pass
                elif value := await self.get_vault(elem):
                    pass
                else:
                    value = xy[0][2]
                if name := await self.get_name(elem):
                    image, number = await asyncio.gather(
                        self.get_img(elem), self.get_number(elem)
                    )
                    yield (
                        {
                            "app": current_apparatus,
                            "value": value,
                            "EG": EG,
                            "number": number,
                            "description": name,
                            "image_path": image,
                        }
                    )

    async def write_csv(self):
        with open("skills.csv", "w", encoding="utf-8") as csvfile:
            fieldnames = ["app", "value", "EG", "number", "description", "image_path"]
            write = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator="\n")
            write.writeheader()
            skills = [i async for i in self.get_skills()]
            write.writerows(skills)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Scrape the Code of Points")
    ap.add_argument("-f", help="Specify XML file to be scraped", required=True)
    args = ap.parse_args()

    if args.f:
        code = Code(args.f)
        asyncio.run(code.write_csv())
