import os
import sys
import urllib.request
from bs4 import BeautifulSoup
import lxml.html as LH
import datetime
import PyPDF2
import requests
import json
import nltk
from nltk.tokenize import sent_tokenize,word_tokenize
from nltk.corpus import stopwords
from collections import defaultdict
from string import punctuation
from heapq import nlargest
import traceback
from gensim.summarization import keywords
import pandas as pd
from xlrd import open_workbook
nltk.download('stopwords')
nltk.download('punkt')

website = "http://www.mca.gov.in"

dict1 = dict([("Companies Act", ["Accounts/Audit","Accounts","Audit","Deposits","Allotment of Securities","Corporate social responsibility","IEPF","Registration of Foreign Companies","Management and Administration","Appointment and Qualification of Directors","Auditor","Cost Records","Declaration and Payment of Dividend","Incorporation","Indian Accounting Standards","Issue of Global Depository Receipt","Meetings of Board and its Powers","Prospectus and Allotment of Securities","Charges","Share Capital and Debentures","Secretarial Standard1 on '"'Meetings of the Board of Directors'"'","Secretarial Standard2 on '"'General Meetings'"'","National Company Law Tribunal ","Compromises, Arrangements and Amalgamation","Restriction on number of layers","Form change"]),
              ("Limited Liability Partnership Act",["Limited Liability","Partnership","Partners"])])

curr_dir = "".join(sys.argv[1:])

def createDirIfNotExists(path) :
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def download_file(download_url, pdf_path): 
    response = urllib.request.urlopen(download_url) 
    print("PDF LAST MODIFIED DATE :: " + str(response.headers.get('Last-Modified')))
    file = open(pdf_path, 'wb+') 
    file.write(response.read()) 
    file.close() 
    print("Completed")

def get_file_header_details(download_url) :
    response = urllib.request.urlopen(download_url)
    return response.headers

#read pdf from a url
def ocr_space_url(url, overlay=False, api_key='test', language='eng'):
    payload = {'url': url,
               'isOverlayRequired': overlay,
               'apikey': "9fd32f060488957",
               'language': language,
               }
    r = requests.post('https://api.ocr.space/parse/image',
                      data=payload,
                      )
    return r.content.decode()

#read pdf from local
def ocr_space_file(filename, overlay=False, api_key='test', language='eng'):
    payload = {'isOverlayRequired': overlay,
               'apikey': "9fd32f060488957",
               'language': language,
               }
    with open(filename, 'rb') as f:
        r = requests.post('https://api.ocr.space/parse/image',
                          files={filename: f},
                          data=payload,
                          )
    return r.content.decode()

def formatTimeStamp(from_format, to_format, date) :
    date_str = datetime.datetime.strptime(date, from_format).strftime(to_format)
    return date_str

