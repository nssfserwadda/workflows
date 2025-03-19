import oracledb
import re
from datetime import datetime
import threading
from django.apps import apps 



def get_trn_payments(nssf_number, trn, legal_start_date, legal_end_date):
    """Fetch total payment allocated amount for a TRN within the legal period."""
    try:
        username = 'DATATES'
        password = 'NSSFdata!1'
        dsn = '192.168.194.37:1521/nssfprddr'

        connection = oracledb.connect(user=username, password=password, dsn=dsn)

        query = """
           SELECT d.NSF_NUMBER, er.TRN, TRUNC(er.PAYMENT_DATE) AS PAYMENT_DATE, 
                  COALESCE(SUM(er.PAYMENT_ALLOCATED_AMOUNT), 0) AS total_payment
            FROM MIS.VW_SUBMISSION_EMPL_REP er
            JOIN MIS.DIM_PARTY d ON er.EMPLOYER_ID = d.PARTY_ROLE_ID
            WHERE PERIOD_START_DATE BETWEEN TO_DATE(:audited_period_startdate, 'DD-MM-YYYY') 
                  AND TO_DATE(:audited_period_enddate, 'DD-MM-YYYY')
                  AND UPPER(TRIM(er.TRN)) = UPPER(TRIM(:trn))
                  AND UPPER(TRIM(d.NSF_NUMBER)) = UPPER(TRIM(:nssf_number))
            GROUP BY d.NSF_NUMBER, er.TRN, TRUNC(er.PAYMENT_DATE)
        """

        with connection.cursor() as cursor:
            cursor.execute(query, {
                "audited_period_startdate": legal_start_date,
                "audited_period_enddate": legal_end_date,
                "trn": trn,
                "nssf_number": nssf_number
            })
            result = cursor.fetchall()

        connection.close()

        if result:
            total_payment = sum(row[3] for row in result)
            latest_payment_date = max(row[2] for row in result)
            return {"total_payment": total_payment, "payment_date": latest_payment_date}
        else:
            return {"total_payment": 0, "payment_date": "N/A"}

    except oracledb.DatabaseError as e:
        return {"total_payment": 0, "payment_date": "N/A"}





def process_trn_in_background(installment, trn, legal_file):
    """Background function to reconcile TRN payments."""
    from .utils import get_trn_payments  # ✅ Prevent circular imports

    trn_data = get_trn_payments(
        legal_file.nssf_number, trn,
        legal_file.audited_period_startdate.strftime('%d-%m-%Y'),
        legal_file.audited_period_enddate.strftime('%d-%m-%Y')
    )

    total_payment = trn_data.get("total_payment", 0)
    payment_date = trn_data.get("payment_date", "N/A")

    # ✅ Skip invalid TRNs (out of scope or wrong company)
    if total_payment == 0:
        print(f"⚠ Skipping TRN {trn}: Out of scope or incorrect company.")
        return

    # ✅ Process valid TRNs
    Payment = apps.get_model('Legal2025', 'Payment')  # ✅ Lazy Import Fix
    payment = Payment.objects.create(
        installment=installment,
        transaction_reference_number=trn,
        amount_paid=total_payment,
        payment_date=payment_date if payment_date != "N/A" else None
    )

    # ✅ Update installment status
    installment.update_status()
    print(f"✅ TRN {trn} reconciled in the background. Amount: {payment.amount_paid}")


# def get_trn_payments(nssf_number, trn, legal_start_date, legal_end_date):
#     """Fetch total payment allocated amount for a TRN within the legal period."""
#     try:
#         username = 'DATATES'
#         password = 'NSSFdata!1'
#         dsn = '192.168.194.37:1521/nssfprddr'

#         oracledb.init_oracle_client()
#         connection = oracledb.connect(user=username, password=password, dsn=dsn)

#         query = """
#            SELECT d.NSF_NUMBER, er.TRN, TRUNC(er.PAYMENT_DATE) AS PAYMENT_DATE, COALESCE(SUM(er.PAYMENT_ALLOCATED_AMOUNT), 0) AS total_payment
#             FROM MIS.VW_SUBMISSION_EMPL_REP er
#             JOIN MIS.DIM_PARTY d ON er.EMPLOYER_ID = d.PARTY_ROLE_ID
#             WHERE PAYMENT_CREATION_DATE >= TO_DATE('01-07-2024','DD-MM-YYYY') 
#             AND PERIOD_START_DATE BETWEEN TO_DATE(:audited_period_startdate, 'DD-MM-YYYY') AND TO_DATE(:audited_period_enddate, 'DD-MM-YYYY')
#             AND UPPER(TRIM(er.TRN)) = UPPER(TRIM(:trn))
#             AND UPPER(TRIM(d.NSF_NUMBER)) = UPPER(TRIM(:nssf_number))
#             GROUP BY d.NSF_NUMBER, er.TRN, TRUNC(er.PAYMENT_DATE)
#         """

#         print("🔍 Query Parameters:")
#         print(f"  - TRN: {trn}")
#         print(f"  - NSSF_NUMBER: {nssf_number}")
#         print(f"  - Start Date: {legal_start_date}")
#         print(f"  - End Date: {legal_end_date}")
        
#         with connection.cursor() as cursor:
#             cursor.execute(query, {
#                 "audited_period_startdate": legal_start_date,
#                 "audited_period_enddate": legal_end_date,
#                 "trn": trn,
#                 "nssf_number": nssf_number 
#             })
#             result = cursor.fetchall()
            
#         connection.close()

#         print("✅ Query Result:", result)

#         # Ensure valid response before returning values
#         if result:
#             total_payment = sum(row[3] for row in result)  # SUM(PAYMENT_ALLOCATED_AMOUNT)
#             latest_payment_date = max(row[2] for row in result)  # Latest PAYMENT_DATE
#             return {
#                 "total_payment": total_payment,
#                 "payment_date": latest_payment_date
#             }
#         else:
#             return {"total_payment": 0, "payment_date": "N/A"}

#     except oracledb.DatabaseError as e:
#         print(f"❌ Database error: {e}")
#         return {"total_payment": 0, "payment_date": "N/A"}

