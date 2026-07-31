from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

# Database Models
from app.models.inventory import Inventory
from app.models.orders import Order
from app.models.order_items import OrderItem
from app.models.pick_tasks import PickTask
from app.models.pick_serials import PickSerial

# Routers
from app.routers.inventory import router as inventory_router
from app.routers.orders import router as orders_router
from app.routers.picking import router as picking_router
from app.routers.rf import router as rf_router
from app.routers.scan import router as scan_router
from app.routers.barcode import router as barcode_router
from app.routers import auth
from app.routers import users
from app.routers import dashboard
from app.routers import inventory_transactions

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Warehouse RF System",
    version="1.0.0"
)

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://warehouse-wms-tgaz.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(inventory_router)
app.include_router(orders_router)
app.include_router(picking_router)
app.include_router(rf_router)
app.include_router(scan_router)
app.include_router(barcode_router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(inventory_transactions.router)

@app.get("/")
def home():
    return {
        "message": "Warehouse RF System is Running"
    }