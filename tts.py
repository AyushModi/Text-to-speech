from gtts import gTTS
import os
import sys
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO

pageNum = 1
upper = 20
overwritePageNum = True
class PdfConverter:

   def __init__(self, file_path):
       self.file_path = file_path
    # convert pdf file to a string which has space among words 
   def convert_pdf_to_txt(self, lower, upper):
       rsrcmgr = PDFResourceManager()
       retstr = StringIO()
       codec = 'utf-8'  # 'utf16','utf-8'
       laparams = LAParams()
       device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
       fp = open(self.file_path, 'rb')
       interpreter = PDFPageInterpreter(rsrcmgr, device)
       password = ""
       maxpages = 0
       caching = True
       pagenos = set()
       lower = lower - 1
       for pageNum, page in enumerate(PDFPage.get_pages(fp)):
           if pageNum >= upper:
               break
           if pageNum >= lower:
               interpreter.process_page(page)
       fp.close()
       device.close()
       str = retstr.getvalue()
       retstr.close()
       return str
    # convert pdf file text to string and save as a text_pdf.txt file
   def save_convert_pdf_to_txt(self):
       content = self.convert_pdf_to_txt(pageNum, upper)
       txt_pdf = open('text_pdf.txt', 'wb')
       
       txt_pdf.seek(0)
       txt_pdf.truncate()

       txt_pdf.write(content.encode('utf-8'))
       txt_pdf.close()

def chooseBook():
    f = open(r"Book paths.txt", "r")
    bookPaths = f.readlines()
    f.close()
    for index, path in enumerate(bookPaths):
        print(str(index + 1) + ")\t" + os.path.basename(path))

    pageIndex = input("Pick book number to generate speech for the next 20 pages for that book: ")
    while not pageIndex.isdigit() or int(pageIndex) > len(bookPaths):
        pageIndex = input("Bad input. Pick book to generate its narration: ")
    return bookPaths[int(pageIndex) - 1]

def initDirectory(filePath):
    if (not os.path.isfile(os.path.abspath(filePath))):
        raise FileExistsError("Not a valid file path")
    else:
        filePath = os.path.abspath(filePath)
        f = open(r"Book paths.txt", "a")
        f.write("\n" + filePath)

def storeRange():
    global pageNum
    global upper
    inp = input("Proceed to generate input for pages " + str(pageNum) + "-" + str(pageNum + 19) + "? ([y]/n): ") 
    if (inp != "y" or inp != ""):
        pageNum = input("Pick start page: ")
        while not pageNum.isdigit() or int(pageNum) == 0:
            pageNum = input("Bad input. Pick start page: ")
        pageNum = int(pageNum)
        upper = input("Pick last page (currently pg." + str(pageNum+19) + "): ")
        if (upper != ""):
            while not upper.isdigit() or int(upper) < pageNum:
                upper = input("Bad input. Pick start page: ")
            upper = int(upper)
        else:
            upper = pageNum + 19

def handleFiles():
    global pageNum
    
    if (len(sys.argv) > 1):
        filePath = sys.argv[1]
        initDirectory(filePath)
    else:
        filePath = chooseBook()
    dirPath = os.path.dirname(filePath)
    pagePath = dirPath + "/pageNum.txt"
    if not os.path.isfile(pagePath):
        f = open(pagePath, "w")
        f.write("1")
        f.close()
    else:
        with open(pagePath,"r+") as pageNumReader:
            pageNum = int(pageNumReader.readlines()[0])
            storeRange()
            pageNumReader.seek(0)
            pageNumReader.truncate()
            pageNumReader.write(str(upper + 1))  
    if not os.path.isdir(dirPath + "/output"):
        os.mkdir(dirPath+"/output")
    print("\n")
    return dirPath, filePath

def generateAudio(dirPath):
    myTxt = pdfConverter.convert_pdf_to_txt(pageNum, upper)
    myTxt = myTxt.replace("\n", " ")
    language = 'en'
    output = gTTS(text=myTxt, lang=language, slow=False)
    print("Complete. Saving audio to file")
    name = str(pageNum)+"-"+str(upper)+".mp3"
    audioPath = dirPath + "/output/" + name
    output.save(audioPath)
    print("Complete")


if __name__ == '__main__':
    dirPath, filePath = handleFiles()     
    print("Extracting text from pdf...")    
    pdfConverter = PdfConverter(file_path=filePath)
    print("Complete. Saving copy of text for review")    
    pdfConverter.save_convert_pdf_to_txt()
    print("Complete. Generating audio")
    generateAudio(dirPath)
    