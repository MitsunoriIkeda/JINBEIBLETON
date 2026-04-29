# Retro-Game AI Music Assistant Station (Skeleton version)

This project is a modular, event-driven AI composition station designed to bridge voice-controlled AI generation with Ableton Live.

## 🚀 Getting Started

### Prerequisites
- **Node.js**: v18+ (Frontend)
- **Python**: v3.9+ (Backend Bridge)
- **Ableton Live**: To receive and send OSC messages.

### Installation

1. **Frontend**:
   ```bash
   cd client
   npm install
   npm run dev
   ```

2. **Backend**:
   ```bash
   cd server
   source venv/bin/activate
   pip install -r requirements.txt
   python main.py
   ```

## 🏗️ Architecture

- **EventBus**: Decoupled message routing between UI and logic.
- **AppState**: Single source of truth for Project Context (`Key`, `BPM`, `Time`).
- **OSC Bridge**: Python FastAPI server bridging WebSocket (Browser) and UDP OSC (Ableton).

## 🎨 Asset Placement
Place your PNG assets in `client/public/assets/`. 
Required files:
- `start.png`, `dog.png`, `signboard-yellow.png`
- `car-green.png`, `car-yellow.png`, `car-red.png`, `car-blue.png`
- `plane-green.png`, `plane-pink.png`, `tractor.png`, `title.png`
- `bgm.mp3`

## 🎹 Global Constraints
The **Key (Tonality)** context is automatically injected into all AI prompt generations via `AIModules.wrapPromptWithContext()`. This ensures absolute consistency across Sample, MIDI, and Analysis generations.

---
**Design Tone**: 90s Arcade / 3DO / Future-Retro.
