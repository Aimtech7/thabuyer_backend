"""core/exceptions.py - Centralized exception handling"""
import logging
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent JSON error responses.
    """
    # Call DRF's default handler first
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            'status': 'error',
            'code': response.status_code,
            'message': _get_error_message(exc),
            'errors': response.data,
        }
        response.data = error_data
        return response

    # Handle Django's ValidationError
    if isinstance(exc, DjangoValidationError):
        data = {
            'status': 'error',
            'code': status.HTTP_400_BAD_REQUEST,
            'message': 'Validation error',
            'errors': exc.message_dict if hasattr(exc, 'message_dict') else {'non_field_errors': exc.messages},
        }
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    # Log unhandled exceptions
    logger.exception('Unhandled exception', exc_info=exc)
    return Response(
        {
            'status': 'error',
            'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'message': 'An internal server error occurred.',
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _get_error_message(exc):
    if isinstance(exc, exceptions.AuthenticationFailed):
        return 'Authentication failed.'
    if isinstance(exc, exceptions.NotAuthenticated):
        return 'Authentication credentials were not provided.'
    if isinstance(exc, exceptions.PermissionDenied):
        return 'You do not have permission to perform this action.'
    if isinstance(exc, Http404):
        return 'The requested resource was not found.'
    if isinstance(exc, exceptions.ValidationError):
        return 'Validation error. Please check your input.'
    if isinstance(exc, exceptions.Throttled):
        return f'Request was throttled. Expected available in {exc.wait} seconds.'
    return 'An error occurred.'
