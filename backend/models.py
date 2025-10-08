from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict


class PersonalInfo(BaseModel):
    name: str
    email: str
    phone: str
    nationality: Optional[str] = None
    age: Optional[int] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    languages: Optional[List[str]] = None


class Education(BaseModel):
    degree: str
    institution: str
    location: str
    year: str
    description: Optional[str] = None
    grade: Optional[str] = None


class Experience(BaseModel):
    title: str
    company: str
    location: str
    years: str
    description: Optional[str] = None
    descrition_list: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    reference: Optional[str] = None
    reference_letter_url: Optional[str] = None


class Project(BaseModel):
    name: str
    role: str
    year: str
    description: str
    skills: Optional[List[str]] = None
    url: Optional[str] = None


class ProfileData(BaseModel):
    personal_info: PersonalInfo
    summary: str
    education: List[Education]
    experience: List[Experience]
    projects: List[Project]
    skills: List[str]


class ProfileResponse(BaseModel):
    id: str
    user_id: str
    profile_data: ProfileData
    created_at: datetime
    updated_at: datetime
