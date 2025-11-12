"""
Template Service - Manages notification templates with variable substitution
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.models import ResponseModel, PaginationMeta
from shared.logger import get_logger, set_correlation_id, correlation_id
from database import get_db, init_db
from models import Template, TemplateCreate, TemplateUpdate, TemplateResponse

logger = get_logger(__name__)

app = FastAPI(
    title="Template Service",
    description="Template management service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request, call_next):
    """Add correlation ID to requests"""
    cid = request.headers.get("X-Correlation-ID")
    set_correlation_id(cid)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id.get() or 'no-id'
    return response


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    logger.info("Template Service started")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "template_service"}


@app.post("/api/v1/templates/", response_model=ResponseModel[TemplateResponse], status_code=status.HTTP_201_CREATED)
async def create_template(template_data: TemplateCreate, db: Session = Depends(get_db)):
    """Create a new template"""
    try:
        # Check if template exists
        existing = db.query(Template).filter(Template.code == template_data.code).first()
        if existing:
            return ResponseModel.error_response(
                error="Template with this code already exists",
                message="Template creation failed"
            )

        db_template = Template(
            code=template_data.code,
            name=template_data.name,
            subject=template_data.subject,
            body=template_data.body,
            notification_type=template_data.notification_type,
            language=template_data.language or "en"
        )
        db.add(db_template)
        db.commit()
        db.refresh(db_template)

        logger.info(f"Template created: {template_data.code}")
        # Convert datetime fields to strings for Pydantic v2
        template_dict = {
            "id": str(db_template.id),
            "code": db_template.code,
            "name": db_template.name,
            "subject": db_template.subject,
            "body": db_template.body,
            "notification_type": db_template.notification_type,
            "language": db_template.language,
            "created_at": db_template.created_at.isoformat() if db_template.created_at else None,
            "updated_at": db_template.updated_at.isoformat() if db_template.updated_at else None,
        }
        return ResponseModel.success_response(
            data=TemplateResponse.model_validate(template_dict),
            message="Template created successfully"
        )
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        db.rollback()
        return ResponseModel.error_response(
            error=str(e),
            message="Failed to create template"
        )


@app.get("/api/v1/templates/{template_code}", response_model=ResponseModel[TemplateResponse])
async def get_template(template_code: str, db: Session = Depends(get_db)):
    """Get template by code"""
    try:
        db_template = db.query(Template).filter(Template.code == template_code).first()
        if not db_template:
            return ResponseModel.error_response(
                error="Template not found",
                message="Template retrieval failed"
            )

        # Convert datetime fields to strings for Pydantic v2
        template_dict = {
            "id": str(db_template.id),
            "code": db_template.code,
            "name": db_template.name,
            "subject": db_template.subject,
            "body": db_template.body,
            "notification_type": db_template.notification_type,
            "language": db_template.language,
            "created_at": db_template.created_at.isoformat() if db_template.created_at else None,
            "updated_at": db_template.updated_at.isoformat() if db_template.updated_at else None,
        }
        return ResponseModel.success_response(
            data=TemplateResponse.model_validate(template_dict),
            message="Template retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving template: {e}")
        return ResponseModel.error_response(
            error=str(e),
            message="Failed to retrieve template"
        )


@app.put("/api/v1/templates/{template_code}", response_model=ResponseModel[TemplateResponse])
async def update_template(
    template_code: str,
    template_data: TemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update template"""
    try:
        db_template = db.query(Template).filter(Template.code == template_code).first()
        if not db_template:
            return ResponseModel.error_response(
                error="Template not found",
                message="Template update failed"
            )

        # Update fields
        if template_data.name:
            db_template.name = template_data.name
        if template_data.subject:
            db_template.subject = template_data.subject
        if template_data.body:
            db_template.body = template_data.body
        if template_data.language:
            db_template.language = template_data.language

        db.commit()
        db.refresh(db_template)

        logger.info(f"Template updated: {template_code}")
        # Convert datetime fields to strings for Pydantic v2
        template_dict = {
            "id": str(db_template.id),
            "code": db_template.code,
            "name": db_template.name,
            "subject": db_template.subject,
            "body": db_template.body,
            "notification_type": db_template.notification_type,
            "language": db_template.language,
            "created_at": db_template.created_at.isoformat() if db_template.created_at else None,
            "updated_at": db_template.updated_at.isoformat() if db_template.updated_at else None,
        }
        return ResponseModel.success_response(
            data=TemplateResponse.model_validate(template_dict),
            message="Template updated successfully"
        )
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        db.rollback()
        return ResponseModel.error_response(
            error=str(e),
            message="Failed to update template"
        )


@app.post("/api/v1/templates/{template_code}/render", response_model=ResponseModel[dict])
async def render_template(
    template_code: str,
    variables: dict,
    db: Session = Depends(get_db)
):
    """Render template with variables (supports {{variable}} syntax)"""
    try:
        db_template = db.query(Template).filter(Template.code == template_code).first()
        if not db_template:
            return ResponseModel.error_response(
                error="Template not found",
                message="Template rendering failed"
            )

        # Convert {{variable}} to {variable} for format()
        def convert_template(text: str) -> str:
            import re
            # Replace {{variable}} with {variable}
            return re.sub(r'\{\{(\w+)\}\}', r'{\1}', text)

        # Render subject and body
        subject_template = convert_template(db_template.subject)
        body_template = convert_template(db_template.body)
        
        rendered_subject = subject_template.format(**variables)
        rendered_body = body_template.format(**variables)

        return ResponseModel.success_response(
            data={
                "subject": rendered_subject,
                "body": rendered_body,
                "notification_type": db_template.notification_type
            },
            message="Template rendered successfully"
        )
    except KeyError as e:
        logger.error(f"Missing variable in template: {e}")
        return ResponseModel.error_response(
            error=f"Missing required variable: {e}",
            message="Template rendering failed"
        )
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        return ResponseModel.error_response(
            error=str(e),
            message="Failed to render template"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

