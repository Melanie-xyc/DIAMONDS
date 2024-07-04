# -*- coding: utf-8 -*-
"""
Created on Fri Jul 28 10:52:19 2023

@author: huberm
"""
###############################################################################
### import packages ###########################################################
import subprocess
import pandas as pd
import re
import datetime
import numpy as np
import math
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import sem, t
from scipy import mean
###############################################################################

#not every time; just needs generated excel 'UNITS_corr.xlsx''
### run QC Script first #######################################################
'''
script_directory = r'Z:\Datamanagement\DIAMONDS\Identify missing data'
script_name = 'DIAMONDS_EDPIC_QC.py'

subprocess.run(['python', script_name], check=True, cwd=script_directory)
'''
###############################################################################

### load data #################################################################
df_original = pd.read_excel(r'H:\Datamanagement\DIAMONDS\Identify missing data\DIAMONDS_ED_PIC_June12_2024_UNITScorr.xlsx')
df_ICU = df_original.loc[(df_original['ICU'] == "YES")  & (df_original['ITU'] == "YES")]
number_ICU = len(df_ICU) #number of ICU patients
###
timepoints = ['BASELINE', 'FIRST', 'FRB_24', 'SECOND', 'THIRD', 'NULL']
###

###extract age of each timepoint for each patient (row)########################
# 1. itreate through DATE_TIME_INVESTIGATIONS
# 2. identify whether cell has content or not (float bzw NaN)
# 3. extract date of investighation
# 4. extract timepoint on same line/ in same subcell, but column TIME_POINT
# 5. Quality check of timepoint values
# 6. append to newly generated columns 'date_investigation_<timepoint>' (<timepoint> == whatever occuring in value_timepoint)
# 7. prepare birthday for later age calculation
# 8. calculate age in months 
list_values_age=[]
list_timepoints_age=[]
for index, cell in df_ICU['DATE_TIME_INVESTIGATIONS'].items(): #e.g. cell = '2020-04-24;11:30:00.000000;2021-05-16;10:30:00.000000'
    position=-1
    if type(cell) != float: #float means NaN (NaN for date_invest)
        values = cell.split(';') #e.g. values = ['2020-04-24', '11:30:00.000000']; type: list || mix date vs. time
        for value in values: #e.g. value = '2020-04-24' or '11:30:00.000000'; type: string
            if '-' in value: #take only dates as value_investdate and not times
                position+=1
                value_investdate = value
                if type(df_ICU.loc[index,'TIME_POINT']) != float: #float means NaN (NaN for timepoint)
                    value_timepoint = df_ICU.loc[index,'TIME_POINT'].split(';')[position] if (position +1 <= len(df_ICU.loc[index, 'TIME_POINT'].split(';'))) else '' #happens more positions in 1. column than in 2. column (mistake) -> take '' as data
                ###quality check of timepoint values:
                value_timepoint = 'NULL' if value_timepoint == '' else value_timepoint
                #all age values in a list
                list_values_age.append(value_investdate)
                list_timepoints_age.append(value_timepoint) if value_timepoint not in list_timepoints_age else ''
                #date_investigation
                df_ICU.loc[index, 'date_investigation_'+value_timepoint] = value_investdate
    else: #NaN (NaN for date_invest)
        position+=1
        value_investdate = cell
        list_values_age.append(value_investdate)
        if type(df_ICU.loc[index,'TIME_POINT']) != float: #float means NaN (NaN for timepoint)
            value_timepoint = df_ICU.loc[index,'TIME_POINT'].split(';')[position] if (position +1 <= len(df_ICU.loc[index, 'TIME_POINT'].split(';'))) else '' #happens more positions in 1. column than in 2. column (mistake) -> take '' as data

df_ICU['DATE_OF_BIRTH'] = pd.to_datetime(df_ICU['DATE_OF_BIRTH']) #define values as datetime
df_ICU['birthday'] = df_ICU['DATE_OF_BIRTH'].dt.date

for timepoint in timepoints:
    df_ICU['date_investigation_'+timepoint] = pd.to_datetime(df_ICU['date_investigation_'+timepoint])
    df_ICU['date_investigation_'+timepoint] = df_ICU['date_investigation_'+timepoint].dt.date #important step, even if no time
    df_ICU['age_investigation_'+timepoint] = (df_ICU['date_investigation_'+timepoint] - df_ICU['birthday'])/np.timedelta64(1, 'M') #trick to get result in months instead of days
    df_ICU['age_investigation_days_'+timepoint] = (df_ICU['date_investigation_'+timepoint] - df_ICU['birthday']).dt.days

###############################################################################
### ANSWERING QUESTION FOR PAPER ##############################################
def age_cutoff(df, liste):
    global count_1week, count_1month
    #modify df_ICU without modifying it outside of the function
    df_ICU_trans = df_ICU.copy()
    #change age in month to age in days
    for timepoint in timepoints:
        df_ICU_trans['age_investigation_'+timepoint] = (df_ICU_trans['date_investigation_'+timepoint] - df_ICU_trans['birthday'])/np.timedelta64(1, 'D') #trick to get result in days
    #count how many patients below 1week or 1month respectively
    count_1week=0
    count_1month=0
    index_out=[]
    for timepoint in timepoints:
        for index, cell in df_ICU_trans['age_investigation_'+timepoint].items():
            #don't consider nan values
            #don't consider patients that were already considered in a previous timepoint
            if not math.isnan(cell) and index not in index_out:
                if cell < 7:
                    count_1week += 1
                    index_out.append(index)
                if cell < 30:
                    count_1month += 1
                    index_out.append(index) if index not in index_out else ''

#age_cutoff(df_ICU, listd)
###############################################################################

###filter for PICU (in addition to ICU at the beginning)#######################
#PICU = patients < 18 y = 216M
indices_todrop=[]
for index,row in df_ICU.iterrows():
    PICU=[]
    for timepoint in timepoints:
        #check for both (<= & > 204, since otherwise (else 'YES') you include NaN)
        if not math.isnan(row['age_investigation_'+timepoint]) and row['age_investigation_'+timepoint]> 216:
            PICU.append('No') if 'No' not in PICU else ''
        elif not math.isnan(row['age_investigation_'+timepoint]) and row['age_investigation_'+timepoint]<= 216: 
            PICU.append('Yes') if 'Yes' not in PICU else ''
    #could test birthdate of NaN agers, but manual checking showed would only be 1-2 patients more
    #if not PICU and row['DATE_OF_BIRTH']: #NaN
        #test_list.append(row['DATE_OF_BIRTH'])
    if 'Yes' not in PICU: #on the other side, if you exclude No's, you would also include NaN agers
        indices_todrop.append(index)    

df_ICU.drop(indices_todrop, inplace=True)

###extract patient location for each timepoint#################################
# 1. iterate through TIME_POINT_1=PATIENT_LOCATION
# 2. extract timepoint and value of each respective subcell
# 3. append the value (value_location) newly generated columns 'location_<timepoint>' (<timepoint> == whatever occuring in value_timepoint)
list_values_location=[] #all location values
list_timepoints_location=[] #possible timepoint values
for index, cell in df_ICU['TIME_POINT_1=PATIENT_LOCATION'].items(): #e.g. cell = 'FIRST=ED; SECOND=ICU'; type: string    
    if type(cell) == str and '=' in cell:
        values = cell.split(';') #e.g. values = ['FIRST=ED', 'SECOND=ICU']; type: list 
        for value in values: #e.g. value = 'SECOND=ICU'
            value_timepoint = value.split('=')[0] #e.g. value_timepoint = 'SECOND'; type: first element of a list (str)
            value_location = value.split('=')[1] #e.g. value_location = 'ICU'; type: second element of a list (str)
            ###deal with NULL values
            value_location = float('NaN') if value_location == 'NULL' else value_location
    else: #(a) single value, which we can not associate to timepoint, or (b) float (meaning NaN)
        value_location = float('NaN')
    #all location values in a list
    list_values_location.append(value_location)
    list_timepoints_location.append(value_timepoint) if value_timepoint not in list_timepoints_location else ''
    #location
    df_ICU.loc[index, 'location_'+value_timepoint] = value_location
###############################################################################

###############################################################################
### EXTRACT DATA ##############################################################
###############################################################################

###extract variable (integer, null) and timepoints#############################
# 1. iterate through column
# 2. extract timepoint and value of each subcell
# 3. append the value to newly generated column '<variable>_<timepoint>'
# NOTE: for wbc/platelets => since units either in *10^9/L or *10^3/µL (or unknown) and *10^9/L == *10^3/µL => no dealing with units, assume all the same (*10^9/L)
def timepoint_equal_integer_or_null(variable_to_name, column_name, data_type):
    list_values = globals().setdefault(f'list_values_{variable_to_name}', [])
    list_unique_timepoints = globals().setdefault(f'list_timepoints_{variable_to_name}', [])
    for index, cell in df_ICU[column_name].items(): #e.g. cell = 'FIRST=120; SECOND=84'; type: string
        ###extract values
        subcells = cell.split(';') #e.g. subcells = ['FIRST=120', 'SECOND=84']; type: list
        for subcell in subcells: #e.g. subcell = 'SECOND=84'
            timepoint = subcell.split('=')[0] #e.g. timepoint = 'SECOND'; type: first element of a list (str)
            value = subcell.split('=')[1] #e.g. value = '84'; type: second element of a list (str)
            ###quality check of value
            if data_type == int:
                #real values (and rubbish too) are displayed as strings ('84') but we want them as integer (84)
                #NULL are also strings, but just won't have digits
                #screens for any digit(s) (and optional minus sign in front) within string -> takes the first sequence -> turn them to integer
                #in case there is no digit -> takes NaN
                value = int(re.findall(r'-?\d+', value)[0]) if re.findall(r'-?\d+', value) else float('NaN')
            elif data_type == float:
                #real values (and rubbish too) are displayed as strings ('0.84') but we want them as float (0.84)
                #NULL are also strings, but just won't have digits
                #screens for any digit(s) followed by '.' followed by digit(s) (and optional minus sign in front) within string -> takes the first sequence -> turn them to float
                #in case there is no digit -> takes NaN
                value = float(re.findall(r'-?\d+\.\d+', value)[0]) if re.findall(r'-?\d+\.\d+', value) else float('NaN')
                #value = float(value) if value.replace('.', '', 1).isdigit() else float('NaN')
            #all values/timepoints in a list
            list_values.append(value) #all values
            list_unique_timepoints.append(timepoint) if timepoint not in list_unique_timepoints else '' #unique timepoints
            #value
            df_ICU.loc[index, f'{variable_to_name}_{timepoint}'] = value

