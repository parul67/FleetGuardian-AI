import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from prometheus_fastapi_instrumentator import Instrumentator


from app.core.config import settings
from app.core.logger import logger
from app.api import api_router
from app.database.session import Base, engine, get_db, SessionLocal
from app.middleware.db_session import DBSessionMiddleware
from app.websocket.manager import video_ws_manager, alert_ws_manager
from app.cv.simulator import driver_cv_simulator
from app.pipelines.safety import safety_pipeline

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    logger.info("Starting up FleetGuardian AI Backend...")
    Base.metadata.create_all(bind=engine)
    
    # Seed default user if none exist
    db = SessionLocal()
    try:
        from app.models.user import User
        from app.core.security import get_password_hash
        if db.query(User).count() == 0:
            logger.info("No users found in database. Seeding default admin user...")
            admin_user = User(
                email="admin@fleetguardian.ai",
                hashed_password=get_password_hash("password123"),
                full_name="Fleet Administrator",
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            logger.info("Seeded default admin user: admin@fleetguardian.ai / password123")
    except Exception as e:
        logger.error(f"Error seeding default user: {e}")
    finally:
        db.close()
        
    yield
    # Shutdown
    logger.info("Shutting down FleetGuardian AI Backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Real-Time Fleet Safety Monitoring Platform API",
    version="1.0.0",
    lifespan=lifespan
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# DB Session Middleware
app.add_middleware(DBSessionMiddleware)

# Prometheus metrics instrumentation (exposes /metrics endpoint)
Instrumentator().instrument(app).expose(app, include_in_schema=False, tags=["monitoring"])

# Mount REST API
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": time.time()}

# WebSocket: Live Alerts Broadcast
@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await alert_ws_manager.connect(websocket)
    logger.info("New client connected to Alerts WebSocket")
    try:
        while True:
            # Keep connection alive by receiving messages
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        alert_ws_manager.disconnect(websocket)
        logger.info("Client disconnected from Alerts WebSocket")

# WebSocket: Live Video Streaming (processes uploads or streams simulation)
@app.websocket("/ws/video")
async def websocket_video(websocket: WebSocket, db: Session = Depends(get_db)):
    await video_ws_manager.connect(websocket)
    logger.info("New client connected to Video WebSocket")
    
    # State flags for driving simulation loop
    streaming_task = None
    
    async def simulation_loop(driver_id: int, vehicle_id: int, trip_id: int):
        try:
            while True:
                # Generate a simulated driving frame and metric payload
                frame, telemetry = driver_cv_simulator.generate_frame()
                
                # Execute integrated safety pipeline (CV + ML + Alerts)
                result = safety_pipeline.process_driving_frame(
                    db, frame=frame, telemetry=telemetry, trip_id=trip_id,
                    driver_id=driver_id, vehicle_id=vehicle_id
                )
                
                # If alerts were triggered, broadcast them to the alert socket
                if result["alerts"]:
                    for a in result["alerts"]:
                        await alert_ws_manager.broadcast({
                            "event": "alert_triggered",
                            "alert": a,
                            "driver_id": driver_id,
                            "vehicle_id": vehicle_id
                        })
                
                # Send processed base64 frame and telemetry to video subscriber
                await websocket.send_json({
                    "image": result["image"],
                    "metrics": result["metrics"],
                    "risk_level": result["risk_level"]
                })
                
                await asyncio.sleep(0.15) # ~6-7 FPS for visual smoothness
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in video simulation loop: {e}")

    try:
        while True:
            # Client sends configuration payload (e.g. driver_id, vehicle_id, trip_id)
            # or binary/base64 frames to process.
            msg = await websocket.receive_json()
            action = msg.get("action")
            
            if action == "start_stream":
                # Start simulator for this driver & vehicle
                driver_id = msg.get("driver_id", 1)
                vehicle_id = msg.get("vehicle_id", 1)
                trip_id = msg.get("trip_id", 1)
                
                # Cancel existing streaming task if running
                if streaming_task:
                    streaming_task.cancel()
                    
                # Launch background task for simulation feed
                streaming_task = asyncio.create_task(simulation_loop(driver_id, vehicle_id, trip_id))
                await websocket.send_json({"status": "stream_started"})
                
            elif action == "stop_stream":
                if streaming_task:
                    streaming_task.cancel()
                    streaming_task = None
                await websocket.send_json({"status": "stream_stopped"})
                
            elif action == "upload_frame":
                # Handle direct frame upload from user's camera
                image_data = msg.get("image")
                if image_data:
                    # Strip base64 header
                    if "," in image_data:
                        image_data = image_data.split(",")[1]
                    import base64
                    import cv2
                    import numpy as np
                    
                    img_bytes = base64.b64decode(image_data)
                    nparr = np.frombuffer(img_bytes, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        driver_id = msg.get("driver_id", 1)
                        vehicle_id = msg.get("vehicle_id", 1)
                        trip_id = msg.get("trip_id", 1)
                        telemetry = msg.get("telemetry", {"speed": 55.0})
                        
                        result = safety_pipeline.process_driving_frame(
                            db, frame=frame, telemetry=telemetry, trip_id=trip_id,
                            driver_id=driver_id, vehicle_id=vehicle_id
                        )
                        
                        # Broadcast alerts
                        if result["alerts"]:
                            for a in result["alerts"]:
                                await alert_ws_manager.broadcast({
                                    "event": "alert_triggered",
                                    "alert": a,
                                    "driver_id": driver_id,
                                    "vehicle_id": vehicle_id
                                })

                        await websocket.send_json({
                            "image": result["image"],
                            "metrics": result["metrics"],
                            "risk_level": result["risk_level"]
                        })

    except WebSocketDisconnect:
        if streaming_task:
            streaming_task.cancel()
        video_ws_manager.disconnect(websocket)
        logger.info("Client disconnected from Video WebSocket")
