# ✨ ledMatrix - LED Display System

Welcome to the **ledMatrix** project, an advanced system designed to create and manage LED matrix displays with features like customizable screen sizes, animated text, GIF display support, and a fully configurable runtime environment. Whether you're building a visual interface for a smart device or creating animated displays, this project provides the foundation.

---

## 📖 Project Description

The **ledMatrix** project enables the creation and control of an LED matrix display system using Python. It allows developers and hardware enthusiasts to build visual applications that are responsive, animated, and highly configurable, using both static and dynamic sources like images and GIFs.

---

## ⚙️ System Behavior

The system operates on a continuous display loop that reads a screen buffer matrix and renders it to an output display (either simulated or connected hardware). Key behaviors include:

- Initialization of a black screen matrix with dimensions defined in the configuration.
- Loading of animated text, static images, or GIFs into the screen buffer.
- Rendering of the display at a fixed frame rate.
- Management of resources such as fonts, images, and animations within their designated modules.

---

## 📂 Code Structure

The repository is organized as follows:

```
ledMatrix/
├── main.py                      # Entry point of the application.
├── config/                      # Configuration files.
│   └── config.yaml              # System configuration (YAML).
├── resource/                    # Media files like images and fonts.
│   ├── *.jpg
│   ├── *.otf
│   └── gifs/                    # GIFs for animations.
├── tools/                       # Utility modules.
│   ├── font.py                  # Scrolling text rendering module.
│   └── image_converter.py       # (Content unavailable)
├── screen.py                    # Screen rendering and display management.
├── configpy.py                  # Configuration loader.
└── requirements.txt             # Python dependencies.
```

---

## 🔌 Hardware Interface

While the current implementation operates in simulation mode, the project is structured to support future integration with hardware-based LED matrices such as:

- WS2812B LED strips
- MAX7219-based LED modules
- Raspberry Pi GPIO-powered matrices

Hardware integration will rely on passing the rendered frame buffer to hardware-specific libraries like `rpi_ws281x` or `luma.led_matrix`.

---

## 📐 Circuit Diagram

*Pending hardware integration – a circuit will be added once hardware modules are implemented.*

---

## 🛠️ Configuration Structure

The system uses a `config.yaml` file located in the `config/` directory to define:

- Screen dimensions
- Frame rate
- Default assets to load
- Font paths and animation settings

Example:

```yaml
display:
  width: 64
  height: 32
  fps: 30

assets:
  font_path: "resource/tiny.otf"
  default_gif: "resource/gifs/cat.gif"
```

---

## 📝 Notes

- This project is currently in **simulation mode**.
- All media files (images, fonts, and GIFs) must be placed in the `resource/` directory.
- Animated text is restricted by pixel width and will auto-scroll when exceeding the display boundary.

---

## ❌ Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` | Missing dependencies | Run `pip install -r requirements.txt` |
| `YAMLError` | Malformed `config.yaml` | Validate YAML formatting |
| `FileNotFound` | Resource not in `resource/` | Move media assets to correct folder |

---

## 🔖 Version

**Current Version:** 1.0.0-alpha  
_Initial release focused on core display functionality and configuration support._

---

## 👥 Team

- **Gabriel** – Lead Developer & System Designer

---

## 💡 Inspirational Phrase

> *"Every pixel tells a story – light it up with purpose."* ✨