legend1 = {'meanbp': ('TIME_POINT_8=MEN_BP', int),
          'sysbp': ('TIME_POINT_6=SYSTOLIC_BP', int), 
          'hr': ('TIME_POINT_5=HEART_RATE', int),
          'spo2': ('TIME_POINT_3=O2_SATURATION', int),
          'wbc': ('TIME_POINT_2=WHITE_CELLS', float),
          'neutro': ('TIME_POINT_4=NEUTROPHILS', float),
          'lympho': ('TIME_POINT_5=LYMPHOCYTES', float),
          'platelets': ('TIME_POINT_3=PLATELETS', float),
          'inr': ('TIME_POINT_21=INR', float),
          'be': ('TIME_POINT_26=BASE_EXCESS', float)} #actually would be with unit, but units other than mmol/L doesn't make sense; so just assume them as mmol/L

for key, value in legend1.items():
    timepoint_equal_integer_or_null(key, value[0], value[1])


###extract variable (float, null), timepoints, and unit (unit, null, rubbish)##
# 1. iterate through column
# 2. extract unite from the same line (index) but from column column "_UNITS" 
# 3. extract timepoint and value of each respective subcell
# 4. append the value to newly generated column '<variable>_org_<timepoint>' & '<variable>_<finalunit>_<timepoint>'
# NOTE: if there is no unit indicated == default unit from ECRF
def timepoint_equal_float_or_null_unit_equal_unit_null_or_rubbish(variable_to_name, column_name, column_unit_name, unit_screening, unit_dictionary, unit_default, unit_final, unit_notfinal, factor):
    list_values = globals().setdefault(f'list_values_{variable_to_name}', [])
    list_units = globals().setdefault(f'list_units_{variable_to_name}', [])
    list_unique_timepoints = globals().setdefault(f'list_timepoints_{variable_to_name}', [])
    for index, cell in df_ICU[column_name].items(): #e.g. cell = 'FIRST=-0.4; SECOND=0.5'; type: string
        ### extract units
        unit = str(df_ICU.loc[index, column_unit_name]) #not automatically str (e.g.: 3.5)
        ###quality check of unit
        #assuming that unit will be the same for the same patient (ignore ';')
        #data is always string (NULL, unit + unwanted appendix/siffix, number)
        #from what they entered (manual check), we only take <[unit_selection]> => ask Blood Gas Analysis vs. also Plasma ok (included at the moment)
        #screens for any <[unit_selection]> in string -> takes the first appearing
        #in case there is no screening result -> takes NaN
        unit = re.findall(unit_screening, unit, re.IGNORECASE)[0] if re.findall(unit_screening, unit, re.IGNORECASE) else float('NaN')
        #replace lowercase 'l' by capital 'L'
        unit = unit.lower() if isinstance(unit, str) else unit  #first everything lower
        dict_unit = unit_dictionary #contains capital L
        for key_tuple, value in dict_unit.items():
            if isinstance(unit, str) and unit in key_tuple: #exlcude float(NaN)
                unit = value
                break
        #all units are either a string (correct unit) or float (NaN) => fill the na-floats with default unit
        if type(unit) == float:
            if math.isnan(unit):
                unit = unit_default
        list_units.append(unit) 
        #unit
        df_ICU.loc[index, f'{variable_to_name}_org_unit'] = unit
        ### extract values
        subcells = cell.split(';') #e.g. subcell = ['FIRST=-0.4', 'SECOND=0.5']; type: list
        for subcell in subcells: #e.g. subcell = 'SECOND=0.5'
            timepoint = subcell.split('=')[0] #e.g. timepoint = 'SECOND'; type: first element of a list (str)
            value = subcell.split('=')[1] #e.g. value = '0.5'; type: second element of a list (str)
            ###quality check of value
            #real values are displayed as strings ('0.05') but we want them as floats (0.5)
            #NULL are also strings, but just won't have digits
            #NOTE: you cannot do it with screening for digits directly, since it will cut the decimals
            value = float(value) if value.replace('.', '', 1).isdigit() else float('NaN')
            #all values in a list
            list_values.append(value)
            list_unique_timepoints.append(timepoint) if timepoint not in list_unique_timepoints else ''
            #value_org & value_finalunit
            #mmol/L = mg/L / molecular weight -> molecular weight of lactate = 90.08
            df_ICU.loc[index, f'{variable_to_name}_org_{timepoint}'] = value
            df_ICU.loc[index, f'{variable_to_name}_{unit_final}_{timepoint}'] = value * factor if unit == unit_notfinal else value


#two different mü => 'μkat/l', 'µkat/l' (first = Greek letter, second = special symbol)
legend2 = {'lactate': ('TIME_POINT_27=LACTATE', 'LACTATE_UNITS', r'mmol/L|mmol/l|mg/L|mg/l', {'mmol/l':'mmol/L', 'mg/l':'mg/L'}, 'mmol/L', 'mmol/L', 'mg/L', (1/90.08)),
           'creatinine': ('TIME_POINT_11=CREATININE', 'CREATININE_UNITS', r'µmol/L|μmol/L|umol/L|micromol/L|micromole/L|mmol/L|g/dL|mg/dL|mg//dL|mf/dl|mg7dl|mg/d|mg7d|mg/fl|m/dl|mg/L|mg/mL|ng/dL', {('umol/l','micromol/l','micromole/l', 'mmol/l','µmol/l', 'μmol/l'):'µmol/L',('mg/dl','mg//dl','mf/dl','ng/dl','g/dl','mg7dl','mg/d','mg7d','mg/fl','m/dl','mg/mg','mg/ml','mg/l','mg/gl'):'mg/dL'}, 'µmol/L', 'µmol/L', 'mg/dL', (88.4)),
           'po2': ('TIME_POINT_28=Arteial_PO2', 'Arterial_PO2_UNITS', r'mm hg|mmhg|kpa|k pa', {('mm hg','mmhg'):'mmHg',('k pa','kpa'):'kPa'}, 'kPa', 'mmHg', 'kPa', (7.501)),
           'pco2': ('TIME_POINT_30=ARTERIAL_PCO2', 'ARTERIAL_PCO2_UNITS', r'mm hg|mmhg|kpa|k pa', {('mm hg','mmhg'):'mmHg',('k pa','kpa'):'kPa'}, 'kPa', 'mmHg', 'kPa', (7.501)),
           'bilirubin': ('TIME_POINT_13=BILIRUBIN', 'BILIRUBIN_UNITS', r'g/dl|mg/dl|micromol/l|micromole/l|umol/l|µmol/l|µmol/l|mmol/l', {('umol/l','micromol/l','micromole/l', 'mmol/l', 'µmol/l', 'µmol/l'):'µmol/L', ('mg/dl','g/dl'):'mg/dL'}, 'µmol/L', 'mg/dL', 'µmol/L', (1/17.1)),
           'alt': ('TIME_POINT_12=ALT', 'ALT_UNITS', r'iu/l|u/l|unit/l|int unit/l|μkat/l|µkat/l|μcat/l|µcat/l|ukat/l|ucat/l|microkat/l|microcat/l', {('iu/l', 'u/l', 'unit/l', 'int unit/l'): 'IU/L', ('μkat/l', 'µkat/l', 'μcat/l', 'µcat/l', 'ukat/l', 'ucat/l', 'microkat/l', 'microcat/l'): 'μcat/L'}, 'IU/L', 'IU/L', 'μcat/L', (60))}

for key, value in legend2.items():
    timepoint_equal_float_or_null_unit_equal_unit_null_or_rubbish(key, value[0], value[1], value[2], value[3], value[4], value[5], value[6], value[7])

###additionally, transfer creatinine to mg/dL##################################
#PSOFA needs creatinine in mg/dL => 1mg/dL - 88.4umol/L -> mg/dL = umol/L / 88.4
#round so that later on, within dictionary, boarders are clear
for timepoint in timepoints:
    df_ICU['creatinine_mg/dL_' + timepoint] = np.round(df_ICU['creatinine_µmol/L_' + timepoint] / 88.4,1)
    
###extract variable (yesno, unk, null) and timepoints##########################
# 1. iterate through column
# 2. extract timepoint and value of each subcell
# 3. append the value to newly generated column '<variable>_<timepoint>'
def timepoint_equal_yesno_unk_or_null(variable_to_name, column_name, yes_selection, no_selection, unk_selection):
    list_values = globals().setdefault(f'list_values_{variable_to_name}', [])
    list_unique_timepoints = globals().setdefault(f'list_timepoints_{variable_to_name}', [])
    for index, cell in df_ICU[column_name].items(): #e.g. cell = 'FIRST=NO; SECOND=Unk'; type: string
        ###extract values
        subcells = cell.split(';') #e.g. subcells = ['FIRST='NO', 'SECOND=Unk']; type: list
        for subcell in subcells: #e.g. subcell = 'SECOND=Unk'
            timepoint = subcell.split('=')[0] #e.g. timepoint = 'SECOND'; type: first element of a list (str)
            value = subcell.split('=')[1] #e.g. value = 'Unk'; type: second element of a list (str)
            ###quality check of value
            #data is always string (YES, NO, Unk, NULL)
            #translate values
            if value in yes_selection:
                value = 'YES'
            elif value in no_selection:
                value = 'NO'
            elif value in unk_selection:
                value = 'Unk'
            else: #NULL, NaN
                value = float('NaN')
            #all values/timepoints in a list
            list_values.append(value) #all values
            list_unique_timepoints.append(timepoint) if timepoint not in list_unique_timepoints else '' #unique timepoints
            #value
            df_ICU.loc[index, f'{variable_to_name}_{timepoint}'] = value

legend3 = {'pupils': ('TIME_POINT_11=PUPILS_DIALATED', ('YES'), ('NO'), ('Unk')),
           'ecmo': ('TIME_POINT_20=ECMO', ('VA', 'VV'), ('NO'), ('Unk')),
           'ecmo_va': ('TIME_POINT_20=ECMO', ('VA'), ('VV', 'NO'), ('Unk')),
           'respsup': ('TIME_POINT_2=VENTILATION', ('Invasive', 'NIV', 'O2_ONLY'), ('No_add_suppt'), ('Unknown')),
           'iv': ('TIME_POINT_2=VENTILATION', ('Invasive'), ('NIV','No_add_suppt', 'O2_ONLY'), ('Unknown')),
           'niv': ('TIME_POINT_2=VENTILATION', ('NIV'), ('Invasive','No_add_suppt', 'O2_ONLY'), ('Unknown')),
           'rrt': ('TIME_POINT_21=RENAL_REPLACEMENT', ('YES'), ('NO'), ('Unk'))}

for key, value in legend3.items():
    timepoint_equal_yesno_unk_or_null(key, value[0], value[1], value[2], value[3])

