# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
###############################################################################
### import packages ###########################################################
import win32com.client
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
###############################################################################

### REMOVE PASSWORD ###########################################################
# load data spreadsheet [excel]
# remove password
# save as excel spreadsheet (same name = rewriting) [excel]
def Remove_password_xlsx(filename, pw_str):
    #it takes long, but if too long, file path is probably wrong
    xcl = win32com.client.Dispatch("Excel.Application")
    wb = xcl.Workbooks.Open(filename, False, False, None, pw_str)
    xcl.DisplayAlerts = False
    wb.SaveAs(filename, None, '', '')
    xcl.Quit() 
    
#Remove_password_xlsx("H:\Datamanagement\DIAMONDS\Identify missing data\DIAMONDS_ED_PIC_June12_2024.xlsx", "")
###############################################################################

### LOAD DATA & QC ############################################################
# load data spreadsheet [excel]
# correct units (according to lab unit CRF [excel], and default units[dictionary from ECRF])
# save as excel spreadsheet (new name) [excel, '_UNITScorr.xlsx']
# create smaller df to proceed
def dataframe (path, export):
    global file, df_original,df, df_ICU, df_notICU
    #load original data
    file=path
    df_original = pd.read_excel(path) #original table
    #correct units
    df_units = pd.read_excel('Labunits_MH.xlsx')
    units_dict = df_units.set_index('SITE_CODE').to_dict(orient='index') #create dictionary from units-file, in form {sitecode1: {'WHITE_CELL_UNIT' : 'g/dl'}, sitecode2:{x:y},...}
    for column in df_units.columns: #go through all columns and check which are to correct with lab units
        if df_original[column].isnull().sum()  >= 1 and column in str(units_dict): #select columns that have NaNs and that are in unit-dictionary
            for index, row in df_original.iterrows(): #iterate over rows of df_ICU (in order to select missing values of selected column)
                if pd.isnull(row[column]): #screen for rows with NaN in the selected column
                    sitecode = row['SITE_CODE'] #identify the sitecode of this row
                    if str(sitecode) in str(units_dict): #only correct units; if sitecode is in unit-dictionary....
                        if column in str(units_dict[sitecode]): #...and if column is in unit-dictionary
                            df_original.loc[index, column] = units_dict[sitecode][column] #replace NaN value of the selected column/row by the respective unit from the unit-dictionary
    #set default units for missing units
    units_default_dict = {'HAEMOGLOBIN_UNIT': 'g/L', 'WHITE_CELLS_UNIT': '10^9/L', 'PLATELETS_UNIT': '10^9/L', 
                          'NEUTROPHILS_UNIT': '10^9/L', 'LYMPHOCYTES_UNITS': '10^9/L', 'MONOCYTES_UNIT': '10^9/L', 
                          'EOSINOPHILS_UNITS': '10^9/L', 'FIBRINOGEN_UNITS': '10^9/L','UREA_UNITS': 'mmol/L', 
                          'CREATININE_UNITS': 'µmol/L', 'ALT_UNITS': 'IU/L', 'BILIRUBIN_UNITS': 'µmol/L', 
                          'ALBUMIN_UNITS': 'g/L','VITAMIN_D_UNITS': 'nmol/L', 'CRP_UNITS': 'mg/L', 'PCT_UNITS': 'ng/mL', 
                          'FERRITIN_UNITS': 'µg/L', 'TROP_T_UNITS': 'ng/L', 'D_DIMER_UNITS': 'ng/mL','INR_UNITS': 'ng/mL', 
                          'BNP_NT_UNITS': 'pg/mL', 'LDH_UNITS': 'IU/L', 'CK_UNITS': 'IU/L', 'SCD_25_UNITS': '[]', 
                          'BASE_EXCESS_UNITS': 'mmol/L', 'LACTATE_UNITS': 'mmol/L', 'Arterial_PO2_UNITS': 'kPa', 
                          'PO2_UNITS': 'kPa', 'ARTERIAL_PCO2_UNITS': 'kPa'}
    for column in df_original.columns:
        if column.endswith(('_UNIT', '_UNITS')):
            if column in units_default_dict:
                df_original[column].fillna(units_default_dict[column], inplace=True)
    #export corrected original data to new file (take only this from now !)
    if export == 'YES':
        df_original.to_excel(file[:-5]+'_UNITScorr.xlsx', index=False)
    #create dataframes to procede
    df = df_original.loc[:,['UNIQUE_PATIENT_ID', 'SITE_CODE', 'DATETIME_FIRST_HOSPITAL', 'ITU', 'DATETIME_ITU', 
                            'DATETIME_FRB', 'TEMPERATURE', 'HEART_RATE', 'RESP_RATE', 'BP_SYSTOLIC', 'OXYGEN_SATURATION',
                            'SATURATION_MEASURED','CENTRAL_CAP_REFILL', 'ILL_APPEARANCE', 'CONSCIOUS_LEVEL', 
                            'CONCIOUS_LEVEL_DETAILS', 'MENTAL_TEST_SCORE', 'TIME_POINT', 'DATE_TIME_INVESTIGATIONS', 
                            'TIME_POINT_2=WHITE_CELLS', 'WHITE_CELLS_UNIT', 'TIME_POINT_3=PLATELETS', 'PLATELETS_UNIT', 
                            'TIME_POINT_4=NEUTROPHILS','NEUTROPHILS_UNIT', 'TIME_POINT_5=LYMPHOCYTES', 
                            'LYMPHOCYTES_UNITS', 'TIME_POINT_8=FIBRINOGEN', 'FIBRINOGEN_UNITS', 'TIME_POINT_9=PT', 
                            'PT_UNITS', 'TIME_POINT_11=CREATININE', 'CREATININE_UNITS', 'TIME_POINT_12=ALT', 
                            'ALT_UNITS', 'TIME_POINT_13=BILIRUBIN', 'BILIRUBIN_UNITS', 'TIME_POINT_26=BASE_EXCESS',
                            'BASE_EXCESS_UNITS', 'TIME_POINT_27=LACTATE', 'LACTATE_UNITS', 'TIME_POINT_28=Arteial_PO2',
                            'Arterial_PO2_UNITS', 'TIME_POINT_29=PO2', 'PO2_UNITS', 'TIME_POINT=DATE_TIME_INVESTIGATIONS',
                            'TIME_POINT_1=PATIENT_LOCATION', 'TIME_POINT_2=VENTILATION', 'TIME_POINT_3=O2_SATURATION',
                            'TIME_POINT_4=FIO2_O2_FLOW', 'FIO2_O2_FLOW_UNITS', 'TIME_POINT_5=HEART_RATE', 
                            'TIME_POINT_6=SYSTOLIC_BP', 'TIME_POINT_7=DIASTOLIC_BP', 'TIME_POINT_8=MEN_BP',
                            'TIME_POINT_9=REPIRATORY_RATE', 'TIME_POINT_10=CAPILLARY_REFILL', 
                            'TIME_POINT_11=PUPILS_DIALATED', 'TIME_POINT_12=GCS_AVPU', 'GCS_AVPU_UNITS', 
                            'TIME_POINT_13=INOTROPES', 'TIME_POINT_20=ECMO', 'TIME_POINT_21=RENAL_REPLACEMENT',
                            'TIME_POINT.1', 'TREATMENT', 'TIME_POINT_1=TREATMENT_NAME', #.1 takes first column with that name 
                            'TIME_POINT_3=TREATMENT_DETAILS_4', 'TREATMENT_NAME_2=TREATMENT_DETAILS', 
                            'SURGICAL_OPERATION_DATE', 'SURGICAL_OPERATION_DETAILS','REQUIRED_BYPASS', 'ADMITTED_ICU_ED',
                            'DIED_ED', 'DATETIME_ICU_DISCHARGE', 'DATETIME_DEATH', 'OXYGEN_Days', 'NIV', 'NIV_days', 
                            'INVASIVE_VENT', 'INVASIVE_VENT_days', 'ICU', 'ICU_days', 'INOTROPES', 'INOTROPES_days', 
                            'ECMO', 'ECMO_days', 'HAEMOFILTRATION', 'HAEMOFILTRATION_days', 'PATIENT_DIED']]
    df_ICU = df.loc[(df['ICU'] == "YES")  & (df['ITU'] == "YES")]
    df_notICU = df.loc[(df['ICU'] == "NO")  & (df['ITU'] == "NO")]
    