def readPDFFileAsString(pdf_path) :
    pdfFileObj = open(pdf_path, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    #print("CREATION DATE :: " + datetime.datetime.strptime(str(pdfReader.getDocumentInfo()['/CreationDate'])[2:-7], "%Y%m%d%H%M%S").strftime("%Y%m%d%H%M%S"))
    print("NUMBER OF PAGES :: " + str(pdfReader.numPages))
    pageObj = pdfReader.getPage(0)
    stringPDF = pageObj.extractText()
    pdfFileObj.close()
    
    return stringPDF

#----------------------------------------
#----------------------------------------


page = urllib.request.urlopen(website)
soup = BeautifulSoup(page, "lxml")
root = LH.fromstring(soup.prettify())

date_now = datetime.datetime.now()

root_dir = createDirIfNotExists(curr_dir + "\\")

print("Root directory = " + root_dir)
pdf_path = createDirIfNotExists(root_dir + "downloaded_pdfs\\")
data_dir = createDirIfNotExists(root_dir + "data\\")
output_dir = createDirIfNotExists(root_dir + "output\\")
error_dir = createDirIfNotExists(root_dir + "error\\")

last_batch_details = {}
current_batch_details = {}

try :
    if(os.path.exists(data_dir + 'last_batch_stats.txt')) :
        fx=open(data_dir + 'last_batch_stats.txt', 'r')

        for line in fx :
            key = line.split('~')[0].replace('\n','')
            val = line.split('~')[1].replace('\n','')
            last_batch_details[key] = val
                              
        fx.close()
    else :
        print("File doesnt exits..May be it is the first time you are running the utility")

except IOError:
    print('An error occurred trying to read/write the file.')

except :
    print("Something went wrong ")
    traceback.print_exc               

fl=open(data_dir + 'scrapped_data.txt','w+', encoding="utf-8")

for atag in root.xpath('//div[@class="threetabs"]//li'):
    try :
        text_content = " ".join(str(atag.text_content()).replace("\n", " ").strip().split())
        actual_content = ""
        if((atag.attrib['class'] == 'impInfoLi' and sum(1 for _ in atag.iter("a")) == 1)
        or (atag.attrib['class'] == 'links_blue')): 
                print("With link")
                for x in atag.iter("a"):
                    link = x.attrib['href']
                    if(link.endswith(".pdf")) :
                        print("This is a PDF url")
                        url = website + link
                        pdf_name = url.split("//")[1].replace("/","_")
                        
                        try :
                            last_modified_date = str(get_file_header_details(url).get('Last-Modified'))
                        except :
                            print("There is some issue while fetching file details")
                            traceback.print_exc
                        
                        #check if the pdf was downloaded in the last-run
                        #text_content = " ".join(str(atag.text_content()).replace("\n", " ").strip().split())
                        if((text_content in last_batch_details and 
                            last_modified_date == str(last_batch_details[text_content]))
                        or (pdf_name in os.listdir(pdf_path)) ) :
                            
                            print(pdf_name + " -- File already exists...skipping download")
                        else :    
                            print("----------------" + text_content + "-----------------")
                            print("Downloading PDF :: " + url)
                            file_path = pdf_path + pdf_name
                            
                            try :
                                download_file(url, file_path)
                            except :
                                print("There is some issue while downloading file")
                                traceback.print_exc
                                
                            print("Reading PDF file as a string from path : " + file_path)
                            pdfString = readPDFFileAsString(file_path)
                        
                            try : 
                                if(pdfString == "") :
                                    ocr_file = ocr_space_file(file_path)
                                    json_str = json.loads(ocr_file)['ParsedResults'][0]['ParsedText']
                                    #print(json_str)
                                    pdfString = json_str
                            except :
                                print("There is some error in parsing the OCR file")
                                print("Error : " + str(json.loads(ocr_file)['ErrorMessage']))
                                pdfString = atag.text_content()
                             
                            actual_content = atag.text_content() + "~" + pdfString
                            #adding current batch details to the file
                            current_batch_details[atag.text_content()] = last_modified_date
                
                    else :
                        print("This is a normal url")
                        url = link
                        if(text_content in last_batch_details) :
                            print("Content already exists..Skipping")
                        else :
                            #add the content to the current_batch_details
                            current_batch_details[text_content] = str(date_now)
                            actual_content = atag.text_content() + '~' + atag.text_content()
        
        elif(atag.attrib['class'] == 'impInfoLi' and sum(1 for _ in atag.iter("a")) == 0) :
                print("Without link")
                
                #text_content = " ".join(str(atag.text_content()).replace("\n", " ").strip().split())
                
                if(text_content in last_batch_details) :
                    print(text_content + " -- Content already exists..Skipping")
                else :
                    #add the content to the current_batch_details
                    current_batch_details[text_content] = str(date_now)
                    actual_content = atag.text_content() + '~' + atag.text_content()
                     
        x = " ".join(actual_content.replace("\n", " ").strip().split())
        
        if x :
            fl.write(x + '\n')
    

    except IOError:
        print('An error occurred trying to read/write the file.')

    except:
        traceback.print_exc()
        print('An error occurred.')  
    
fl.close()    

    
with open(data_dir + 'last_batch_stats.txt' , "a") as f:
    for key in current_batch_details :
        data = " ".join(str(key).replace("\n", " ").strip().split())
        f.write(data + "~" + current_batch_details[key] + "\n")
     
        
#filter out irrelevant info
f2=open(data_dir + 'scrapped_data.txt','r', encoding = 'utf-8')
f3=open(data_dir + 'categorized_data.txt','w+', encoding = 'utf-8')

try :
    if (os.stat(data_dir + 'scrapped_data.txt').st_size!=0) :
        for line in f2: 
            keywrd_found = False
            #print(line)
            content = ""
            if("~" in line and line) :
                if(line.replace("\n","").split("~")[1].strip() != "") :
                    content = line.split("~")[1]
                elif(line.split("~")[1].strip() == "") :
                    content = line.split("~")[0]
            for key in dict1 :
                for keywrd in dict1[key] :
                    if (keywrd.lower() in content.lower() and not keywrd_found) :
                        f3.write(key + "~" + content)
                        keywrd_found = True
 
except :
    print("Something went wrong")
    traceback.print_exc()
    
    
f2.close()
f3.close()


#--------------------------------------------------------
#SUMMARIZER
#--------------------------------------------------------

#import sumy
class FrequencySummarizer:
  def __init__(self, min_cut=0.1, max_cut=0.7):
    """
     Initilize the text summarizer.
     Words that have a frequency term lower than min_cut
     or higer than max_cut will be ignored.
    """
    self._min_cut = min_cut
    self._max_cut = max_cut
    self._stopwords = set(stopwords.words('english') + list(punctuation))

  def _compute_frequencies(self, word_sent):
    """
      Compute the frequency of each of word.
      Input:
       word_sent, a list of sentences already tokenized.
      Output:
       freq, a dictionary where freq[w] is the frequency of w.
    """
    freq = defaultdict(int)
    for s in word_sent:
      for word in s:
        if word not in self._stopwords:
          freq[word] += 1
    # frequencies normalization and fitering
    m = float(max(freq.values()))
    for w in list(freq.keys()):
      freq[w] = freq[w]/m
      if freq[w] >= self._max_cut or freq[w] <= self._min_cut:
        del freq[w]
    return freq

  def summarize(self, text, n):
    """
      Return a list of n sentences
      which represent the summary of text.
    """
    sents = sent_tokenize(text)
    assert n <= len(sents)
    word_sent = [word_tokenize(s.lower()) for s in sents]
    self._freq = self._compute_frequencies(word_sent)
    ranking = defaultdict(int)
    for i,sent in enumerate(word_sent):
      for w in sent:
        if w in self._freq:
          ranking[i] += self._freq[w]
    sents_idx = self._rank(ranking, n)    
    return [sents[j] for j in sents_idx]

  def _rank(self, ranking, n):
    """ return the first n sentences with highest ranking """
    return nlargest(n, ranking, key=ranking.get)

#-----------------------------------------------------------

fs = FrequencySummarizer()

indata = pd.DataFrame(columns=['Category','Text'])

if(os.path.exists(data_dir + 'categorized_data.txt') and 
   os.stat(data_dir + 'categorized_data.txt').st_size > 0) :
    indata = pd.read_csv(data_dir + "categorized_data.txt", sep="~",).drop_duplicates()

indata.to_csv(data_dir + "categorized_data_without_duplicates.txt", sep="~", index = False,)

file3 = open(data_dir + "categorized_data_without_duplicates.txt", 'r')
file4 = open(data_dir + "categorized_data_final.txt", 'w')

#put in headers
#file4.write("Website~Extract Date~List of Enactments~Actual Content~Summary~Relevant keywords\n")

for line in file3 :
    text = line.split("~")[1]
    #print(text)
    for s in fs.summarize(text, 1):
        D=keywords(text).replace('\n',',')
        #print(D)
        file4.write(website + '~' + str(date_now) + '~' + line.replace("\n","") + "~" + s + "~" + str(D) + "\n")
        #print(line.replace("\n","") + "~" + s)
    
file3.close()
file4.close()

#import to a excel
#coding:utf-8

columns = ['Website','Extract Date','List of Enactments','Actual Content','Summary','Relevant keywords']

csv_old = pd.DataFrame(columns=columns)

try :
    if(os.stat(root_dir + "\IRCUM_Utility.xlsm").st_size > 0) :
        '''csv_old = pd.read_csv(output_dir + "regulatory_compliance_file_old.txt", 
                              encoding='utf8', 
                              sep='\t', 
                              dtype='unicode', 
                              names=columns,
                              skiprows=2).dropna(how = 'any') '''
        
        csv_old = pd.read_excel(root_dir + "\IRCUM_Utility.xlsm", sheetname="Sheet1", skiprows=2, index = False)
        
except :
    traceback.print_exc
        
csv_new = pd.DataFrame(columns=columns) 

if(os.path.exists(data_dir + 'categorized_data_final.txt') and 
   os.stat(data_dir + 'categorized_data_final.txt').st_size > 0) :
    csv_new = pd.read_csv(data_dir + "categorized_data_final.txt", encoding='utf8', sep='~', dtype='unicode', names=columns)
    
csv_final = pd.concat([csv_old, csv_new])

csv_final.to_csv(output_dir + "regulatory_compliance_file.csv", index=False, header=True)