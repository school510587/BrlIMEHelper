# Braille IME Helper
Version 2.1

## Introduction
Braille IME Helper (BrlIMEHelper) enables users to input Chinese characters directly through the braille keyboard on a braille display. When no braille keyboard is available, the addon can also simulate it using a computer keyboard. With conversion from braille input to IME operations by the addon, users familiar to braille rules can input Chinese characters without learning other input methods and keyboard layouts. So far, the addon is an implementation based on [bopomofo braille](https://en.wikipedia.org/wiki/Taiwanese_Braille) and 微軟注音 IME commonly used in Taiwan, but its concept can be extended to other braille systems and IMEs in the future.

## Features
1. Chinese input (including punctuations and math symbols) through the braille keyboard.
2. Simulating braille keyboard by a computer keyboard.
3. Allowing system and NVDA keyboard shortcuts.
4. Different braille composition modes for different windows.
5. Allowing password input on a web browser by the braille keyboard.
6. Various customization options from users' feedback.

## System and environment requirements
Before installation, check the following environment settings:

- NVDA 2017.3 or later.
- 微軟注音 must be your default IME with the following configuration:
    * The composition mode must be default to alphanumeric.
    * Use standard bopomofo keyboard layout. (default)
    * The function of the left Shift must be to toggle the composition mode. (default)
- If you would like to simulate braille keyboard by a computer keyboard, check that it supports NKRO (N-key rollover). See also: [What PC keyboards allow for 6-key braille data entry?](https://www.duxburysystems.com/faq2.asp?faq=32&fbclid=IwAR0zdRHClvT5gikN_RqAEX_phxEp51HZX9dtDGUkWU5gTprmvBUPyBs5cFk)
- Please prevent Braille IME Helper from running with other applications or addons related to braille input, such as [PC Keyboard Braille Input for NVDA](https://addons.nvda-project.org/addons/pcKeyboardBrailleInput.en.html) addon and [Braille Chewing](https://github.com/EasyIME/PIME "PIME").
- It is suggested to disable "Report changes to the reading string" option of NVDA's input composition settings to enjoy better experience during quick typing.
- It is suggested to set the braille input table to "English (U.S.) 8 dot computer braille", so that NVDA's behavior is closer to the habit of Taiwanese users.

## Manipulation

### Shortcuts
* Braille keyboard:
    + Dots 4, 5, 6 + Space: Toggle between alphanumeric and native modes. The effect is the same as pressing Shift on a computer keyboard.
    + Dot 1 + Space: Review the braille buffer, i.e., what you just enter in native mode before finish of composition. (Example: 135 126 is insufficient for composition, but this function shows that you have entered ㄅㄛ.)
    + Dots 2, 4, 5 + Space: Clear braille buffer on typo to re-enter the correct content.
    + Dots 1, 2, 3 + Space: Enable/Disable braille input simulation in IME alphanumeric mode.
* Computer keyboard:
    + NVDA+Ctrl+6: Enable/Disable the feature of simulating braille keyboard by a computer keyboard.
    + F, D, S, J, K, L, A, semicolon `[;:]`, and space bar: Dot 1 through 8 and braille space.
    + 0 through 9: Reserved for number input and candidate word selection.
    + NumPad (optional feature, with Num Lock on): Input of a braille cell dot by dot.
        - 0 through 8: The braille space and dots 1 through 8.
        - 9: Clear uncompleted braille cell.
        - Decimal point `[.]`: Complete input of one braille cell.
        - Divide `[/]`: View uncommitted braille cell.

### Options

#### Automatically enable braille keyboard simulation when NVDA starts
If checked, braille keyboard simulation is enabled automatically when NVDA starts.

#### Disable braille keyboard simulation by default in IME alphanumeric mode
If checked, the user can always type characters by the current keyboard layout in IME alphanumeric mode. The option improves experience of users who are familiar to the standard computer keyboard but new to IME keyboard layout of its native mode.

#### "Braille Keys" and "Ignored Keys"
Users can determine positions of braille dots, braille space, and ignored (reserved) keys for braille keyboard simulation in BrlIMEHelper settings dialog. Braille keyboard simulation is automatically disabled when either of the "Braille Keys" or the "Ignored Keys" edit control is focused. Exact 9 braille keys are required, but number of ignored keys is unlimited. If a key appears in both options, "Braille Keys" takes precedence. After entering all key positions by single computer keyboard strokes, `[Apply]` or `[OK]` button press is necessary to take effect. Occasionally, the "Braille Keys" option may not fully work, because simultaneous transmission of some key commands is unsupported by internal design of your computer (or notebook) keyboard. Please change your configuration to find a set of feasible braille keys.

#### Free all non-braille keys during braille keyboard simulation in IME alphanumeric mode
If checked, all keys, except the braille keys, are ignored during braille keyboard simulation in IME alphanumeric mode.

#### Keyboard Mapping
The option corresponds to the configuration of keyboard layout in IME native mode.

#### Allow dot-by-dot braille input via numpad during braille keyboard simulation
If checked, the user can input braille cells dot by dot via the numpad with Num Lock on.

#### Indication of manual/automatic toggle of braille keyboard simulation
The two options determines indication of toggle of braille keyboard simulation. Particularly, automatic toggling may occur after change of foreground window and/or options of the addon.

#### Consistent braille keyboard simulation toggle state for all processes
If checked, there is only one single state of braille keyboard simulation toggle, which is the behavior of all versions earlier than 2.0. Otherwise, the addon logs state of each process independently. A user who allows different IMEs for different windows may uncheck this option to reduce times of toggling braille keyboard simulation. Note that all toggle states of processes become the default state of NVDA starting if this option is changed from unchecked to checked.

### Remarks
1. In alphanumeric mode, the effect is determined by NVDA's braille input table.
2. The original NVDA behavior of dot 7, dot 8, and dot 7 + dot 8 is preserved in both modes.
3. The addon do not influence other buttons on a braille display, such as buttons for scrolling and positioning.
4. Users may manage all above shortcuts via NVDA input gestures dialog and BrlIMEHelper settings dialog.
5. If no composed character is spoken after composition completion, then IME may get stuck by unreasonable (phonetic) input.

## Issues and ways of development
- Known bugs:
    * When "Show messages indefinitely" option is enabled, the message does not disappear as the content of composition changes.
    * NVDA braille does not reflect immediately as user input in "Braille Keys" and "Ignored Keys" edit controls.
- Possible improvements in the future:
    * Allow users to customize the default state of the addon.
    * Allow users to customize dot patterns of symbols, and/or to load dot patterns from braille translation tables.
    * Allow the addon to work with other IMEs.

## Contributors
- Bo-Cheng Jhan &lt;<school510587@yahoo.com.tw>&gt;
- 黃偉豪 &lt;<hurt.nzsmr@gmail.com>&gt;

## Acknowledgement
- BrlIMEHelper has been sponsored by [Taiwan Visually Impaired People Association](https://www.twvip.org) &lt;<vipastaiwan@gmail.com>&gt; from 2019/07/01 to 2020/06/30, hereby express our sincere appreciation.

## History of changes

### Version 0.0
* The initial version.

### Version 0.1
* Refactor the documentation, so that it becomes more readable by users.
* Reset the braille buffer when the foreground window changes.

### Version 0.2
* Fixed the wrong behavior of simulation of dot 7 (A) in explorer.
* Split __init__.py into two files.

### Version 0.3
* Enable localization of messages.
* Implement new braille parsing scheme.
* Add "addon_lastTestedNVDAVersion" information.
* Add rules to ensure input of a single bopomofo symbol.
* Correct several input dot patterns of math symbols.

### Version 0.4
* Implement compatibility of braille pattern prefixes by delayed input sending.
* Try to substitute the most recent braille input on braille input rejection.
* Change the braille pattern of ∠ into ⠫⠪ (1246-246), i.e. the prefix of ←.

### Version 0.5
* Code refactoring.
* Stop simulating braille keyboard by a computer keyboard in browse mode.
* Assign proper documentation and category to each script.

### Version 0.6
* Implement a toggle to enable/disable braille input simulation in IME alphanumeric mode.
* Handle bopomofo.json path in str type.
* Do not simulate braille input if some modifier key is still held down on loading BrlIMEHelper keyboard hooks.

### Version 0.7
* Add dot pattern variants of some symbols.
* Let braille shortcuts be manageable by NVDA input gesture manager.
* Adjust some coding style of command scripts.

### Version 1.0
* Support NVDA 2019.3 based on Python 3.
* Implement a dialog for user configurations.

### Version 1.1
* Use a more proper sound effect for the warning of typo.
* Allow users to customize positions of braille keys and ignored keys on a computer keyboard.
* Add an `[Apply]` button into the settings dialog.

### Version 1.2
* Allow users to ignore all non-braille keys during braille keyboard simulation in alphanumeric mode.
* Add "Keyboard Mapping" option corresponding to the keyboard mapping option of 微軟注音 IME.
* Allow braille input of rhymes with ⡼ prefix.

### Version 2.0
* Allow dot-by-dot braille input via numpad keys.
* Add feedback manners of audio and none for indication of braille keyboard simulation toggle.
* Allow independent state of braille keyboard simulation toggle for each process.
* Modify keyboard shortcut NVDA+X to NVDA+Ctrl+6.
* Add specification for all options into readme.md.
* Code refactoring.