###extract gcs scores and timepoints for each patient (row)####################
# 1. itreate through TIME_POINT_12=GCS_AVPU
# 2. identify subcells with GCS
# 3. extract timepoint where =GCS
# 4. extract gcs scores on same line/ in same subcell, but column GCS_AVPU_UNITS
# 5. Quality check of gcs value
# 6. append to newly generated columns 'gcs_<timepoint>' (<timepoint> == whatever occuring in value_timepoint)
# 7. calculate pelod_gcs points in newly generated column 'pelod_gcs_<timepoint>'
list_values_gcs=[] #all gcs values in one list for easier check
list_timepoints_gcs=[] #all possible timepoint values in one list for later reference
for index, cell in df_ICU['TIME_POINT_12=GCS_AVPU'].items(): #e.g. cell = 'FIRST=AVPU; SECOND=GCS'; type: string
    values = cell.split(';') #e.g. values = ['FIRST=AVPU', 'SECOND=GCS']; type: list
    position=-1
    for value in values: #e.g. value = 'SECOND=GCS'
        position+=1 #position of value in values; (0,...,n)
        if 'GCS' in value: #only take GCS
            value_timepoint = value.split('=')[0] #e.g. value_timepoint = 'SECOND'
            #either string + ';' ->  take the right position within cell -> happens more positions in 1. column than in 2. column (mistake) -> take '' as data
            if (type(df_ICU.loc[index, 'GCS_AVPU_UNITS']) == str) and (';' in df_ICU.loc[index, 'GCS_AVPU_UNITS']):
                value_gcs = df_ICU.loc[index, 'GCS_AVPU_UNITS'].split(';')[position] if (position +1 <= len(df_ICU.loc[index, 'GCS_AVPU_UNITS'].split(';'))) else '' #position starts with 0, while len with 1
            #or datetime (mistake)
            elif isinstance(df_ICU.loc[index, 'GCS_AVPU_UNITS'], datetime.datetime):
                value_gcs = float('NaN')
            #or simple integer/string -> take the cell
            else:
                value_gcs = df_ICU.loc[index, 'GCS_AVPU_UNITS'] 
            ###quality check of value_gcs:
            if type(value_gcs) == str: #takes care of strings
                #screens for any digit(s) within string -> takes the first sequence of digits -> turn them to integer
                #in case there is no digit -> takes NaN
                value_gcs = int(re.findall(r'\d+', value_gcs)[0]) if re.findall(r'\d+', value_gcs) else float('NaN')
            #all gcs values in a list
            list_values_gcs.append(value_gcs)
            list_timepoints_gcs.append(value_timepoint) if value_timepoint not in list_timepoints_gcs else ''
            #gcs
            df_ICU.loc[index, 'gcs_'+value_timepoint] = value_gcs

###extract fio2 and timepoints for each patient (row)##########################
# 1. iterate through TIME_POINT_4=FIO2_O2_FLOW
# 2. extract unite from the same line (index) but from column FIO2_O2_FLOW_UNITS 
# 3. extract timepoint and value of each respective subcell
# 4. append to the value (value_fio2) to newly generated columns 'fio2_<timepoint>'
list_values_fio2=[] #all fio2 values
list_timepoints_fio2=[] #possible timepoint values
list_units_fio2=[] #all fio2 units
for index, cell in df_ICU['TIME_POINT_4=FIO2_O2_FLOW'].items():
    ### extract unit
    value_unit = df_ICU.loc[index, 'FIO2_O2_FLOW_UNITS']
    ###quality check of value_unit
    #assuming that unit will be the same for the same patient (ignore ';')
    #from what they entered (manual check), we only take L_min, percnt -> use only percnt
    #data is either NaN (float) or string (L_min, percnt, NULL)
    if type(value_unit) == str: 
        #screens for any entered unit, ignoring the lower/upper case
        #in case there is no screening result -> takes NaN
        value_unit = re.findall(r'percnt|L_min', value_unit, re.IGNORECASE) if re.findall(r'percnt|L_min', value_unit, re.IGNORECASE) else float('NaN')
        #if only percnt or only L_min -> take it for all timepoints
        if ('percnt' in value_unit) and ('L_min' not in value_unit):
            position_list = ['valid']
            value_unit = 'percnt'
        elif ('L_min' in value_unit) and ('percnt' not in value_unit):
            position_list=[] #create empty position_list since there is no position for percnt
            value_unit = 'L_min'
        #if a mix between the two, take units per position and append the position number of percnt to a list, in order to extract the value
        else: #mix
            position_list=[]
            position=-1
            for unit in value_unit:
                value_unit = value_unit #stays a list
                position +=1
                position_list.append(position) if unit == 'percnt' else '' #extract positions we want (percnt)
    else:
        position_list=[]
        value_unit = float('NaN')
    list_units_fio2.append(value_unit) 
    ### extract value
    values = cell.split(';') #e.g. values = ['FIRST=0.21', 'SECOND=1']; type: list
    position=-1
    for value in values: #e.g. value = 'SECOND=1'
        position += 1
        #check whether position_list valid (only percnt) or position in position_list (will be position for percnt)
        if ('valid' in position_list) or (position in position_list):
            value_timepoint = value.split('=')[0] #e.g. value_timepoint = 'SECOND'; type: first element of a list (str)
            value_fio2 = value.split('=')[1] #e.g. value_fio2 = '1'; type: second element of a list (str)
            ###quality check of value_fio2
            #real fio2 values are displayed as strings ('0.05') but we want them as floats (0.5)
            #NULL are also strings, but just won't have digits
            #NOTE: you cannot do it with screening for digits directly, since it will cut the decimals
            value_fio2 = float(value_fio2) if value_fio2.replace('.', '', 1).isdigit() else float('NaN')
            #all fio2 values in a list
            list_values_fio2.append(value_fio2)
            list_timepoints_fio2.append(value_timepoint) if value_timepoint not in list_timepoints_fio2 else ''
            #fio2 + transformat ([%]->[]) + QC (cannot be below 21%)
            if (value_fio2 >= 21) and (value_fio2 <= 100):
                df_ICU.loc[index, 'fio2_'+value_timepoint] = (value_fio2/100) 
            elif (value_fio2 >= 0.21) and (value_fio2 <= 1): #actually should not be the case since %, but logical error
                df_ICU.loc[index, 'fio2_'+value_timepoint] = value_fio2
            else:
                float('NaN')

#for non-ventilated patients, replace fio2=NULL with fio2=0.21
for timepoint in timepoints:
    df_ICU.loc[(df_ICU['fio2_'+timepoint].isna()) & 
               (df_ICU['iv_'+timepoint] == 'NO') &
               (df_ICU['niv_'+timepoint] == 'NO'),
               'fio2_'+timepoint] = 0.21

###extract dopamine, adrenaline, noradrenaline and timepoints for each patient (row)
# 1. iterate through TIME_POINT_<catechol>
# 2. extract timepoint and value of each subcell
# 3. append to the value (value_<catechol>) newly generated columns '<catechol>_<timepoint>'
list_values_catechol=[] #all <catechol> values (last element)
list_timepoints_catechol=[] #possible timepoint values (last element)
list_catechol = ['14=ADRENALINE', '15=NORADRENALINE', '16=DOPAMINE', '17=DOBUTAMINE', '18=VASOPRESSIN',
                 '19=MILRINONE']
def catechol_timepoint(catechol):
    for index, cell in df_ICU['TIME_POINT_'+ catechol].items(): #e.g. cell = 'FIRST=0.12; SECOND=0.84'; type: string
        ###extract values
        values = cell.split(';') #e.g. values = ['FIRST=0.12', 'SECOND=0.84']; type: list
        for value in values: #e.g. value = 'SECOND=0.84'
            value_timepoint = value.split('=')[0] #e.g. value_timepoint = 'SECOND'; type: first element of a list (str)
            value_catechol = value.split('=')[1] #e.g. value_catechol = '0.84'; type: second element of a list (str)
            ###quality check of value_catechol
            #real catechol values are displayed as strings ('0.05') but we want them as floats (0.5)
            #NULL are also strings, but just won't have digits
            #NaN will be float
            #NOTE: you cannot do it with screening for digits directly, since it will cut the decimals
            value_catechol = float(value_catechol) if value_catechol.replace('.', '', 1).isdigit() else float('NaN')
            #all catechol values in a list
            list_values_catechol.append(value_catechol)
            list_timepoints_catechol.append(value_timepoint) if value_timepoint not in list_timepoints_catechol else ''
            #catechol (catechol='14=ADRENALINE' -> take part after '=' and make it lowercase)
            df_ICU.loc[index, catechol.split('=')[1].lower() + '_' + value_timepoint] = value_catechol

for element in list_catechol: #extract value and timepoint of all 4 catecholamines
    catechol_timepoint(element)

###calculate vis score for each timepoint and patient (row)####################
for timepoint in timepoints:
    #replace NaN values with 0 (otherwise result is NaN as soon as one column NaN)
    df_ICU[f'vis_{timepoint}'] = (df_ICU[f'dopamine_{timepoint}'].fillna(0) + 
                                  df_ICU[f'dobutamine_{timepoint}'].fillna(0) + 
                                  100 * df_ICU[f'adrenaline_{timepoint}'].fillna(0) + 
                                  10 * df_ICU[f'milrinone_{timepoint}'].fillna(0) +
                                  10000 * df_ICU[f'vasopressin_{timepoint}'].fillna(0) + 
                                  100 * df_ICU[f'noradrenaline_{timepoint}'].fillna(0))

###state number of catecholamines for each timepoint
#NULL values in any catecholamine is treated as dose of 0 (not optimal, but more often true than wrong)
for index, row in df_ICU.iterrows():
    for timepoint in timepoints:
        numb = 0
        for catechol in list_catechol:
            catechol_columnname = catechol.split('=')[1].lower() + '_' + timepoint
            numb += 1 if (not np.isnan(df_ICU.loc[index, catechol_columnname] > 0) and df_ICU.loc[index, catechol_columnname] > 0) else 0
        df_ICU.loc[index, 'catechol_numb_'+timepoint] = numb

###additionally, calculate spo2[%]/fio2[] + po2[mmHg]/fio2[]###################
for timepoint in timepoints:
    df_ICU['spo2/fio2_'+timepoint] = df_ICU['spo2_'+timepoint] / df_ICU['fio2_'+timepoint]
    df_ICU['po2/fio2_'+timepoint] = df_ICU['po2_mmHg_'+timepoint] / df_ICU['fio2_'+timepoint]

###############################################################################
### PELOD #####################################################################
###############################################################################