#dataframe("DIAMONDS_ED_PIC_June12_2024.xlsx", 'YES')
###############################################################################

###############################################################################
### PLOT QC ###################################################################
###############################################################################

### Nan's #####################################################################
def plot_nas100(df: pd.DataFrame, saving):
    if df.isnull().sum().sum() != 0:
        na_df = (df.isnull().sum() / len(df)) * 100
        
        ###deal with matrix missing data that is not NA
        #create a list with column names that containe BASELINE in column, meaning they need to be checked beyonde na
        def find_columns_with_value(df, value):
            global columns_with_value
            columns_with_value=[]
            for column in df.columns:
                if df[column].astype(str).str.contains(value).any():
                    columns_with_value.append(column)
        find_columns_with_value(df_ICU, 'BASELINE') 
        '''#add per missing BASELINE/FIRST/FRB_24 (all need to be present): Na +=1 for respective variable
        for col in columns_with_value: #colum by column (to be checked)
            for i in range(0, len(df)):
                if type(df[col].iat[i]) == str:
                    #for 4x treatment columns, handling it differently
                    if col not in ['TIME_POINT.1', 'TREATMENT', 'TIME_POINT_1=TREATMENT_NAME', 'TREATMENT_NAME_2=TREATMENT_DETAILS', 'TIME_POINT_3=TREATMENT_DETAILS_4']:
                        if "BASELINE" not in df[col].iat[i] or "FIRST" not in df[col].iat[i] or "FRB_24" not in df[col].iat[i]:
                            na_df[col] += 1/len(df)*100
                    #treatment columns
                    else:
                        if 'ANTIBIOTIC' in df['TIME_POINT_1=TREATMENT_NAME'].iat[i] or 'STEROID' in df['TIME_POINT_1=TREATMENT_NAME'].iat[i]: #check only anti + stero treatments
                            if "BASELINE" not in df[col].iat[i] or "FIRST" not in df[col].iat[i] or "FRB_24" not in df[col].iat[i]:
                                na_df[col] += 1/len(df)*100'''
        ###
        #create a list with column names that have an '_days' analogue (take column name with _days)
        def find_columns_with_days(df):
            global columns_with_days
            columns_with_days = []
            for column in df.columns:
                if column + '_days' in df.columns:
                    columns_with_days.append(column + '_days')
        find_columns_with_days(df_ICU)
        #subtract Na -= 1 from variables with _days that have in their normal analogue the value 'NO'
        for col in columns_with_days:
            for i in range(0, len(df)):
                if df[col[:-5]].iat[i] == 'NO' and pd.isna(df[col].iat[i]):
                    na_df[col] -= 1/len(df)*100
        ###
        #No NaN for DATETIME_DEATH if PATIENT_DIED == 'NO'
        #No NaN for surgery variables if all surgery variables are empty
        for i in range(0,len(df)):
            if df['PATIENT_DIED'].iat[i] == 'NO' and pd.isna(df['DATETIME_DEATH'].iat[i]):
                na_df['DATETIME_DEATH'] -= 1/len(df)*100
            if pd.isna(df['SURGICAL_OPERATION_DATE'].iat[i]) and pd.isna(df['SURGICAL_OPERATION_DETAILS'].iat[i]) and pd.isna(df['REQUIRED_BYPASS'].iat[i]):
                na_df['SURGICAL_OPERATION_DATE'] -= 1/len(df)*100
                na_df['SURGICAL_OPERATION_DETAILS'] -= 1/len(df)*100
                na_df['REQUIRED_BYPASS'] -= 1/len(df)*100
            #if 'ANTIBIOTIC' not in df['TIME_POINT_1=TREATMENT_NAME'].iat[i] or 'STEROID' not in df['TIME_POINT_1=TREATMENT_NAME'].iat[i]:
        ###############################################
        
        #sort bars descending starting from bottom
        na_df = na_df.drop(na_df[na_df == 0].index).sort_values(ascending=False)
        #na_df -> missing (new dataframe, just with new column name and values are rounded to one decimal)
        missing = pd.DataFrame({'% Missing (#Patients tot: ' +str(len(df)) +')':round(na_df, 1)})
        #plot
        ax = missing.plot(kind = "barh", figsize=(16,18), color="rosybrown")
        ax.bar_label(ax.containers[0]) #label each bar with the respective value
        ax.legend().get_frame().set_facecolor('white')

        #save as png:
        if saving == 'YES':
            plt.savefig('Missings_NaPlot%.png', format='png', dpi=1200, bbox_inches="tight")

