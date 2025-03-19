import os
import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
from django.core.files.storage import FileSystemStorage
from io import BytesIO
import base64  # For encoding binary data

models_dir = os.path.join('media', 'models')

# Load or train model on demand
def train_model():
    data = pd.read_excel('test_data_set.xlsx')
    X = data['NAMES']
    y = data['SECTOR']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    X_train = X_train.dropna()

    tfidf = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    X_train_tfidf = tfidf.fit_transform(X_train)
    X_test_tfidf = tfidf.transform(X_test)

    model = RandomForestClassifier(n_estimators=150, random_state=42)
    model.fit(X_train_tfidf, y_train)

    joblib.dump(model, 'random_forest_model.pkl')
    joblib.dump(tfidf, 'tfidf_vectorizer.pkl')

    y_pred = model.predict(X_test_tfidf)
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print(classification_report(y_test, y_pred))

# Predict on new data
def predict_new_data(file_path):
    try:
        model = joblib.load(os.path.join(models_dir, 'random_forest_model.pkl'))
        tfidf = joblib.load(os.path.join(models_dir, 'tfidf_vectorizer.pkl'))

        # Load the uploaded file
        new_data = pd.read_excel(file_path)

        # Validate if the required column exists
        if 'NAMES' not in new_data.columns:
            raise ValueError("The uploaded file does not contain the required column: 'NAMES'.")

        new_company_names = new_data['NAMES']

        # Transform and predict
        new_company_tfidf = tfidf.transform(new_company_names)
        predicted_sectors = model.predict(new_company_tfidf)

        # Add predictions to the DataFrame
        new_data['Predicted_Sector'] = predicted_sectors

        # Create an in-memory file for download
        output = BytesIO()
        new_data.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        return output

    except Exception as e:
        # Raise the exception to be handled in the view
        raise ValueError(f"Error processing the file: Please crosscheck the file attached")


def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        
        try:
            # Read the uploaded file into memory
            file_stream = BytesIO(uploaded_file.read())
            output_file = predict_new_data(file_stream)

            # Encode the output file as base64
            request.session['output_file'] = base64.b64encode(output_file.getvalue()).decode('utf-8')

            return render(request, 'sectorisation/sect_upload.html', {
                "message": "File processed successfully. Click the button below to download the results."
            })
        except ValueError as e:
            # Return an error message if the file processing fails
            return render(request, 'sectorisation/sect_upload.html', {
                "error_message": str(e)
            })
    else:
        sample_data = {
            'NAMES': ['John.G Advocates', 'Little Flowers Academy', 'KK and Associates']
        }
        return render(request, 'sectorisation/sect_upload.html', {"sample_data": sample_data})



def download_results(request):
    # Decode the base64-encoded binary data from the session
    output_file_data = request.session.get('output_file')
    if output_file_data:
        output_file_bytes = base64.b64decode(output_file_data)
        response = HttpResponse(output_file_bytes, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="predicted_sectors.xlsx"'
        return response
    else:
        return HttpResponse("No file available for download.")




