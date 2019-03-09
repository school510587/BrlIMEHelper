# Braille IME Helper
Version 0.0

## Introduction
Convenient Chinese input remains a hard problem for braille users who are not accustomed to computer keyboard layout. Input of alphabetic language can be carried out directly by braille keyboard on a braille display, but it is not the case for ideographic language users because of variety of characters. Though braille rules of Chinese (e.g. bopomofo braille) have been simplified based on pronunciation, it contains consonants, rhymes, and tones, and there are even more complicated cases such as combined rhymes (rhymes with medials). To reduce burden of reading, the mapping from cells to phonemes is not one-to-one. Braille IME Helper (the addon) is a mediator between braille keyboard and IMEs, which converts the sequence of braille input into the corresponding sequence of phonemes and submits it to the IME. With help of NVDA, the addon is able to get information of IME composition mode and input messages from a braille keyboard, and provide the feature of braille Chinese input. Besides, the addon enables users to have different composition modes in different windows. Even if a true braille keyboard is not available, the addon allows users to simulate braille input by a computer keyboard, which significantly saves input time for users not familiar to the standard bopomofo keyboard layout.

## Prerequisite
Before installation, check the following environment settings:

- The addon requires NVDA 2017.3 or later, but description of this instruction refers mainly to Windows 10 and the latest version of NVDA.
- 微軟注音 must be your default IME, and the composition mode is default to alphanumeric. The factory default mode is usually native, and you can find the option in 微軟注音 configuration of "Region and Language" settings to change it.
- Your 微軟注音 must use the standard bopomofo keyboard layout. It is the factory default, you can also find this option in 微軟注音 configuration.
- Your 微軟注音 must set the function of the left Shift to toggling composition modes. This is the factory default, and you can find this option in advanced 微軟注音 configuration.
- Please prevent Braille IME Helper from running with other applications or addons related to braille input, such as [PC Keyboard Braille Input for NVDA](https://addons.nvda-project.org/addons/pcKeyboardBrailleInput.en.html) addon and [Braille Chewing](https://github.com/EasyIME/PIME "PIME").
- It is suggested to disable "Report changes to the reading string" option of NVDA's input composition settings to enjoy better experience during quick typing.
- It is suggested to set the braille input table to "English (U.S.) 8 dot computer braille", so that NVDA's behavior is closer to the habit of Taiwanese users.
- If you would like to simulate braille keyboard by a computer keyboard, check that it supports NKRO (N-key rollover).
  See also: [What PC keyboards allow for 6-key braille data entry?](https://www.duxburysystems.com/faq2.asp?faq=32&fbclid=IwAR0zdRHClvT5gikN_RqAEX_phxEp51HZX9dtDGUkWU5gTprmvBUPyBs5cFk)

## Features
1. Chinese input (including punctuations and math symbols) through the braille keyboard.
2. Simulating braille keyboard by a computer keyboard.
3. Allowing system and NVDA keyboard shortcuts.
4. Different braille composition modes for different windows.
5. Allowing password input on a web browser by the braille keyboard.

## Manipulation by a braille keyboard
- Please remember the following hotkeys:
    * Dots 4, 5, 6 + Space: Toggle between alphanumeric and native modes. The effect is the same as pressing Shift on a computer keyboard.
    * Dot 1 + Space: Review the braille buffer, i.e., what you just enter in native mode before finish of composition. (Example: 135 126 is insufficient for composition, but this function shows that you have entered ㄅㄛ.)
    * Dots 2, 4, 5 + Space: Clear braille buffer on typo to re-enter the correct content.
- In alphanumeric mode, the effect is determined by NVDA's braille input table.
- The original NVDA behavior of dot 7, dot 8, and dot 7 + dot 8 is preserved in both modes.
- The addon do not influence other buttons on a braille display, such as buttons for scrolling and positioning.

## Manipulation by a computer keyboard
- NVDA+X enables/disables the feature of simulating braille keyboard by a computer keyboard.
- Keys on a computer keyboard is categorized into several classes:
    1. Braille keys: There are 9 keys, i.e. F, D, S, J, K, L, A, semicolon, and space bar, corresponding to dot 1 through 8 and braille space, respectively.
    2. Modifier keys: Ctrl, Alt, Shift, Win, and NVDA keys. The addon does not intercept modifier keys and any key pressed with any modifier key held down.
    3. Reserved keys: Keys with specific functions in general cases, such as Backspace, Tab, Enter, Esc, and the entire numpad. The addon does not intercept reserved keys. Note: Main 0 to 9 keys also belong to this class, so that users can input numbers and specify candidate words.
    4. Other keys: Non-braille ASCII keys will be disabled by the addon.
- Any gesture presented in "Manipulation by a braille keyboard" section can be performed using braille keys listed above.
- Gesture consisting of both braille keys and non-braille keys on the main keyboard results in warning sound and no action.

## Contributors
- Bo-Cheng Jhan <school510587@yahoo.com.tw>

## Issues and ways of development
- Known bugs:
    * If the foreground window changes during braille composition, braille buffer will keep its content. The correct behavior is to clear braille buffer.
    * When "Show messages indefinitely" option is enabled, the message does not disappear as the content of composition changes.
- Possible improvements in the future:
    * Allow users to customize the default state of the addon.
    * Allow users to customize position of simulated braille buttons on a computer keyboard.
    * Allow users to customize dot patterns of symbols, and/or to load dot patterns from braille translation tables.
    * Allow the addon to work with other IMEs.
    * Allow the addon to work with other bopomofo keyboard layouts.

## History of changes

### Version 0.0
* The initial version.
