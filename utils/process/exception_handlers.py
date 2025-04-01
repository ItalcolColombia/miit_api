# # app/core/exception_handlers.py
# from fastapi import Request, HTTPException
# from fastapi.responses import JSONResponse
#
# async def http_exception_handler(request: Request, exc: HTTPException):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"detail": exc.detail},
#     )
#
# async def general_exception_handler(request: Request, exc: Exception):
#     return JSONResponse(
#         status_code=500,
#         content={"detail": "An unexpected error occurred."},
#     )
#
# async def on_auth_error(request: Request, exc: Exception):
#     return JSONResponse(
#         status_code=401,
#         content={"detail": "Authentication failed."},
#     )