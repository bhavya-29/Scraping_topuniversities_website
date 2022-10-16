#Importing all the required libraries
import time
import bs4
from bs4 import BeautifulSoup
from selenium.common.exceptions import *
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import json
import requests
import re

#Function to get URLs of each specific college from list of collges in "https://www.topuniversities.com/university-rankings/world-university-rankings/2023" page
def get_uni_information(driver,unilist):

    url = r"https://www.topuniversities.com/university-rankings/world-university-rankings/2023" #given URL
    
    # Open url and get the QS Ranking html page
    time.sleep(2)
    driver.get(url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    #each div tag with class name "row ind" is contains information of specific college
    x = soup.find_all("div", class_="row ind")
    for clg in x:
        info=clg.find("div",class_="td-wrap")
        #Extracting the url of each college using <a> tag from href field 
        a_tag = clg.find('a')
        name=a_tag.get_text()
        url=a_tag.get('href')
        ##unilist is list of lists where each sublist contains name of the university and its URL.
        unilist.append([name,url])


    #As each page has only 10 results, moving to next page to get other universities information
    
    for i in range(5):
        try:
            element= driver.find_element(By.XPATH, '//*[@id="alt-style-pagination"]/li['+str(3+i)+']/a')
            #element= driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[1]/div[2]/main/section/div/section/section/div/div/article/div/div/div[3]/div/div[1]/div/div[3]/div[4]/div[2]/div/ul/li[7]/a')           
            driver.execute_script('arguments[0].scrollIntoView();', element)
            driver.execute_script('window.scrollBy(0, -200);')
            element.click()
            time.sleep(4)
            html = driver.page_source
            soup = BeautifulSoup(html, features="html.parser")
            x = soup.find_all("div", class_="row ind")
            for clg in x:
                info=clg.find("div",class_="td-wrap")
                a_tag = clg.find('a')
                name=a_tag.get_text()
                url=a_tag.get('href')
                unilist.append([name,url])
        except:
            pass
    
    element= driver.find_element(By.XPATH, '//*[@id="alt-style-pagination"]/li[5]/a')
    #element= driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[1]/div[2]/main/section/div/section/section/div/div/article/div/div/div[3]/div/div[1]/div/div[3]/div[4]/div[2]/div/ul/li[7]/a')           
    driver.execute_script('arguments[0].scrollIntoView();', element)
    driver.execute_script('window.scrollBy(0, -200);')
    element.click()
    time.sleep(4)
    html = driver.page_source
    soup = BeautifulSoup(html, features="html.parser")
    x = soup.find_all("div", class_="row ind")
    for clg in x:
        info=clg.find("div",class_="td-wrap")
        a_tag = clg.find('a')
        name=a_tag.get_text()
        url=a_tag.get('href')
        unilist.append([name,url])
        
    
    return unilist

#Function to get detailed information of each university
def get_info_from_each_university(driver,res):
    final_clg_info=[]#A list to store information of each university
    for clg in res:
        try:
            #From the list of URLs, we got from get_uni_information() function, we append basic URL of topuniversities website at the beginning to get final URL of each specific univeristy
            url = r"https://www.topuniversities.com"+str(clg[1])
            '''
            r1 = requests.get(url)
            content = r1.content      
            soup = BeautifulSoup(content, "html.parser")
            '''
            time.sleep(2)
            #Open url and get the university html page
            driver.get(url)
            time.sleep(5)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            x = soup.find("div", class_="layout__region layout__region--second col-lg-9")
            info={"University Name":clg[0]}
            try:
                #Only Some of the university links has Covid 19 Information, If present we extract by using div tag with certain class name
                info.update({"Covid 19 Information":(x.find("div",class_="summary")).text})
            except:
                pass
            
            #Getting University Information like Number of Students,Faculty,..etc
            x = soup.find("div",class_="block block-qs-profiles block-university-information-profile2")
            titles=[val.text for val in x.find_all("h5",class_="studstaff-subsection-title")]
            values=[val.text for val in x.find_all("h4",class_="studstaff-subsection-count")]
            info.update({"University Information":dict(zip(titles,values))})

            #Getting link to download scholarship guide
            x = soup.find("div",class_="block block-qs-profiles block-tuition-fees-and-scholarships-profile2")
            guide_url = "https://www.topuniversities.com"+x.find("a",class_="scholarship-download")['href']
            info.update({"Scholarships_guide":guide_url})

            #Extracting Rankings and Ratings of each university
            x = soup.find("div",class_="block block-qs-profiles block-university-highlights-profile2")
            info.update({"Rankings & ratings":x.find("p").text})

            #Getting differnt ranks given to the university
            x = soup.find("div",class_="tab-content ranktab") 
            rankings=x.find_all('li',class_="nav-item")
            ranking_pairs=[]
            for val in rankings:
                s=val.text
                if any(chr.isdigit() for chr in s):
                    try:
                        temp = re.compile("([0-9-+]*)([a-zA-Z ]*)")
                        res = temp.match(val.text[1:]).groups()
                    except:
                        temp = re.compile("([0-9]-+)*([a-zA-Z ]*)")
                        res = temp.match(val.text[2:]).groups()
                    ranking_pairs.append(res)
            info.update({"Rankings":dict(ranking_pairs)})

            #Getting link to get all ranking data
            info.update({"View All Ranking Data":"https://www.topuniversities.com"+x.find("a",class_="white-blue-brand active")['href']})

            #Extracting all the information of courses provided by university, some university URLs are not provided with this information
            x = soup.find("div",class_="block block-qs-profiles block-available-programs-tu-profile2")
            list_of_courses = x.find_all("div",class_="views-row")
            sub_courses=[]
            for course in list_of_courses:
                li =[val.find('span').text for val in course.find_all("a",class_="width-100 inside-tabs _gtmtrackDeptProgram_js")]
                sub_courses.append(li[0])

            info.update({"Available Courses":sub_courses})

        except:
            pass



        final_clg_info.append(info)#storing all the information of university in key value pairs as a dictionary and storing them in main list


    #Storing the output in a JSON File, Output File named as extracted_info.json

    with open("extracted_info.json", "w") as write_file:
        json.dump(final_clg_info, write_file, indent=4)

    #Simply printing the resultant output    
    print(json.dumps(final_clg_info),len(final_clg_info))

    
    



driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
res=get_uni_information(driver,[])#Calling this function to get all the URLs of universities
get_info_from_each_university(driver,res)#Calling this function to get information of each university and storing the output in extracted_info.json file 
driver.quit()