###calculate pelod subpoints###################################################
for timepoint in timepoints:
    ### pelod gcs points (pelod_gcs_<timepoint>)
    df_ICU.loc[df_ICU['gcs_'+timepoint] <5, 'pelod_gcs_'+timepoint] = 4
    df_ICU.loc[(df_ICU['gcs_'+timepoint] >=5) & (df_ICU['gcs_'+timepoint] <11), 'pelod_gcs_'+timepoint] = 1
    df_ICU.loc[df_ICU['gcs_'+timepoint] >=11, 'pelod_gcs_'+timepoint] = 0
    ### pelod pupils point (pelod_pupils_<timepoint>)
    df_ICU.loc[df_ICU['pupils_'+timepoint] == 'YES', 'pelod_pupils_' + timepoint] = 5
    df_ICU.loc[(df_ICU['pupils_'+timepoint] == 'NO') | (df_ICU['pupils_'+timepoint] == 'Unk'), 'pelod_pupils_' + timepoint] = 0
    ### pelod lactate points (pelod_lactate_<timepoint>)
    df_ICU.loc[df_ICU['lactate_mmol/L_'+timepoint] >=11, 'pelod_lactate_'+timepoint] = 4
    df_ICU.loc[(df_ICU['lactate_mmol/L_'+timepoint] >=5) & (df_ICU['lactate_mmol/L_'+timepoint] <11), 'pelod_lactate_'+timepoint] = 1
    df_ICU.loc[df_ICU['lactate_mmol/L_'+timepoint] <5, 'pelod_lactate_'+timepoint] = 0
    ### pelod meanbp points (pelod_creatinine_<timepoint>)
    # dependent on age => dictionary with age and bp as key-tuple (key[0], key[1]) and the pelod points as value
    # .between() includes by default both given borders; just be careful when variable has decimals (here: age, bot not meanbp) -> state inclusive=left/right/neither/both
    dictionary = {('<1', '<=16'):6, ('<1', '.between(17,30)'):3, ('<1', '.between(31,45)'):2, ('<1', '>=46'):0, 
                  ('.between(1,12,inclusive="left")', '<=24'):6, ('.between(1,12,inclusive="left")', '.between(25,38)'):3, ('.between(1,12,inclusive="left")', '.between(39,54)'):2, ('.between(1,12,inclusive="left")', '>=55'):0, 
                  ('.between(12,24,inclusive="left")', '<=30'):6, ('.between(12,24,inclusive="left")', '.between(31,43)'):3, ('.between(12,24,inclusive="left")', '.between(44,59)'):2, ('.between(12,24,inclusive="left")', '>=60'):0,
                  ('.between(24,60,inclusive="left")', '<=31'):6, ('.between(24,60,inclusive="left")', '.between(32,45)'):3, ('.between(24,60,inclusive="left")', '.between(46,61)'):2, ('.between(24,60,inclusive="left")', '>=62'):0,
                  ('.between(60,144,inclusive="left")', '<=35'):6, ('.between(60,144,inclusive="left")', '.between(36,48)'):3, ('.between(60,144,inclusive="left")', '.between(49,66)'):2, ('.between(60,144,inclusive="left")', '>=65'):0,
                  ('>=144', '<=37'):6, ('>=144', '.between(38,51)'):3, ('>=144', '.between(52,66)'):2, ('>=144', '>=67'):0} 
    for key,value in dictionary.items():
        df_ICU.loc[(eval(f'df_ICU["meanbp_"+timepoint] {key[1]}')) & (eval(f'df_ICU["age_investigation_"+timepoint] {key[0]}'))  , 'pelod_meanbp_'+timepoint] = value
    ### pelod creatinine points 
    # dependent on age => dictionary with age and creatinine as key-tuple (key[0], key[1]) and the pelod points as value
    dictionary = {('<1', '>=70'):2, ('<1', '<70'):0, 
                  ('.between(1,12,inclusive="left")', '>=23'):2, ('.between(1,11)', '<23'):0, 
                  ('.between(12,24,inclusive="left")', '>=35'):2, ('.between(12,23)', '<35'):0,
                  ('.between(24,60,inclusive="left")', '>=51'):2, ('.between(24,59)', '<51'):0,
                  ('.between(60,144,inclusive="left")', '>=59'):2, ('.between(60,143)', '<59'):0,
                  ('>=144', '>=93'):2, ('>=144', '<93'):0}
    for key,value in dictionary.items():
        df_ICU.loc[(eval(f'df_ICU["creatinine_µmol/L_"+timepoint] {key[1]}')) & (eval(f'df_ICU["age_investigation_"+timepoint] {key[0]}'))  , 'pelod_creatinine_'+timepoint] = value
    ### pelod po2/fio2 points (pelod_po2/fio2_<timepoint>)
    df_ICU.loc[df_ICU['po2/fio2_'+timepoint]<=60, 'pelod_po2/fio2_'+timepoint] = 2
    df_ICU.loc[df_ICU['po2/fio2_'+timepoint]>60, 'pelod_po2/fio2_'+timepoint] = 0
    ### pelod pco2 points (pelod_pco2_<timepoint>)
    df_ICU.loc[df_ICU['pco2_mmHg_'+timepoint]>=95, 'pelod_pco2_'+timepoint] = 3
    df_ICU.loc[(df_ICU['pco2_mmHg_'+timepoint]<95) & (df_ICU['pco2_mmHg_'+timepoint]>58), 'pelod_po2/fio2_'+timepoint] = 1
    df_ICU.loc[df_ICU['pco2_mmHg_'+timepoint]<=58, 'pelod_pco2_'+timepoint] = 0
    #pelod iv points (pelod_iv_<timepoint>)
    df_ICU.loc[df_ICU['iv_'+timepoint] == 'YES', 'pelod_iv_' + timepoint] = 3
    df_ICU.loc[df_ICU['iv_'+timepoint] == 'NO', 'pelod_iv_' + timepoint] = 0
    ### pelod wbc points (pelod_wbc_<timepoint>)
    df_ICU.loc[df_ICU['wbc_'+timepoint] <= 2, 'pelod_wbc_' + timepoint] = 2
    df_ICU.loc[df_ICU['wbc_'+timepoint] > 2, 'pelod_wbc_' + timepoint] = 0
    ### pelod platelets points (pelod_platelets_<timepoint>)
    df_ICU.loc[df_ICU['platelets_'+timepoint] <= 76, 'pelod_platelets_' + timepoint] = 2
    df_ICU.loc[(df_ICU['platelets_'+timepoint] > 76) & (df_ICU['platelets_'+timepoint] < 142), 'pelod_platelets_' + timepoint] = 1
    df_ICU.loc[df_ICU['platelets_'+timepoint] >= 142, 'pelod_platelets_' + timepoint] = 0

###correct pelod points########################################################
###set <pelod_variable>_<timepoint> == 0 if for the respective <timepoint> at 
###least three >pelod_variable<_<timepoint> has a real value 
pelod_variables=['pelod_gcs', 'pelod_pupils','pelod_lactate', 'pelod_meanbp', 'pelod_creatinine', 'pelod_po2/fio2', 
                'pelod_pco2', 'pelod_iv', 'pelod_wbc', 'pelod_platelets']
for index,row in df_ICU.iterrows(): #row = row (patient)
    for timepoint in timepoints: #e.g. timepoint='FIRST'
        count_notnan=0
        for variable in pelod_variables: #e.g. variable='pelod_gcs'
            if not math.isnan(row[variable+'_'+timepoint]): #e.g. row['pelod_gcs_FIRST'] != NaN
                count_notnan+=1 #count_notnan = number of pelod_variables per timepoint have a value
        if count_notnan > 2: #you can adjust this number (will be the min #variables that need to be true)
            for variable in pelod_variables:
                if math.isnan(row[variable+'_'+timepoint]): #replace NaN variables if there are points for other variable at this timepoint
                    df_ICU.loc[index, variable+'_'+timepoint] = 0

###calculate cluster pelod and pelod###########################################
for timepoint in timepoints:
    ### cluster pelod score
    # alegbra works well with NaN => if one of the terms is NaN, result will be NaN
    # pelod cns
    df_ICU['pelod_CNS_' + timepoint] = df_ICU['pelod_gcs_'+timepoint] + df_ICU['pelod_pupils_'+timepoint]
    # pelod cvs
    df_ICU['pelod_CVS_' + timepoint] = df_ICU['pelod_lactate_'+timepoint] + df_ICU['pelod_meanbp_'+timepoint]
    # pelod RENAL 
    df_ICU['pelod_RENAL_'+timepoint] = df_ICU['pelod_creatinine_'+timepoint]
    # pelod RESP
    df_ICU['pelod_RESP_' + timepoint] = df_ICU['pelod_po2/fio2_'+timepoint] + df_ICU['pelod_pco2_'+timepoint] + df_ICU['pelod_iv_'+timepoint]
    # pelod HEM 
    df_ICU['pelod_HEM_' + timepoint] = df_ICU['pelod_wbc_'+timepoint] + df_ICU['pelod_platelets_'+timepoint]
    ### pelod score 
    # alegbra works well with NaN => if one of the terms is NaN, result will be NaN
    df_ICU['pelod_score_' + timepoint] = df_ICU['pelod_CNS_'+timepoint] + df_ICU['pelod_CVS_'+timepoint] + df_ICU['pelod_RENAL_'+timepoint] + df_ICU['pelod_RESP_'+timepoint] + df_ICU['pelod_HEM_'+timepoint]

###############################################################################
### Alluvial Organ Dysfunction dependent on timepoint #########################
#new columns pelod_number_orgdys_<timepoint> counting the number of organdysfunctions per patient and timepoint
for index, row in df_ICU.iterrows():
    for timepoint in ['BASELINE','FIRST','FRB_24','SECOND','THIRD']:
        orgdys_count=0
        na_count=0
        for orgdys in ['pelod_CNS', 'pelod_CVS', 'pelod_RENAL', 'pelod_RESP', 'pelod_HEM']:
            orgdys_count += 1 if row[orgdys+'_'+timepoint] >1 else 0 #definition 'organdysfunction' = pelod subscore > 1
            #normally nan would be replaced by 0 with the condition above
            #but if all 5 pelod subscores are NaN we want orgdys = NaN
            if math.isnan(row[orgdys+'_'+timepoint]):
                na_count += 1
                orgdys_count = float('NaN') if na_count > 4 else orgdys_count
        df_ICU.loc[index,'pelod_number_orgdys_'+timepoint] = orgdys_count  
###############################################################################

###############################################################################
### PSOFA #####################################################################
###############################################################################

# if there is no unit indicated == default unit from the CRF
# cavet: psofa referes actually to the worst values within 24h-intervals (we don't have 24h and only 1 measure!!!)

