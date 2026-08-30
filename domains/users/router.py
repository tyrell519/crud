from fastapi import APIRouter, Depends

from domains.users.dependencies import get_user_service
from domains.users.schemas import UserCreate, UserOut, UserUpdate
from domains.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", status_code=201, response_model=UserOut)
def create_user(payload: UserCreate, service: UserService = Depends(get_user_service)):
    return service.create_user(payload)


@router.get("", response_model=list[UserOut])
def list_users(service: UserService = Depends(get_user_service)):
    return service.list_users()


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    return service.get_user(user_id)


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    service: UserService = Depends(get_user_service),
):
    return service.update_user(user_id, payload)


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, service: UserService = Depends(get_user_service)):
    service.delete_user(user_id)
