#!/usr/bin/env python3
"""Generate the Voice Typing Setup Guide PDF."""

from fpdf import FPDF


class GuidePDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(130, 130, 130)
            self.cell(0, 10, "Voice Typing - Setup Guide", align="C", new_x="LMARGIN", new_y="NEXT")
            self.line(10, 18, 200, 18)
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def title_page(self):
        self.add_page()
        self.ln(60)
        self.set_font("Helvetica", "B", 36)
        self.set_text_color(30, 30, 30)
        self.cell(0, 20, "Voice Typing", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_font("Helvetica", "", 18)
        self.set_text_color(80, 80, 80)
        self.cell(0, 12, "Setup Guide", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(8)
        self.set_font("Helvetica", "", 12)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, "Hold a key, speak, text appears.", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 10, "Offline voice typing powered by OpenAI Whisper.", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(30)
        self.set_draw_color(200, 200, 200)
        self.line(60, self.get_y(), 150, self.get_y())
        self.ln(10)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "Supports macOS and Windows", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 8, "Works completely offline - no internet needed after setup", align="C", new_x="LMARGIN", new_y="NEXT")

    def section_title(self, title):
        self.ln(6)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(30, 30, 30)
        self.cell(0, 14, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(50, 120, 200)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 80, self.get_y())
        self.set_line_width(0.2)
        self.ln(6)

    def sub_title(self, title):
        self.ln(4)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(50, 50, 50)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text):
        self.set_font("Helvetica", "", 11)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 7, text)
        self.ln(2)

    def step(self, number, title, description):
        self.ln(2)
        # Step number circle
        self.set_fill_color(50, 120, 200)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 12)
        x = self.get_x()
        y = self.get_y()
        self.ellipse(x, y, 9, 9, style="F")
        self.set_xy(x, y + 0.5)
        self.cell(9, 8, str(number), align="C")
        # Step title
        self.set_xy(x + 12, y)
        self.set_text_color(30, 30, 30)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
        # Step description
        self.set_x(x + 12)
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(70, 70, 70)
        self.multi_cell(170, 6.5, description)
        self.ln(2)

    def code_block(self, code):
        self.set_font("Courier", "", 10)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(30, 30, 30)
        self.set_draw_color(200, 200, 200)
        x = self.get_x() + 12
        self.set_x(x)
        lines = code.strip().split("\n")
        block_height = len(lines) * 7 + 8
        self.rect(x, self.get_y(), 165, block_height, style="FD")
        self.ln(4)
        for line in lines:
            self.set_x(x + 4)
            self.cell(0, 7, line, new_x="LMARGIN", new_y="NEXT")
        self.ln(6)

    def tip_box(self, text):
        self.ln(2)
        self.set_fill_color(230, 245, 255)
        self.set_draw_color(50, 120, 200)
        x = self.get_x()
        y = self.get_y()
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(50, 120, 200)
        # Calculate height
        self.set_xy(x + 4, y + 4)
        self.cell(10, 6, "TIP:")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 80, 120)
        self.multi_cell(160, 6, text)
        h = self.get_y() - y + 4
        self.rect(x, y, 180, h, style="FD")
        # Re-draw text on top
        self.set_xy(x + 4, y + 4)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(50, 120, 200)
        self.cell(10, 6, "TIP:")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 80, 120)
        self.multi_cell(160, 6, text)
        self.ln(4)

    def warning_box(self, text):
        self.ln(2)
        self.set_fill_color(255, 245, 230)
        self.set_draw_color(220, 150, 50)
        x = self.get_x()
        y = self.get_y()
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(200, 120, 20)
        self.set_xy(x + 4, y + 4)
        self.cell(20, 6, "NOTE:")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(140, 90, 20)
        self.multi_cell(155, 6, text)
        h = self.get_y() - y + 4
        self.rect(x, y, 180, h, style="FD")
        # Re-draw
        self.set_xy(x + 4, y + 4)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(200, 120, 20)
        self.cell(20, 6, "NOTE:")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(140, 90, 20)
        self.multi_cell(155, 6, text)
        self.ln(4)

    def table_row(self, col1, col2, col3, col4, is_header=False):
        self.set_font("Helvetica", "B" if is_header else "", 10)
        if is_header:
            self.set_fill_color(50, 120, 200)
            self.set_text_color(255, 255, 255)
        else:
            self.set_fill_color(245, 245, 245) if self.get_y() % 2 == 0 else self.set_fill_color(255, 255, 255)
            self.set_text_color(50, 50, 50)
        self.cell(30, 8, col1, border=1, fill=True, align="C")
        self.cell(30, 8, col2, border=1, fill=True, align="C")
        self.cell(30, 8, col3, border=1, fill=True, align="C")
        self.cell(40, 8, col4, border=1, fill=True, align="C")
        self.ln()