###calculate psofa subpoints###################################################
for timepoint in timepoints:
    ### psofa respiratory points
    df_ICU.loc[(df_ICU['po2/fio2_'+timepoint]<100) & (df_ICU['respsup_'+timepoint]=='YES'), 'psofa_respiratory_'+timepoint] = 4
    df_ICU.loc[(df_ICU['po2/fio2_'+timepoint]<200) & (df_ICU['po2/fio2_'+timepoint]>=100) & (df_ICU['respsup_'+timepoint]=='YES'), 'psofa_respiratory_'+timepoint] = 3
    df_ICU.loc[(df_ICU['po2/fio2_'+timepoint]<300) & (df_ICU['respsup_'+timepoint] != 'YES'), 'psofa_respiratory_'+timepoint] = 2
    df_ICU.loc[(df_ICU['po2/fio2_'+timepoint]<400) & (df_ICU['po2/fio2_'+timepoint]>=300), 'psofa_respiratory_'+timepoint] = 1
    df_ICU.loc[(df_ICU['po2/fio2_'+timepoint]>=400), 'psofa_respiratory_'+timepoint] = 0
    ### psofa coagulation points
    df_ICU.loc[df_ICU['platelets_'+timepoint] < 20, 'psofa_coagulation_' + timepoint] = 4
    df_ICU.loc[(df_ICU['platelets_'+timepoint] < 50) & (df_ICU['platelets_'+timepoint] >= 20), 'psofa_coagulation_' + timepoint] = 3
    df_ICU.loc[(df_ICU['platelets_'+timepoint] < 100) & (df_ICU['platelets_'+timepoint] >= 50), 'psofa_coagulation_' + timepoint] = 2
    df_ICU.loc[(df_ICU['platelets_'+timepoint] < 150) & (df_ICU['platelets_'+timepoint] >= 100), 'psofa_coagulation_' + timepoint] = 1
    df_ICU.loc[df_ICU['platelets_'+timepoint] >= 150, 'psofa_coagulation_' + timepoint] = 0
    ### psofa hepatic points
    df_ICU.loc[df_ICU['bilirubin_mg/dL_'+timepoint] >=12, 'psofa_hepatic_'+timepoint] = 4
    df_ICU.loc[(df_ICU['bilirubin_mg/dL_'+timepoint] >=6) & (df_ICU['bilirubin_mg/dL_'+timepoint] <12), 'bilirubin_mg/dL_'+timepoint] = 3
    df_ICU.loc[(df_ICU['bilirubin_mg/dL_'+timepoint] >=2) & (df_ICU['bilirubin_mg/dL_'+timepoint] <6), 'bilirubin_mg/dL_'+timepoint] = 2
    df_ICU.loc[(df_ICU['bilirubin_mg/dL_'+timepoint] >=1.2) & (df_ICU['bilirubin_mg/dL_'+timepoint] <2), 'bilirubin_mg/dL_'+timepoint] = 1
    df_ICU.loc[df_ICU['bilirubin_mg/dL_'+timepoint] <1.2, 'psofa_hepatic_'+timepoint] = 0
    ### psofa cardiovascular points (first considering only bp, following lines will adapt that)
    # dependent on age => create a dictionary with age and bp as key-tuple (key[0], key[1]) and the psofa points as value
    dictionary = {('<1', '<46'):1, ('<1', '>=46'):0, 
                  ('.between(1,12,inclusive="left")', '<55'):1, ('.between(1,12,inclusive="left")', '>=55'):0, 
                  ('.between(12,24,inclusive="left")', '<60'):1, ('.between(12,24,inclusive="left")', '>=60'):0,
                  ('.between(24,60,inclusive="left")', '<62'):1, ('.between(24,60,inclusive="left")', '>=62'):0,
                  ('.between(60,144,inclusive="left")', '<65'):1, ('.between(60,144,inclusive="left")', '>=65'):0,
                  ('.between(144,217,inclusive="left")', '<67'):1, ('.between(144,217,inclusive="left")', '>=67'):0,
                  ('>=217', '<70'):1, ('>=217', '>=70'):0}
    for key,value in dictionary.items():
        df_ICU.loc[(eval(f'df_ICU["meanbp_"+timepoint] {key[1]}')) & (eval(f'df_ICU["age_investigation_"+timepoint] {key[0]}'))  , 'psofa_cardiovascular_'+timepoint] = value
    ### change psofa cardiovascular points (based on catecholamines)
    df_ICU.loc[((df_ICU['dopamine_'+timepoint] >0) & (df_ICU['dopamine_'+timepoint] <=5)) | (df_ICU['dobutamine_'+timepoint] >0), 'psofa_cardiovascular_'+timepoint] = 2
    df_ICU.loc[((df_ICU['dopamine_'+timepoint] >5) & (df_ICU['dopamine_'+timepoint] <=15)) | ((df_ICU['adrenaline_'+timepoint] >0) & (df_ICU['adrenaline_'+timepoint] <=0.1)) | ((df_ICU['noradrenaline_'+timepoint] >0) & (df_ICU['noradrenaline_'+timepoint] <=0.1)), 'psofa_cardiovascular_'+timepoint] = 3
    df_ICU.loc[(df_ICU['dopamine_'+timepoint] >15) | (df_ICU['adrenaline_'+timepoint] >0.1) | (df_ICU['noradrenaline_'+timepoint] >0.1), 'psofa_cardiovascular_'+timepoint] = 4
    ### psofa neurologic points
    df_ICU.loc[df_ICU['gcs_'+timepoint] == 15, 'psofa_neurologic_'+timepoint] = 0
    df_ICU.loc[(df_ICU['gcs_'+timepoint] <15) & (df_ICU['gcs_'+timepoint] >=13), 'psofa_neurologic_'+timepoint] = 1
    df_ICU.loc[(df_ICU['gcs_'+timepoint] <13) & (df_ICU['gcs_'+timepoint] >=10), 'psofa_neurologic_'+timepoint] = 2
    df_ICU.loc[(df_ICU['gcs_'+timepoint] <10) & (df_ICU['gcs_'+timepoint] >=6), 'psofa_neurologic_'+timepoint] = 3
    df_ICU.loc[df_ICU['gcs_'+timepoint] <6, 'psofa_neurologic_'+timepoint] = 4
    ### psofa renal points
    # dependent on age => create a dictionary with age and creatinine as key-tuple (key[0], key[1]) and the pelod points as value
    # make upper border +0.1 but exclude it, so in case a value with more than one decimal won't accidently be excluded
    dictionary = {('<1', '<0.8'):0, ('<1', '.between(0.8,1,inclusive="left")'):1, ('<1', '.between(1.0,1.2,inclusive="left")'):2, ('<1', '.between(1.2,1.6,inclusive="left")'):3, ('<1','>=1.6'):4,
                  ('.between(1,12,inclusive="left")', '<0.3'):0, ('.between(1,12,inclusive="left")', '.between(0.3,0.5,inclusive="left")'):1, ('.between(1,12,inclusive="left")', '.between(0.5,0.8,inclusive="left")'):2, ('.between(1,12,inclusive="left")', '.between(0.8,1.2,inclusive="left")'):3, ('.between(1,12,inclusive="left")', '>=1.2'):4,
                  ('.between(12,24,inclusive="left")', '<0.4'):0, ('.between(12,24,inclusive="left")', '.between(0.4,0.6,inclusive="left")'):1, ('.between(12,24,inclusive="left")', '.between(0.6,1.1,inclusive="left")'):2, ('.between(12,24,inclusive="left")', '.between(1.1,1.5,inclusive="left")'):3, ('.between(12,24,inclusive="left")', '>=1.5'):4,
                  ('.between(24,60,inclusive="left")', '<0.6'):0, ('.between(24,60,inclusive="left")', '.between(0.6,0.9,inclusive="left")'):1, ('.between(24,60,inclusive="left")', '.between(0.9,1.6,inclusive="left")'):2, ('.between(24,60,inclusive="left")', '.between(1.6,2.3,inclusive="left")'):3, ('.between(24,60,inclusive="left")', '>=2.3'):4,
                  ('.between(60,144,inclusive="left")', '<0.7'):0, ('.between(60,144,inclusive="left")', '.between(0.7,1.1,inclusive="left")'):1, ('.between(60,144,inclusive="left")', '.between(1.1,1.8,inclusive="left")'):2, ('.between(60,144,inclusive="left")', '.between(1.8,2.6,inclusive="left")'):3, ('.between(60,144,inclusive="left")', '>=2.6'):4,
                  ('.between(144,216)', '<1.0'):0, ('.between(144,216)', '.between(1.0,1.7,inclusive="left")'):1, ('.between(144,216)', '.between(1.7,2.9,inclusive="left")'):2, ('.between(144,216)', '.between(2.9,4.2,inclusive="left")'):3, ('.between(144,216)', '>=4.2'):4,
                  ('>216', '<1.2'):0, ('>216', '.between(1.2,2,inclusive="left")'):1 , ('>216', '.between(2,3.5,inclusive="left")'):2, ('>216', '.between(3.5,5,inclusive="left")'):3, ('>216', '>=5'):4}
    for key,value in dictionary.items():
        df_ICU.loc[(eval(f'df_ICU["creatinine_mg/dL_"+timepoint] {key[1]}')) & (eval(f'df_ICU["age_investigation_"+timepoint] {key[0]}'))  , 'psofa_renal_'+timepoint] = value

###correct psofa points########################################################
###set <psofa_variable>_<timepoint> == 0 if for the respective <timepoint> at 
### least three >psofa_variable<_<timepoint> must have a real value 
psofa_variables=['psofa_respiratory','psofa_coagulation','psofa_hepatic', 
                'psofa_cardiovascular', 'psofa_neurologic', 'psofa_renal']
for index,row in df_ICU.iterrows(): #row = row (patient)
    for timepoint in timepoints: #e.g. timepoint='FIRST'
        count_notnan=0
        for variable in psofa_variables: #e.g. variable='psofa_respiratory'
            if not math.isnan(row[variable+'_'+timepoint]): #e.g. row['psofa_respiratory_FIRST'] != NaN
                count_notnan+=1 #count_notnan = number of psofa_variables per timepoint having a value
        if count_notnan > 2: #you can adjust this number (will be the min #variables that need to be true)
            for variable in psofa_variables:
                if math.isnan(row[variable+'_'+timepoint]): #replace NaN variables if there are points for other variable at this timepoint
                    df_ICU.loc[index, variable+'_'+timepoint] = 0

###calculate psofa#############################################################
for timepoint in timepoints: 
    # alegbra works well with NaN => if one of the terms is NaN, result will be NaN
    df_ICU['psofa_score_' + timepoint] = (
        df_ICU['psofa_respiratory_' + timepoint] + 
        df_ICU['psofa_coagulation_' + timepoint] + 
        df_ICU['psofa_hepatic_' + timepoint] + 
        df_ICU['psofa_cardiovascular_' + timepoint] + 
        df_ICU['psofa_neurologic_' + timepoint] + 
        df_ICU['psofa_renal_' + timepoint])

###############################################################################
### PODIUM ####################################################################
###############################################################################

