from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
import os
import sys
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
   def save_convert_pdf_to_txt(self, lower, upper):
       content = self.convert_pdf_to_txt(lower, upper)
       if (content == None): 
           print("Error in reading pdf. Exiting")
           sys.exit(1)
       content = content.replace("\n", " ").replace("\t", " ")
       content = ' '.join(content.split())
       print("Complete. Saving copy of text for review")  
       print("Number of characters is " + str(len(content))) 
       txtBackup = os.path.abspath(os.path.join(os.path.dirname(__file__), 'text_pdf.txt'))  
       with open(txtBackup, 'wb') as txt_pdf:
           txt_pdf.seek(0)
           txt_pdf.truncate()
           txt_pdf.write(content.encode('utf-8'))
       toProceed = input("Proceed to generating audio (Y/n)? ")       
       while toProceed != 'Y':
           if (toProceed == 'n'):
               sys.exit()
           toProceed = input("Proceed (Y/n)? ")
       return content