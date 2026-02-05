import random
from typing import List, Optional
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import os

app = FastAPI(title="F1 Strategy Simulator", description="Mock F1 Race Strategy Dashboard")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Mock Data
DRIVERS = {
    "Verstappen": {"base_pace": 80.0, "consistency": 0.95},
    "Hamilton": {"base_pace": 80.2, "consistency": 0.94},
    "Leclerc": {"base_pace": 80.1, "consistency": 0.92},
    "Norris": {"base_pace": 80.3, "consistency": 0.93},
    "Alonso": {"base_pace": 80.4, "consistency": 0.96},
}

TRACKS = {
    "Monza": {"base_time": 78.0, "degradation_factor": 1.1},
    "Silverstone": {"base_time": 86.0, "degradation_factor": 1.2},
    "Spa": {"base_time": 102.0, "degradation_factor": 1.3},
    "Monaco": {"base_time": 70.0, "degradation_factor": 0.8},
}

TYRES = {
    "Soft": {"speed_bonus": -1.5, "degradation_rate": 0.15},
    "Medium": {"speed_bonus": -0.8, "degradation_rate": 0.08},
    "Hard": {"speed_bonus": 0.0, "degradation_rate": 0.04},
}

WEATHER_EFFECTS = {
    "Sunny": {"time_penalty": 0.0, "risk_factor": 1.0},
    "Rainy": {"time_penalty": 12.0, "risk_factor": 1.5},
}

class SimulationRequest(BaseModel):
    driver: str
    track: str
    compound: str
    weather: str
    laps: int

class SimulationResult(BaseModel):
    avg_lap_time: float
    pit_strategy: str
    final_position: int
    lap_data: List[float]
    tyre_data: List[float]
    total_time: float

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/setup", response_class=HTMLResponse)
async def race_setup(request: Request):
    return templates.TemplateResponse("setup.html", {
        "request": request,
        "drivers": list(DRIVERS.keys()),
        "tracks": list(TRACKS.keys()),
        "tyres": list(TYRES.keys()),
        "weather": list(WEATHER_EFFECTS.keys())
    })

@app.post("/api/simulate", response_model=SimulationResult)
async def simulate_race(sim_data: SimulationRequest):
    driver_stats = DRIVERS.get(sim_data.driver, DRIVERS["Verstappen"])
    track_stats = TRACKS.get(sim_data.track, TRACKS["Monza"])
    tyre_stats = TYRES.get(sim_data.compound, TYRES["Medium"])
    weather_stats = WEATHER_EFFECTS.get(sim_data.weather, WEATHER_EFFECTS["Sunny"])
    
    base_lap_time = track_stats["base_time"] + driver_stats["base_pace"] - 80.0 # Normalize base pace
    base_lap_time += tyre_stats["speed_bonus"]
    base_lap_time += weather_stats["time_penalty"]
    
    lap_times = []
    tyre_health = []
    current_tyre_health = 100.0
    
    current_lap_time = base_lap_time
    
    pit_stops = 0
    pit_strategy_text = "1 Stop (Lap " + str(int(sim_data.laps / 2)) + ")"
    
    # Simple strategy logic
    if sim_data.compound == "Soft" and sim_data.laps > 20:
         pit_strategy_text = "2 Stops (Lap " + str(int(sim_data.laps/3)) + ", " + str(int(2*sim_data.laps/3)) + ")"
    elif sim_data.compound == "Hard":
         pit_strategy_text = "1 Stop (Lap " + str(int(sim_data.laps * 0.6)) + ")"

    
    for lap in range(1, sim_data.laps + 1):
        # Degrade tyres
        deg = tyre_stats["degradation_rate"] * track_stats["degradation_factor"]
        # Random variance
        variance = random.uniform(-0.5, 0.5) * (1.0 - driver_stats["consistency"])
        
        # Lap time calculation
        # As tyre health drops, lap time increases
        # 100% health = 0 penalty. 0% health = big penalty
        tyre_factor = (100.0 - current_tyre_health) * 0.05 
        
        lap_time = current_lap_time + tyre_factor + variance
        
        # Pit stop logic (simple simulation)
        if current_tyre_health < 30: # Force pit
            lap_time += 20.0 # Pit stop time
            current_tyre_health = 100.0
            pit_stops += 1
            
        lap_times.append(round(lap_time, 3))
        tyre_health.append(round(current_tyre_health, 1))
        
        current_tyre_health -= deg
        if current_tyre_health < 0: current_tyre_health = 0

    total_time = sum(lap_times)
    avg_lap = total_time / sim_data.laps
    
    # Mock final position based on total time randomness relative to a "winner time"
    # Just random for fun since we don't simulate others
    final_pos = random.randint(1, 20)
    if sim_data.driver in ["Verstappen", "Hamilton", "Leclerc"] and avg_lap < (track_stats["base_time"] + 2.0):
        final_pos = random.randint(1, 4)
        
    return {
        "avg_lap_time": round(avg_lap, 3),
        "pit_strategy": pit_strategy_text,
        "final_position": final_pos,
        "lap_data": lap_times,
        "tyre_data": tyre_health,
        "total_time": round(total_time, 3)
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
