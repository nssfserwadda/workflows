from django.shortcuts import render,redirect
from django.db.models import Q
import base64

from .models import Suspense, SuspenseSummary, URA_tins, FundTins, EmploymentHistory, SuspenseLeads

from .forms import SearchSuspenseForm, EmpSearchSuspenseForm, NsfSearchSuspenseForm, NsfSummarySearchForm
from django.contrib.auth.decorators import login_required


import requests
import json
import pandas as pd
import xmltodict
import psycopg2
import threading
from rapidfuzz import process, fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import time
import warnings
from concurrent.futures import ThreadPoolExecutor

from django.http import HttpResponse
import io  # Required for handling the Excel file in memory
import openpyxl

warnings.filterwarnings("ignore")

from django.shortcuts import render

def start_page_view(request):
    return render(request, 'start_page_view.html')  # Replace 'my_template.html' with your actual template name



# Create your views here.
def suspensesearch(request):

    # Initialize form for searching members
    search_form = SearchSuspenseForm(request.GET or None)
    results = []
    if request.method == "GET":
        if search_form.is_valid():
            query = search_form.cleaned_data['q']
            results = Suspense.objects.filter(member_name__icontains=query)

    return render(request, 'member_suspensesearch.html', {'search_form': search_form, 'results': results})


# Create your views here.
def empl_suspensesearch(request):

    # Initialize form for searching members
    search_form = EmpSearchSuspenseForm(request.GET or None)
    results = []
    if request.method == "GET":
        if search_form.is_valid():
            query = search_form.cleaned_data['q']
            results = Suspense.objects.filter(employer_name__icontains=query)

    return render(request, 'employer_suspensesearch.html', {'search_form': search_form, 'results': results})

# Create your views here.
def nsf_suspensesearch(request):

    # Initialize form for searching members
    search_form = NsfSearchSuspenseForm(request.GET or None)
    results = []
    if request.method == "GET":
        if search_form.is_valid():
            query = search_form.cleaned_data['q']
            results = Suspense.objects.filter(employerno__icontains=query)

    return render(request, 'nsf_suspensesearch.html', {'search_form': search_form, 'results': results})

# Create your views here.
@login_required
def search_suspense_summary(request):

    # Initialize form for searching members
    query = request.GET.get('q', '').strip()  # Remove leading/trailing spaces
    #headline = "Search All Suspense"
    search_results = []  

    if query:
        search_results = SuspenseSummary.objects.filter(
            Q(employerno__icontains=query) |
            Q(employer_name__icontains=query) 
          
        )
        headline = f"Search Results for '{query}'"

    context = {
        'search_results': search_results,
        #'headline': headline,
        'query': query,
    }

    return render(request, 'search_suspense_summary.html', context)





@login_required
def search_all_suspense(request):
    """
    View to search all suspense records based on any field.
    """
    query = request.GET.get('q', '').strip()  # Remove leading/trailing spaces
    headline = "Search All Suspense"
    search_results = []  

    if query:
        search_results = Suspense.objects.filter(
            Q(member_name__icontains=query) |
            Q(employer_name__icontains=query) |
            Q(employerno__icontains=query) |
            Q(member_identificat_val__icontains=query) |
            Q(employer_identificat_val__icontains=query)
        )
        headline = f"Search Results for '{query}'"

    context = {
        'search_results': search_results,
        'headline': headline,
        'query': query,
    }

    return render(request, 'all_suspense_search.html', context)

# Create your views here.
@login_required
def search_ura_tins(request):

    # Initialize form for searching members
    query = request.GET.get('q', '').strip()  # Remove leading/trailing spaces
    #headline = "Search All Suspense"
    search_results = []  

    if query:
        search_results = URA_tins.objects.filter(
            Q(taxpayer_name__icontains=query) |
            Q(trading_name__icontains=query) |
            Q(business_name__icontains=query) |
            Q(taxpayer_id__icontains=query) 
            
          
        )
        headline = f"Search Results for '{query}'"

    context = {
        'search_results': search_results,
        #'headline': headline,
        'query': query,
    }

    return render(request, 'search_ura_tins.html', context)


