import traceback
from typing import List

from lark.exceptions import VisitError

from pydantic import ValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi import Request
from fastapi.responses import JSONResponse

from optimade.models import OptimadeError, ErrorResponse, ErrorSource

from .config import CONFIG
from .routers.utils import meta_values


def general_exception(
    request: Request,
    exc: Exception,
    status_code: int = 500,  # A status_code in `exc` will take precedence
    errors: List[OptimadeError] = None,
) -> JSONResponse:
    debug_info = {}
    if CONFIG.debug:
        tb = "".join(
            traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)
        )
        print(tb)
        debug_info[f"_{CONFIG.provider.prefix}_traceback"] = tb

    try:
        http_response_code = int(exc.status_code)
    except AttributeError:
        http_response_code = int(status_code)

    try:
        title = str(exc.title)
    except AttributeError:
        title = str(exc.__class__.__name__)

    try:
        detail = str(exc.detail)
    except AttributeError:
        detail = str(exc)

    if errors is None:
        errors = [OptimadeError(detail=detail, status=http_response_code, title=title)]

    try:
        response = ErrorResponse(
            meta=meta_values(
                url=str(request.url),
                data_returned=0,
                data_available=0,
                more_data_available=False,
                **debug_info,
            ),
            errors=errors,
        )
    except Exception:
        # This was introduced due to the original raise of an HTTPException if the
        # path prefix could not be found, e.g., `/v0`.
        # However, due to the testing, this error cannot be raised anymore.
        # Instead, an OPTIMADE warning should be issued.
        # Having this try and except is still good practice though.
        response = ErrorResponse(errors=errors)

    return JSONResponse(
        status_code=http_response_code,
        content=jsonable_encoder(response, exclude_unset=True),
    )


def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return general_exception(request, exc)


def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    return general_exception(request, exc)


def validation_exception_handler(request: Request, exc: ValidationError):
    status = 500
    title = "ValidationError"
    errors = set()
    for error in exc.errors():
        pointer = "/" + "/".join([str(_) for _ in error["loc"]])
        source = ErrorSource(pointer=pointer)
        code = error["type"]
        detail = error["msg"]
        errors.add(
            OptimadeError(
                detail=detail, status=status, title=title, source=source, code=code
            )
        )
    return general_exception(request, exc, status_code=status, errors=list(errors))


def grammar_not_implemented_handler(request: Request, exc: VisitError):
    rule = getattr(exc.obj, "data", getattr(exc.obj, "type", str(exc)))

    status = 501
    title = "NotImplementedError"
    detail = (
        f"Error trying to process rule '{rule}'"
        if not str(exc.orig_exc)
        else str(exc.orig_exc)
    )
    error = OptimadeError(detail=detail, status=status, title=title)
    return general_exception(request, exc, status_code=status, errors=[error])


def not_implemented_handler(request: Request, exc: NotImplementedError):
    status = 501
    title = "NotImplementedError"
    detail = str(exc)
    error = OptimadeError(detail=detail, status=status, title=title)
    return general_exception(request, exc, status_code=status, errors=[error])


def general_exception_handler(request: Request, exc: Exception):
    return general_exception(request, exc)
