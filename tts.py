import os
import sys
import webbrowser
import traceback
from io import StringIO, BytesIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from google.cloud import texttospeech
from pydub import AudioSegment

pageNum = 1
upper = 20
overwritePageNum = True
API_PATH = os.path.join(os.path.dirname(__file__), "tts_api.json")
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
       print("Complete. Saving copy of text for review")  
       print("Number of characters is " + str(len(content)))   
       with open('text_pdf.txt', 'wb') as txt_pdf:
           txt_pdf.seek(0)
           txt_pdf.truncate()
           txt_pdf.write(content.encode('utf-8'))
       toProceed = input("Proceed to generating audio (Y/n)? ")       
       while toProceed != 'Y':
           if (toProceed == 'n'):
               sys.exit()
           pageIndex = input("Proceed (Y/n)? ")
       return content

def chooseBook():
    f = open(r"Book paths.txt", "r")
    bookPaths = f.readlines()
    bookPaths = list(map(lambda x: x.strip(), bookPaths))
    newPaths = []
    deletions = []
    f.close()
    for path in bookPaths:
        if (os.path.isfile(path)):
            newPaths.append(path)
        else:
            deletions.append(path)
    if (len(deletions) > 0):
        print("Invalid path(s) in 'Book paths.txt'")
        for invldPath in deletions:
            print("\tDeleting:\t" + invldPath)
        print("\n")
        with open("Book paths.txt", "w") as f:
            for path in newPaths:
                f.write(path + "\n")
    print("Book paths:")
    for index, path in enumerate(newPaths):
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
        f.write(filePath + "\n")

def storeRange():
    global pageNum
    global upper
    upper = pageNum + 19
    inp = input("Proceed to generate input for pages " + str(pageNum) + "-" + str(upper) + "? ([y]/n): ") 
    if (inp != "y" and inp != "Y" and inp != ""):
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
    
    print("Book chosen\t" + os.path.basename(filePath))
    dirPath = os.path.dirname(filePath)
    pagePath = dirPath + "/pageNum.txt"
    if not os.path.isfile(pagePath):
        pageNum = 1
        f = open(pagePath, "w")
        f.write("1")
        f.close()
    else:
        with open(pagePath,"r+") as pageNumReader:
            pageNum = int(pageNumReader.readlines()[0])
    storeRange()
    with open(pagePath,"r+") as updater:
        updater.seek(0)
        updater.truncate()
        updater.write(str(upper + 1))  
    if not os.path.isdir(dirPath + "/output"):
        os.mkdir(dirPath+"/output")
    print("\n")
    return dirPath, filePath



def getDictation(text, generatedOutput):    

    # Instantiates a client
    client = texttospeech.TextToSpeechClient()
    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code='en-US',
        name='en-US-Wavenet-D',
        ssml_gender=texttospeech.SsmlVoiceGender.MALE)

    # Select the type of audio file you want returned
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        effects_profile_id = ['headphone-class-device']
        )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(input=synthesis_input, voice=voice,audio_config=audio_config)
    s = BytesIO(response.audio_content)
    generatedOutput += AudioSegment.from_file(s, format='mp3')
    generatedOutput += AudioSegment.silent(duration=750)
    return generatedOutput
    
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

def generateAudio(myTxt, dirPath, generatedOutput):     
    phrases = myTxt.split('. ')
    sentences = phrases[0]
    total = len(phrases)
    try:
        printProgressBar(1, total, prefix = 'Progress:', suffix = 'Complete', length = 50)
        for i, phrase in enumerate(phrases[1:]):
            if (len(sentences) + len(phrase) >= 4999):
                generatedOutput = getDictation(sentences, generatedOutput)
                sentences = phrase
            else:
                sentences += ". " + phrase        
            printProgressBar(i + 2, total, prefix = 'Progress:', suffix = 'Complete', length = 50)
        print("Complete. Saving audio to file.")
        if (len(sentences) > 0):
            generatedOutput = getDictation(sentences, generatedOutput)
    except Exception as e:
        print("\n\nUnexpected error.\n-----------------")
        traceback.print_exc()
        print("-----------------\n\nIncomplete audio generated. Saving to file anyway.")
    finally:
        name = str(pageNum)+"-"+str(upper)+".mp3"
        audioPath = dirPath + "/output/" + name
        generatedOutput.export(audioPath, format='mp3')
        print('Audio content written to file ' + audioPath)
        webbrowser.open(os.path.realpath(dirPath + "/output/"))

def setCredentials():
    abs_path = os.path.abspath(API_PATH)
    if (not os.path.isfile(abs_path)):
        raise FileExistsError("API path is not valid:\t" + os.path.abspath(abs_path))
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=abs_path

if __name__ == '__main__':
    generatedOutput = AudioSegment.silent(duration=0)
    setCredentials()
    dirPath, filePath = handleFiles()     
    pdfConverter = PdfConverter(file_path=filePath)
    print("Extracting text from pdf...")      
    text = pdfConverter.save_convert_pdf_to_txt()
    print("Generating audio")
    generateAudio(text, dirPath, generatedOutput)
    