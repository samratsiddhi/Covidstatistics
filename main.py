#covid live stats
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd
from flask import Flask,redirect,url_for,request,render_template,flash
import requests
from bs4 import BeautifulSoup
import numpy as np


def extract_world_data():
    # scarping data from the given url using beautiful soup
    url = 'https://www.worldometers.info/coronavirus/'
    html = requests.get(url)

    soup = BeautifulSoup(html.content,'html.parser')
    table = soup.find(id='main_table_countries_today')

    # retriving the header row for country statistics
    table_header = table.find_all('th')
    headers=[]

    for i in range(15):
        if i>0:
            headers.append(table_header[i].text.replace("\n","").replace("\xa0",""))

    # retriving the body for country statistics
    data = pd.DataFrame(columns = headers)
    for row in table.find('tbody').find_all('tr'):
        col = row.find_all('td')
        if (col != []):
            # removing white spaces
            country = col[1].text.strip()
            # replacing N/A or null values with 0 and convrting the data type to int 
            totalCases = 0 if col[2].text.strip() == "" else int(col[2].text.strip().replace(',',''))
            newCases = 0 if col[3].text == "" else int(col[3].text.strip().replace(',',''))
            totalDeaths = 0 if col[4].text.strip() == "" else int(col[4].text.strip().replace(',',''))
            newDeaths = 0 if col[5].text == "" else int(col[5].text.strip().replace(',',''))
            totalRecovered = 0 if col[6].text == "" or col[6].text == "N/A" else int(col[6].text.strip().replace(',',''))
            newRecovered = 0 if col[7].text == "" or col[7].text == "N/A" else int(col[7].text.strip().replace(',',''))
            activeCases = 0 if col[8].text == "" or col[8].text == "N/A" else int(col[8].text.strip().replace(',',''))
            serious = 0 if col[9].text == "" or col[9].text == "N/A" else int(col[9].text.strip().replace(',',''))
            totCases_per_n = 0 if col[10].text == "" or col[10].text == "N/A" else float(col[10].text.strip().replace(',',''))
            deaths = 0 if col[11].text == "" or col[11].text == "N/A" else float(col[11].text.strip().replace(',',''))
            totalTests = 0 if col[12].text == "" or col[12].text == "N/A" else int(col[12].text.strip().replace(',',''))
            tests_per_n = 0 if col[13].text == "" or col[13].text == "N/A" else float(col[13].text.strip().replace(',',''))
            population =  0 if col[14].text.strip() == "" or col[14].text == "N/A" else int(col[14].text.strip().replace(',',''))
            
            # adding the row to dataframa
            d = {
                'Country,Other':country,
                'TotalCases': totalCases,
                'NewCases': newCases,
                'TotalDeaths': totalDeaths ,
                'NewDeaths': newDeaths,
                'TotalRecovered': totalRecovered,
                'NewRecovered':newRecovered,
                'ActiveCases':activeCases,
                'Serious,Critical':serious,
                'TotCases/1M pop':totCases_per_n,
                'Deaths/1M pop': deaths,
                'TotalTests':totalTests,
                'Tests/1M pop':tests_per_n,
                'Population':population
                }             
            data.loc[len(data.index)] = d 
    #selecting only the continents data
    continent_data = data[:7]

    #selecting only the country data
    country_data = data[8:]

    #write the data to csv files
    country_data.to_csv("country_covid_data.csv", index= False)
    continent_data.to_csv("continent_covid_data.csv", index= False)

    # world statistics
    covid_dict = {
        "Coronavirus Cases": continent_data['TotalCases'].sum(),
        "Recovered": continent_data['TotalRecovered'].sum(),
        "Deaths" : continent_data['TotalDeaths'].sum(),
        "activecases" : continent_data['ActiveCases'].sum(),
        "seriouscases" : continent_data['Serious,Critical'].sum()
    }

    #call to create bar chart of top 20 countries affected by covid
    top20_countries_afected_by_covid(country_data)

    #call to create pie chart of total cases , total recovered and total deaths in the world
    pie_chart_world_data(covid_dict)

    #call to create bar chart top 5 countires with most death per million
    deaths_per_million(country_data)

    #call to create bar chart of total cases in each continent 
    continent_total_cases(continent_data)

    # scatter plot of total cases vs total test
    scatter_plot(country_data)

    #call to create pie chart of total cases and polpulation of the world
    totalPop_vsCovidCases(covid_dict)

    #call to create pie chart of total active cases and how many of them are serious
    world_active_serious(covid_dict)

    return covid_dict

def extract_nepal_data():
    # read country data
    df = pd.read_csv('country_covid_data.csv') 

    #read nepals data  only
    nepal_df = pd.DataFrame()
    nepal_df = df[df['Country,Other'] == 'Nepal']

    nepal_covid_stats =  {'TotalCases': int(nepal_df['TotalCases']),
                    'TotalRecovered': int(nepal_df['TotalRecovered']),
                     'TotalDeaths': int(nepal_df['TotalDeaths']),
                     'NewCases': int(nepal_df['NewCases']),
                     'TotalTests': int(nepal_df['TotalTests']),
                     'NewRecovered': int(nepal_df['NewRecovered']),
                     'NewDeaths': int(nepal_df['NewDeaths']),
                     'Population':int(nepal_df['Population']) ,
                     'ActiveCases':int(nepal_df['ActiveCases']) ,
                     'SeriousCases':int(nepal_df['Serious,Critical']) 
                    }
    
    nepal_population_vs_covid(nepal_df)

    nepal_recovered_vs_death(nepal_df)

    active_serious(nepal_df)

    return nepal_covid_stats


