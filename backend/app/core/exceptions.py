import logging
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers global exception handlers enforcing a standardized error response envelope:
    {
        "code": str,
        "message": str,
        "details": dict | list | None
    }
    """
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        code_map = {
            status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
            status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
            status.HTTP_403_FORBIDDEN: "FORBIDDEN",
            status.HTTP_404_NOT_FOUND: "NOT_FOUND",
            status.HTTP_409_CONFLICT: "CONFLICT",
            status.HTTP_422_UNPROCESSABLE_ENTITY: "UNPROCESSABLE_ENTITY",
        }
        error_code = code_map.get(exc.status_code, "HTTP_ERROR")
        
        detail_msg = exc.detail if isinstance(exc.detail, str) else "An HTTP error occurred."
        details_payload = exc.detail if not isinstance(exc.detail, str) else None

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": error_code,
                "message": detail_msg,
                "details": details_payload
            },
            headers=getattr(exc, "headers", None)
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": "VALIDATION_ERROR",
                "message": "Request payload validation failed.",
                "details": exc.errors()
            }
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "N/A")
        logger.error(f"[RequestID: {request_id}] Unhandled server exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred.",
                "details": None
            }
        )
