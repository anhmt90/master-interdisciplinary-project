# Project acquisition_analysis
This project encompasses a library for collecting L---e--- profiles, extracting relevant employment data from them for the analysis of job transition behaviors in the context of a Managment Research at Chair for Technology and Innovation Management @TUM.
<a href="https://drive.google.com/file/d/1l-7bo2Bq4gIS_ZmNfHUT8iorgDDFVn8P/view?usp=sharing">Presentation slides</a>  (updated 25/09/2020)

Following are the steps for the complete pipeline of the process:


## Module `scraping`
The module is used to collect L---e--- profiles. It also includes tasks that need to be done before and after the profile collection. <br>

**Note**: Please configure the corresponding paths and parameters in the file ***./config.py*** before running any submodules.  

### 1. Create an account list for manual sign-up at L---e---
To obtain full information of profiles, we need to be able to log in the platform. Therefore, data used for signing up fake L---e--- accounts should be created beforehand. The submodule ***scraping/account.py*** can be used for this purpose. 

Configure the `ACCOUNT_PARAMS` parameters for ***scraping/account.py*** in file in ***./config.py*** and run the following to create data for a set of accounts:
 
 ```python
python -m scraping.account
```

### 2. Use Account Signup Assistant (experimental)
Currently the module ***scraping/account_signup_assistant.py*** does not work well since it gets detected by L---e--- during the signup. The result is we get a phone verification instead of CAPTCHA. For this reason, **manual** signup is preferred by the account data created in the previous step. 

**Parameters** : `ACCOUNT_SIGNUP_ASSISTANT_PARAMS` 

**Run**:
```python
python -m scraping.account_signup_assistant
```

### 3. Filter out duplicate profile URLs

The URLs to profiles should be preprocessed to remove duplications within each URL file (intra-duplicates) as well as between them (inter-duplicates).  

**Parameters**: `URL_FILTER_PARAMS`

**Run**:
```python
python -m scraping.duplicate_url_filter
``` 

### 4. Collect profiles

Run the scraper to collect profiles and save them as HTML pages into local storage

**Parameters**: `SCRAPER_PARAMS`

**Run**:
```python
python -m scraping.l---e---_profile_scraper
``` 

### 5. Validate the results

Validate whether there are missing profiles and faulty profiles in the set of profiles that have been scraped.

**Parameters**: `VALIDATOR_PARAMS`

**Run**:
```python
python -m scraping.validator
``` 


## Module `analysis`

### 6. Extract relevant employment data
After collecting the raw data, which are  HTML profile pages, we need to extract the employment status from them for further analysis and create the so called *intermediate data* or *extracted data*.

**Parameters**: `EXTRACTOR_PARAMS`

**Run**:
```python
python -m analysis.extractor
``` 

### 7. Inspect job transition patterns by acquisitions
By using the extracted employment data from step 6., we now can compare that with the acquisition data and inspect job transition patterns of employees when their companies are acquired. The results will be stored in CSV format for visualization in the next step.

**Parameters**: `INSPECTOR_PARAMS`

**Run**:
```python
python -m analysis.inspector
``` 

### 8. Visualize the results

Graphs to visualize the results of the analysis in the previous step are shown in ipython file ***analysis/Analysis for Job Transition Pattern by Acquisitions.ipynb***. Please use 'jupyter notebook' or 'jupyter lab' to run the file.

## Appendix

To debug or visualize the employment timeframes together with the respective acquisition for each employee, please pickle a list of timeframes when running file ***analysis/inspector.py*** and then use the ipython notebook ***analysis/Timeframes Visualization.ipynb*** to load the pickle files to see the visualization. 

**Parameters**: `TIMEFRAMES_VISUALIZATION_PARAMS`