#create bar graph of top 5 countires with most death per million
def deaths_per_million(country_data):
    top_cases_per_million = pd.DataFrame(country_data.sort_values(by="Deaths/1M pop", ascending = False))[:5]
    fig, ax = plt.subplots()
    y = top_cases_per_million['Country,Other']
    x = top_cases_per_million['Deaths/1M pop']
    ax.barh(y, x)
    ax.set_ylabel("Countries")
    ax.set_xlabel("Deaths per million")

    fig.savefig('static/images/most_death_per_million_.png')


# function to create pie chart of nepal population vs total cases
def nepal_population_vs_covid(nepal_df):
    labels = ['Affected', 'Unaffected']
    values = [int(nepal_df['TotalCases']), int(nepal_df['Population'])-int(nepal_df['TotalCases'])]
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, explode=[0.1, 0.1], autopct='%1.1f%%')
    fig.savefig('static/images/nepal_pop_vs_cases.png')


# function to pie chart of revory vs death in nepal
def nepal_recovered_vs_death(nepal_df):
    labels = ['TotalRecovered', 'TotalDeaths']
    values = [int(nepal_df['TotalRecovered']), int(nepal_df['TotalDeaths'])]
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, explode=[0.1, 0.1], autopct='%1.1f%%')
    fig.savefig('static/images/nepal_recovered_vs_death.png')

# function to create bar graph of top 50 countries affected by covid
def top20_countries_afected_by_covid(country_data):
    top20 = country_data.sort_values(by='TotalCases', ascending=False)[:20]
    fig, ax = plt.subplots()
    bar_width = 0.25
    r1 = np.arange(len(top20))
    r2 = [x + bar_width for x in r1]
    ax.bar(r1, top20['TotalCases'], color='b', width=bar_width, label='Total Cases')
    ax.bar(r2, top20['TotalRecovered'], color='r', width=bar_width, label='Total Recoveries')
    ax.set_xticks([r + bar_width/2 for r in range(len(top20))])
    ax.set_xticklabels(top20['Country,Other'], rotation=90, fontsize=7)
    ax.legend()
    ax.set_ylabel("Number of Cases and Recoveries (in 100 million)")
    fig.savefig('static/images/TotalCaseCountry.png')


#function to create pie chart  total recovered and total deaths in the world
def pie_chart_world_data(covid_dict):
    labels = ['Deaths', 'Recovered']
    values = [covid_dict['Deaths'], covid_dict['Recovered']]
    fig, ax = plt.subplots()
    ax.pie(values,labels=labels, explode=[0, 0.5],  autopct='%1.1f%%')
    fig.savefig('static/images/WorldStatspie.png')


#function to create bar chart of total cases in each continent 
def continent_total_cases(continent_data):
    continents = list(continent_data['Country,Other'])
    TotalCase = list(continent_data['TotalCases'])
    c = ['red', 'yellow', 'black', 'blue', 'orange','maroon']
    fig, ax = plt.subplots()
    ax.bar(continents, TotalCase, color=c)
    plt.xticks(rotation=20)
    ax.set_ylabel("Total Cases (in 100 million)")
    fig.savefig('static/images/continent_total_cases.png')

def scatter_plot(country_data):
    x = country_data['Tests/1M pop']
    y = country_data['TotCases/1M pop']
    fig, ax = plt.subplots()
    ax.scatter(x, y)
    ax.set_xlabel('Total Tests in millions')
    ax.set_ylabel('TotalCases')
    fig.savefig('static/images/scatterplot.png') 

def active_serious(nepal_df):
    active = int(nepal_df['ActiveCases'])
    serious = int(nepal_df['Serious,Critical'])
    c = ['blue', 'orange']
    fig, ax = plt.subplots()
    ax.bar(("active","serious"),(active,serious) , color=c, width=0.2)
    ax.set_ylabel("Number of Cases")  
    fig.savefig('static/images/active_serious.png')

def totalPop_vsCovidCases(covid_dict):
    labels = ['Affected', 'Unaffected']
    values = [int(covid_dict['Coronavirus Cases']), 7000000000-int(covid_dict['Coronavirus Cases'])]
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, explode=[0.1, 0.1], autopct='%1.1f%%')
    fig.savefig('static/images/totalPop_vsCovidCases.png')

def world_active_serious(covid_dict):
    labels = ['Not Serious Cases', 'Serious Cases']
    values = [int(covid_dict['activecases'])-int(covid_dict['seriouscases']), int(covid_dict['seriouscases'])]
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, explode=[0.1, 0.1], autopct='%1.1f%%')
    fig.savefig('static/images/world_active_serious.png')


app = Flask(__name__)
app.secret_key = "12345"


@app.route("/")
def home():
    covid_stats = extract_world_data()
    return render_template('world.html',stats = covid_stats)
    # return render_template('world.html')



@app.route("/nepal")
def nepal():
    nepal_stats = extract_nepal_data()
    return render_template('nepal.html',stats = nepal_stats)
    # return render_template('nepal.html')



if __name__ == "__main__":
    app.run(debug=True)