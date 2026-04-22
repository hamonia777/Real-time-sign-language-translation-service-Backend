from main.domain.user.dto.user_dto import UserCreateDomainDto
from main.domain.user.entity.user import User
from main.domain.user.repository.user_repository import UserRepository, get_user_repository
from fastapi import Depends

class UserService:
    def __init__(self, user_repo: UserRepository = Depends(get_user_repository)):
        self.user_repo = user_repo

    async def create_user(self, dto: UserCreateDomainDto) -> User:
        new_user = User(
            email=dto.email,
            nickname=dto.nickname,
            phone_num=dto.phone_number
        )
        return await self.user_repo.save(new_user)