for timepoint in timepoints:
    ### NEUROLOGY #############################################################
    ### podium gcs points
    df_ICU.loc[df_ICU['gcs_'+timepoint] <=8, 'podium_NEURO_'+timepoint] = 1
    ### podium 0 points; define 0 since NaN's will be NaN
    df_ICU.loc[df_ICU['gcs_'+timepoint] >8, 'podium_NEURO_'+timepoint] = 0
    ### RESPIRATORY ###########################################################
    ### podium "fio2 AND po2/fio2" points 
    # /// maybe replace NULL fio2 in beginning with 0.21 ///
    df_ICU.loc[(df_ICU['po2/fio2_'+timepoint] <= 300) & (df_ICU['fio2_'+timepoint] >= 0.4), 'podium_RESP_'+timepoint] = 1
    ### podium "fio2 AND spo2/fio2" points 
    # only if podium_RESP_<timepoint> still NaN
    # /// maybe replace NULL fio2 in beginning with 0.21 ///
    df_ICU.loc[(df_ICU['podium_RESP_'+timepoint].isna()) & (df_ICU['spo2/fio2_'+timepoint] <= 264) & (df_ICU['fio2_'+timepoint] >= 0.4), 'podium_RESP_'+timepoint] = 1
    ### podium "NIV and fio2" points 
    # only if podium_RESP_<timepoint> still NaN
    # /// maybe replace NULL fio2 in beginning with 0.21///
    df_ICU.loc[(df_ICU['podium_RESP_'+timepoint].isna()) & (df_ICU['niv_'+timepoint] == 'YES') & (df_ICU['fio2_'+timepoint] >= 0.4), 'podium_RESP_'+timepoint] = 1
    ### podium "IV" points
    # only if podium_RESP_<timepoint> still NaN
    df_ICU.loc[(df_ICU['podium_RESP_'+timepoint].isna()) & (df_ICU['iv_'+timepoint] == 'YES'), 'podium_RESP_'+timepoint] = 1
    ### podium "ECLS and IV" points 
    # only if podium_RESP_<timepoint> still NaN
    df_ICU.loc[(df_ICU['podium_RESP_'+timepoint].isna()) & (df_ICU['iv_'+timepoint] == 'YES') & (df_ICU['ecmo_'+timepoint] == 'YES'), 'podium_RESP_'+timepoint] = 2
    ### podium 0 points (only one combination needs to be present); define 0 since NaN's will be NaN
    df_ICU.loc[(df_ICU['podium_RESP_'+timepoint].isna()) &
               (
               ((df_ICU['po2/fio2_'+timepoint].notna()) & (df_ICU['fio2_'+timepoint].notna())) |
               ((df_ICU['spo2/fio2_'+timepoint].notna()) & (df_ICU['fio2_'+timepoint].notna())) |
               ((df_ICU['niv_'+timepoint].notna()) & (df_ICU['fio2_'+timepoint].notna())) | 
               (df_ICU['iv_'+timepoint].notna())
               ),
               'podium_RESP_'+timepoint] = 0
    ### CARDIOVASCULAR ########################################################
    ### podium "hr and age" *subpoints*
    # dependent on age => create a dictionary with age and bp as key-tuple (key[0], key[1]) and the podium points as value
    dictionary = {('.between(0,12)', '>180'):1, # 0-1 year 
                  ('.between(12,72,inclusive="neither")', '>160'):1, # >1 - <6 year
                  ('.between(72,156,inclusive="left")', '>150'):1, # 6 - <13 year
                  ('.between(156,216,inclusive="left")', '>130'):1 # 13 - <18 year
                  }
    for key,value in dictionary.items():
        df_ICU.loc[(eval(f'df_ICU["age_investigation_"+timepoint] {key[0]}')) & (eval(f'df_ICU["hr_"+timepoint] {key[1]}')) , 'podium_hr_'+timepoint] = value
    ### podium "bp and age" *subpoints*
    # dependent on age => create a dictionary with age and bp as key-tuple (key[0], key[1]) and the podium points as value
    # right border (included) will be left border (included) of next range; but ok, will be left border of next range therefore, meaning less restrictive, but all ages caught like that
    dictionary = {('.between(0,0.23)', '<50'):1, # 0 - 1 week (0.23 month)
                  ('.between(7,31,inclusive="right")', '<70'):1, # >1 week (0.23 month) - 1 month
                  ('.between(1,72,inclusive="neither")', '<75'):1, # >1 month - <6 years
                  ('.between(72,216,inclusive="left")', '<80'):1 #6 years - <18 years
                  }
    for key,value in dictionary.items():
            df_ICU.loc[(eval(f'df_ICU["age_investigation_"+timepoint] {key[0]}')) & (eval(f'df_ICU["meanbp_"+timepoint] {key[1]}')) , 'podium_bp_'+timepoint] = value
    ### podium vis score *subpoints*
    df_ICU.loc[df_ICU['vis_'+timepoint] >= 5, 'podium_vis_'+timepoint] = 1
    ### podium lactate *subpoints*
    df_ICU.loc[df_ICU['lactate_mmol/L_'+timepoint] >= 3, 'podium_lactate_'+timepoint] = 1
    ### podium help points (sum up the subpoints that are not sufficient on themselves)
    df_ICU[f'podium_help_{timepoint}'] = (df_ICU[f'podium_hr_{timepoint}'].fillna(0) + 
                                          df_ICU[f'podium_bp_{timepoint}'].fillna(0) + 
                                          df_ICU[f'podium_vis_{timepoint}'].fillna(0) + 
                                          df_ICU[f'podium_lactate_{timepoint}'].fillna(0))
    ### podium "VA ECMO" points
    df_ICU.loc[df_ICU['ecmo_va_'+timepoint] == 'YES', 'podium_CARDIO_'+timepoint] = 2
    ### podium "two or more help points AND lactate >=5 (instead only >=3 as defined in helper points)" points
    # only if podium_CARDIO_<timepoint> still NaN
    df_ICU.loc[(df_ICU['podium_CARDIO_'+timepoint].isna()) & (df_ICU['podium_help_'+timepoint] >=2) & (df_ICU['lactate_mmol/L_'+timepoint] >=5), 'podium_CARDIO_'+timepoint] = 2
    ### podium "two or more help points" points
    # only if podium_CARDIO_<timepoint> still NaN
    df_ICU.loc[(df_ICU['podium_CARDIO_'+timepoint].isna()) & (df_ICU['podium_help_'+timepoint] >=2), 'podium_CARDIO_'+timepoint] = 1
    ### podium 0 points (only one combination needs to be present; actually would need two from helper; vis excluded since never NaN); define 0 since NaN's will be NaN
    df_ICU.loc[(df_ICU['podium_CARDIO_'+timepoint].isna()) &
               (
               ((df_ICU['age_investigation_'+timepoint].notna()) & (df_ICU['hr_'+timepoint].notna())) |
               ((df_ICU['age_investigation_'+timepoint].notna()) & (df_ICU['meanbp_'+timepoint].notna())) | 
               (df_ICU['ecmo_va_'+timepoint].notna()) |
               (df_ICU['lactate_mmol/L_'+timepoint].notna())
               ),
               'podium_CARDIO_'+timepoint] = 0
    ### RENAL #################################################################
    # original paper defined differently (e.g. no cutoffs etc.); continuous paper defines cutoffs but different
    ### podium creatinine cutoffs
    cutoff=1 ###implement logics with age?
    df_ICU.loc[df_ICU['creatinine_µmol/L_'+timepoint]> cutoff, 'podium_RENAL_'+timepoint] = 1
    ### podium rrt points
    # only if podium_RENAL_<timepoint> still NaN
    df_ICU.loc[(df_ICU['podium_RENAL_'+timepoint].isna()) & (df_ICU['rrt_'+timepoint] == 'YES'), 'podium_RENAL_'+timepoint] = 1
    ### podium 0; define 0 since NaN's will be NaN
    df_ICU.loc[(df_ICU['podium_RENAL_'+timepoint].isna()) &
               (
               (df_ICU['creatinine_µmol/L_'+timepoint].notna()) | 
               (df_ICU['rrt_'+timepoint].notna())
               ),
               'podium_RENAL_'+timepoint] = 0
    ### GASTRO ################################################################
    ### no data 
    ### HEPATIC ###############################################################
    ### podium coag encephal *subpoints*
    df_ICU.loc[df_ICU['inr_'+timepoint] > 2, 'podium_coag_encephal_'+timepoint] = 1
    df_ICU.loc[(df_ICU['inr_'+timepoint] > 1.5) & 
               (df_ICU['podium_NEURO_'+timepoint] == 1), 'podium_coag_encephal_'+timepoint] = 1
    ### podium ALT points
    df_ICU.loc[(df_ICU['podium_coag_encephal_'+timepoint] == 1) & 
               (df_ICU['alt_IU/L_'+timepoint] > 100), 'podium_HEPATIC_'+timepoint] = 1
    ### podium bilirubin points
    # only if podium_HEPATIC_<timepoint> still NaN
    df_ICU.loc[(df_ICU['podium_HEPATIC_'+timepoint].isna()) & 
               (df_ICU['podium_coag_encephal_'+timepoint] == 1) & 
               (df_ICU['bilirubin_mg/dL_'+timepoint] > 5), 'podium_HEPATIC_'+timepoint] = 1
    ### podium 0 points (only one combination needs to be present); define 0 since NaN's will be NaN
    df_ICU.loc[(df_ICU['podium_HEPATIC_'+timepoint].isna()) &
               (
               ((df_ICU['podium_coag_encephal_'+timepoint].notna()) & (df_ICU['alt_IU/L_'+timepoint].notna())) |
               ((df_ICU['podium_coag_encephal_'+timepoint].notna()) & (df_ICU['bilirubin_mg/dL_'+timepoint].notna()))
               ),
               'podium_HEPATIC_'+timepoint] = 0
    ### HEMATOLOGY ############################################################
    ### podium platelets points
    df_ICU.loc[(df_ICU['platelets_'+timepoint] < 100, 'podium_HEMAT_'+timepoint)] = 1
    ### podium wbc points
    # only if podium_HEMAT_<timepoint> still NaN
    df_ICU.loc[(df_ICU['podium_HEMAT_'+timepoint].isna()) &
               (df_ICU['wbc_'+timepoint] <3), 'podium_HEMAT_'+timepoint] = 1
    ### podium 0; define 0 since NaN's will be NaN
    df_ICU.loc[(df_ICU['podium_HEMAT_'+timepoint].isna()) &
               (
               (df_ICU['platelets_'+timepoint].notna()) | 
               (df_ICU['wbc_'+timepoint].notna())
               ),
               'podium_HEMAT_'+timepoint] = 0
    ### COAGULATION ###########################################################
    ### podium platelets & inr points
    df_ICU.loc[(df_ICU['platelets_'+timepoint] < 1000) &
               (df_ICU['inr_'+timepoint] > 1.5) &
               (df_ICU['podium_HEPATIC_'+timepoint] == 0), 'podium_COAG_'+timepoint] = 1
    ### podium 0; define 0 since NaN's will be NaN
    df_ICU.loc[(df_ICU['podium_COAG_'+timepoint].isna()) &
               (df_ICU['platelets_'+timepoint].notna()) &
               (df_ICU['inr_'+timepoint].notna()),
               'podium_COAG_'+timepoint] = 0
    ### IMMUNE ################################################################
    ### podium neutrophil points
    df_ICU.loc[df_ICU['neutro_'+timepoint] < 0.5, 'podium_IMMUNE_'+timepoint] = 1
    ### podium lymphocyte points
    # only if podium_IMMUNE_<timepoint> still NaN
    df_ICU.loc[(df_ICU['podium_IMMUNE_'+timepoint].isna()) &
               (df_ICU['lympho_'+timepoint] < 1), 'podium_IMMUNE_'+timepoint] = 1
    ### podium 0; define 0 since NaN's will be NaN
    df_ICU.loc[(df_ICU['podium_IMMUNE_'+timepoint].isna()) &
               (
               (df_ICU['neutro_'+timepoint].notna()) | 
               (df_ICU['lympho_'+timepoint].notna())
               ),
               'podium_IMMUNE_'+timepoint] = 0

