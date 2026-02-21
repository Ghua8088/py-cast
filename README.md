![Bite Banner](bite-banner.png)

# Bite 

**Bite** is a blazing fast, cross-platform extensible launcher designed to replace your default system spotlight. Built with **Pytron Kit**, it combines the speed of native system integration with the flexibility of web technologies.

> *Inspired by Raycast and Alfred, but built for cross-platform efficiency.*

## [**Download Bite**](https://pytron-kit.github.io/bite)

##  Features
Bite is absolutely packed with tools, settings, and native system integration to supercharge your workflow. Because there are so many built-in capabilities, we've moved the full breakdown into its own document!

📖 **[Read the Full Feature List here](features.md)**

## ️ Installation

### Running from Source
Ensure you have [Python 3.8+](https://www.python.org/) and [Node.js](https://nodejs.org/) installed.

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/bite.git
   cd bite
   ```

2. **Install Dependencies**
   ```bash
   pip install pytron-kit
   pytron install
   ```

3. **Run Bite**
   ```bash
   python app.py
   ```

###  Building for Production
To create a standalone executable:

```bash
python packaging/package.py
```

## ️ Usage

| Shortcut | Action |
|----------|--------|
| **`Alt + B`** | Toggle Bite Search Bar |
| `Esc` | Close Bite |
| `Enter` | Execute / Open Result |

### Power User Tips
- Type **`re:`** followed by a regex pattern to advanced-search files.
- Type a path (e.g., `C:\` or `/`) to navigate directories instantly.
- Type **`calc`** or just numbers to use the calculator.

## ️ Built With
- **[Pytron Kit](https://github.com/pytron-kit)** - Electronic-like framework for Python.
- **React** - Frontend UI.
- **Vite** - Build tool.