#plot_nas100(df_ICU, '')

### Crossvalidation ###########################################################
def crossvalid_notICU(df: pd.DataFrame):
    if df.isnull().sum().sum() != 0:
        na_df = (df.isnull().sum())
        ###deal with NO Data
        for i in range(0, len(df)):
            if df['ADMITTED_ICU_ED'].iat[i] == 'NO':
                na_df['ADMITTED_ICU_ED'] += 1
        ###
        na_df = na_df[['DATETIME_ITU', 'ADMITTED_ICU_ED', 'DATETIME_ICU_DISCHARGE', 'ICU_days']]
        missing = pd.DataFrame({'#Missing out of ' +str(len(df)) :na_df})
        ax = missing.plot(kind = "barh", figsize=(16,10))
        ax.bar_label(ax.containers[0])
        plt.show()
        
#crossvalid_notICU(df_notICU)

def crossv_ventIV(df: pd.DataFrame):
    global df_ventIV, INVASIVE_VENTwrong, INVASIVE_VENTmissing
    #select columns/variables I want:
    df_ventIV = df[['UNIQUE_PATIENT_ID', 'SITE_CODE', 'INVASIVE_VENT', 'TIME_POINT_2=VENTILATION']]
    #define possible conditions for INVASIVE_VENT ('Unk' created for data entry 'Unk' and 'NaN'):
    conditions = [(df_ventIV['INVASIVE_VENT'] == 'YES'), (df_ventIV['INVASIVE_VENT'] == 'NO'), (df_ventIV['INVASIVE_VENT'] == 'Unk')]
    choices = ['Yes', 'No', 'Unk']
    #create 2x new columns that will be plot:
    df_ventIV['INVASIVE_VENTcat'] = np.select(conditions, choices, default='Unk') #with default = 'Unkn' everything else goes to 'Unkn', also NaN
    df_ventIV['TIME_POINT_2=VENTILATIONcat'] = np.where(df['TIME_POINT_2=VENTILATION'].str.contains('Invasive'), 'Invasive', 'Other')
    #plot:
    #loc used for oder on x-axis
    ax = df_ventIV.groupby(['INVASIVE_VENTcat', 'TIME_POINT_2=VENTILATIONcat']).size().unstack().loc[['Yes', 'No', 'Unk']].plot(kind='bar', figsize=(8,10), stacked=True, color=["lightskyblue", "lightgrey"])
    #create x-labels:
    ax.bar_label(ax.containers[0], label_type='center')
    ax.bar_label(ax.containers[1], label_type='center')
    #sort legend:
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], title='TIME_POINT_2=VENTILATIONcat')
    #flag patients to send back:
    df_ventIV.loc[(df_ventIV['INVASIVE_VENTcat'] == 'No') & (df_ventIV['TIME_POINT_2=VENTILATIONcat'] == 'Invasive'), 'Flag'] = 1
    df_ventIV.loc[df_ventIV['INVASIVE_VENTcat'] == 'Unk', 'Flag'] = 2
    #generate lists of patients to send back:
    INVASIVE_VENTwrong = df_ventIV[['UNIQUE_PATIENT_ID', 'SITE_CODE']].loc[df_ventIV['Flag'] == 1].values.tolist()
    INVASIVE_VENTmissing = df_ventIV[['UNIQUE_PATIENT_ID', 'SITE_CODE']].loc[df_ventIV['Flag'] == 2].values.tolist()

