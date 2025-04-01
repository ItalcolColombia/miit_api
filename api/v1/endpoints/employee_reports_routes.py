from fastapi import APIRouter, Depends, HTTPException, status
from api.v1.middleware.auth_middleware import get_current_user
from core.di.services import get_employee_reports_service
from services.employee_reports_service import EmployeeReportsService
from schemas.employee import SalaryReport, AgeReport
from schemas.usuarios_schema import UsuarioResponse

router = APIRouter(prefix="/reports/employees", tags=["Employee reports"])

@router.get("/salary/", response_model=SalaryReport)
async def get_salary_report(
    current_user: UsuarioResponse = Depends(get_current_user),
    reports_service: EmployeeReportsService = Depends(get_employee_reports_service)
):
    report = await reports_service.get_salary_report()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No employees found")
    return report

@router.get("/age/", response_model=AgeReport)
async def get_age_report(
    current_user: UsuarioResponse = Depends(get_current_user),
    reports_service: EmployeeReportsService = Depends(get_employee_reports_service)
):
    report = await reports_service.get_age_report()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No employees found")
    return report