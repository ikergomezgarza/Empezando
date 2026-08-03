# Accretion / dilution model Screening Tool

A python projects that pulls real data from the company you desire from yahoo finance
and calculates if a merger wil be beneficial or not


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

In these project is the full pipeline for analizing if a company is viable to merge by getting some company data
and also by using a accretion / diluted model we would evalate it, with many parameters to change from the prime offer interest rates,
the taxes, teh portion of stock and cash, the fees and synergies, at the end it give you a clean df with a sesitivity analisis
to compare many possible outcomes (% stock/ prime offer), and one color with resutls being >0 green 0 to -5% yellow and <5% red
along with all the data of the trnsaccion


---

## Setup
### Dependencies
pip install yfinance pandas numpy

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
    └── P5_accretion-dilution_model/
        ├── P5_accretion-dilution_model.ipynb
        ├── L5_learn.ipynb
        └── README.md
---

## Pipeline
acq_dict, tgt_dict = get_companys_datas(acq,tgt, verbose= True)
contract_offer(acq_dict, tgt_dict, verbose=True )
sensitivity_accretion_dilution(acq_dict, tgt_dict)

---

## Functions

### get_companys_datas()
Pulls from Yfinance of both comanies
input: both company ticker (acq, tgt)
output: acq and tgt libraries

### contract_offer()
With both compaies data does all the necesary calculation to give the result( full model one funcion)
input: company acq and tgt dict
output: accretion_dilution_pct

### highlight_irr_accdil()
Gives colors to sensitivity table
>0 green 0 to -5% yellow and < -5% red

### sensitivity_accretion_dilution()
loops around %stock / premium price 10% steps or 20% steps
input: company acq and tgt 
output: sensitivity df

### accretion_dilution_model()
Full pipeline to just put the data
input: input: company acq and tgt 
output: full results

## Known Limitations
-Doesnt filter between type of companies
-Might not have all companies
-Is very standar and has all the variables flexible but deficult to add more
-Is in python not exportable to excel 
-doesnt calculate the synergies you ahve to put the pct
- Use standar market %

---

## Next Steps
- [ ] Add revolver to debt schedule
- [ ] Add more robustness
- [ ] Add sector filter to skip banks and insurance companies
- [ ]Add other ways to add companies not only stock market ones




### Learning Resources
- [Wall street prep: Accretion/Dilution Analysis](https://www.wallstreetprep.com/knowledge/financial-modeling-quick-lesson-accretion-dilution-model//)

### AI Contributions
Claude (Anthropic) assisted with:
- Debugging and error handling logic
- Verify financial formulas outputs
- Read massive outputs for possible errors 
- DataFrame styling assitance
- Less ussage than P4

All financial logic was learned and validated by the author.
Code was written by the author with AI guidance.