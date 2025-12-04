import os
import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill
from fastapi.responses import FileResponse

import app.database as db
from app.services.employee_service import EmployeeService

REPORT_DIR = "app/reports"
os.makedirs(REPORT_DIR, exist_ok=True)


def safe_get(data: dict, key: str):
    """This returns value or 'data unavailable' if missing."""
    return data.get(key, "data unavailable") or "data unavailable"

#fetching from database
def fetch_report_data():
    """
    Loads:
    - employees.json
    - leave_requests.json
    - leave_balances.json

    Enhances data by:
    - calculating service years
    - attaching remaining vacation & sick balances
    - flagging sick document uploaded
    """

    employees = db.read_all_records("employees")
    leave_requests = db.read_all_records("leave_requests")
    leave_balances = db.read_all_records("leave_balances")

    # Build map of leave balances
    balance_map = {}
    for lb in leave_balances:
        emp_id = lb["employee_id"]

        if emp_id not in balance_map:
            balance_map[emp_id] = {"vacation": None, "sick": None}

        if lb["leave_type"] == "vacation":
            balance_map[emp_id]["vacation"] = lb["remaining_days"]

        elif lb["leave_type"] == "sick":
            balance_map[emp_id]["sick"] = lb["remaining_days"]


    # Enhance employee records-
    enhanced_emps = []
    for e in employees:
        emp_id = e["id"]

        enhanced_emps.append({
            **e,
            "service_years": EmployeeService.calc_years_of_service(e["date_hired"]),
            "vacation_balance": balance_map.get(emp_id, {}).get("vacation", "data unavailable"),
            "sick_balance": balance_map.get(emp_id, {}).get("sick", "data unavailable"),
        })

    # Enhance leave request records
    enhanced_reqs = []
    for lr in leave_requests:

        doc_uploaded = (
            lr.get("sick_note") is not None
            and isinstance(lr.get("sick_note"), dict)
        )

        enhanced_reqs.append({
            **lr,
            "has_document": doc_uploaded
        })

    return enhanced_emps, enhanced_reqs

# Formatting
def autofit_columns(file_path: str):
    wb = openpyxl.load_workbook(file_path)
    for sheet in wb.worksheets:
        for column_cells in sheet.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter
            for cell in column_cells:
                try:
                    length = len(str(cell.value))
                    if length > max_length:
                        max_length = length
                except:
                    pass
            sheet.column_dimensions[column_letter].width = max_length + 2
    wb.save(file_path)

def apply_conditional_formatting(file_path: str):
    wb = openpyxl.load_workbook(file_path)

    for sheet in wb.worksheets:
        header = [cell.value for cell in sheet[1]]

        for row in sheet.iter_rows(min_row=2):
            # vaca balance
            try:
                idx = header.index("Remaining Vacation")
                cell = row[idx]
                if isinstance(cell.value, int) and cell.value <= 3:
                    cell.fill = PatternFill(start_color="FFC7CE", fill_type="solid")
            except:
                pass

            # sick balance
            try:
                idx = header.index("Remaining Sick")
                cell = row[idx]
                if isinstance(cell.value, int) and cell.value <= 2:
                    cell.fill = PatternFill(start_color="FFEB9C", fill_type="solid")
            except:
                pass

            #if there's no leave status
            try:
                idx = header.index("Leave Status")
                cell = row[idx]
                if cell.value == "pending":
                    cell.fill = PatternFill(start_color="FFFF00", fill_type="solid")
            except:
                pass

    wb.save(file_path)

#Excel generator
def generate_excel_report(employees: list, leave_records: list):
    """
    Takes enhanced employees + leave records
    and generates a workbook with 2 sheets:
    Fortnightly & Monthly
    """

    emp_map = {e["id"]: e for e in employees}
    rows = []

    for rec in leave_records:
        emp = emp_map.get(rec.get("employee_id"))
        if not emp:
            continue

        rows.append({
            "Employee ID": safe_get(emp, "id"),
            "Employee Name": safe_get(emp, "name"),
            "Email": safe_get(emp, "email"),
            "Employment Type": safe_get(emp, "type"),
            "Employee Start Date": safe_get(emp, "date_hired"),
            "Length of Service (Years)": safe_get(emp, "service_years"),

            "Leave Type": safe_get(rec, "leave_type"),
            "Leave Status": safe_get(rec, "status"),
            "Start Date": safe_get(rec, "start_date"),
            "End Date": safe_get(rec, "end_date"),

            "Supporting Document Uploaded": safe_get(rec, "has_document"),

            "Remaining Vacation": safe_get(emp, "vacation_balance"),
            "Remaining Sick": safe_get(emp, "sick_balance"),
        })

    if not rows:
        raise ValueError("No leave records found.")

    df = pd.DataFrame(rows)

    # SPLIT SHEETS
    fortnightly = df[df["Employment Type"] == "fortnightly"]
    monthly = df[df["Employment Type"] == "monthly"]

    workbook_path = os.path.join(REPORT_DIR, "combined_leave_report.xlsx")

    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        if not fortnightly.empty:
            fortnightly.to_excel(writer, sheet_name="Fortnightly", index=False)
        if not monthly.empty:
            monthly.to_excel(writer, sheet_name="Monthly", index=False)

    autofit_columns(workbook_path)
    apply_conditional_formatting(workbook_path)

    return workbook_path