#crossv_ventIV(df_ICU)

def crossv_ventNIV(df: pd.DataFrame):
    global df_ventNIV, NIVwrong, NIVmissing
    #select columns/variables I want:
    df_ventNIV = df[['UNIQUE_PATIENT_ID', 'SITE_CODE', 'NIV', 'TIME_POINT_2=VENTILATION']]
    #define possible conditions for NIV ('Unk' created for data entry 'Unk' and 'NaN'):
    conditions = [(df_ventNIV['NIV'] == 'YES'), (df_ventNIV['NIV'] == 'NO'), (df_ventNIV['NIV'] == 'Unk')]
    choices = ['Yes', 'No', 'Unk']
    #create 2x new columns that will be plot:
    df_ventNIV['NIVcat'] = np.select(conditions, choices, default='Unk')
    df_ventNIV['TIME_POINT_2=VENTILATIONcat'] = np.where(df['TIME_POINT_2=VENTILATION'].str.contains('NIV'), 'NIV', 'Other')
    #plot:
    #loc used for oder on x-axis
    ax= df_ventNIV.groupby(['NIVcat', 'TIME_POINT_2=VENTILATIONcat']).size().unstack().loc[['Yes', 'No', 'Unk']].plot(kind='bar', figsize=(8,10), stacked=True, color=["yellowgreen", "lightgrey"])
    #create x-labels:
    ax.bar_label(ax.containers[0], label_type='center')
    ax.bar_label(ax.containers[1], label_type='center')
    #sort legend:
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], title='TIME_POINT_2=VENTILATIONcat')
    #flag patients to send back:
    df_ventNIV.loc[(df_ventNIV['NIVcat'] == 'No') & (df_ventNIV['TIME_POINT_2=VENTILATIONcat'] == 'NIV'), 'Flag'] = 1
    df_ventNIV.loc[df_ventNIV['NIVcat'] == 'Unk', 'Flag'] = 2
    #generate lists of patients to send back:
    NIVwrong = df_ventNIV[['UNIQUE_PATIENT_ID', 'SITE_CODE']].loc[df_ventNIV['Flag'] == 1].values.tolist()
    NIVmissing = df_ventNIV[['UNIQUE_PATIENT_ID', 'SITE_CODE']].loc[df_ventNIV['Flag'] == 2].values.tolist()

