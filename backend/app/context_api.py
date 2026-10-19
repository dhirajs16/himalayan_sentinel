"""Public, bounded read-only contextual evidence routes."""

from fastapi import APIRouter, HTTPException, Query

from app.context_data import store

router = APIRouter(prefix="/api/v1/public/context", tags=["public context"])


@router.get("/catalog")
def catalog():
    return store.catalog()


@router.get("/lakes")
def lakes(
    q: str = Query("", max_length=150),
    country: str = Query("", max_length=80),
    basin: str = Query("", max_length=80),
    district: str = Query("", max_length=80),
    offset: int = Query(0, ge=0, le=100000),
    limit: int = Query(50, ge=1, le=100),
):
    return store.query(
        "lakes",
        q=q,
        country=country,
        basin=basin,
        district=district,
        offset=offset,
        limit=limit,
    )


@router.get("/events")
def events(
    q: str = Query("", max_length=150),
    country: str = Query("", max_length=80),
    basin: str = Query("", max_length=80),
    district: str = Query("", max_length=80),
    offset: int = Query(0, ge=0, le=100000),
    limit: int = Query(50, ge=1, le=100),
):
    return store.query(
        "events",
        q=q,
        country=country,
        basin=basin,
        district=district,
        offset=offset,
        limit=limit,
    )


@router.get("/population/{district}")
def population(district: str):
    if len(district) > 80:
        raise HTTPException(status_code=422, detail="District name is too long")
    try:
        return store.population(district)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown district") from None
