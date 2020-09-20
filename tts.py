import os
import sys
import webbrowser
import traceback
from scripts.pdfReader import PdfConverter
from io import BytesIO
from google.cloud import texttospeech
from pydub import AudioSegment

lower = 1
upper = 20
overwritePageNum = True
API_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Resources', "tts_api.json"))
book_paths = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Resources', 'Book paths.txt'))

def chooseBook():
    if os.path.isfile(book_paths):  
        with open(book_paths, "r") as f:
            bookPaths = f.readlines()
            bookPaths = list(map(lambda x: x.strip(), bookPaths))
            newPaths = set()
            deletions = set()
        
        for path in bookPaths:
            if (os.path.isfile(path)):
                newPaths.add(path)
            else:
                deletions.add(path)
        if (len(deletions) > 0):
            print("Invalid path(s) in 'Resources/Book paths.txt'")
            for invldPath in deletions:
                print("\tDeleting:\t" + invldPath)
            print("\n")
            with open(book_paths, "w") as f:
                for path in newPaths:
                    f.write(path + "\n")
        print("Book paths:")
        for index, path in enumerate(newPaths):
            print(str(index + 1) + ")\t" + os.path.basename(path))  

        pageIndex = input("Pick book number to generate speech for the next 20 pages for that book: ")
        while not pageIndex.isdigit() or int(pageIndex) > len(bookPaths):
            pageIndex = input("Bad input. Pick book to generate its narration: ")
        return bookPaths[int(pageIndex) - 1]
    else:
        newBook = input('Enter the path to the pdf book you want to read: ')
        while not os.path.isfile(newBook):
            newBook = input('Invalid path. Enter the path to the pdf book you want to read: ')
        with open(book_paths, "w") as f:
            f.write(newBook + '\n')
        return newBook

def initDirectory(filePath):
    if (not os.path.isfile(os.path.abspath(filePath))):
        raise FileExistsError(f"Not a valid file path: '{filePath}'" )
    else:
        filePath = os.path.abspath(filePath)
        f = open(book_paths, "a")
        f.write(filePath + "\n")

def storeRange():
    global lower
    global upper
    upper = lower + 19
    inp = input("Proceed to generate input for pages " + str(lower) + "-" + str(upper) + "? ([y]/n): ") 
    if (inp != "y" and inp != "Y" and inp != ""):
        lower = input("Pick start page: ")
        while not lower.isdigit() or int(lower) == 0:
            lower = input("Bad input. Pick start page: ")
        lower = int(lower)
        upper = input("Pick last page (currently pg." + str(lower+19) + "): ")
        if (upper != ""):
            while not upper.isdigit() or int(upper) < lower:
                upper = input("Bad input. Pick start page: ")
            upper = int(upper)
        else:
            upper = lower + 19

def handleFiles():
    global lower

    if (len(sys.argv) > 1):        
        filePath = os.path.abspath(sys.argv[1])
        initDirectory(filePath)
    else:
        filePath = os.path.abspath(chooseBook())
    
    print("Book chosen\t" + os.path.basename(filePath))
    dirPath = os.path.dirname(filePath)
    pagePath = os.path.abspath(os.path.join(dirPath, 'pageNum.txt'))
    if not os.path.isfile(pagePath):
        lower = 1
        with open(pagePath, "w") as f:
            f.write("1")        
    else:
        with open(pagePath,"r+") as pageNumReader:
            lower = int(pageNumReader.readlines()[0])
    storeRange()
    with open(pagePath,"r+") as updater:
        updater.seek(0)
        updater.truncate()
        updater.write(str(upper + 1))  
    outputFolder = os.path.abspath(os.path.join(dirPath, "output"))
    if not os.path.isdir(outputFolder):
        os.mkdir(outputFolder)
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
        name = str(lower)+"-"+str(upper)+".mp3"
        folderPath = os.path.abspath(os.path.join(dirPath, 'output'))
        audioPath = os.path.abspath(os.path.join(folderPath, name))
        generatedOutput.export(audioPath, format='mp3')
        print('Audio content written to file ' + audioPath)
        webbrowser.open(os.path.realpath(folderPath))

def setCredentials():
    if (not os.path.isfile(API_PATH)):
        raise FileExistsError("API path is not valid:\t" + API_PATH)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=API_PATH


if __name__ == '__main__':
    generatedOutput = AudioSegment.silent(duration=0)
    setCredentials()
    dirPath, filePath = handleFiles()     
    pdfConverter = PdfConverter(file_path=filePath)
    print("Extracting text from pdf...")      
    text = pdfConverter.save_convert_pdf_to_txt(lower, upper)
    print("Generating audio")
    generateAudio(text, dirPath, generatedOutput)
    