#crossv_ventNIV(df_ICU)

def crossv_inotrp(df: pd.DataFrame):
    global df_inotrp, INOTROPESwrong, INOTROPESmissing
    #select columns/variables I want:
    df_inotrp = df[['UNIQUE_PATIENT_ID', 'SITE_CODE', 'INOTROPES', 'TIME_POINT_13=INOTROPES']]
    #define possible conditions for INOTROPES ('Unk' created for data entry 'Unk' and 'NaN'):
    conditions = [(df_inotrp['INOTROPES'] == 'YES'), (df_inotrp['INOTROPES'] == 'NO'), (df_inotrp['INOTROPES'] == 'Unk')]
    choices = ['Yes', 'No', 'Unk']
    #create 2x new columns that will be plot:
    df_inotrp['INOTROPEScat'] = np.select(conditions, choices, default='Unk')
    df_inotrp['TIME_POINT_13=INOTROPEScat'] = np.where(df['TIME_POINT_13=INOTROPES'].str.contains('YES'), 'Yes', 'Other')
    #plot:
    #loc used for oder on x-axis
    ax= df_inotrp.groupby(['INOTROPEScat', 'TIME_POINT_13=INOTROPEScat']).size().unstack().loc[['Yes', 'No', 'Unk'], ['Yes', 'Other']].plot(kind='bar', figsize=(8,10), stacked=True, color=["orange", "lightgrey"]) #sort=False to keep row order WITHIN group
    #create x-labels:
    ax.bar_label(ax.containers[0], label_type='center')
    ax.bar_label(ax.containers[1], label_type='center')
    #sort legend:
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], title='TIME_POINT_13=INOTROPEScat')
    #flag patients to send back:
    df_inotrp.loc[(df_inotrp['INOTROPEScat'] == 'No') & (df_inotrp['TIME_POINT_13=INOTROPEScat'] == 'Yes'), 'Flag'] = 1
    df_inotrp.loc[df_inotrp['INOTROPEScat'] == 'Unk', 'Flag'] = 2
    #generate lists of patients to send back:
    INOTROPESwrong = df_inotrp[['UNIQUE_PATIENT_ID', 'SITE_CODE']].loc[df_inotrp['Flag'] == 1].values.tolist()
    INOTROPESmissing = df_inotrp[['UNIQUE_PATIENT_ID', 'SITE_CODE']].loc[df_inotrp['Flag'] == 2].values.tolist()

