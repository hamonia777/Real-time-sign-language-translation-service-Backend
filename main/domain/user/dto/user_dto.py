from dataclasses import dataclass

@dataclass
class UserCreateDomainDto:
    email: str
    nickname: str
    phone_number: str