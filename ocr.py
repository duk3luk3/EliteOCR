import cv2
import cv2.cv as cv
import tesseract
import re
from collections import Counter
from bs4 import BeautifulSoup
from PyQt4.QtCore import QSettings
from imageprocessing import *
from settings import Settings

#OCR engines:
from ocrmethods import OCRAreasFinder, TesseractStation, TesseractStationMulti, TesseractMarket1, Levenshtein, NNMethod

class OCR():
    def __init__(self, color_image):
        self.settings = Settings()
        self.repeats = 1
        self.image = color_image
        self.contrast_station_img = makeCleanStationImage(self.image)
        self.contrast_commodities_img = makeCleanImage(self.image)
        self.ocr_areas = OCRAreasFinder(color_image)
        self.station = self.readStationName()
        self.commodities = self.readMarket()
        
    def readStationName(self):
        station_name = TesseractStation(self.contrast_station_img, self.ocr_areas.station_name)
        station_name1 = TesseractStationMulti(self.image, station_name.result[0])
        if len(station_name.result) > 0:
            return station_name.result[0]
        else:
            return None
        
    def readMarket(self):
        market_table = TesseractMarket1(self.contrast_commodities_img, self.ocr_areas.market_table)
        clean_commodities = Levenshtein(market_table.result, self.settings.app_path)
        clean_numbers = NNMethod(self.contrast_commodities_img, market_table.result, self.settings.app_path)
        
        #return self.compareResults(market_table.result,[market_table2.result])
        return clean_numbers.result
        
    def compareResults(self, first, additional):
        for i in range(len(first)):
            internal = 0
            for j in range(len(first[i].items)):
                item = first[i].items[j]
                if item != None:
                    alternatives = []
                    if self.testTypeConformity(j, item.value):
                        alternatives.append(item.value)
                    for k in range(len(additional)):
                        if i < len(additional[k]):
                            if self.checkResultCompatible(first[i], additional[k][i]):
                                newi = ""
                                for l in range(len(item.value.split(' '))):
                                    newi += additional[k][i][internal+l].value + " "
                                if j != 0:
                                    newi = newi.replace('.', ',')
                                if self.testTypeConformity(j, newi):
                                    alternatives.append(newi.strip())

                    if len(additional) > 1:
                        most_common = Counter(alternatives).most_common()
                        if len(most_common) > 0:
                            item.value = most_common[0][0]
                            item.confidence = most_common[0][1]/(self.repeats+1.0)
                            item.optional_values = self.sortAlternatives(most_common)
                    else:
                        item.value = alternatives[1]
                        item.optional_values = list(set(alternatives))
                        
                    internal += len(item.value.split(' '))
        return first
        
    def testTypeConformity(self, index, item):
        numlist = [1, 2, 3,5]
        if index in numlist:
            return re.match("^[0-9,]*$", item.strip())
        else:
            return re.match("^[-A-Z. ]*$", item.strip())
            
    def checkResultCompatible(self, one, two):
        entries = 0
        for item in one.items:
            if item != None:
                entries += 1
        entries += len(one.items[0].value.split(" "))-1
        if entries == len(two):
            return True
        else:
            return False       

    def sortAlternatives(self, alt):
        sorted = []
        for tuple in alt:
            sorted.append(tuple[0])
        return sorted