import traceback
from typing import Dict, Any

from lark.exceptions import VisitError

from pydantic import ValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from optimade.models import Error, ErrorResponse, ErrorSource

from .config import CONFIG
from .routers.utils import meta_values


def general_exception(
    request: Request, exc: Exception, **kwargs: Dict[str, Any]
) -> JSONResponse:
    tb = "".join(
        traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)
    )
    print(tb)

    try:
        status_code = exc.status_code
    except AttributeError:
        status_code = kwargs.get("status_code", 500)

    detail = getattr(exc, "detail", str(exc))

    errors = kwargs.get("errors", None)
    if not errors:
        errors = [
            Error(detail=detail, status=status_code, title=str(exc.__class__.__name__))
        ]

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            ErrorResponse(
                meta=meta_values(
                    url=str(request.url),
                    data_returned=0,
                    data_available=0,
                    more_data_available=False,
                    **{CONFIG.provider["prefix"] + "traceback": tb},
                ),
                errors=errors,
            ),
            exclude_unset=True,
        ),
    )


def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return general_exception(request, exc)


def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    return general_exception(request, exc)


def validation_exception_handler(request: Request, exc: ValidationError):
    status = 500
    title = "ValidationError"
    errors = []
    for error in exc.errors():
        pointer = "/" + "/".join([str(_) for _ in error["loc"]])
        source = ErrorSource(pointer=pointer)
        code = error["type"]
        detail = error["msg"]
        errors.append(
            Error(detail=detail, status=status, title=title, source=source, code=code)
        )
    return general_exception(request, exc, status_code=status, errors=errors)


def grammar_not_implemented_handler(request: Request, exc: VisitError):
    rule = getattr(exc.obj, "data", getattr(exc.obj, "type", str(exc)))

    status = 501
    title = "NotImplementedError"
    detail = (
        f"Error trying to process rule '{rule}'"
        if not str(exc.orig_exc)
        else str(exc.orig_exc)
    )
    error = Error(detail=detail, status=status, title=title)
    return general_exception(request, exc, status_code=status, errors=[error])


def general_exception_handler(request: Request, exc: Exception):
    return general_exception(request, exc)
