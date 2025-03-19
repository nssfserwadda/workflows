import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadFileForm
import os
from django.conf import settings

import numpy as np
import pandas as pd
import cx_Oracle
from sqlalchemy import create_engine, text
import requests, json, xmltodict
from fuzzywuzzy import fuzz

import warnings

# Suppress specific warning
warnings.filterwarnings('ignore', category=UserWarning, message='pandas only supports SQLAlchemy connectable')

conn = cx_Oracle.connect('DATATES/NSSFdata!1@NSSFPRDDR')

# Create SQLAlchemy engine for Oracle
engine = create_engine('oracle+cx_oracle://DATATES:NSSFdata!1@NSSFPRDDR')

# Define your query with parameters
query = """
SELECT er.EMPLOYER_NAME, er.EMPLOYER_IDENTIFICAT_VAL, er.PAYMENT_ALLOCATED_AMOUNT, er.PERIOD_START_DATE,
       mr.MEMBER_NAME, mr.MEMBER_IDENTIFICAT_VAL, mr.PAID_MEMBER_CONTR,
       ROUND(mr.PAID_MEMBER_CONTR / 0.15, 0) AS SALARY
FROM MIS.VW_SUBMISSION_EMPL_REP er
JOIN MIS.VW_SUBMISSION_MEMB_REP mr
ON er.SUBMISSION_INSTANCE_ID = mr.SUBMISSION_INSTANCE_ID
WHERE er.PERIOD_START_DATE BETWEEN TO_DATE(:start_date, 'DD-MM-YYYY') AND TO_DATE(:end_date, 'DD-MM-YYYY')
AND EMPLOYER_IDENTIFICAT_VAL = :employer_id
"""





def read_master_dataframe():
    # Update this path to your master Excel file location

    master_file_path = os.path.join(settings.MEDIA_ROOT, 'somefiles', 'master_file.xlsx')

    #data=pd.read_csv('C:/WORK/ULTIMATE REPORTING/Automations//nssf_returns3.txt', encoding='latin1', delimiter='|')
    return pd.read_excel(master_file_path)

def reconcile_dataframes(df1, df2):
    # Assuming we want to find rows in df1 that are not in df2 based on all columns
    df_diff = df1[~df1.apply(tuple,1).isin(df2.apply(tuple,1))]
    return df_diff

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            start_date1 = form.cleaned_data['start_date']
            end_date1 = form.cleaned_data['end_date']
            employer_nssf_number = form.cleaned_data['employer_nssf_number']


            # Convert the dates to the required format
            start_date_str = start_date1.strftime('%d-%m-%Y')  # Format: day-month-year
            end_date_str = end_date1.strftime('%d-%m-%Y')      # Format: day-month-year

            df1 = pd.read_excel(uploaded_file)
            
            df2 = read_master_dataframe()
            #df2 = df6
            result_df = reconcile_dataframes(df1, df2)

            row_index = 2
            column_index = 2
            cell_value = df1.iloc[row_index, column_index]
            TIN = df1.iloc[4,2]
            
            # Define parameter values

            params = {
                'start_date': start_date_str,
                'end_date': end_date_str,
                'employer_id': employer_nssf_number
            }
