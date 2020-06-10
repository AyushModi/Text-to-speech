import os
import webbrowser
import sys
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO, BytesIO
import time
class PdfConverter:

   def __init__(self, file_path):
       self.file_path = file_path
    # convert pdf file to a string which has space among words 
   def convert_pdf_to_txt(self):
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
       for pageNum, page in enumerate(PDFPage.get_pages(fp)):
            interpreter.process_page(page)
       fp.close()
       device.close()
       str = retstr.getvalue()
       retstr.close()
       return str
    # convert pdf file text to string and save as a text_pdf.txt file

def convertFile():
    filePath = sys.argv[1]  
    pdfConverter = PdfConverter(file_path=filePath)
    content = pdfConverter.convert_pdf_to_txt()
    content = content.replace("\n", " ").replace("\t", " ")
    content = ' '.join(content.split())
    print(len(content))

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '=', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill*filledLength + '>'*(0 if iteration == total else 1) + '-'*(length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def progress():
    total = 50
    printProgressBar(0, total, prefix = 'Progress:', suffix = 'Complete', length = 50)
    for i in range(total):
        time.sleep(1)
        printProgressBar(i + 1, total, prefix = 'Progress:', suffix = 'Complete', length = 50)
if __name__ == '__main__':
    # convertFile()
    progress()