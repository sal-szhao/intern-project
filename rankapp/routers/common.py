from fastapi import APIRouter, Depends, HTTPException, Form
from typing_extensions import Annotated
from ..dependencies import get_db
from ..database import Session
from ..utils import common_utils as common

router = APIRouter(
    prefix="/common",
    tags=["common"],
    # dependencies=[Depends(get_db)],
    # responses={404: {"description": "Not found"}},
)

SessionDep = Annotated[Session, Depends(get_db)]

@router.get("/f_name")
async def get_contract_type(
    db: SessionDep,
):
    contract_types = common.get_contract_type(db=db)

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": contract_types,
    }

@router.get("/f_company")
async def get_contract_type(
    db: SessionDep,
):
    companies = common.get_company(db=db)

    return {
        "code": 200,
        "msg": "success",
        "status": "ok",
        "statusText": "请求成功",
        "data": companies,
    }