# check for employer names similarity


            


            # Use pd.read_sql with SQLAlchemy engine and parameters
            #df6 = pd.read_sql(query, engine, params=params)
            df6 = pd.read_sql(query, con=conn, params=params)
            #df2 = df6


            #df6=pd.read_sql(quer,con)

            # Convert result_df to HTML table for easy display
            #result_html = result_df.to_html()
            df6['PERIOD'] =  df6['PERIOD_START_DATE'].dt.month + df6['PERIOD_START_DATE'].dt.year*100
            df7 = df6[['MEMBER_NAME','MEMBER_IDENTIFICAT_VAL','PERIOD','PAID_MEMBER_CONTR','SALARY']]
            #df7['contbn_entry'] = df7['MEMBER_IDENTIFICAT_VAL']+'_'+df7['PERIOD'].astype(str)
            df7.loc[:, 'contbn_entry'] = df7['MEMBER_IDENTIFICAT_VAL'] + '_' + df7['PERIOD'].astype(str)

            df8 = pd.read_excel(uploaded_file, skiprows=7)
            df8['Member NSSF number'] = df8['Member NSSF number'].astype('Int64').astype(str)
            df8['PERIOD'] = df8['Contribution Year']*100+df8['Contribution Month']
            df8['NSSF15'] = df8['Gross Pay']*0.15
            df9 = df8[['Member NSSF number','Member Name','PERIOD','NSSF15','Gross Pay']]
            df9['contbn_entry'] = df9['Member NSSF number']+'_'+df9['PERIOD'].astype(str)

            emp_column_names = {'Member NSSF number': 'emp_Member_NSSFno', 'Member Name': 'emp_member_name', 'PERIOD': 'emp_period',\
                                'NSSF15':'emp_NSSF15','Gross Pay':'emp_gross_pay','contbn_entry':'contribution_id'}
            
            our_column_names = {'MEMBER_IDENTIFICAT_VAL': 'our_Member_NSSFno', 'MEMBER_NAME': 'our_member_name', 'PERIOD': 'our_period',\
                                'PAID_MEMBER_CONTR':'our_NSSF15','SALARY':'our_gross_pay','contbn_entry':'contribution_id'}

           
            df9 = df9.rename(columns=emp_column_names)
            df7 = df7.rename(columns=our_column_names)
          


            df10 = pd.merge(df9, df7, on='contribution_id', how='outer')
            df10['emp_NSSF15'] = df10['emp_NSSF15'].fillna(0)
            df10['our_NSSF15'] = df10['our_NSSF15'].fillna(0)
            df10['emp_member_name'] = df10['emp_member_name'].fillna('')
            df10['our_member_name'] = df10['our_member_name'].fillna('')

            #df10 = df10.fillna('')
            df10['Emp_vs_NSSF_amount'] = df10['emp_NSSF15'].astype(float)-df10['our_NSSF15'].astype(float)
            df10['Name_Similarity'] = df10.apply(lambda row: fuzz.ratio(row['emp_member_name'], row['our_member_name']), axis=1)
            

            df11 = pd.pivot_table(df10, 
               index=['our_period'], 
               values=['emp_NSSF15','our_NSSF15','emp_member_name','our_member_name','Emp_vs_NSSF_amount'], 
               aggfunc={'emp_NSSF15':np.sum,'our_NSSF15':np.sum,'Emp_vs_NSSF_amount':np.sum,'emp_member_name':pd.Series.nunique,'our_member_name':pd.Series.nunique})
            
            
            

            df11 = df11.reset_index()
            df11[['Emp_vs_NSSF_amount', 'emp_NSSF15', 'emp_member_name','our_NSSF15', 'our_member_name']] = df11[['Emp_vs_NSSF_amount', 'emp_NSSF15', 'emp_member_name','our_NSSF15', 'our_member_name']].astype(float)  
            df11['our_period'] = df11['our_period'].astype('Int64').astype(str)
            df11 = df11.rename(columns={'our_period': 'PERIOD'})

# generate a periods dataframe
            periods = []

            # Loop through the range of dates, generating periods
            current_date = start_date1

            while current_date <= end_date1:
                # Format the period as YYYYMM
                period = current_date.strftime('%Y%m')
                periods.append(period)
                
                # Move to the next month
                # Adding one month and resetting the day to the first of the month
                next_month = current_date + pd.DateOffset(months=1)
                current_date = next_month.replace(day=1)

            # Create a DataFrame from the periods
            df_periods = pd.DataFrame(periods, columns=['PERIOD'])

            df12 = pd.merge(df_periods, df11, on='PERIOD', how='outer').fillna(0)

