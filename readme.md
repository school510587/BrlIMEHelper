# Braille IME Helper
Version 0.5

## Introduction
Braille IME Helper (BrlIMEHelper) enables users to input Chinese characters directly through the braille keyboard on a braille display. When no braille keyboard is available, the addon can also simulate it using a computer keyboard. With conversion from braille input to IME operations by the addon, users familiar to braille rules can input Chinese characters without learning other input methods and keyboard layouts. So far, the addon is an implementation based on [bopomofo braille](https://en.wikipedia.org/wiki/Taiwanese_Braille) and 微軟注音 IME commonly used in Taiwan, but its concept can be extended to other braille systems and IMEs in the future.

## Features
1. Chinese input (including punctuations and math symbols) through the braille keyboard.
2. Simulating braille keyboard by a computer keyboard.
3. Allowing system and NVDA keyboard shortcuts.
4. Different braille composition modes for different windows.
5. Allowing password input on a web browser by the braille keyboard.

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
- Shortcuts
    * Braille keyboard:
        + Dots 4, 5, 6 + Space: Toggle between alphanumeric and native modes. The effect is the same as pressing Shift on a computer keyboard.
        + Dot 1 + Space: Review the braille buffer, i.e., what you just enter in native mode before finish of composition. (Example: 135 126 is insufficient for composition, but this function shows that you have entered ㄅㄛ.)
        + Dots 2, 4, 5 + Space: Clear braille buffer on typo to re-enter the correct content.
    * Computer keyboard:
        + NVDA+X: Enable/Disable the feature of simulating braille keyboard by a computer keyboard.
        + F, D, S, J, K, L, A, semicolon: Dot 1 through 8.
        + 0 through 9: Reserved for number input and candidate word selection.
- Remarks
    1. In alphanumeric mode, the effect is determined by NVDA's braille input table.
    2. The original NVDA behavior of dot 7, dot 8, and dot 7 + dot 8 is preserved in both modes.
    3. The addon do not influence other buttons on a braille display, such as buttons for scrolling and positioning.

## Issues and ways of development
- Known bugs:
    * When "Show messages indefinitely" option is enabled, the message does not disappear as the content of composition changes.
- Possible improvements in the future:
    * In browse mode, single letter navigation should always work.
    * Allow users to customize the default state of the addon.
    * Allow users to customize position of simulated braille buttons on a computer keyboard.
    * Allow users to customize dot patterns of symbols, and/or to load dot patterns from braille translation tables.
    * Allow the addon to work with other IMEs.
    * Allow the addon to work with other bopomofo keyboard layouts.

## Contributors
- Bo-Cheng Jhan <school510587@yahoo.com.tw>
- 黃偉豪 <hurt.nzsmr@gmail.com>

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
* implement new braille parsing scheme.
* Add "addon_lastTestedNVDAVersion" information.
* Add rules to ensure input of a single bopomofo symbol.
* Correct several input dot patterns of math symbols.

### Version 0.4
* implement compatibility of braille pattern prefixes by delayed input sending.
* Try to substitute the most recent braille input on braille input rejection.
* Change the braille pattern of ∠ into ⠫⠪ (1246-246), i.e. the prefix of ←.

### Version 0.5
* Code refactoring.
* Stop simulating braille keyboard by a computer keyboard in browse mode.
* Assign proper documentation and category to each script.