@login_required
def other_suspense_summary_view(request):
    """
    View to filter Suspense records and return a summarized DataFrame-style output with TIN included.
    """
    filter_type = request.GET.get('filter_type', None)
    filters = Q()

    # Ensure the table does not appear before filtering
    if not filter_type:
        return render(request, 'other_suspense_summary_view.html', {'df2': None, 'message': None})

    # Apply selected filter
    if filter_type == "payment_date":
        payment_start_date = request.GET.get('payment_start_date', None)
        payment_end_date = request.GET.get('payment_end_date', None)
        if payment_start_date and payment_end_date:
            filters &= Q(payment_date__range=[payment_start_date, payment_end_date])

    elif filter_type == "end_date":
        end_start_date = request.GET.get('end_start_date', None)
        end_end_date = request.GET.get('end_end_date', None)
        if end_start_date and end_end_date:
            filters &= Q(end_date__range=[end_start_date, end_end_date])

    elif filter_type == "contribution":
        min_contr = request.GET.get('min_contr', None)
        max_contr = request.GET.get('max_contr', None)
        if min_contr:
            filters &= Q(init_member_suspense_contr__gte=float(min_contr))
        if max_contr:
            filters &= Q(init_member_suspense_contr__lte=float(max_contr))

    # ✅ Fetch filtered results and join with FundTins to get the TIN
    queryset = Suspense.objects.filter(filters).values(
        'employerno', 'employer_name', 'init_member_suspense_contr', 'member_name', 'end_date', 'start_date'
    )

    df = pd.DataFrame.from_records(queryset)
    if df.empty:
        return render(request, 'other_suspense_summary_view.html', {'df2': None, 'message': 'No results found.'})

    # ✅ Get TINs from FundTins
    tin_queryset = FundTins.objects.values('employerno', 'tin')
    df_tins = pd.DataFrame.from_records(tin_queryset)

    # ✅ Merge TINs with the main DataFrame
    df = df.merge(df_tins, on="employerno", how="left")  # Left join to keep all suspense records

    # ✅ Summarize results
    df2 = df.groupby(['employerno', 'employer_name', 'tin']).agg({
        'init_member_suspense_contr': 'sum',
        'member_name': 'count',
        'start_date': 'min',
        'end_date': ['max', 'nunique']
    }).reset_index()

    df2.columns = ['employerno', 'employer_name', 'tin', 'total_suspense_contr', 'records_count', 'from_date', 'to_date', 'scope_months']

    # ✅ Sort by total_suspense_contr in descending order
    df2 = df2.sort_values(by="total_suspense_contr", ascending=False)

    df2_records = df2.to_dict(orient='records')

    return render(request, 'other_suspense_summary_view.html', {'df2': df2_records, 'message': None})




