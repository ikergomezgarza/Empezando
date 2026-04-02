# Relative Valuation Tool

this one was hard in 2 ways getting and choosing a way to filter the companies and download all the data
and deal with all the data and big funccions keeping track with evrything and adding some points to not break
and handle df in dctionaries and clean all of them, and the printing format to practice

---

## Table of Contents
- [Overview](#overview)
- [Setup](#setup)
- [Project Structure](#project-structure)
- [Pipeline](#pipeline)
- [Functions](#functions)
- [Known Limitations](#known-limitations)
- [Next Steps](#next-steps)

---

## Overview

A tool that compares a company valuation based on other companies, companies in the sector with same size and growth,
companies that are in teh same industry and sector, and similar companies in the same index as the companie, and base 
on the median value we recalculate the enterprice value and market cap


---

## Setup
### Dependencies
pip install yfinance pandas numpy finvizfinance

### Path
import sys
sys.path.append('/path/to/Empezando')

---

## Project Structure 
(AI did this thing i wouldnt have known)
Empezando/
├── Functions.py
├── README.md
├── requirements.txt
└── projects/
    └── P6_Relative_valuation/
        ├── P6_Relative_Valuation.ipynb
        ├── L6_learn.ipynb
        └── README.md
---

## Pipeline
stock_dict= company_data(ticker)
stock_areas= get_company_area(stock_dict)
all_dfs= get_competition(stock_areas)
all_dfs_clean= clean_dfs(all_dfs, ticker)   
all_dataframes = all_values(all_dfs_clean, ticker)
build_table(all_dataframes, ticker)

---

## Functions

### company_data(ticker)
Pulls from finviz data companie
input: ticker
output: dict of company data

### get_company_area(stock_dict)
Getts the sector industry and indexes that the companie is in 
input: company dict
output: dict with sector industr y and indexes

### get_index_companies(stock_areas)
Gives the indexes cause they have diferent names in finviz
input: the areas 
output:indexes

### get_competition(stock_areas)
Gets the companies to evaluate and puts them in a dict all the data
input: the areas
output: companies similar in that area

### filter_df(df, market_cap, past_sales_5, eps_next_5)
Filters the companies so we dont have a lot of copanies and we just get the most similar ones
input: input:df and taget data companies
output: the filterd df

### clean_dfs(all_dfs, ticker)
With the dict cleans all teh df to use the data that we needed
input: all the dfs and the companie name to filter
output: all the names of the companies we are going to use

### all_values(all_dfs_clean, ticker)
Gets the values of the companies compatition to further build the table
input: df with names to search
output: final data to put in the table

### build_table(all_dataframes, ticker)
Builds all the tables with the mean median company diference(comapny-median) and expected values
input: all the dfs with final data
output: the table with all comparisopns

### relative_valuation(ticker):
Pipiline of the whole program
input: just the company name 
output: final table whole output with check points in case of error


## Known Limitations
- It is limited to 4 indexes
- Many companies not find all the data
- may not find companies from outside usa
- The filters of market cap are very generilize
- The amount of time it takes to pull the data is a lot becasue of finding sectors
- double pull to get each companie data
- data might missed

## Next Steps
- [ ] Do the table in other format
- [ ] Make it more flexible
- [ ] Handle better all the errors
- [ ]




### Learning Resources
- [Relative Valuation Models](https://corporatefinanceinstitute.com/resources/valuation/relative-valuation-models/)

### AI Contributions
Claude (Anthropic) assisted with:
- Debugging and error handling logic
- Verify financial formulas outputs
- Read massive outputs for possible errors 
- DataFrame styling assitance
- Less ussage than P4, p5 in some things, more usage in debugging

All financial logic was learned and validated by the author.
Code was written by the author with AI guidance.