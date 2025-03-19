from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Suspense, FundTins, SuspenseSummary, URA_tins, EmploymentHistory, SuspenseLeads

class SuspenseAppTests(TestCase):

    def setUp(self):
        # Setup test user for authenticated views
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client = Client()

        # Sample data for Suspense model
        self.suspense = Suspense.objects.create(
            member_name="John Doe",
            employer_name="Test Employer",
            employerno="123456",
            #employererrrno="1234563",
            init_member_suspense_contr=1500.50
        )

    # def test_suspense_model_str(self):
    #     self.assertEqual(str(self.suspense), "John Doe")

    def test_suspense_model_str(self):
        self.assertEqual(str(self.suspense), "Jane Doe")  # This will fail

    def test_suspensesearch_view(self):
        response = self.client.get(reverse('msp_search'), {'q': 'John'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")

    def test_empl_suspensesearch_view(self):
        response = self.client.get(reverse('esp_search'), {'q': 'Test Employer'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Employer")

    def test_nsf_suspensesearch_view(self):
        response = self.client.get(reverse('nsf_search'), {'q': '123456'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "123456")

    def test_search_all_suspense_authenticated(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('susp_all'), {'q': 'John'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")

    def test_search_all_suspense_unauthenticated(self):
        response = self.client.get(reverse('susp_all'), {'q': 'John'})
        self.assertNotEqual(response.status_code, 200)  # Should redirect to login

    def test_suspense_summary_creation(self):
        fund_tin = FundTins.objects.create(
            employerno="654321",
            employer_name="Employer Two",
            tin="123456789",
            name_from_ura="URA Employer",
            matching_percentage=95,
            source_of_tin="Manual"
        )

        summary = SuspenseSummary.objects.create(
            employerno="654321",
            employer_name="Employer Two",
            total_suspense_contr=3000.0,
            records_count=10,
            tin=fund_tin
        )
        self.assertEqual(str(summary), "Employer Two - 654321")

    def test_ura_tins_creation(self):
        ura_tin = URA_tins.objects.create(
            taxpayer_name="Taxpayer",
            taxpayer_id="9999999999"
        )
        self.assertEqual(str(ura_tin), "Taxpayer (9999999999)")

    def test_employment_history_creation(self):
        emp_history = EmploymentHistory.objects.create(
            member_number="001",
            employer_name="Test Employer",
            category="Full-time"
        )
        self.assertEqual(str(emp_history), "001 - Test Employer (Full-time)")

    def test_suspense_leads_creation(self):
        lead = SuspenseLeads.objects.create(
            member_name="Jane Doe",
            #end_date="2025-03-17",
            end_date="20250317",
            init_member_suspense_contr=2000.0,
            employer_name="Employer Three",
            employerno="321321",
            member_month_year_s="March 2025",
            employeename="Jane Doe",
            employeetin=1234567890,
            employeetodt="2025-03-31",
            basicsalary=5000.0,
            grosstotincome=6000.0,
            member_month_year="March 2025",
            ura_based_nssf=900.0,
            name="Jane Doe",
            email="janeexamplecom",
            #email="jane@example.com",
            contact="0700123456",
            new_name="Jane D.",
            percentage_match=99.0,
            num_best_matches=1,
            mobile="0700123456"
        )
        self.assertEqual(str(lead), "Jane Doe - Employer Three")