###correct podium points#######################################################
###set <podium_variable>_<timepoint> == 0 if for the respective <timepoint> at 
### least three >podium_variable<_<timepoint> must have a real value 
podium_variables = ['podium_NEURO', 'podium_RESP', 'podium_CARDIO', 
                    'podium_RENAL', 'podium_HEPATIC', 'podium_HEMAT', 
                    'podium_COAG', 'podium_IMMUNE']

for index,row in df_ICU.iterrows(): #row = row (patient)
    for timepoint in timepoints: #e.g. timepoint='FIRST'
        count_notnan=0
        for variable in podium_variables: #e.g. variable='podium_NEURO'
            if not math.isnan(row[variable+'_'+timepoint]): #e.g. row['podium_NEURO_FIRST'] != NaN
                count_notnan+=1 #count_notnan = number of podium_variables per timepoint having a value
        if count_notnan > 2: #you can adjust this number (will be the min #variables that need to be true)
            for variable in podium_variables:
                if math.isnan(row[variable+'_'+timepoint]): #replace NaN variables if there are points for other variable at this timepoint
                    df_ICU.loc[index, variable+'_'+timepoint] = 0

###calculate podium#############################################################
for timepoint in timepoints: 
    # alegbra works well with NaN => if one of the terms is NaN, result will be NaN
    df_ICU['podium_score_' + timepoint] = (
        df_ICU['podium_NEURO_' + timepoint] + 
        df_ICU['podium_RESP_' + timepoint] + 
        df_ICU['podium_CARDIO_' + timepoint] + 
        df_ICU['podium_RENAL_' + timepoint] + 
        df_ICU['podium_HEPATIC_' + timepoint] + 
        df_ICU['podium_HEMAT_' + timepoint] + 
        df_ICU['podium_COAG_' + timepoint] + 
        df_ICU['podium_IMMUNE_' + timepoint])

###############################################################################
### GOLDSTEIN #################################################################
###############################################################################
for timepoint in timepoints:
    ### RESPIRATORY ###########################################################
    ### goldstein respiratory points
    df_ICU.loc[(df_ICU['po2/fio2_'+timepoint] <300) |
               (df_ICU['pco2_mmHg_'+timepoint] >65) |
               (df_ICU['niv_'+timepoint] == 'YES') |
               (df_ICU['iv_'+timepoint] == 'YES') |
               (df_ICU['ecmo_'+timepoint] == 'YES'), 
               'goldstein_RESP_'+timepoint] = 1
    ### goldstein 0 points; define 0 since NaN's will be NaN
    # only if goldstein_RESP_<timepoint> still NaN AND
    # at least one value needs to be present
    df_ICU.loc[((df_ICU['goldstein_RESP_'+timepoint].isna()) &
                ((df_ICU['po2/fio2_'+timepoint].notna()) |
                 (df_ICU['pco2_mmHg_'+timepoint].notna()) | 
                 (df_ICU['niv_'+timepoint].notna()) |
                 (df_ICU['niv_'+timepoint].notna()) |
                 (df_ICU['ecmo_'+timepoint].notna()))), 
               'goldstein_RESP_'+timepoint] = 0
    ### CARDIOVASCULAR ########################################################
    ### goldstein sysbp points
    # dependent on age => create a dictionary with age and bp as key-tuple (key[0], key[1]) and the goldstein points as value
    dictionary = {('.between(0,0.23,inclusive="left")', '<59'):1, #0 - <1 week (0.23 month)
                  ('.between(0.23,1,inclusive="left")', '<79'):1, #1 week (0.23 month) - <1 month (go up to max days of a month to make sure not missing any patients due to changing from _days to _months)
                  ('.between(1,12,inclusive="left")', '<75'):1, #1 month - <12 month (1 year)
                  ('.between(12,72,inclusive="left")', '<74'):1, #1 year - <6 years 
                  ('.between(72,156,inclusive="left")', '<83'):1, #5 years - <13 years 
                  ('>=156', '<90'):1 #>= 13 years
                  }
    for key,value in dictionary.items():
            df_ICU.loc[(eval(f'df_ICU["age_investigation_"+timepoint] {key[0]}')) & (eval(f'df_ICU["sysbp_"+timepoint] {key[1]}')) , 'goldstein_bp_'+timepoint] = value
    ### goldstein cardio points
    df_ICU.loc[(df_ICU['goldstein_bp_'+timepoint] == 1 |
                (df_ICU['adrenaline_'+timepoint].notna()) |
                 (df_ICU['noradrenaline_'+timepoint].notna()) |
                 (df_ICU['dobutamine_'+timepoint].notna()) |
                 (df_ICU['dopamine_'+timepoint] > 5 |
                 ((df_ICU['be_'+timepoint] < -5) & #BE and lactate needs to be present together
                 (df_ICU['lactate_mmol/L_'+timepoint] > 2))
                 )),
               'goldstein_CARDIO_'+timepoint] = 1
    ### goldstein 0 points; define 0 since NaN's will be NaN
    # only if goldstein_CARDIO_<timepoint> still NaN AND
    # at least one value/criteria needs to be present
    df_ICU.loc[((df_ICU['goldstein_CARDIO_'+timepoint].isna()) &
                ((df_ICU['goldstein_bp_'+timepoint].notna()) |
                 (df_ICU['adrenaline_'+timepoint].notna()) | 
                 (df_ICU['noradrenaline_'+timepoint].notna()) |
                 (df_ICU['dobutamine_'+timepoint].notna()) |
                 (df_ICU['dopamine_'+timepoint].notna()) |
                 ((df_ICU['be_'+timepoint].notna()) & #BE and lactate needs to be present together
                 (df_ICU['lactate_mmol/L_'+timepoint].notna())) 
                 )), 
               'goldstein_CARDIO_'+timepoint] = 0
    ### NEURO #################################################################
    ### goldstein neuro points
    df_ICU.loc[df_ICU['gcs_'+timepoint] <= 11, 'goldstein_NEURO_'+timepoint] = 1
    ### goldstein 0 points; define 0 since NaN's will be NaN
    df_ICU.loc[df_ICU['gcs_'+timepoint] > 11, 'goldstein_NEURO_'+timepoint] = 0
    ### HEMAT #################################################################
    ### goldstein hematology points
    df_ICU.loc[((df_ICU['platelets_'+ timepoint] < 80) |
               (df_ICU['inr_'+timepoint] > 2)),
               'goldstein_HEMAT_'+timepoint] = 1
    ### goldstein 0 points; define 0 since NaN's will be NaN
    # only if goldstein_HEMAT_<timepoint> still NaN AND
    # at least one value needs to be present
    df_ICU.loc[((df_ICU['goldstein_HEMAT_'+timepoint].isna()) &
                ((df_ICU['platelets_'+timepoint].notna()) |
                 (df_ICU['inr_'+timepoint].notna()) 
                 )), 
               'goldstein_HEMAT_'+timepoint] = 0
    ### RENAL #################################################################
    ### goldstein renal points
    # dependent on age => create a dictionary with age and creatinine as key-tuple (key[0], key[1]) and the goldstein points as value
    # borders copied from X script ("2x age-adapted creatinine cut-offs per Goldstein")
    # apparently in [µmol/L]; maybe ask if first category should not include age of 0, and if last category only 13-16 or up to 18
    dictionary = {('.between(0.23,1,inclusive="left")', '>=(2*69)'):1, #1 week (0.23 months) - <1 month
                  ('.between(1,12,inclusive="left")', '>=(2*22)'):1, #1 month - <1 year
                  ('.between(12,36,inclusive="left")', '>=(2*34)'):1, #1 year - <3 year
                  ('.between(36,72,inclusive="left")', '>=(2*50)'):1, #3 year - <6 years 
                  ('.between(72,156,inclusive="left")', '>=(2*58)'):1, #6 years - <13 years 
                  ('>=156', '>=(2*92)'):1 #>= 13 years
                  }
    for key,value in dictionary.items():
        df_ICU.loc[(eval(f'df_ICU["creatinine_µmol/L_"+timepoint] {key[1]}')) & (eval(f'df_ICU["age_investigation_"+timepoint] {key[0]}'))  , 'goldstein_RENAL_'+timepoint] = value
    ### goldstein 0 points; define 0 since NaN's will be NaN
    # only if goldstein_RENAL<timepoint> still NaN AND
    # at least one value needs to be present
    df_ICU.loc[((df_ICU['goldstein_RENAL_'+timepoint].isna()) &
                (df_ICU['creatinine_µmol/L_'+timepoint].notna())
                 ), 
               'goldstein_RENAL_'+timepoint] = 0
    ### HEPATIC ###############################################################
    ### goldstein hepatic points (ALT)
    # dependent on age => create a dictionary with age and ALT as key-tuple (key[0], key[1]) and the goldstein points as value
    # borders copied from X script
    # apparently in [IU/L]; maybe ask if first category should not include age of 0, and if last category only 13-16 or up to 18
    dictionary = {('.between(0.23,12,inclusive="left")', '>=98'):1, #1 week (0.23 months) - <1 year
                  ('.between(12,48,inclusive="left")', '>=58'):1, #1 year - <4 year
                  ('.between(48,84,inclusive="left")', '>=78'):1, #4 year - <7 year
                  ('.between(84,156,inclusive="left")', '>=88'):1, #7 year - <13 years 
                  ('>=156', '>=90'):1 #>= 13 years
                  }
    for key,value in dictionary.items():
        df_ICU.loc[(eval(f'df_ICU["alt_IU/L_"+timepoint] {key[1]}')) & (eval(f'df_ICU["age_investigation_"+timepoint] {key[0]}'))  , 'goldstein_HEPATIC_'+timepoint] = value
    ### goldstein hepatic points (bilirubin)
    # only if goldstein_HEPATIC_<timepoint> still NaN AND
    # not for neonates (<28 days or 1 month, respectively)
    df_ICU.loc[((df_ICU['goldstein_HEPATIC_'+timepoint].isna()) &
                (df_ICU['bilirubin_mg/dL_'+timepoint] >= 4) &
                (df_ICU['age_investigation_'+timepoint] >= 1)), 
               'goldstein_HEPATIC_'+timepoint] = 1
    ### goldstein 0 points; define 0 since NaN's will be NaN
    # only if goldstein_HEPATIC_<timepoint> still NaN AND
    # at least one value needs to be present
    df_ICU.loc[((df_ICU['goldstein_HEPATIC_'+timepoint].isna()) &
                ((df_ICU['alt_IU/L_'+timepoint].notna()) |
                 (df_ICU['bilirubin_mg/dL_'+timepoint].notna())
                 )), 
               'goldstein_HEPATIC_'+timepoint] = 0
    
### correct goldstein points ##################################################
### set <goldstein_variable>_<timepoint> == 0 if for the respective 
### <timepoint> at least three >podium_variable<_<timepoint> must have a 
### real value 
goldstein_variables = ['goldstein_RESP', 'goldstein_CARDIO', 
                       'goldstein_NEURO', 'goldstein_HEMAT',
                       'goldstein_RENAL', 'goldstein_HEPATIC']