def generate():
    pdf = GuidePDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ============================================================
    # TITLE PAGE
    # ============================================================
    pdf.title_page()

    # ============================================================
    # TABLE OF CONTENTS
    # ============================================================
    pdf.add_page()
    pdf.section_title("Table of Contents")
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(50, 50, 50)
    toc = [
        ("1.", "What is Voice Typing?"),
        ("2.", "What You Need"),
        ("3.", "macOS Setup (Automatic)"),
        ("4.", "Windows Setup (Automatic)"),
        ("5.", "macOS Permissions (Important!)"),
        ("6.", "How to Use Voice Typing"),
        ("7.", "Changing Settings"),
        ("8.", "Available Whisper Models"),
        ("9.", "Troubleshooting"),
        ("10.", "Useful Commands"),
    ]
    for num, item in toc:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(12, 9, num)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 9, item, new_x="LMARGIN", new_y="NEXT")

    # ============================================================
    # SECTION 1: What is Voice Typing?
    # ============================================================
    pdf.add_page()
    pdf.section_title("1. What is Voice Typing?")
    pdf.body_text(
        "Voice Typing is a simple app that lets you type with your voice. "
        "Just hold down a key on your keyboard, speak into your microphone, "
        "and your words will appear wherever your cursor is - in any app!"
    )
    pdf.body_text(
        "The best part? Everything runs on your computer. Your voice never "
        "leaves your machine. No internet connection is needed after the "
        "initial setup. It uses a technology called Whisper (made by OpenAI) "
        "to understand your speech."
    )

    pdf.sub_title("Key Features")
    features = [
        "Works offline - no internet needed after setup",
        "Works in any app - Word, browsers, chat apps, etc.",
        "Supports many languages (auto-detects by default)",
        "Runs quietly in the background",
        "Starts automatically when you turn on your computer",
    ]
    for f in features:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(50, 50, 50)
        pdf.set_x(15)
        pdf.cell(5, 7, "-")
        pdf.cell(0, 7, f, new_x="LMARGIN", new_y="NEXT")

    # ============================================================
    # SECTION 2: What You Need
    # ============================================================
    pdf.add_page()
    pdf.section_title("2. What You Need")
    pdf.body_text("Before you start, make sure you have these things:")

    pdf.sub_title("For Both macOS and Windows")
    reqs = [
        "A working microphone (built-in or external)",
        "An internet connection (only for the initial setup to download files)",
        "About 500 MB of free disk space",
    ]
    for r in reqs:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(50, 50, 50)
        pdf.set_x(15)
        pdf.cell(5, 7, "-")
        pdf.cell(0, 7, r, new_x="LMARGIN", new_y="NEXT")

    pdf.sub_title("Software Requirements")
    pdf.body_text(
        "Python 3.10 or higher must be installed on your computer. "
        "Don't worry if you don't have it - the steps below will guide you "
        "through installing it."
    )

    # ============================================================
    # SECTION 3: macOS Setup
    # ============================================================
    pdf.add_page()
    pdf.section_title("3. macOS Setup (Automatic)")
    pdf.body_text(
        "Follow these steps carefully. Each step is explained in simple "
        "language. If you get stuck, check the Troubleshooting section at the end."
    )

    pdf.sub_title("Part A: Install Python (if not installed)")
    pdf.step(1, "Open Terminal",
             'Press Command + Space to open Spotlight Search. Type "Terminal" and press Enter. '
             "A black/white window will open - this is where you type commands.")
    pdf.step(2, "Check if Python is installed",
             "Type this command and press Enter:")
    pdf.code_block("python3 --version")
    pdf.body_text(
        'If you see something like "Python 3.10.0" or higher, Python is already installed. '
        "Skip to Part B. If you see an error, continue to Step 3."
    )
    pdf.step(3, "Install Python using Homebrew",
             "First, install Homebrew (a tool that helps install software). "
             "Copy and paste this entire line into Terminal and press Enter:")
    pdf.code_block('/bin/bash -c "$(curl -fsSL\n  https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
    pdf.body_text("Wait for it to finish (it may ask for your password). Then install Python:")
    pdf.code_block("brew install python")

    pdf.add_page()
    pdf.sub_title("Part B: Install Voice Typing")
    pdf.step(4, "Download Voice Typing",
             "If you have the voice_typing folder already, skip this step. "
             "Otherwise, download and unzip the voice_typing folder to your Desktop.")
    pdf.step(5, "Install the app",
             "Type these commands one by one, pressing Enter after each:")
    pdf.code_block('cd ~/Desktop/voice_typing\npip3 install .')
    pdf.body_text(
        "Wait for it to finish. You will see a message saying "
        '"Successfully installed voice-typing" when it\'s done. '
        "This also downloads all the needed components automatically."
    )

    pdf.step(6, "Test that it works",
             "Type this command and press Enter:")
    pdf.code_block("voice-typing")
    pdf.body_text(
        'You should see "Voice Typing is running. Hold \'right_shift\' to record." '
        "Press Control + C to stop it for now."
    )

    pdf.sub_title("Part C: Make it Start Automatically")
    pdf.step(7, "Create the auto-start file",
             "Copy and paste this entire block into Terminal and press Enter. "
             "This creates a file that tells macOS to start Voice Typing automatically:")
    pdf.code_block(
        'cat > ~/Library/LaunchAgents/com.voice-typing.plist << \'EOF\'\n'
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"\n'
        '  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        '<dict>\n'
        '    <key>Label</key>\n'
        '    <string>com.voice-typing</string>\n'
        '    <key>ProgramArguments</key>\n'
        '    <array>\n'
        '        <string>PYTHON_PATH</string>\n'
        '        <string>-m</string>\n'
        '        <string>voice_typing</string>\n'
        '    </array>\n'
        '    <key>RunAtLoad</key>\n'
        '    <true/>\n'
        '    <key>StandardOutPath</key>\n'
        '    <string>/tmp/voice-typing.log</string>\n'
        '    <key>StandardErrorPath</key>\n'
        '    <string>/tmp/voice-typing.err</string>\n'
        '</dict>\n'
        '</plist>\n'
        'EOF'
    )

    pdf.add_page()
    pdf.warning_box(
        "In the file above, replace PYTHON_PATH with your actual Python path. "
        'To find it, run: which python3   (it will show something like '
        '"/usr/local/bin/python3" or "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3")'
    )

    pdf.step(8, "Activate auto-start",
             "Type this command and press Enter:")
    pdf.code_block("launchctl load ~/Library/LaunchAgents/com.voice-typing.plist")
    pdf.body_text(
        "That's it! Voice Typing will now start automatically every time "
        "you log in to your Mac. It runs silently in the background."
    )

    pdf.tip_box(
        "To stop auto-start later, run: "
        "launchctl unload ~/Library/LaunchAgents/com.voice-typing.plist"
    )

    # ============================================================
    # SECTION 4: Windows Setup
    # ============================================================
    pdf.add_page()
    pdf.section_title("4. Windows Setup (Automatic)")
    pdf.body_text(
        "Follow these steps carefully on your Windows computer."
    )

    pdf.sub_title("Part A: Install Python")
    pdf.step(1, "Download Python",
             "Open your web browser and go to: https://www.python.org/downloads/  "
             'Click the big yellow "Download Python" button.')
    pdf.step(2, "Run the installer",
             "Open the downloaded file. IMPORTANT: Check the box that says "
             '"Add Python to PATH" at the bottom of the installer window. '
             'Then click "Install Now".')
    pdf.warning_box(
        'You MUST check "Add Python to PATH". If you forget this step, '
        "the commands below will not work. If you already installed Python "
        "without this option, uninstall it and install again with the box checked."
    )
    pdf.step(3, "Verify Python is installed",
             "Press Windows + R, type cmd, and press Enter to open Command Prompt. Type:")
    pdf.code_block("python --version")
    pdf.body_text('You should see "Python 3.x.x". If so, Python is ready.')

    pdf.add_page()
    pdf.sub_title("Part B: Install Voice Typing")
    pdf.step(4, "Open Command Prompt",
             'Press Windows + R, type "cmd", and press Enter.')
    pdf.step(5, "Navigate to the voice_typing folder",
             "If the folder is on your Desktop, type:")
    pdf.code_block("cd %USERPROFILE%\\Desktop\\voice_typing")
    pdf.step(6, "Install the app",
             "Type this command and press Enter:")
    pdf.code_block("pip install .")
    pdf.body_text(
        "Wait for it to finish. This downloads and installs everything automatically."
    )
    pdf.step(7, "Test that it works",
             "Type this command:")
    pdf.code_block("voice-typing")
    pdf.body_text(
        'You should see "Voice Typing is running." Press Control + C to stop it for now.'
    )

    pdf.sub_title("Part C: Make it Start Automatically")
    pdf.step(8, "Find the voice-typing location",
             "In Command Prompt, type:")
    pdf.code_block("where voice-typing")
    pdf.body_text(
        "Write down or copy the path it shows (something like "
        '"C:\\Users\\YourName\\AppData\\Local\\Programs\\Python\\Python31x\\Scripts\\voice-typing.exe").'
    )

    pdf.add_page()
    pdf.step(9, "Open the Startup folder",
             "Press Windows + R, type this, and press Enter:")
    pdf.code_block("shell:startup")
    pdf.body_text("This opens a folder in File Explorer.")

    pdf.step(10, "Create a shortcut",
             "Right-click inside the folder, choose New > Shortcut. "
             "In the location box, paste the path from Step 8. "
             'Click Next, name it "Voice Typing", and click Finish.')

    pdf.body_text(
        "That's it! Voice Typing will now start automatically every time "
        "you log in to Windows. It runs silently in the background."
    )

    pdf.tip_box(
        "To stop auto-start later, just delete the shortcut from the Startup folder. "
        "Open it again with: Windows + R, then type shell:startup"
    )

    # ============================================================
    # SECTION 5: macOS Permissions
    # ============================================================
    pdf.add_page()
    pdf.section_title("5. macOS Permissions (Important!)")
    pdf.body_text(
        "macOS requires you to give special permissions for Voice Typing to work. "
        "Without these, the app cannot detect your keyboard or type text for you."
    )

    pdf.sub_title("Grant Accessibility Permission")
    pdf.step(1, "Open System Settings",
             "Click the Apple menu in the top-left corner and choose System Settings.")
    pdf.step(2, "Go to Privacy & Security",
             "In the left sidebar, click Privacy & Security.")
    pdf.step(3, "Click Accessibility",
             "Scroll down and click Accessibility.")
    pdf.step(4, "Add your terminal app",
             'Click the "+" button. Find and add Terminal (or iTerm, or your terminal app). '
             "Make sure the toggle next to it is turned ON.")

    pdf.sub_title("Grant Input Monitoring Permission")
    pdf.step(5, "Go back to Privacy & Security",
             "Click the back arrow.")
    pdf.step(6, "Click Input Monitoring",
             "Scroll down and click Input Monitoring.")
    pdf.step(7, "Add your terminal app",
             'Click the "+" button. Add the same terminal app. Toggle it ON.')

    pdf.sub_title("Grant Microphone Permission")
    pdf.step(8, "Go to Microphone",
             "Go back to Privacy & Security and click Microphone.")
    pdf.step(9, "Add your terminal app",
             "Add your terminal app and make sure it is toggled ON.")

    pdf.warning_box(
        "After granting all permissions, RESTART your terminal app completely "
        "(quit it and reopen). The permissions won't work until you restart."
    )

    # ============================================================
    # SECTION 6: How to Use
    # ============================================================
    pdf.add_page()
    pdf.section_title("6. How to Use Voice Typing")
    pdf.body_text("Using Voice Typing is very simple:")

    pdf.step(1, "Place your cursor",
             "Click where you want the text to appear. This can be in any app - "
             "a document, email, chat window, browser, etc.")
    pdf.step(2, "Hold the hotkey",
             "Press and HOLD the Right Shift key on your keyboard. "
             "A tray icon will change color to show it's recording.")
    pdf.step(3, "Speak clearly",
             "While holding the key, speak naturally into your microphone. "
             "Speak at a normal pace - you don't need to talk slowly.")
    pdf.step(4, "Release the key",
             "When you're done speaking, release the Right Shift key. "
             "The app will process your speech and type the text at your cursor. "
             "This usually takes 1-3 seconds.")

    pdf.tip_box(
        "The default hotkey is Right Shift. You can change this in the settings "
        "(see Section 7). Other popular choices: Right Ctrl, Right Alt, or a function key."
    )

    # ============================================================
    # SECTION 7: Changing Settings
    # ============================================================
    pdf.add_page()
    pdf.section_title("7. Changing Settings")
    pdf.body_text(
        "You can customize Voice Typing by editing the settings file or "
        "by using command-line options."
    )

    pdf.sub_title("Option A: Edit the Config File")
    pdf.body_text("The settings file is located at:")
    pdf.code_block("~/.voice_typing/config.json          (macOS)\n%USERPROFILE%\\.voice_typing\\config.json  (Windows)")
    pdf.body_text("Open it in any text editor. Here is an example with all settings:")
    pdf.code_block(
        '{\n'
        '    "hotkey": "right_shift",\n'
        '    "whisper_model": "base",\n'
        '    "language": null,\n'
        '    "typing_method": "clipboard"\n'
        '}'
    )

    pdf.sub_title("Settings Explained")
    settings = [
        ("hotkey", "The key you hold to record. Options: right_shift, left_shift, right_ctrl, left_ctrl, right_alt, left_alt, right_cmd, left_cmd, caps_lock, f1 through f20."),
        ("whisper_model", 'The AI model used for speech recognition. Options: tiny, base, small, medium, large-v3. See Section 8 for details.'),
        ("language", 'Set to a language code like "en" for English, "es" for Spanish, etc. Set to null to auto-detect the language.'),
        ("typing_method", '"clipboard" (default, faster) pastes text from clipboard. "simulate" types each key individually (slower but preserves clipboard).'),
    ]
    for name, desc in settings:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 7, name, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(80, 80, 80)
        pdf.set_x(15)
        pdf.multi_cell(175, 6, desc)
        pdf.ln(3)

    pdf.sub_title("Option B: Use Command-Line Options")
    pdf.body_text("You can also pass settings when starting the app:")
    pdf.code_block(
        "voice-typing --hotkey right_ctrl\n"
        "voice-typing --model small\n"
        "voice-typing --language en\n"
        "voice-typing --typing-method simulate\n"
        "voice-typing -v                          (verbose/debug mode)"
    )

    # ============================================================
    # SECTION 8: Whisper Models
    # ============================================================
    pdf.add_page()
    pdf.section_title("8. Available Whisper Models")
    pdf.body_text(
        "Voice Typing uses Whisper AI models for speech recognition. "
        "Larger models are more accurate but slower and use more disk space. "
        "The model downloads automatically the first time you use it."
    )
    pdf.ln(4)

    pdf.set_draw_color(200, 200, 200)
    pdf.table_row("Model", "Size", "Speed", "Accuracy", is_header=True)
    pdf.table_row("tiny", "75 MB", "Fastest", "Lower")
    pdf.table_row("base", "142 MB", "Fast", "Good")
    pdf.table_row("small", "466 MB", "Medium", "Better")
    pdf.table_row("medium", "1.5 GB", "Slow", "Great")
    pdf.table_row("large-v3", "3 GB", "Slowest", "Best")

    pdf.ln(4)
    pdf.tip_box(
        'The "base" model is the default and works well for most people. '
        'If you want better accuracy, try "small". Only use "large-v3" '
        "if you have a powerful computer and need maximum accuracy."
    )

    # ============================================================
    # SECTION 9: Troubleshooting
    # ============================================================
    pdf.add_page()
    pdf.section_title("9. Troubleshooting")

    problems = [
        (
            "Nothing happens when I hold the key",
            "macOS: Make sure you granted Accessibility and Input Monitoring permissions (Section 5). Restart your terminal after granting them.\n\n"
            "Windows: Try running Command Prompt as Administrator.",
        ),
        (
            "I get a 'command not found' error",
            'Python might not be in your PATH. Try running with the full path:\n\n'
            "macOS: /Library/Frameworks/Python.framework/Versions/3.x/bin/voice-typing\n"
            "Windows: Check the path from 'where python' and look in the Scripts folder.",
        ),
        (
            "The transcription is inaccurate",
            "Try using a larger model (small or medium). Make sure your microphone is working and you're speaking clearly. Reduce background noise. You can also set a specific language instead of auto-detect.",
        ),
        (
            "The app crashes on startup",
            "Make sure you have Python 3.10 or higher. Run: python3 --version to check. If you have an older version, install a newer one.",
        ),
        (
            "Auto-start is not working (macOS)",
            "Check that the plist file exists: ls ~/Library/LaunchAgents/com.voice-typing.plist\n"
            "Check for errors: cat /tmp/voice-typing.err\n"
            "Make sure the Python path in the plist file is correct.",
        ),
        (
            "Auto-start is not working (Windows)",
            'Open the Startup folder (Windows + R, type shell:startup) and check that the shortcut is there. Right-click the shortcut, choose Properties, and verify the target path is correct.',
        ),
    ]
    for title, desc in problems:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(200, 60, 60)
        pdf.cell(0, 8, f"Problem: {title}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(70, 70, 70)
        pdf.set_x(15)
        pdf.multi_cell(175, 6, f"Solution: {desc}")
        pdf.ln(4)

    # ============================================================
    # SECTION 10: Useful Commands
    # ============================================================
    pdf.add_page()
    pdf.section_title("10. Useful Commands")

    pdf.sub_title("macOS Commands")
    mac_cmds = [
        ("Start Voice Typing", "voice-typing"),
        ("Stop Voice Typing", "Press Control + C in Terminal"),
        ("Start auto-start service", "launchctl load ~/Library/LaunchAgents/com.voice-typing.plist"),
        ("Stop auto-start service", "launchctl unload ~/Library/LaunchAgents/com.voice-typing.plist"),
        ("Check if it's running", "ps aux | grep voice-typing"),
        ("View logs", "cat /tmp/voice-typing.log"),
        ("View errors", "cat /tmp/voice-typing.err"),
    ]
    for label, cmd in mac_cmds:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 7, label, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Courier", "", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.set_x(15)
        pdf.cell(0, 6, cmd, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    pdf.sub_title("Windows Commands")
    win_cmds = [
        ("Start Voice Typing", "voice-typing"),
        ("Stop Voice Typing", "Press Control + C in Command Prompt"),
        ("Open Startup folder", "Press Windows + R, type shell:startup"),
        ("Check if it's running", "tasklist | findstr voice"),
    ]
    for label, cmd in win_cmds:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 7, label, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Courier", "", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.set_x(15)
        pdf.cell(0, 6, cmd, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    # Save
    output_path = "/Users/ryzex/Desktop/Personal Project/voice_typing/Voice_Typing_Setup_Guide.pdf"
    pdf.output(output_path)
    print(f"PDF saved to: {output_path}")


if __name__ == "__main__":
    generate()