# generate a URA PAYE dataframe
            tin = df1.iloc[4, 2]
            nssf_no = df1.iloc[2, 2]
            from_date = start_date1.strftime("%Y-%m-%d")
            to_date = end_date1.strftime("%Y-%m-%d")


            r = requests.post(
                "https://esbinternal.nssfug.org/services/RegURAGetPayeScheduleService",
                data = json.dumps({"TIN":tin,
                    "FromDate":from_date,
                    "ToDate":to_date}),
                headers={"Content-Type": "application/xml"},
            )

            xml_data = r.text
            ppp = xml_data.find("BasicSalary")       

            if ppp<0:
                pf5 = pd.DataFrame(columns = ['PERIOD','URA_based_15','URA_Members'])
                #df5 = df4[['EmployerTin','EmployerName','CPERIOD','URA_based_15','EmployeeTIN']]
            else:    

                my_dict = xmltodict.parse(xml_data)
                my_list = my_dict['root']['Body']['GetPayeScheduleResponse']['GetPayeScheduleResult']['a:PayeDataContract.PayeInfo']
                pf = pd.DataFrame(my_list)
                pf.columns = pf.columns.str.replace('a:', '')
                pf2=pf.loc[:, ~pf.columns.isin(['StatusCode', 'StatusDesc'])]

                warnings.filterwarnings("ignore")
                pf2['ChargeableIncome'] = pf2['ChargeableIncome'].astype(float)
                Employer = pf2['EmployerName'][0]

                pf4 = pd.pivot_table(pf2, 
                        index=['EmployeeToDt'], 
                        values=['BasicSalary','ChargeableIncome','GrossTotIncome','HousingAllowance','OtherTaxableBenf',
                                'PayableTaxOnIncome','TotTaxDeducted','EmployeeTIN','EmployerTin','EmployerName'], 
                        aggfunc={'BasicSalary':np.sum,'ChargeableIncome':np.sum,'GrossTotIncome':np.sum,'HousingAllowance':np.sum,
                                    'OtherTaxableBenf':np.sum,'PayableTaxOnIncome':np.sum,'TotTaxDeducted':np.sum,'EmployeeTIN':pd.Series.nunique,
                                    'EmployerTin':np.max,'EmployerName':np.max})   

                pf4 = pf4.reset_index()
                pf4['EmployeeToDt'] = pd.to_datetime(pf4['EmployeeToDt'], errors = 'ignore')
                pf4['PERIOD']=pf4['EmployeeToDt'].dt.month + pf4['EmployeeToDt'].dt.year*100
                pf4['URA_based_15'] = pf4['ChargeableIncome']*0.15
                pf5 = pf4[['PERIOD','URA_based_15','EmployeeTIN']]
                pf5.columns = ['PERIOD','URA_based_15','URA_Members']
                pf5['PERIOD'] = pf5['PERIOD'].astype('Int64').astype(str)
            
            df13 = pd.merge(df12, pf5, on='PERIOD', how='outer').fillna(0)
            df13['URA_VS_NSSF_amount'] = df13['URA_based_15']-df13['our_NSSF15']
            df13['URA_VS_NSSF_members'] = df13['URA_Members']-df13['our_member_name']
            df13['Emp_VS_NSSF_members'] = df13['emp_member_name']-df13['our_member_name']

            df14 = df13[['PERIOD','our_NSSF15','emp_NSSF15','URA_based_15','our_member_name','emp_member_name','URA_Members','Emp_vs_NSSF_amount',\
                         'URA_VS_NSSF_amount','Emp_VS_NSSF_members','URA_VS_NSSF_members']]
            
            emp_name_from_EMP = df1.iloc[3, 2]
            emp_name_from_NSSF = df6['EMPLOYER_NAME'][0]
            emp_name_similarity = fuzz.ratio(emp_name_from_EMP, emp_name_from_NSSF)
            namelist = [emp_name_from_EMP, emp_name_from_NSSF, Employer]
            #name_df = pd.DataFrame (namelist, columns = ['Names'])
            #name_df = pd.DataFrame (namelist, columns = ['Name from employer','Name from NSSFNo','Name from TIN'])

            emp_names = {
                'Employer Name source': ['Employer','NSSF Number','TIN'],
                'Employer Name': [emp_name_from_EMP, emp_name_from_NSSF, Employer]
            }
            name_df = pd.DataFrame(emp_names)



            result_html = df14.to_html()

            return HttpResponse(result_html)
        



    else:
        form = UploadFileForm()

    return render(request, 'upload.html', {'form': form})

