# -*- coding: utf-8 -*-
"""
Created on Fri Jan 19 11:03:26 2024

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
import math
### import variables ##########################################################
from DIAMONDS_PELOD_PSOFA_PODIUM_GOLD_reviewed import df_ICU, df_original #//// ADAPT ! /// 
###############################################################################
'''
#not every time; just needs generated excel 'UNITS_corr.xlsx''
### run QC Script first #######################################################
script_directory_qc = r'H:\Datamanagement\DIAMONDS\Identify missing data'
script_name_qc = 'DIAMONDS_EDPIC_QC.py'
subprocess.run(['python', script_name_qc], check=True, cwd=script_directory_qc)
'''
#every time; since needs variables
### run Score Script first ####################################################
script_directory_scores = r'H:\Datamanagement\DIAMONDS\Organdysfunction'
script_name_scores = 'DIAMONDS_PELOD_PSOFA_PODIUM_GOLD_reviewed.py' #//// ADAPT ! /// 
subprocess.run(['python', script_name_scores], check=True, cwd=script_directory_scores)
###############################################################################

###############################################################################
### PLOT PELOD ################################################################
###############################################################################
#sns.set_theme(style=None)
score_list = ['pelod', 'psofa', 'podium', 'goldstein'] #//// ADAPT ! /// 


### PELOD Scores / Mortality ##################################################
###prepare data
#latest score
for index,row in df_ICU.iterrows():
    for timepoint in ['BASELINE', 'FIRST', 'FRB_24', 'SECOND', 'THIRD']:
        for score in score_list:
            if not math.isnan(row[f'{score}_score_{timepoint}']):
                df_ICU.loc[index,f'{score}_score_latest'] = row[f'{score}_score_{timepoint}']
#Died, #Patient
df_ICU['Died'] = 0
df_ICU['Patient'] = 1
df_ICU.loc[df_ICU['PATIENT_DIED'] == 'YES', 'Died'] = 1
df_melt_dict = {}
#df_melt grouping according latest score -> checking how many patients, died etc.
#dictionary containing df_melt for each score (can access them using keys like 'df_melt_pelod') 
for score in score_list:
    #f.e.g.: df_melt_dict[f'df_melt_{score}'] == df_melt_pelod
    df_melt_dict[f'df_melt_{score}'] = df_ICU.groupby([f'{score}_score_latest']).aggregate({'Patient': 'count', 'Died': 'sum'}).reset_index()
    df_melt_dict[f'df_melt_{score}']['Died_%'] = df_melt_dict[f'df_melt_{score}']['Died']/df_melt_dict[f'df_melt_{score}']['Patient']*100

###plot Score / Mortality
def plot_mortality(df_melt_score, score, saving):
    plt.figure(figsize=(10,6))
    g = sns.barplot(data=df_melt_score, x=f'{score}_score_latest', y='Died_%', palette="Blues_d")
    g.set_yticks([0,15,30,45,60])
    g.set_xticklabels(df_melt_score[f'{score}_score_latest'].unique().astype(int)) #makes a tick for every unique value in pelod_score_latest column etc.
    #g.set_xticklabels([0,1,2,3,4,5,6,7,8,9,10,11,12,13])
    g.set_ylabel("Died [%]")
    g.set_xlabel(f"{score.upper()} Score")
    sns.despine(top=True, right=True,bottom=True)
    #annotate bars with 'absolute number died / total'
    ax = g.axes #if it's a FacetGrid you call it by g.ax
    for i, bar in enumerate(ax.patches):
        height = bar.get_height()
        ax.annotate(str(df_melt_score['Died'].iloc[i]) + '/' + str(df_melt_score['Patient'].iloc[i]), (bar.get_x() + bar.get_width() / 2, height+0.3), color='grey', ha='center', va='bottom', fontsize=8)
    #save plot
    if saving == 'YES':
        plt.savefig('PELOD_Mortality_PICU_AUG.png', format='png', dpi=1200, bbox_inches="tight")

#plot_mortality(df_melt_dict['df_melt_pelod'], 'pelod', '')
#plot_mortality(df_melt_dict['df_melt_psofa'], 'psofa', '')
#plot_mortality(df_melt_dict['df_melt_podium'], 'podium', '')
#plot_mortality(df_melt_dict['df_melt_goldstein'], 'goldstein', '')

### Specificity / Sensitivity #################################################
###prepare data
for score in score_list:
    df_melt_score = df_melt_dict[f'df_melt_{score}'] #///rename to make it easier
    df_melt_score['Alive'] = df_melt_score['Patient'] - df_melt_score['Died'] #will also contain NaN and Unkn from PATIENT_DIED
    df_melt_score = df_melt_score.append(pd.Series(0, index=df_melt_score.columns),ignore_index=True) #0 row at the end to get 1/0 point in the final graph
    df_melt_score['tot_alive'] = sum(df_melt_score['Alive']) #total PICU patients alive having a score (df_ICU_melt), same number for each line
    df_melt_score['tot_died'] = sum(df_melt_score['Died']) #total PICU patients died having a score (df_ICU_melt), same number for each line
    #truepos: total PICU patients died having a score like on the current line or a higher score
    #these patients we will catch if we consider all the patients as dead with the score from the current line or a higher score)
    df_melt_score['truepos'] = 0
    for i in range(0, len(df_melt_score)):
        df_melt_score['truepos'].iloc[i] = df_melt_score['tot_died'].iloc[i] - df_melt_score['Died'].iloc[:i].sum() if i >0 else df_melt_score['tot_died'].iloc[i]
    #falsepos: total PICU patients alive having a score like on the current line or a higher score
    #these patients we will accidently catch if we consider all the patients as dead with the score from the current line or a higher score)
    df_melt_score['falsepos'] = 0
    for i in range(0, len(df_melt_score)):
        df_melt_score['falsepos'].iloc[i] = df_melt_score['tot_alive'].iloc[i] - df_melt_score['Alive'].iloc[:i].sum() if i >0 else df_melt_score['tot_alive'].iloc[i]
    #Sensitivity = truepos/tot_died
    df_melt_score['sensitivity'] =  df_melt_score['truepos']/df_melt_score['tot_died']
    #Specificity = falsepos/tot_alive
    df_melt_score['specificity'] =  df_melt_score['falsepos']/df_melt_score['tot_alive']
    df_melt_score['1-specificity'] = 1- df_melt_score['specificity'] 
    df_melt_dict[f'df_melt_{score}'] = df_melt_score #///rename back (store the altered df within the original)

###plot 1-specificity / sensitivity
def plot_sensitivity(df_melt_score, score, saving):
    plt.figure(figsize=(6,6))
    h = sns.lineplot(data=df_melt_score, y='sensitivity', x='1-specificity')
    h.invert_xaxis()
    h.set_ylabel("Sensitivity")
    h.set_xlabel("Specificity")
    plt.plot([1.025, -0.025], [-0.025, 1.025], color='gray', linestyle='-', linewidth=0.8)
    auc = np.trapz(df_melt_score['sensitivity'], df_melt_score['1-specificity'])
    # Calculate the standard error of the AUC
    std_err = sem(df_melt_score['sensitivity'] * df_melt_score['1-specificity'])
    # Calculate the degrees of freedom
    df_melt_score_len = len(df_melt_score) - 1
    # Calculate the t-score for a 95% confidence interval
    t_score = t.ppf(0.975, df_melt_score_len)
    # Calculate the margin of error
    margin_of_error = t_score * std_err
    # Calculate the lower and upper limits of the 95% CI
    lower_limit = auc - margin_of_error
    upper_limit = auc + margin_of_error
    #draw box with AUC within plot
    h.get_figure().text(0.62, 0.175, 'AUC: '+str(np.round(auc,2)) + ' ('+str(np.round(lower_limit,2))+', '+str(np.round(upper_limit,2)) +')',fontsize=10, verticalalignment='top', horizontalalignment='left', bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.3))
    if saving == 'YES':
        plt.savefig('PELOD_AUC_PICU_AUG.png', format='png', dpi=1200, bbox_inches="tight")

#plot_sensitivity(df_melt_dict['df_melt_pelod'], 'pelod', '')
#plot_sensitivity(df_melt_dict['df_melt_psofa'], 'psofa', '')
#plot_sensitivity(df_melt_dict['df_melt_podium'], 'podium', '')
#plot_sensitivity(df_melt_dict['df_melt_goldstein'], 'goldstein', '')

### Facetgrid {SCORE} / Timepoint ###############################################
###prepare data for histplot
df_timepoint_dict = {}
df_timepointgroup_dict = {}
df_timepointgroup2_dict = {}

for score in score_list:
    #put all the timepoints in a column (variable) and all {score}_scores in another column (value)
    #dictionary containing df_timepoint for each score (can access them using keys like 'df_timepoint_pelod') 
    #f.e.g.: df_timepoint_dict[f'df_timepoint_{score}'] == df_melt_pelod
    df_timepoint_dict[f'df_timepoint_{score}'] = df_ICU.groupby([f'{score}_score_latest']).aggregate({'Patient': 'count', 'Died': 'sum'}).reset_index()
    df_timepoint_dict[f'df_timepoint_{score}']['Died_%'] = df_melt_dict[f'df_melt_{score}']['Died']/df_melt_dict[f'df_melt_{score}']['Patient']*100

    df_timepoint_dict[f'df_timepoint_{score}'] = pd.melt(df_ICU, id_vars=['UNIQUE_PATIENT_ID'],value_vars=[f'{score}_score_BASELINE', f'{score}_score_FIRST', f'{score}_score_FRB_24', f'{score}_score_SECOND', f'{score}_score_THIRD'])
    df_timepoint_dict[f'df_timepoint_{score}']['variable'] = df_timepoint_dict[f'df_timepoint_{score}']['variable'].str.split('_').str[-1]
    #rename timepoint 24 to FRB_24
    df_timepoint_dict[f'df_timepoint_{score}'].loc[df_timepoint_dict[f'df_timepoint_{score}']['variable'] == '24', 'variable'] = 'FIRST+24h'

    ###prepare data for barplot with percentage
    #groupby timepoint (column variable) and count how many scores (column value)
    df_timepointgroup_dict[f'df_timepointgroup_{score}'] = df_timepoint_dict[f'df_timepoint_{score}'].groupby(['variable']).aggregate({'value': 'count'}).reset_index()
    #iterate over the df_timepoint_{score} row, take the timepoint from column variable, go to the df_timepointgroup_{score} 
    #and search this timepoint in the column variable, extract the count value on the same row and column value, 
    #go back to df_timepoint_{score} and put the count value in the column #Patients in timepoint on the row you are
    for index,row in df_timepoint_dict[f'df_timepoint_{score}'].iterrows():
        df_timepoint_dict[f'df_timepoint_{score}'].loc[index,'#Patients in timepoint'] = df_timepointgroup_dict[f'df_timepointgroup_{score}'].loc[df_timepointgroup_dict[f'df_timepointgroup_{score}']['variable']==row['variable'], 'value'].values[0]
    #calculate for each patient (row) what percentage /she represents of his group (timepoint & score)
    df_timepoint_dict[f'df_timepoint_{score}']['Percentage'] = np.round(1/df_timepoint_dict[f'df_timepoint_{score}']['#Patients in timepoint']*100,1) #1 since 1 patient per line
    #groupby timepoint (column variable) and score (column value) and sum the percentages for each of this group
    df_timepointgroup2_dict[f'df_timepointgroup2_{score}'] = df_timepoint_dict[f'df_timepoint_{score}'].groupby(['variable', 'value']).aggregate({'Percentage': 'sum'}).reset_index()

###plot histplot
def plot_timepoint(df_timepoint_score, score, saving):
    # Initialize the FacetGrid object
    sns.set_theme(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})
    pal = sns.cubehelix_palette(10, rot=-.25, light=.7)
    g = sns.FacetGrid(df_timepoint_score, row="variable", hue="variable", aspect=8.333, height=0.9, palette=pal) #height=height, width=height*aspect; width=7.5 nice
    
    # Draw the densities in a few steps
    g.map(sns.histplot, "value", discrete=True)
    
    # passing color=None to refline() uses the hue mapping
    g.refline(y=0, linewidth=2, linestyle="-", color=None, clip_on=False)
    
    # Define and use a simple function to label the plot in axes coordinates
    def label(x, color, label):
        ax = plt.gca()
        ax.bar_label(ax.containers[0], fontsize='x-small', color='grey')
        ax.text(0, 0.2, label, fontweight="bold", color=color, ha="left", va="center", transform=ax.transAxes)
    
    g.map(label, "value")
    
    # Set the subplots to overlap
    g.figure.subplots_adjust(hspace=0.3)
    
    # Remove axes details that don't play well with overlap
    g.set_titles("")
    g.set(yticks=[], ylabel="", xlabel=f"{score} Score")
    g.despine(bottom=True, left=True)

    # set variable xticks and -labels
    max_xtick = df_timepoint_score['value'].max()
    min_xtick = df_timepoint_score['value'].min() - 3 if max_xtick >10 else df_timepoint_score['value'].min() - 2 # Set the minimum x-tick value to minus, so we get space in the beginning for labels
    xticks = list(range(int(min_xtick), int(max_xtick) + 1)) #+1 since upper range does exclude limit
    g.set(xticks=xticks) # Set the x-axis ticks and labels dynamically based on the minimum and maximum values
    g.set_xticklabels([str(i) if i >= 0 else '' for i in xticks]) # Label only ticks from 0 to max value, others are labeled as ''
    
    # save plot
    if saving == 'YES':
        plt.savefig(f'{score}_Histplot_Timepoints_AUG.png', format='png', dpi=1200, bbox_inches="tight")

#plot_timepoint(df_timepoint_dict['df_timepoint_pelod'], 'PELOD', '')
#plot_timepoint(df_timepoint_dict['df_timepoint_psofa'], 'PSOFA', '')
#plot_timepoint(df_timepoint_dict['df_timepoint_podium'], 'PODIUM', '')
#plot_timepoint(df_timepoint_dict['df_timepoint_goldstein'], 'GOLDSTEIN', '')

###plot barplot percentage
def plot_timepoint_perc(df_timepointgroup2_score, score, saving):
    global test, test2
    # Initialize the FacetGrid object
    pal = sns.cubehelix_palette(10, rot=-.25, light=.7)
    g = sns.FacetGrid(df_timepointgroup2_score, row="variable", hue="variable", aspect=8.333, height=0.9, palette=pal) #height=height, width=height*aspect; width=7.5 nice
    # Draw the densities in a few steps
    g.map(sns.barplot, 'value',"Percentage")
    # passing color=None to refline() uses the hue mapping
    g.refline(y=0, linewidth=2, linestyle="-", color=None, clip_on=False)
    # Define and use a simple function to label the plot in axes coordinates
    def label(x, color, label):
        ax = plt.gca()
        labels = [f'{val:.1f}%' for val in x]  # Format the labels with '%' symbol
        ax.bar_label(ax.containers[0], labels=labels, fontsize='x-small', color='grey') #fmt: formating with % behind
        ax.text(0, 0.2, label, fontweight="bold", color=color, ha="left", va="center", transform=ax.transAxes)
    g.map(label, "Percentage")
    
    # Set the subplots to overlap
    g.figure.subplots_adjust(hspace=0.3)
    # Remove axes details that don't play well with overlap
    g.set_titles("")
    g.set(yticks=[], ylabel="", xlabel=f"{score} Score")
    g.despine(bottom=True, left=True)
    # Set variable xticks and -labels
    max_xtick = df_timepointgroup2_score['value'].max()
    min_xtick = df_timepointgroup2_score['value'].min() - 3 if max_xtick >10 else df_timepointgroup2_score['value'].min() - 2 # Set the minimum x-tick value to minus, so we get space in the beginning for labels
    xticks = list(range(int(min_xtick), int(max_xtick) + 1)) #+1 since upper range does exclude limit
    g.set(xticks=xticks) # Set the x-axis ticks and labels dynamically based on the minimum and maximum values
    g.set_xticklabels([str(i) if i >= 0 else '' for i in xticks]) # Label only ticks from 0 to max value, others are labeled as ''
    # save plot
    if saving == 'YES':
        plt.savefig(f'{score}_Barplot_Timepoints_AUG.png', format='png', dpi=1200, bbox_inches="tight")

#plot_timepoint_perc(df_timepointgroup2_dict['df_timepointgroup2_pelod'], 'PELOD', '')
#plot_timepoint_perc(df_timepointgroup2_dict['df_timepointgroup2_psofa'], 'PSOFA', '')
#plot_timepoint_perc(df_timepointgroup2_dict['df_timepointgroup2_podium'], 'PODIUM', '')
#plot_timepoint_perc(df_timepointgroup2_dict['df_timepointgroup2_goldstein'], 'GOLDSTEIN', '')

### Age & Gender ##############################################################
###prepare data
for index,row in df_ICU.iterrows():
    for timepoint in ['BASELINE', 'FIRST', 'FRB_24', 'SECOND', 'THIRD']:
        if not math.isnan(row['age_investigation_'+timepoint]):
            df_ICU.loc[index,'age_investigation_latest'] = row['age_investigation_'+timepoint]/12
df_ICU.loc[df_ICU['age_investigation_latest']<0, 'age_investigation_latest'] = float('NaN')

###plot data
def plot_age_gender(df, saving):
    #sns.set_theme(style=None)
    plt.figure(figsize=(10,6))
    palette={'M': sns.cubehelix_palette(dark=.25, light=.75)[0], 'F':sns.cubehelix_palette(dark=.25, light=.75)[2]}
    m = sns.histplot(data=df, x="age_investigation_latest", hue="GENDER", binwidth=0.5, palette=palette, alpha=.6)
    m.spines[['right', 'bottom', 'top']].set_visible(False)
    m.set_xlabel("Age [Years]")
    m.set_ylabel("Number of Patients")
    m.get_legend().legendPatch.set_facecolor('white')
    m.set(xticks=[0,2,4,6,8,10,12,14,16,18])
    m.set_xticklabels([0,2,4,6,8,10,12,14,16,18])
    m.get_figure().text(0.815, 0.725, 'Mean: '+str(np.round(df_ICU['age_investigation_latest'].mean(),2)),fontsize=11, verticalalignment='top', horizontalalignment='left', bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.3))
    if saving == 'YES':
        plt.savefig('Age_Gender_Histplot_AUG.png', format='png', dpi=1200, bbox_inches="tight")

plot_age_gender(df_ICU, '')

### LOS & Mortality ###########################################################
###prepare data
df_ICU['DATETIME_ITU'] = pd.to_datetime(df_ICU['DATETIME_ITU'])
df_ICU['DATETIME_ICU_DISCHARGE'] = pd.to_datetime(df_ICU['DATETIME_ICU_DISCHARGE'])
df_ICU['LOS'] = df_ICU['DATETIME_ICU_DISCHARGE'] - df_ICU['DATETIME_ITU']
df_ICU['LOS'] = df_ICU['LOS'].dt.days

# Create categories for days difference
#bins = [0, 1, 2, 3, 4, 5, 10, 20, 30, np.inf]  # Define your own bins as needed
#labels = ['<1', '1-2', '2-3', '3-4','4-5','5-10','10-20','20-30', '30+']  # Labels for the categories
bins = [-1, 2, 7, 14, 28, np.inf]  # Define your own bins as needed; -1 since border won't be considered, starts with 0
labels = ['< 2', '2-7', '7-14', '14-28', '28+']  # Labels for the categories

df_ICU['LOS'] = pd.cut(df_ICU['LOS'], bins=bins, labels=labels)

# Group by the categories and calculate mortality percentage
df_ICU_LOS = df_ICU.groupby('LOS')['Died'].mean() * 100
df_ICU_LOS = df_ICU_LOS.reset_index()

###plot LOS / Mortality
def plot_los_mortality(df, saving):
    plt.figure(figsize=(6.5,5))
    n = sns.barplot(data=df, x='LOS', y='Died', palette=sns.cubehelix_palette()[1:])
    #g.set_yticks([0,20,40,60,80,100])
    #g.set_xticklabels([0,1,2,3,4,5,6,7,8,9,10,11,12,13])
    n.set_ylabel("Died [%]")
    n.set_xlabel("LOS [Days]")
    sns.despine(top=True, right=True,bottom=True)
    #annotate bars with 'absolute number died / total'
    ax = n.axes #if it's a FacetGrid you call it by g.ax
    for i, bar in enumerate(ax.patches):
        height = bar.get_height()
        ax.annotate(str(np.round(df_ICU_LOS['Died'].iloc[i],2)) +' %', (bar.get_x() + bar.get_width() / 2, height+0.05), color='grey', ha='center', va='bottom', fontsize=9)
    #save plot
    if saving == 'YES':
        plt.savefig('LOS_Mortality_AUG.png', format='png', dpi=1200, bbox_inches="tight")

plot_los_mortality(df_ICU_LOS, '')

###############################################################################
###############################################################################
number_ED_PICU = len(df_original)
#number_ICU displayed right before PICU filter
number_PICU = len(df_ICU)
number_PICU_PELOD_3 = df_timepoint_dict['df_timepoint_pelod']['value'].count()
number_PICU_PSOFA_3 = df_timepoint_dict['df_timepoint_psofa']['value'].count()
number_PICU_latest_PELOD = df_ICU['pelod_score_latest'].count()
number_PICU_latest_PSOFA = df_ICU['psofa_score_latest'].count()
###############################################################################
###############################################################################
###############################################################################
