import uvicorn
from fastapi import FastAPI
from .routers import common, rank, net

app = FastAPI()

app.include_router(common.router)
app.include_router(rank.router)
app.include_router(net.router)








    

# @app.exception_handler(404)
# async def http_exception_handler(request, exc):
#     return templates.TemplateResponse("errors/404.html", {"request": request})

