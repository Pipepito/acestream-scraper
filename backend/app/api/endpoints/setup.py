"""Wizard endpoints run blocking file I/O in FastAPI's worker pool."""
from fastapi import APIRouter, HTTPException, Response, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.repositories.settings_repository import SettingsRepository
from app.schemas.setup import SetupState, SetupUpdate
from app.services.setup_service import SetupService
from runtime_config import ConfigConflict, ConfigError

router = APIRouter(tags=['setup'])


def _call(action, db):
    try:
        return action(SetupService(SettingsRepository(db)))
    except ConfigConflict as error:
        raise HTTPException(409, str(error)) from None
    except ConfigError as error:
        raise HTTPException(422, str(error)) from None
    except OSError:
        raise HTTPException(503, 'Cannot access runtime configuration. Check permissions on the database directory.') from None


@router.get('', response_model=SetupState)
def get_setup(response: Response, db: Session = Depends(get_db)):
    response.headers['Cache-Control'] = 'no-store'
    return _call(lambda service: service.state(), db)


@router.put('', response_model=SetupState)
def save_setup(request: SetupUpdate, response: Response, db: Session = Depends(get_db)):
    response.headers['Cache-Control'] = 'no-store'
    return _call(lambda service: service.save(request), db)
