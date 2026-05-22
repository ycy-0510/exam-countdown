from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from ..app import templates
from ..auth import verify_credentials

router = APIRouter(tags=["Auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/config")
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(),
    password: str = Form(),
):
    login_success = verify_credentials(username=username, password=password)
    if login_success:
        request.session["user"] = username
        return RedirectResponse("/config", status_code=303)
    else:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Username or Password is wrong!"},
            status_code=401,
        )
    
@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")
