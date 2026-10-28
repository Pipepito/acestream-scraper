"""Wizard endpoints run blocking file I/O in FastAPI's worker pool."""
from fastapi import APIRouter, HTTPException, Response
from app.schemas.setup import SetupState, SetupUpdate
from app.services.setup_service import SetupService
from runtime_config import ConfigConflict, ConfigError

router = APIRouter(tags=['setup'])


def _call(action):
    try:
        return action(SetupService())
    except ConfigConflict as error:
        raise HTTPException(409, str(error)) from None
    except ConfigError as error:
        raise HTTPException(422, str(error)) from None
    except OSError:
        raise HTTPException(503, 'Cannot access runtime configuration. Check permissions on the database directory.') from None


@router.get('', response_model=SetupState)
def get_setup(response: Response):
    response.headers['Cache-Control'] = 'no-store'
    return _call(lambda service: service.state())


@router.put('', response_model=SetupState)
def save_setup(request: SetupUpdate, response: Response):
    response.headers['Cache-Control'] = 'no-store'
    return _call(lambda service: service.save(request))
