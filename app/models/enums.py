from enum import  Enum

class PaymentType(str, Enum):
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"

class LeaveType(str, Enum):
    VACATION = "vacation"
    SICK = "sick"

class LeaveStatus(str, Enum):
    APPROVED = "approved"
    DENIED = "denied"
    PENDING = "pending"
    FLAGGED = "flagged"

class Role(str, Enum):
    HR = "hr"
    ACCOUNTS = "accounts"
    MANAGER = "manager"