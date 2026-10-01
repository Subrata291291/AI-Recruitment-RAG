from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.matching.fit_analysis import match_candidates_to_jd


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.post("")
async def search_candidates(
    company_id: str = Form(...),
    file: UploadFile = File(...),
    top_k: int | None = Form(None),
) -> dict[str, Any]:

    # ---------------------------------------------------------
    # 1. Validate company
    # ---------------------------------------------------------

    if not company_id.strip():
        raise HTTPException(
            status_code=400,
            detail="company_id cannot be empty.",
        )

    # ---------------------------------------------------------
    # 2. Validate uploaded file
    # ---------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="JD file is required.",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF JD files are supported.",
        )

    # ---------------------------------------------------------
    # 3. Validate top_k
    # ---------------------------------------------------------

    if top_k is not None and top_k <= 0:
        raise HTTPException(
            status_code=400,
            detail="top_k must be greater than 0.",
        )

    # ---------------------------------------------------------
    # 4. Save uploaded JD temporarily
    # ---------------------------------------------------------

    temp_dir = Path("data") / "tmp"

    temp_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = temp_dir / file.filename

    try:

        contents = await file.read()

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Uploaded JD file is empty.",
            )

        temp_path.write_bytes(
            contents
        )

        # -----------------------------------------------------
        # 5. Run JD → Candidate matching
        # -----------------------------------------------------

        result = match_candidates_to_jd(
            jd_path=temp_path,
            company_id=company_id,
            top_k=top_k,
        )

        return result

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Candidate search failed: {exc}",
        ) from exc

    finally:

        # -----------------------------------------------------
        # 6. Remove temporary JD
        # -----------------------------------------------------

        if temp_path.exists():

            temp_path.unlink()