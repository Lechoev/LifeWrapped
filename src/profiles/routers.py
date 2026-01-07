from datetime import date
from typing import Optional

from fastapi import APIRouter, UploadFile
from fastapi.params import Depends, File, Form

from src.auth_user.dependencies import get_current_verified_user

from src.common.decorators import file_exceptions
from src.common.utils import upload_img

from src.profiles.decorators import profile_exceptions
from src.profiles.services import ProfileService
from src.profiles.dependencies import get_profile_service

router = APIRouter(tags=["profiles"])


@router.post('/v1/create-profiles')
@profile_exceptions
@file_exceptions
async def create_profiles(
        first_name: Optional[str] = Form(None, max_length=100, min_length=3),
        last_name: Optional[str] = Form(None, max_length=100, min_length=3),
        bio: Optional[str] = Form(None),
        avatar: Optional[UploadFile] = File(None),
        birth_date: Optional[date] = Form(None),
        service: ProfileService = Depends(get_profile_service),
        current_user: int = Depends(get_current_verified_user),
) -> dict:
    avatar_path = await upload_img(img=avatar, user_id=current_user) if avatar else None
    profile_data = {
        "user_id": current_user,
        "first_name": first_name,
        "last_name": last_name,
        "bio": bio,
        "birth_date": birth_date,
        "avatar_url": avatar_path,
    }
    result = await service.create_profile(user_id=current_user, profile_data=profile_data)
    return {'status': 'success', 'data': result}


@router.patch('/v1/update-profiles')
@profile_exceptions
@file_exceptions
async def update_profiles(
        current_user: int = Depends(get_current_verified_user),
        first_name: Optional[str] = Form(None, max_length=100),
        last_name: Optional[str] = Form(None, max_length=100),
        bio: Optional[str] = Form(None, max_length=1000),
        birth_date: Optional[date] = Form(None),
        avatar: Optional[UploadFile] = File(None),
        services: ProfileService = Depends(get_profile_service),
) -> dict:
    update_data = {}
    if first_name is not None:
        update_data["first_name"] = first_name
    if last_name is not None:
        update_data["last_name"] = last_name
    if bio is not None:
        update_data["bio"] = bio
    if birth_date is not None:
        update_data["birth_date"] = birth_date

    if avatar:
        avatar_path = await upload_img(img=avatar, user_id=current_user)
        update_data["avatar_url"] = avatar_path
    await services.update_profile(user_id=current_user, update_data=update_data)
    return {"status": "success", "msg": "Профиль успешно обновлён", "data": update_data}


@router.get('/v1/get-profiles')
@profile_exceptions
async def get_profiles(
        current_user: int = Depends(get_current_verified_user),
        services: ProfileService = Depends(get_profile_service),
):
    result = await services.get_profile(user_id=current_user)
    return {"status": "success", "data": result}