def export_to_excel(df, nssfno, tin, from_date, to_date):
    """Generates an Excel file from a DataFrame and returns it as an HTTP response."""
    
    # ✅ Ensure no timezone issues in datetime columns
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)  # ✅ Remove timezone information

    # ✅ Create an in-memory output file
    output = io.BytesIO()

    # ✅ Write DataFrame to an Excel file in memory
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name="Suspense Data", index=False)

    output.seek(0)  # ✅ Reset buffer position to start

    # ✅ Set response headers to force file download
    response = HttpResponse(
        output.read(), 
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = f'attachment; filename="suspense_data.xlsx"'
    
    return response





def fetch_single_tin(tin, result_list):
    api_url = f'https://trex.nssfug.org:4405/uraapi/api/Ura/Get?tin={tin}'
    try:
        response = requests.get(api_url, timeout=5)  # Set timeout
        if response.status_code == 200:
            data = response.json()
            if not data:
                print(f"WARNING: No data returned for TIN {tin}")
            
            df = pd.DataFrame.from_dict(data, orient='index').T
            df3 = df.iloc[:, 2:6]

            # Fill missing values
            df3['name'] = df3['name'].fillna("Unknown")
            df3['tin'] = df3['tin'].fillna(tin)
            df3['email'] = df3['email'].fillna("No Email")
            df3['contact'] = df3['contact'].fillna("No Contact")

            result_list.append(df3[['name', 'tin', 'email', 'contact']])
        else:
            print(f"ERROR: API request failed for TIN {tin} (Status Code: {response.status_code})")

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network issue for TIN {tin}: {e}")

def fetch_ura_contacts_bulk(tins):
    """ Fetch contacts using thread pool (limits concurrency to avoid missing data). """
    result_list = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:  # Limit to 10 parallel API calls
        executor.map(lambda tin: fetch_single_tin(tin, result_list), tins)

    return pd.concat(result_list, ignore_index=True) if result_list else pd.DataFrame(columns=['name', 'tin', 'email', 'contact'])




def fetch_employee_data(tin, from_date, to_date): 
    """ Fetch employee data and merge contacts efficiently. """
    response = requests.post(
        "https://esbinternal.nssfug.org/services/RegURAGetPayeScheduleService",
        data=json.dumps({"TIN": tin, "FromDate": from_date, "ToDate": to_date}),
        headers={"Content-Type": "application/xml"},
    )

    xml_data = response.text
    if "BasicSalary" not in xml_data:
        return pd.DataFrame(columns=['EmployeeName', 'EmployeeTIN', 'EmployeeToDt', 'BasicSalary', 'GrossTotIncome', 'member_month_year'])

    my_dict = xmltodict.parse(xml_data)
    my_list = my_dict['root']['Body']['GetPayeScheduleResponse']['GetPayeScheduleResult']['a:PayeDataContract.PayeInfo']
    df = pd.DataFrame(my_list)
    df.columns = df.columns.str.replace('a:', '')

    # Select relevant columns & remove duplicates
    df1 = df[['EmployeeName', 'EmployeeTIN', 'EmployeeToDt', 'BasicSalary', 'GrossTotIncome']]
    df1.drop_duplicates(subset=['EmployeeTIN', 'EmployeeToDt'], inplace=True)

    # ✅ Convert EmployeeToDt to datetime format
    df1['EmployeeToDt'] = pd.to_datetime(df1['EmployeeToDt'], errors='coerce')

    # ✅ Create new column concatenating EmployeeName with Month-Year from EmployeeToDt
    df1['member_month_year'] = df1['EmployeeName'].astype(str) + " " + df1['EmployeeToDt'].dt.strftime('%B %Y')


    # Convert 'GrossTotIncome' to numeric, forcing errors to NaN if conversion fails
    df1['GrossTotIncome'] = pd.to_numeric(df1['GrossTotIncome'], errors='coerce')
    df1['ura_based_nssf'] = df1['GrossTotIncome'] * 0.15  # Multiply by 15%

    # Fetch unique TINs in batch using multi-threading
    unique_tins = df1['EmployeeTIN'].unique()
    contact_details = fetch_ura_contacts_bulk(unique_tins)

    # Merge contacts efficiently
    merged_df = df1.merge(contact_details, left_on='EmployeeTIN', right_on='tin', how='left').drop(columns=['tin'])
    merged_df = merged_df[merged_df['contact'].notna() & (merged_df['contact'] != '')]

    return merged_df



def get_suspense(emp_number, from_date, to_date):
    """
    Fetch records from the Suspense table using Django ORM.
    """
    queryset = Suspense.objects.filter(
        employerno=emp_number,
        end_date__range=[from_date, to_date]
    ).values(
        'member_name',
        'end_date',
        'init_member_suspense_contr',
        'employer_name',
        'employerno'
    )

    # Convert QuerySet to Pandas DataFrame
    df = pd.DataFrame.from_records(queryset)

    # Ensure 'end_date' column is in datetime format
    if not df.empty and 'end_date' in df.columns:
        df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')

        # Create new column concatenating member_name with Month-Year from end_date
        df['member_month_year_s'] = df['member_name'] + " " + df['end_date'].dt.strftime('%B %Y')

    return df if not df.empty else pd.DataFrame(columns=['member_name', 'end_date', 'init_member_suspense_contr', 'employer_name', 'employerno', 'member_month_year_s'])

### **Step 4: FAST Approximate Name Matching with TF-IDF Cosine Similarity**
def match_names_fast(names_to_match, df_lookup, column='EmployeeName'):
    """
    **Super Fast Name Matching using TF-IDF Cosine Similarity**
    - Converts text data into TF-IDF vectors.
    - Computes cosine similarity (much faster than fuzzy matching).
    - Returns best match and similarity score.
    """
    lookup_names = df_lookup[column].tolist()

    # Vectorize text (Convert names into numerical format)
    vectorizer = TfidfVectorizer().fit(lookup_names + names_to_match)
    lookup_vectors = vectorizer.transform(lookup_names)
    match_vectors = vectorizer.transform(names_to_match)

    # Compute similarity
    similarities = cosine_similarity(match_vectors, lookup_vectors)

    # Get best matches
    best_match_indices = similarities.argmax(axis=1)  # Best match index for each name
    best_scores = similarities.max(axis=1) * 100  # Convert to percentage

    # Count occurrences of best score
    num_best_matches = (similarities == similarities.max(axis=1)[:, None]).sum(axis=1)

    matched_data = df_lookup.iloc[best_match_indices].reset_index(drop=True)
    matched_data['new_name'] = matched_data[column]
    matched_data['percentage_match'] = best_scores
    matched_data['num_best_matches'] = num_best_matches
    #matched_data['percentage_match'] = matched_data['percentage_match'].round(decimals = 0)
    #cf['period'] = cf['period'].astype(int)

    return matched_data

### **Step 5: Compare Suspense with Optimized Processing**

def compare_suspense(nssfno, tin, from_date, to_date):
    # Fetch data efficiently
    bf = get_suspense(nssfno, from_date, to_date)
    gf = fetch_employee_data(tin, from_date, to_date)
    cf =bf.copy()

    if bf.empty or gf.empty:
        return pd.DataFrame(), pd.DataFrame()  # ✅ Return two empty DataFrames

    # Perform bulk name matching using fast TF-IDF cosine similarity
    matched_df = match_names_fast(bf['member_name'].tolist(), gf, 'EmployeeName')
    matched_df2 = match_names_fast(bf['member_month_year_s'].tolist(), gf, 'member_month_year')

    # Merge matched results into bf
    cf = pd.concat([bf.reset_index(drop=True), matched_df.reset_index(drop=True)], axis=1)#.sort_values(by=['percentage_match'], ascending=False)
    bf = pd.concat([bf.reset_index(drop=True), matched_df2.reset_index(drop=True)], axis=1)#.sort_values(by=['percentage_match'], ascending=False)

   
        

    return cf,bf





@login_required
def compare_suspense_view(request):
    """
    View to accept NSSF Number, TIN, Employer Name, From Date, and To Date 
    and return the processed `bf` data.
    """
    # Get user inputs
    nssfno = request.GET.get('nssfno', None)
    tin = request.GET.get('tin', None)
    #employer_name = request.GET.get('employer_name', None)
    from_date = request.GET.get('from_date', None)
    to_date = request.GET.get('to_date', None)

    employer = Suspense.objects.filter(employerno=nssfno).values('employer_name').first()
    export = request.GET.get('export', '')  # ✅ Ensure export is always defined



    #employer_name = employer['employer_name']
   

    if employer:
        employer_name = employer.get('employer_name', 'Unknown Employer')
    else:
        employer_name = "Unknown Employer"


    # Ensure all required inputs are provided before processing
    if not all([nssfno, tin, employer_name, from_date, to_date]):
        return render(request, 'compare_suspense.html', {'df2': None})

    # Fetch and process the data
    cf, bf = compare_suspense(nssfno, tin, from_date, to_date)


    # ✅ Properly check if DataFrame `bf` is empty
    if bf is None or bf.empty:
        return render(request, 'compare_suspense.html', {
            'df2': None, 
            'message': 'No matching records found.',
            'nssfno': nssfno,
            'tin': tin,
            'employer_name': employer_name,
            'from_date': from_date,
            'to_date': to_date
        })



    # Convert DataFrame to dictionary for rendering in the template
    df2_records = bf.to_dict(orient='records')
        # Handle Excel Export Request
    if export == "excel":
        return export_to_excel(bf, nssfno, tin, from_date, to_date)

    return render(request, 'compare_suspense.html', {
        'df2': df2_records,

        'nssfno': nssfno,
        'tin': tin,
        'employer_name': employer_name,
        'from_date': from_date,
        'to_date': to_date
    })


@login_required
def compare_suspense_view222(request):
    """
    View to accept NSSF Number, TIN, Employer Name, From Date, and To Date 
    and return the processed `bf` data.
    """
    # Get user inputs
    nssfno = request.GET.get('nssfno', None)
    tin = request.GET.get('tin', None)
    from_date = request.GET.get('from_date', None)
    to_date = request.GET.get('to_date', None)
    process = request.GET.get('process', 'no')  # ✅ Get the process flag (default: 'no')

    employer = Suspense.objects.filter(employerno=nssfno).values('employer_name').first()
    export = request.GET.get('export', '')

    if employer:
        employer_name = employer.get('employer_name', 'Unknown Employer')
    else:
        employer_name = "Unknown Employer"

    # ✅ If process == 'no', just render the form with pre-filled values (DO NOT RUN PROCESSING)
    if process == 'no':
        return render(request, 'compare_suspense22.html', {
            'df2': None,
            'nssfno': nssfno,
            'tin': tin,
            'employer_name': employer_name,
            'from_date': from_date,
            'to_date': to_date
        })

    # ✅ Ensure all required inputs are provided before processing
    if not all([nssfno, tin, from_date, to_date]):
        return render(request, 'compare_suspense22.html', {
            'df2': None,
            'nssfno': nssfno,
            'tin': tin,
            'employer_name': employer_name,
            'from_date': from_date,
            'to_date': to_date,
            'message': "Missing required fields."
        })

    # ✅ Run the processing logic only if process == 'yes'
    cf, bf = compare_suspense(nssfno, tin, from_date, to_date)

    # # ✅ Handle Excel Export Request
    # if export == "excel":
    #     if bf is not None and not bf.empty:
    #         return export_to_excel(bf, nssfno, tin, from_date, to_date)
    #     else:
    #         return HttpResponse("No data available for export.", content_type="text/plain")    

        # ✅ Handle Excel Export Request
    if export == "excel":
        if bf is not None and not bf.empty:
            # ✅ Convert DataFrame to Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                bf.to_excel(writer, sheet_name="Suspense Data", index=False)

            output.seek(0)
            encoded_output = base64.b64encode(output.read()).decode('utf-8')  # ✅ Convert to base64
            
            # ✅ Debugging: Print to check if it's being stored
            print("Saving file in session...")

            # ✅ Store in session
            request.session['output_file'] = encoded_output
            request.session.modified = True  # ✅ Ensure session gets updated

            # ✅ Debugging: Check if session is storing it correctly
            print("Stored file:", len(encoded_output))

            return redirect('download_results')

        else:
            return HttpResponse("No data available for export.", content_type="text/plain")


    if bf is None or bf.empty:
        return render(request, 'compare_suspense22.html', {
            'df2': None,
            'nssfno': nssfno,
            'tin': tin,
            'employer_name': employer_name,
            'from_date': from_date,
            'to_date': to_date,
            'message': "No matching records found."
        })

    # ✅ Processed results only show when process == 'yes'
    return render(request, 'compare_suspense22.html', {
        'df2': bf.to_dict(orient='records'),
        'nssfno': nssfno,
        'tin': tin,
        'employer_name': employer_name,
        'from_date': from_date,
        'to_date': to_date,
        'bf':bf
    })



def download_results(request): 
    """Retrieve the stored file from the session and send it as a download."""
    output_file_data = request.session.get('output_file')

    # ✅ Debugging: Print session keys to check if file exists
    print("Session keys:", request.session.keys())

    if output_file_data:
        output_file_bytes = base64.b64decode(output_file_data)

        response = HttpResponse(
            output_file_bytes, 
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="suspense_data.xlsx"'

        # ✅ Remove the file from session after download
        del request.session['output_file']
        request.session.modified = True  # ✅ Ensure session updates

        return response
    else:
        return HttpResponse("No file available for download.", content_type="text/plain")


# Create your views here.
@login_required
def search_employmeny_history(request):

    # Initialize form for searching members
    query = request.GET.get('q', '').strip()  # Remove leading/trailing spaces
    #headline = "Search All Suspense"
    search_results = []  

    if query:
        search_results = EmploymentHistory.objects.filter(
            Q(member_number__icontains=query) |
            Q(member_name__icontains=query) |
            Q(employer_name__icontains=query)
           
            
          
        )
        headline = f"Search Results for '{query}'"

    context = {
        'search_results': search_results,
        #'headline': headline,
        'query': query,
    }

    return render(request, 'search_employmeny_history.html', context)



def suspense_leads_view(request):
    """ View function to display EmployeeRecord data in a table. """
    records = SuspenseLeads.objects.all()
    return render(request, 'suspense_leads.html', {'records': records})