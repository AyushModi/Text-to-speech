import os
import sys
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO, BytesIO
from google.cloud import texttospeech
from pydub import AudioSegment

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
       if (content == None): 
           print("Error in reading pdf. Exiting")
           sys.exit(1)
       content = content.replace("\n", " ").replace("\t", " ")
       content = ' '.join(content.split())
       toProceed = input("Number of characters is " + str(len(content)) + ". Proceed (Y/n)? ")       
       while toProceed != 'Y':
           if (toProceed == 'n'):
               sys.exit()
           pageIndex = input("Proceed (Y/n)? ")
       print("Complete. Saving copy of text for review")  
       with open('text_pdf.txt', 'wb') as txt_pdf:
           txt_pdf.seek(0)
           txt_pdf.truncate()
           txt_pdf.write(content.encode('utf-8'))
       return content

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
        filePath = sys.argv[1].replace('\\','/')
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



def getDictation(text, generatedOutput):    

    # Instantiates a client
    client = texttospeech.TextToSpeechClient()
    # Set the text input to be synthesized
    synthesis_input = texttospeech.types.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.types.VoiceSelectionParams(
        language_code='en-US',
        name='en-US-Wavenet-D',
        ssml_gender=texttospeech.enums.SsmlVoiceGender.MALE)

    # Select the type of audio file you want returned
    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3)

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(synthesis_input, voice, audio_config)
    s = BytesIO(response.audio_content)
    generatedOutput += AudioSegment.from_file(s, format='mp3')
    generatedOutput += AudioSegment.silent(duration=750)
    return generatedOutput
    

def generateAudio(myTxt, dirPath, generatedOutput):     
    phrases = myTxt.split('. ')
    sentences = phrases[0]
    try:
        for phrase in phrases[1:]:
            if (len(sentences) + len(phrase) >= 4999):
                generatedOutput = getDictation(sentences, generatedOutput)
                sentences = phrase
            else:
                sentences += ". " + phrase        
            
        print("Complete. Saving audio to file.")
        if (len(sentences) > 0):
            generatedOutput = getDictation(sentences, generatedOutput)
    except:
        print("Unexpected error.\n", sys.exc_info()[0])
    finally:
        print("Saving audio to file.")
        name = str(pageNum)+"-"+str(upper)+".mp3"
        audioPath = dirPath + "/output/" + name
        generatedOutput.export(audioPath, format='mp3')
        print('Audio content written to file ' + audioPath)

if __name__ == '__main__':
    generatedOutput = AudioSegment.silent(duration=0)
    dirPath, filePath = handleFiles()     
    pdfConverter = PdfConverter(file_path=filePath)
    print("Extracting text from pdf...")      
    text = pdfConverter.save_convert_pdf_to_txt()
    print("Complete. Generating audio")
    generateAudio(text, dirPath, generatedOutput)
    