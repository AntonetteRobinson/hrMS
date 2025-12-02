from datetime import date

import app.database as db
from app.models.enums import PaymentType, LeaveType
from app.models.leave_balance import LeaveBalance

def parse_date(d) -> date:
    """Convert string to date"""
    return date.fromisoformat(d) if isinstance(d, str) else d


class EmployeeService:
    """Handles calculations/logic related to an employee"""

    @staticmethod
    def calc_years_of_service(date_hired: date) -> int:
        """Calculates the years of service from the date dired"""
        today = date.today()
        years = today.year - date_hired.year
        if today.month < date_hired.month or (today.month == date_hired.month and today.day < date_hired.day):
            years -= 1
        return years

    @staticmethod
    def calc_vacation_days(date_hired: date, pay_type: PaymentType):
        """Calculates vacation days based on length of service and pay type"""
        years = EmployeeService.calc_years_of_service(date_hired)

        if pay_type == PaymentType.FORTNIGHTLY:
            return 10 if years < 7 else 15
        else:
            if years < 5:
                return 10
            elif years < 10:
                return 15
            return 20

    @staticmethod
    def calc_sick_days(date_hired: date) -> int:
        """Calculates sick days based on length of service"""
        years = EmployeeService.calc_years_of_service(date_hired)
        return 10 if years >= 1 else 0

    @staticmethod
    def init_leave_balance(employee: dict, year: int) -> None:
        """Initializes/updates the leave balances for an employee for a given year"""

        # Calculate the leave entitlements for employee
        vacation_days = EmployeeService.calc_vacation_days(parse_date(employee["date_hired"]), employee["type"])
        sick_days = EmployeeService.calc_sick_days(parse_date(employee["date_hired"]))


        # VACATION DAYS
        # Query the database to check if employee already has stored vacation days for a given year
        vacation_balance = db.find_one("leave_balances", employee_id=employee["id"], year=year, leave_type=LeaveType.VACATION)

        # Update existing record incase leave policy has changed
        if vacation_balance:
            db.update_record("leave_balances", vacation_balance["id"],{
                "entitled_days": vacation_days,
                "remaining_days": vacation_days - vacation_balance["used_days"],
                "last_updated": date.today()
            })
        else:
            db.create_record("leave_balances", {
                "employee_id": employee["id"],
                "year": year,
                "leave_type": LeaveType.VACATION,
                "entitled_days": vacation_days,
                "used_days": 0,
                "remaining_days": vacation_days,
                "last_updated": date.today()
            })


        # SICK DAYS
        sick_balance = db.find("leave_balances", employee_id=employee["id"], year=year, leave_type=LeaveType.SICK)

        if sick_balance:
            db.update_record("leave_balances", sick_balance["id"], {
                "entitled_days": sick_days,
                "remaining_days": sick_days - sick_balance["used_days"],
                "last_updated": date.today()
            })
        else:
            db.create_record("leave_balances", {
                "employee_id": employee["id"],
                "year": year,
                "leave_type": LeaveType.SICK,
                "entitled_days": sick_days,
                "used_days": 0,
                "remaining_days": sick_days,
                "last_updated": date.today()
            })