from datetime import date

from sqlmodel import Session, select

from app.models.employee import Employee
from app.models.enums import PaymentType, LeaveType
from app.models.leave_balance import LeaveBalance


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
    def init_leave_balance(session: Session, employee: Employee, year: int) -> None:
        """Initializes/updates the leave balances for an employee for a given year"""

        # Calculate the leave entitlements for employee
        vacation_days = EmployeeService.calc_vacation_days(employee.date_hired, employee.type)
        sick_days = EmployeeService.calc_sick_days(employee.date_hired)

        # VACATION DAYS
        # Query the database to check if employee already has stored vacation days for a given year
        vacation_balance = session.exec(
            select(LeaveBalance).where(
                LeaveBalance.employee_id == employee.id,
                LeaveBalance.year == year,
                LeaveBalance.leave_type == LeaveType.VACATION
            )
        ).first()

        # Update existing record incase leave policy has changed
        if vacation_balance:
            vacation_balance.entitled_days = vacation_days
            vacation_balance.remaining_days = vacation_days - vacation_balance.used_days
        else:
            vacation_balance = LeaveBalance(
                employee_id = employee.id,
                year = year,
                leave_type = LeaveType.VACATION,
                entitled_days = vacation_days,
                remaining_days = vacation_days
            )
            session.add(vacation_balance)

        # SICK DAYS
        sick_balance = session.exec(
            select(LeaveBalance).where(
                LeaveBalance.employee_id == employee.id,
                LeaveBalance.year == year,
                LeaveBalance.leave_type == LeaveType.SICK
            )
        ).first()

        if sick_balance:
            sick_balance.entitled_days = sick_days
            sick_balance.remaining_days = sick_days - sick_balance.used_days
        else:
            sick_balance = LeaveBalance(
                employee_id=employee.id,
                year=year,
                leave_type=LeaveType.VACATION,
                entitled_days=sick_days,
                remaining_days=sick_days
            )
            session.add(sick_balance)

        session.commit()