#crossv_inotrp(df_ICU)
###############################################################################

###############################################################################
### MAILING-LIST ##############################################################
###############################################################################

# create empty df as template for mailing-list excel [df]
# load Sitecodes excel [excel]
# merge df_sites & df_mailing
# save Mailing-List with Sitdecodes to excel [excel]
def mailing(excel_sitecodes, saving):
    # !!!! need to have crossvalidations before running for global parameters !!!
    global Mailing
    #Create dictionary of all problem-lists:
    problem_dict = {'INVASIVE_VENTwrong': INVASIVE_VENTwrong, 'INVASIVE_VENTmissing': INVASIVE_VENTmissing, 'NIVwrong': NIVwrong, 'NIVmissing': NIVmissing, 'INOTROPESwrong': INOTROPESwrong, 'INOTROPESmissing': INOTROPESmissing}
    #Concatenate all sub-lists into one big list (problem_list):
    problem_list = [item for sublist in problem_dict.values() for item in sublist]
    #Get all unique sitecodes in the problem_list as a new list:
    sitecodes_list = sorted(set([x[1] for x in problem_list]))
    #Create an empty data frame with the sitecodes as the index and the list names as columns:
    df_mailing = pd.DataFrame(index=sitecodes_list, columns=problem_dict.keys())
    df_mailing = df_mailing.fillna('')
    #For each key and patient_sitecode in the problem_list, iterate over the sitecode_list and append patients to the list corresponding to the sitecode:
    for key, value in problem_dict.items():
        for patient_site in value:
            for i in sitecodes_list:
                if patient_site[1] == i:
                    if df_mailing.loc[i, key] == '':
                        df_mailing.loc[i, key] = str(patient_site[0])
                    else:
                        df_mailing.loc[i, key] += ', ' + str(patient_site[0])
    #Fill empty cells with NaN:
    df_mailing = df_mailing.replace('', pd.NA)
    #Expand index to multiindex sitecode + sitename, with the sitename originating from another excel:
    df_sites = pd.read_excel(excel_sitecodes)
    df_mailing.reset_index(inplace=True) #set sitecode index to normal column with column title 'index'
    df_mailing = df_mailing.rename(columns={'index':'Site code'}) #rename index-column for merging
    Mailing = pd.merge(df_mailing, df_sites, on='Site code', how='left') #
    Mailing = Mailing.set_index(['Site code', 'Study site (as at 26-01-2021)'])
    #save Mailing to an excel file:
    if saving == 'YES':
        Mailing.to_excel('Mailinglist_Dec23.xlsx')

#mailing('Sitecodes_MH.xlsx', '')
###############################################################################

            