from datetime import timedelta
from app.models.enums import LeaveStatus, LeaveType
from app.models.leave_balance import LeaveBalance
from app.models.leave_request import LeaveRequest

class LeaveService:

    def __init__(self, employee_service):
        self.employee_service = employee_service

    #Keeps count of working days
    def working_days(self, start, end):
        count = 0
        current = start
        while current <= end:
            if current.weekday() < 5:
                count += 1
            current += timedelta(days=1)
        return count
    
    #Leave calculator
    def calc_leave_days(self, request: LeaveRequest, balance: LeaveBalance):
        if request.leave_type == LeaveType.VACATION:
            return self.working_days(request.start_date, request.end_date)
        elif request.leave_type == LeaveType.SICK:
            return (request.end_date - request.start_date) + 1

    #Leave balance check    
    def has_enough(self, balance: LeaveBalance, days_needed):
        return balance.remaining_days >= days_needed
    
    #Deducts leave days from balance
    def deduct_leave(self, balance: LeaveBalance, days):
        balance.used_days += days
        balance.leave_balance()
        self.employee_service.init_leave_balance(balance)

    #Process leave requests
    def process_leave_request(self, leave_request: LeaveRequest, balance: LeaveBalance):
        #Validates leave requests
        leave_request.validate_dates()

        #Check if document is required
        leave_request.req_sick_doc()

        #Calculates leave days requested
        days_requested = self.calc_leave_days(leave_request)

        #Validates remaining balance
        if not self.has_enough(balance, days_requested):
            raise ValueError("Insufficient leave balance.")
        
        #Deducts leave
        self.deduct_leave(balance, days_requested)

        #Automatically updates request status to approved
        leave_request.status = LeaveStatus.APPROVED

        return{
            "request_id": leave_request.id,
            "days_deducted": days_requested,
            "remaining_days": balance.remaining_days,
            "status": leave_request.status
        }