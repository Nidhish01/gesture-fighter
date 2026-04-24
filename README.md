# 🎮 Gesture Fighter - Space Shooter

A unique, hands-free Space Shooter game built with Python, Pygame, and MediaPipe! Control your spaceship using computer vision hand-tracking. Hold an open palm to move, a fist to shoot, and point your finger to do both simultaneously!

## 📸 Demo

*(Add a GIF or screenshot of gameplay here!)*

## ✨ Features

- **Computer Vision Controls**: Play entirely with your webcam using hand gestures.
- **Dynamic Wave System**: Fight through endless waves of enemies, with a Boss appearing every 5 waves.
- **Power-Ups**: Collect Health, Shield, Rapid Fire, Bombs, and Extra Lives.
- **Particle System**: Beautiful explosions, engine trails, and spark effects.
- **Combo System**: Rack up a high score by chaining together enemy kills quickly!

## 🖐️ Gesture Controls

Make sure your webcam is pointing clearly at your hand. The game will track your gestures in real-time.

| Gesture | Action |
| :--- | :--- |
| **Open Palm** | Track and Move the ship |
| **Fist** | Stop moving and Shoot |
| **Pointed Finger** | Move AND Shoot at the same time |
| **Peace Sign** | Activate Shield |
| **Thumbs Up** | Pause / Unpause the game |

*Keyboard Fallback: WASD to move, J/K/L/P for actions.*

## 🚀 Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Nidhish01/gesture-fighter.git
   cd gesture-fighter
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: .\venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: The game requires `mediapipe==0.10.14` to support legacy solutions on Python 3.12)*

4. **Run the Game!**
   ```bash
   python main.py --camera 0
   ```
   *Press `F1` in-game to toggle the camera feed overlay, or `F2` to toggle debug information.*

## 🛠️ Built With
- **[Pygame](https://www.pygame.org/)** - Game engine
- **[MediaPipe](https://developers.google.com/mediapipe)** - Hand tracking machine learning model
- **[OpenCV](https://opencv.org/)** - Webcam capture

## 📝 License
This project is open-source and available under the MIT License.