for index,row in df_ICU.iterrows(): #row = row (patient)
    for timepoint in timepoints: #e.g. timepoint='FIRST'
        count_notnan=0
        for variable in goldstein_variables: #e.g. variable='goldstein_NEURO'
            if not math.isnan(row[variable+'_'+timepoint]): #e.g. row['goldstein_NEURO_FIRST'] != NaN
                count_notnan+=1 #count_notnan = number of goldstein_variables per timepoint having a value
        if count_notnan > 2: #you can adjust this number (will be the min #variables that need to be true)
            for variable in goldstein_variables:
                if math.isnan(row[variable+'_'+timepoint]): #replace NaN variables if there are points for other variable at this timepoint
                    df_ICU.loc[index, variable+'_'+timepoint] = 0
    
### calculate goldstein #######################################################
for timepoint in timepoints:
    # alegbra works well with NaN => if one of the terms is NaN, result will be NaN
    df_ICU['goldstein_score_' + timepoint] = (
        df_ICU['goldstein_RESP_' + timepoint] + 
        df_ICU['goldstein_CARDIO_' + timepoint] + 
        df_ICU['goldstein_NEURO_' + timepoint] + 
        df_ICU['goldstein_HEMAT_' + timepoint] + 
        df_ICU['goldstein_RENAL_' + timepoint] + 
        df_ICU['goldstein_HEPATIC_' + timepoint]
    )

###############################################################################
### PHOENIX ###################################################################
###############################################################################
for timepoint in timepoints:
    # since multiple variable levels rating the same subscore, there is the risk
    # that a patient match for the same subscore to different values
    # solution: start giving the lower points and to the end the higher scores,
    # so the higher scores will overwrite the lowers if present
    ### RESPIRATORY ###########################################################
    ### phoenix respiratory points
    df_ICU.loc[(df_ICU['po2/fio2_'+timepoint] >=400) |
               ((df_ICU['spo2/fio2_'+timepoint] >=292) &
                (df_ICU['spo2_'+timepoint] <=97)), 
               'phoenix_RESP_'+timepoint] = 0
    df_ICU.loc[((df_ICU['po2/fio2_'+timepoint] <400) & 
                (df_ICU['respsup_'+timepoint] == 'YES')) |
               ((df_ICU['spo2/fio2_'+timepoint] <292) &
                (df_ICU['spo2_'+timepoint] <=97) &
                (df_ICU['respsup_'+timepoint] == 'YES')), 
               'phoenix_RESP_'+timepoint] = 1
    df_ICU.loc[((df_ICU['po2/fio2_'+timepoint] <=200) & 
                (df_ICU['iv_'+timepoint] == 'YES')) |
               ((df_ICU['spo2/fio2_'+timepoint] <=220) &
                (df_ICU['spo2_'+timepoint] <=97) &
                (df_ICU['iv_'+timepoint] == 'YES')), 
               'phoenix_RESP_'+timepoint] = 2
    df_ICU.loc[((df_ICU['po2/fio2_'+timepoint] <100) & 
                (df_ICU['iv_'+timepoint] == 'YES')) |
               ((df_ICU['spo2/fio2_'+timepoint] <148) &
                (df_ICU['spo2_'+timepoint] <=97) &
                (df_ICU['iv_'+timepoint] == 'YES')), 
               'phoenix_RESP_'+timepoint] = 3
    ### CARDIOVASCULAR ########################################################
    # need to calculate CARDIO subscore even if two out of three subvariables (used 
    # in the subscore) are missing; therefore keep NaN in subvariables until
    # you calculate the CARDIO subscore, and if then at least one subvariable value
    # present, set the respective NaN subvariables to 0
    # NOTE: catechol_numb was decided to never be NaN but substituted by 0 
    # (since 90% or more of NaN catechols are meant to be 0)
    # THEREFORE: CARDIO subscore always has one out of three subvariables present
    # and following every NaN subvariable will be replaced by 0; can do this directly
    # phoenix vasoactiva points
    df_ICU.loc[(df_ICU['catechol_numb_'+timepoint] == 0), 'phoenix_catechol_'+timepoint] = 0 #don't need to specify NaN, since catechol_numb already takes 0 for NaN values
    df_ICU.loc[(df_ICU['catechol_numb_'+timepoint] == 1), 'phoenix_catechol_'+timepoint] = 1
    df_ICU.loc[(df_ICU['catechol_numb_'+timepoint] >= 2), 'phoenix_catechol_'+timepoint] = 2
    # phoenix lactate points
    df_ICU.loc[(df_ICU['lactate_mmol/L_'+timepoint] <5) | (np.isnan(df_ICU['lactate_mmol/L_'+timepoint])), 'phoenix_lactate_'+timepoint] = 0
    df_ICU.loc[(df_ICU['lactate_mmol/L_'+timepoint] >=5) & (df_ICU['lactate_mmol/L_'+timepoint] <11), 'phoenix_lactate_'+timepoint] = 1
    df_ICU.loc[(df_ICU['lactate_mmol/L_'+timepoint] >=11), 'phoenix_lactate_'+timepoint] = 2
    # phoenix meanbp points
    # meanbp dependent on age => create a dictionary with age and meanbp as key-tuple (key[0], key[1]) and the phoenix points as value
    dictionary = {('<1', '>30'):1, # <1 month
                  ('.between(1,12,inclusive="left")', '>38'):0, #1 month - <1 year
                  ('.between(12,24,inclusive="left")', '>43'):0, #2 year - <2 year
                  ('.between(24,60,inclusive="left")', '>44'):0, #5 year - <5 years 
                  ('.between(60,144,inclusive="left")', '>48'):0, #5 years - <12 years 
                  ('>=144', '>51'):1, #>= 12 years (anyway filtered for < 18y)
                  ('<1', '.between(17,30)'):1, # <1 month
                  ('.between(1,12,inclusive="left")', '.between(25,38)'):1, #1 month - <1 year
                  ('.between(12,24,inclusive="left")', '.between(31,43)'):1, #2 year - <2 year
                  ('.between(24,60,inclusive="left")', '.between(32,44)'):1, #5 year - <5 years 
                  ('.between(60,144,inclusive="left")', '.between(36,48)'):1, #5 years - <12 years 
                  ('>=144', '.between(38,51)'):1, #>= 12 years (anyway filtered for < 18y)
                  ('<1', '<17'):1, # <1 month
                  ('.between(1,12,inclusive="left")', '<25'):2, #1 month - <1 year
                  ('.between(12,24,inclusive="left")', '<31'):2, #2 year - <2 year
                  ('.between(24,60,inclusive="left")', '<32'):2, #5 year - <5 years 
                  ('.between(60,144,inclusive="left")', '<36'):2, #5 years - <12 years 
                  ('>=144', '<38'):1 #>= 12 years (anyway filtered for < 18y)
                  }
    for key,value in dictionary.items():
        df_ICU.loc[(eval(f'df_ICU["age_investigation_"+timepoint] {key[0]}')) & (eval(f'df_ICU["meanbp_"+timepoint] {key[1]}')), 'phoenix_meanbp_'+timepoint] = value
    df_ICU.loc[np.isnan(df_ICU['meanbp_'+timepoint]), 'meanbp_'+timepoint] = 0 #set NaN to 0 (read header paragraph)
    # phoenix cardio points
    df_ICU['phoenix_CARDIO_'+timepoint] = df_ICU['phoenix_catechol_'+timepoint] + df_ICU['phoenix_lactate_'+timepoint] + df_ICU['phoenix_CARDIO_'+timepoint]
    #######correct phoenix cardio points calculation, maybe with loc ask Chatgpt
    #######read again phoenix section to understand nan/0 thingy
    #process further steps with phoenix, read fussnoten in pdf
    
    
    
    
    
###############################################################################
###sort newly generated columns within a cluster and keep them at the end of the dataframe
#create order for new columns
suffixes = ['BASELINE', 'FIRST', '24', 'SECOND', 'THIRD', 'NULL', 'unit'] #only 24 instead of FRB_24, since will cut with the '_'
prefixes = ['date_investigation', 'age_investigation', 'age_investigation_days', 'location', 'gcs', 'pupils', 
            'lactate_org', 'lactate_mmol/L', 'meanbp', 'sysbp', 'hr', 'creatinine_org', 'creatinine_µmol/L', 'creatinine_mg/dL', 
            'po2_org', 'po2_mmHg', 'fio2', 'po2/fio2', 'pco2_org', 'pco2_mmHg', 'spo2', 'spo2/fio2', 'iv', 'niv', 'wbc',
            'neutro', 'lympho', 'platelets', 'inr', 'be', 'respsup', 'bilirubin_org', 'bilirubin_mg/dL', 'alt_org', 'alt_IU/L', 
            'adrenaline','noradrenaline', 'dopamine', 'dobutamine', 'vasopressin', 'milrinone', 'vis', 'catechol_numb', 'ecmo', 'ecmo_va', 
            'rrt', 'pelod_gcs', 'pelod_pupils', 'pelod_lactate','pelod_meanbp', 'pelod_creatinine', 'pelod_po2/fio2', 
            'pelod_pco2', 'pelod_iv', 'pelod_wbc', 'pelod_platelets', 'pelod_CNS', 'pelod_CVS', 'pelod_RENAL', 
            'pelod_RESP', 'pelod_HEM', 'pelod_score', 'pelod_number_orgdys', 'psofa_respiratory','psofa_coagulation', 
            'psofa_hepatic', 'psofa_cardiovascular', 'psofa_neurologic', 'psofa_renal', 'psofa_score', 'podium_NEURO', 
            'podium_RESP', 'podium_hr', 'podium_bp', 'podium_vis', 'podium_lactate', 'podium_help', 'podium_CARDIO',
            'podium_RENAL', 'podium_coag_encephal', 'podium_HEPATIC', 'podium_HEMAT', 'podium_COAG', 'podium_IMMUNE',
            'podium_score', 'goldstein_RESP', 'goldstein_bp', 'goldstein_CARDIO', 'goldstein_NEURO', 'goldstein_HEMAT',
            'goldstein_RENAL', 'goldstein_HEPATIC', 'goldstein_score', 'phoenix_RESP', 'phoenix_catechol',
            'phoenix_lactate', 'phoenix_meanbp', 'phoenix_CARDIO'] 

#Sort columns within each prefix group using the custom order
sorted_columns = []
unsorted_columns = []
for prefix in prefixes:
    prefix_columns = [col for col in df_ICU.columns if col.startswith(prefix)]
    sorted_prefix_columns = sorted(prefix_columns, key=lambda col: (suffixes.index(col.split('_')[-1]), col))
    sorted_columns.extend(sorted_prefix_columns)
unsorted_columns.extend([col for col in df_ICU.columns if col not in sorted_columns])

#Reorder the DataFrame columns
df_ICU = df_ICU[unsorted_columns+sorted_columns]
###############################################################################

###############################################################################
###export dataframe to excel###################################################
df_ICU.to_excel('PICU_Junetest.xlsx', index=False)
###############################################################################

