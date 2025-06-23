# Braille IME Helper
Version 2.7

## Introduction
Braille IME Helper (BrlIMEHelper) enables users to input Chinese characters directly through the braille keyboard on a braille display. When no braille keyboard is available, the addon can also simulate it using a computer keyboard (i.e. QWERTY keyboard). With conversion from braille input to IME operations by the addon, users familiar to braille rules can input Chinese characters without learning the keyboard mappings of the input methods. So far, the addon is an implementation based on [bopomofo braille](https://en.wikipedia.org/wiki/Taiwanese_Braille) and Microsoft Phonetic IME (微軟注音) commonly used in Taiwan, and its concept can be extended to other braille systems and IMEs in the future.

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
- The IME must be properly configured, and the detail is presented in the next paragraph.
- If you would like to simulate braille keyboard by a computer keyboard, check that it supports NKRO (N-key rollover). See also: [What PC keyboards allow for 6-key braille data entry?](https://www.duxburysystems.com/faq2.asp?faq=32&fbclid=IwAR0zdRHClvT5gikN_RqAEX_phxEp51HZX9dtDGUkWU5gTprmvBUPyBs5cFk)
- Please prevent Braille IME Helper from running with other applications or addons related to braille input, such as [PC Keyboard Braille Input for NVDA](https://addons.nvda-project.org/addons/pcKeyboardBrailleInput.en.html) addon and [Braille Chewing](https://github.com/EasyIME/PIME "PIME").
- It is suggested to disable "Report changes to the reading string" option of NVDA's input composition settings to enjoy better experience during quick typing.
- It is suggested to set the braille input table to "English (U.S.) 8 dot computer braille", so that NVDA's behavior is closer to the habit of Taiwanese users.

This addon assumes that the user configures the IME as follows, but he/she can also change related options to suit the actual circumstance.

| Windows version | Windows 10 2004 and above | Vista to Windows 10 1909 | Windows XP Service Pack 3 |
| --------------- | ------------------------- | ------------------------ | ------------------------- |
| Default IME | Microsoft Phonetic IME | Microsoft Phonetic IME | United States Keyboard Layout |
| Default input conversion mode | Alphanumeric | Alphanumeric | Native (New Phonetic IME) |
| Input conversion mode toggle | `[Ctrl]+[Space]` | Left `[Shift]` | `[Ctrl]+[Space]` |
| Keyboard mapping | Standard | Standard | Standard (New Phonetic IME) |
| Remarks | &nbsp; | &nbsp; | Switch between United States Keyboard Layout and New Phonetic IME by `[Ctrl]+[Space]`. |

## Manipulation

### Gestures

The addon provides both computer-keyboard and braille-keyboard gestures. Before introduction, please comprehend the following terms:

1. Computer keyboard: It contains a main keyboard and a numpad. Names of its keys are enclosed by brackets in this section.
2. Braille keys: 9 keys mapped to dots 1 through 8 and the braille space. According to rules defined by the input translation table, the user can type characters via them.
3. Braille keyboard: A physical braille keyboard consisting of 9 braille keys usually belongs to a braille display. However, the addon also offers a virtual braille keyboard emulated by a computer keyboard to facilitate manipulation by users who prefer braille input.
4. Braille pattern: The appearance of a string of braille cells. More clearly, it means which dots compose the cell(s).

#### Computer Keyboard

Here is a summary to show the most basic computer keyboard gestures the user has to know. The following subsections deliver necessary explanation for the terms in the table.

* NVDA+Ctrl+6: Enable/Disable the feature of braille keyboard emulation.
* F, D, S, J, K, L, A, semicolon `[;:]`, and space bar: Dot 1 through 8 and braille space in braille keyboard emulation.
* 0 through 9: Reserved for number input and candidate word selection in 9-key braille input manner.
* NumPad (optional feature, with Num Lock on): Input of a braille cell dot by dot.
    + 0 through 9: The dot numbers or the routing index.
        1. 0 through 8: The braille space and dots 1 through 8; 9: Clear uncompleted braille cell.
        2. The routing index, i.e. the 0-based number of the braille cell.
    + Decimal point `[.]`: Complete input of one braille cell. (double-clickable)
    + Multiply `[*]`: Complete input of a routing index. (double-clickable)
    + Divide `[/]`: View the uncommitted braille cell and/or the routing index.
    + Subtract `[-]`: Scroll the braille display back.
    + Add `[+]`: Scroll the braille display forward.
* NVDA+PrintScreen: Copy the raw text content of the braille display to the clipboard.
    + Press once: Copy this line.
    + Press twice: Copy this line and the focus context presentation.
* NVDA+Win+PrintScreen: Copy the braille patterns on the braille display to the clipboard.
    + Press once: Copy currently displayed braille cells.
    + Press twice: Copy all braille cells of this line.
* NVDA+Win+A: View the state of BrlIMEHelper.
* NVDA+Win+U: Turn on/off the internal code braille.

##### Braille keyboard emulation

Except to use the physical braille keyboard, the addon provides three ways to help the user typewrite in braille through a computer keyboard: 9-key braille input manner, Full-keyboard braille input manner, and Dot-by-dot input manner.

###### 9-key braille input manner

It is popularly called "6-dot input" and "8-dot input". Nine keys on the computer keyboard are selected to emulate the physical braille keyboard, which are F, D, S, J, K, L, A, semicolon `[;:]`, and the space bar by default. The process that NVDA handles the input by the emulated braille keyboard is the same as that for the braille input generated by a physical braille keyboard. Thus, they enable the user to typewrite in input translation rules and to send braille gestures.

Note: Success of the input depends on the physical constraints of the computer keyboard. For a computer keyboard without NKRO, it is possible that press of some pair of keys results in the effect of pressing only one of them. Before bug report about unreasonable behavior caused by the emulated braille keyboard, please check correctness of the braille input through input help of NVDA.

###### Full-keyboard braille input manner

It is suitable for the users who are familiar to the computer keyboard layout but new to the IME keyboard mapping. Its difference from 9-key braille input manner is the correspondence between the keys and the braille patterns. A key (with or without Shift) corresponds to a braille pattern, which is defined by the OUTPUT translation table. Here are two examples for the reader to comprehend its usage and effect.

Example 1:

1. Set the output translation table and the input translation table to "Chinese (Taiwan, Mandarin)" and "Unicode braille", respectively.
2. Switch Microsoft Phonetic IME to the alphanumeric input conversion mode.
3. Use "Switch the input manner of the main keyboard" (see "Common Braille Gestures") to switch to Full-keyboard NVDA Braille Input.
4. On an edit control, type anything as if no braille keyboard emulation were running.

After the 4 steps, you would find that the braille pattern of the output text is the same as your input characters, but the text actually consists of Unicode braille characters, which show the process of your braille input. That is, if the input translation table is not "Unicode braille", then these Unicode braille characters will be translated back to the ordinary alphanumeric symbols before output.

Example 2:

1. Set the output translation table to "Chinese (Taiwan, Mandarin)" without limit to the input translation table.
2. Switch Microsoft Phonetic IME to the native input conversion mode.
3. Use "Switch the input manner of the main keyboard" (see "Common Braille Gestures") to switch to Full-keyboard Braille IME.
4. On an edit control, type 5 characters as follows, `a&'=1`, where `&` is 7 of the main keyboard modified by a Shift key.

After the 4 steps, you would find that the composition window displays 中文 or other Chinese characters read as Zhong1Wen2. That is, the braille pattern of `a&'=1` is ⠁⠯⠄⠿⠂, which is the same as that of 中文.

Some users are used to input in braille, but not enough flexibility of their finger joints makes them commit many mistakes during the process of operating the physical braille keyboard or 9-key braille input. The design of Full-keyboard braille input manner attempts to facilitate their input process. On touching the braille cells, the reader usually thinks of the characters they represent rather than the numbers of the dots. Conversely, it's just as easy for the user to express the desired braille cells with characters. In this input manner, the addon translates the computer keyboard presses into the braille input messages according to the current braille output translation table. For example, "f" is translated into ⠋, which is determined by the current braille output translation table. Then, a key press on a computer keyboard generating a lowercase f represents the braille input of ⠋. In other words, to type "f" by the computer keyboard is equivalent to simultaneous presses of the dots 1, 2, and 4 on the braille keyboard.

As shown in the explanation of the first example, Full-keyboard braille input manner does not have distinct effect in the IME alphanumeric input conversion mode with the usual configuration. Therefore, it is the extension of "Disable braille keyboard simulation in IME alphanumeric mode" prior to version 2.3 of the addon.

Note: The method to generate a braille gesture in this input manner follows that in 9-key braille input manner, i.e. to hold down the braille space along with the other dot 1 to dot 8 simultaneously.

Note: Please choose a computer braille output translation table to work with Full-keyboard braille input manner. Otherwise, the result may not be as expected. For example, the classical grade one U.S. English braille displays `⠠⠠⠁⠃⠉` for `ABC`, but `ABC` keys modified by a Shift key result in 6 braille patterns `⠠⠁⠠⠃⠠⠉`, which is explicitly different.

Remark: If press of the space bar does not result in a Unicode braille space (⠀), then it is caused by a bug of the old NVDA versions. Please upgrade NVDA to fix this problem.

###### Dot-by-dot input manner

Dot-by-dot input manner is independent of the other two braille keyboard emulation modes. If it is enabled, the user can input dot numbers of each braille cell via the numpad with Num Lock on. For example, `[1][2][.] [1][2][3][5][.] [1][2][3][.]` results in "brl" displayed in the text edit. The functions of the numpad keys are presented by the summary at the beginning of this section. The manner allows the user to send braille gestures consisting of more than 6 dots (or space) regardless of the physical constraint of the computer keyboard.

##### The internal code braille

The internal code braille does not exist in any of the current NVDA output translation braille tables. It is implemented by BrlIMEHelper to provide an approach to uniquely distinguish every character, including digits, English alphabets, bopomofo symbols, and Han characters. It ensures that the reader may read all of the characters in Unicode without ambiguity, but the braille patterns are hard to be memorized. However, the internal code braille pattern helps the user find some specific Han character without description from the candidates of a bopomofo IME.

The internal code braille presents the internal code of each character, i.e. the bytes to compose it. In other words, the internal code means the actual data representation for each character in the disk. The mapping from the characters to the internal code is the encoding, and different encodings result in different internal code for the same character. BrlIMEHelper constructs the internal code braille by [UTF-8](https://en.wikipedia.org/wiki/UTF-8) encoding. This leads to the same braille patterns for ASCII (half-shape alphanumeric) characters as 8-dot English braille. Han characters and full-shape punctuation marks are thereby accentuated.

##### The state of BrlIMEHelper

There are three components in the state of BrlIMEHelper: The braille buffer, the input mode, and the IME state. Here is an example of the BrlIMEHelper state message:

`⠙⠜ (145-345); 9-key Braille IME; Microsoft Phonetic IME {-NH}`

The components, separated by semicolons, are described as follows.

###### The braille buffer

The braille patterns a user just enters in the native input conversion mode are stored in the braille buffer before the end of composition. For example, 145 345 is insufficient for composition, but a review of the braille buffer shows that `⠙⠜` has been entered.

When the braille buffer holds a string of braille patterns enough to compose a character, the braille composition procedure is completed. Generally, the composed character appears in the input method composition edit directly. However, if the braille pattern string is a prefix of the other character, then the completed character appears after 0.25 second. Input of the next braille pattern within the time period lets BrlIMEHelper make an early decision. If the new braille pattern can be appended to the original braille string in the buffer to compose a complete character or to form a prefix of some other character, then braille composition continues without output. Otherwise, the composed character is put on the IME composition edit, and the buffer keeps the new braille pattern only.

For example, the braille pattern of "∠" is `⠫⠪`, which is the prefix of "←". After input of `⠫⠪`, the user may wait for 0.25 second until "∠" appears on the IME composition edit, or input the next braille pattern. If the next is `⠒`, then `⠫⠪⠒` forms a prefix of "←" without output. Otherwise, "∠" is put on the IME composition edit, and the new braille pattern is preserved by the buffer.

Besides completion, several circumstances cause interruption of braille composition. The braille buffer is cleared on occurrence of any case listed below.

- Manually terminate: Execute the function to clear the braille buffer by the default 2, 4, 5 + space or some custom gesture.
- NVDA enters the browse mode.
- The current window loses focus.
- Input method change.
- Input conversion mode (e.g. alphanumeric, native) change.
- Cursor move within the input method composition edit.
- The end of IME composition.
- The candidate list gains the focus.

Except that the first one is done intendedly by the user, the others belong to manipulation error. The braille buffer is cleared along with the sound effect of typo.

###### The input mode

The component consists of two parts, the input manner and the input handler. In the example, "9-key" and "Braille IME" are the input manner and the input handler, respectively.

Although the addon provides 3 braille input manners, only 9-key braille input manner and Full-keyboard input manner are shown here. They are indicated by "9-key" and "Full-keyboard" respectively. If braille keyboard emulation is not enabled, then the part of the input manner will be absent.

The input handler, which may be either NVDA Braille Input or Braille IME, must be present. Each of them is a part of program that collects and interpretes the braille input. The native NVDA braille input handler, represented by NVDA Braille Input, translates the collected braille input into the equivalent keyboard messages through the input translation table, and sends them to the system. However, "Braille IME" means that the addon takes over the translation of the braille input.

###### The IME state

The component consists of two parts, the IME name and the input conversion mode. Microsoft Phonetic IME and `{-NH}` exactly correspond to both of them. Because NVDA can only passively obtain the information of the current IME via the input method change notification and the input conversion mode change notification, the component may present a result by guess. Besides, the input conversion mode is represented by some alphabets and symbols enclosed by a pair of braces for simplicity.

An IME name led by `(?)` indicates that it is a result by guess. At the start of NVDA, the addon collects information of the IMEs and the keyboard layouts in this computer. If the keyboard layout of the foreground application corresponds to an IME, then the IME name is determined. Otherwise, that "Consistent braille keyboard simulation toggle state for all processes" option is checked means that the answer is the current IME of NVDA. Finally, when the IME name cannot be concluded by these rules, guess that the answer is the default IME of NVDA.

The first character of the input conversion mode shows availability of the IME. In some special circumstances, such as the browse mode, the IME has no effect, which is represented by a plus sign (`+`). Conversely, a minus sign (`-`) represents that the IME is available. The subsequent may be a question mark (`?`) or several alphabets. Because each application has its own input conversion mode, the question mark represents that NVDA has not recorded the current input conversion mode of the application. Otherwise, there are at least two alphabets to indicate the input conversion mode. The first is Alphanumeric/Native input, and the second is Half/Full shape. Japanese IMEs need two more alphabets. The third is Hiragana/Katakana input. The forth is R or a minus sign (`-`) for Roman input or not.

Note that the addon does not take over the process of the braille input in native input conversion mode for all Chinese IMEs. Some Chinese IMEs, e.g. Microsoft ChangJie IME (微軟倉頡), does not compose Han characters via phonetic symbols. The NVDA braille input behavior is preserved under such circumstance.

There is an other notable case that the NVDA braille input behavior is also preserved during input composition of a phonetic IME. On word selection, the IME handles the keyboard input according to the corresponding alphanumeric characters rather than the native symbols of the keys. Therefore, the addon shows NVDA braille input along with the N flag representing the native input conversion mode.

#### Braille Gestures

A braille gesture consists of the braille space and other braille dot(s). It allows the user to execute some specific function or emulate some key shortcut by the braille keyboard. With these braille gestures, the user may reduce the chance of moving his/her hands away from braille keys, and thus efficiency of operation is enhanced.

The subsequent two subsections introduce braille gestures. The first subsection outlines some common braille gestures and suggestions for the user to quickly remember them. The second subsection provides a table to enumerate all braille gestures defined by this addon. Note that braille gestures executing BrlIMEHelper functions are available via both physical and virtual braille keyboards, but other braille gestures can only be used with the virtual braille keyboard.

To simplify subsequent content of the section, a braille gesture is described only by its braille dot(s), without mentioning the braille space.

Compatibility warning: NVDA versions earlier than 2018.3 disallow braille input from "No braille", so source of gestures provided by the addon is "braille keyboard". If the running braille display driver does not define the same gesture, then braille input generated by its physical braille keyboard may cause execution of them, which does not happen in newer NVDA versions.

##### Common Braille Gestures

<b>BrlIMEHelper Functions</b>

| Dots (+ braille space) | Function | Quick Memory |
| :--------------------- | :------- | :----------- |
| 456 | Switch between IME alphanumeric and native input conversion modes | The same as 視窗導盲鼠系統 |
| 245 | Clear braille buffer on typo to re-enter the correct content | ㄘ of 錯（ㄘㄨㄛˋ） is represented by dots 2, 4, and 5 |
| 123 | Switch the input manner of the main keyboard | The same as 視窗導盲鼠系統 |
| 136 | Switch between the Unicode braille input translation table and any other table | The first alphabet of Unicode u is represented by dots 1, 3, and 6 |

Additional instructions of these gestures are as follows:

2, 4, 5 + space has an additional effect. It makes NVDA dismiss braille message without update of any control content.

After press of dots 1, 3, 6 + space, the braille input translation table becomes "Unicode braille" immediately. The next press will let it become the original table selected by the user. However, if the original braille input translation table is "Unicode braille", then it will become "English (U.S.) 8 dot computer braille".

<b>Document Editing</b>

| Dots (+ braille space) | Function | Quick Memory |
| :--------------------- | :------- | :----------- |
| 346   | `[`&uarr;`]` | &nbsp; |
| 146   | `[`&darr;`]` | &nbsp; |
| 126   | `[`&larr;`]` | Gesture of dots 1, 2, 6 represents &lt; pointing to the left |
| 345   | `[`&rarr;`]` | Gesture of dots 3, 4, 5 represents &gt; pointing to the right |
| 45    | `[Home]` (move the cursor to head of a line) | &nbsp; |
| 1246  | `[End]` (move the cursor to end of a line) | &nbsp; |
| 246   | Page Up (move the cursor to the previous page) | &nbsp; |
| 1256  | Page Down (move the cursor to the next page) | &nbsp; |
| 1247  | `[Ctrl]+[F]` (find) | Dot 7 (Ctrl) + dots 1, 2, 4 (f) |
| 17    | `[Ctrl]+[A]` (select all) | Dot 7 (Ctrl) + dot 1 (a) |
| 147   | `[Ctrl]+[C]` (copy) | Dot 7 (Ctrl) + dots 1, 4 (c) |
| 13467 | `[Ctrl]+[X]` (cut) | Dot 7 (Ctrl) + dots 1, 3, 4, 6 (x) |
| 12367 | `[Ctrl]+[V]` (paste) | Dot 7 (Ctrl) + dots 1, 2, 3, 6 (v) |
| 13567 | `[Ctrl]+[Z]` (undo) | Dot 7 (Ctrl) + dots 1, 3, 5, 6 (z) |
| 3456  | `[Delete]` (remove text right to the cursor) | It is easy to link cross shape of # to "delete" |

<b>Windows System Key Shortcuts</b>

| Dots (+ braille space) | Function | Quick Memory |
| :--------------------- | :------- | :----------- |
| 14    | `[Ctrl]` (left) | The first alphabet c is represented by dots 1 and 4 |
| 134   | `[Alt]` (left) | The first alphabet m of "menu" is represented by dots 1, 3, 4 |
| 234   | `[Shift]` (left) | The first alphabet s is represented by dots 2, 3, 4 |
| 2456  | `[Win]` (left) | The first alphabet w is represented by dots 2, 4, 5, 6 |
| 34    | `[Tab]` | The first alphabet t contains dots 3 and 4 |
| 16    | `[Shift]+[Tab]` | Dots 1 and 6 form a reverse shape of dots 3 and 4 |
| 12346 | `[App]` (show the popup menu) | &nbsp; |
| 1346  | `[Alt]+[F4]` (close the window) | The `[X]` button at the top right of a window |
| 2346  | `[Esc]` | &nbsp; |
| 25678 | `[Win]+[D]` (show the desktop) | Dots 7 and 8 (Win) + dots 2, 5, 6 (d at lower position, i.e. 4) |
| 678   | `[Win]+[T]` (switch to the toolbar) | &nbsp; |
| 27, 237, ..., 357, 3567 | `[F1]` through `[F10]` | Dot 7 + ten braille digits |

<b>NVDA Operations</b>

| Dots (+ braille space) | Function | Quick Memory |
| :--------------------- | :------- | :----------- |
| 1345  | `[NVDA]+[N]` (show the NVDA menu) | The alphabet key is N |
| 12456 | `[NVDA]+[`&darr;`]` (say all from the system caret) | The dots form a shape of a down-pointing thumb |
| 12356 | `[NVDA]+[F9]` (mark the beginning position) | The meaning of "begin" of a left parenthesis |
| 23456 | `[NVDA]+[F10]` (mark the end position) | The meaning of "end" of a right parenthesis |
| 2, 23, ..., 35 | Numpad 1 through 9 (review cursor operations) | Digits represented by dots 2, 3, 5 and 6 |

##### All Braille Gestures

Here is a table listing all supported braille gestures.

Before start, pease note that functions of most of the braille gestures can be induced by dot 7 and dot 8. Dot 7 represents that the emulated key shortcut contains `[Ctrl]`, or it is one of function keys `[F1]` to `[F12]`. Dot 8 represents that the emulated key shortcut contains either `[Alt]` or `[NVDA]` key. Both dots 7 and 8 represents that the emulated key shortcut contains either of `[Ctrl]+[Alt]` and `[Win]`. Anyway, proper comprehension of the design principle would help the reader to remember a lot of braille gestures at short notice.

The original proposal of design in Chinese is available in [message #3664 of nvda-tw group](https://groups.io/g/nvda-tw/message/3664).

| Dots (+ braille space) | Function | + dot 7 | + dot 8 | + dots 7 and 8 |
| :--------------------- | :------- | :------ | :------ | :------------- |
| 1     | Review the braille buffer | `[Ctrl]+[A]` | `[Alt]+[A]` | `[Ctrl]+[Alt]+[A]` |
| 12    | None | `[Ctrl]+[B]` | `[Alt]+[B]` | `[Ctrl]+[Alt]+[B]` |
| 14    | `[Ctrl]` | `[Ctrl]+[C]` | `[Alt]+[C]` | `[Ctrl]+[Alt]+[C]` |
| 145   | None | `[Ctrl]+[D]` | `[Alt]+[D]` | `[Ctrl]+[Alt]+[D]` |
| 15    | None | `[Ctrl]+[E]` | `[Alt]+[E]` | `[Ctrl]+[Alt]+[E]` |
| 124   | None | `[Ctrl]+[F]` | `[Alt]+[F]` | `[Ctrl]+[Alt]+[F]` |
| 1245  | None | `[Ctrl]+[G]` | `[Alt]+[G]` | None |
| 125   | None | `[Ctrl]+[H]` | `[Alt]+[H]` | `[Ctrl]+[Alt]+[H]` |
| 24    | None | `[Ctrl]+[I]` | `[Alt]+[I]` | `[Ctrl]+[Alt]+[I]` |
| 245   | Clear braille buffer on typo to re-enter the correct content | `[Ctrl]+[J]` | `[Alt]+[J]` | `[Ctrl]+[Alt]+[J]` |
| 13    | None | `[Ctrl]+[K]` | `[Alt]+[K]` | `[Ctrl]+[Alt]+[K]` |
| 123   | Switch the input manner of the main keyboard | `[Ctrl]+[L]` | `[Alt]+[L]` | `[Ctrl]+[Alt]+[L]` |
| 134   | `[Alt]` | `[Ctrl]+[M]` | `[Alt]+[M]` | `[Ctrl]+[Alt]+[M]` |
| 1345  | Show the NVDA menu | `[Ctrl]+[N]` | `[Alt]+[N]` | None |
| 135   | None | `[Ctrl]+[O]` | `[Alt]+[O]` | `[Ctrl]+[Alt]+[O]` |
| 1234  | None | `[Ctrl]+[P]` | `[Alt]+[P]` | None |
| 1235  | None | `[Ctrl]+[R]` | `[Alt]+[R]` | None |
| 234   | `[Shift]` | `[Ctrl]+[S]` | `[Alt]+[S]` | `[Ctrl]+[Alt]+[S]` |
| 2345  | None | `[Ctrl]+[T]` | `[Alt]+[T]` | None |
| 136   | Switch between the Unicode braille input translation table and any other table | `[Ctrl]+[U]` | `[Alt]+[U]` | `[Ctrl]+[Alt]+[U]` |
| 1236  | None | `[Ctrl]+[V]` | `[Alt]+[V]` | None |
| 2456  | `[Win]` | `[Ctrl]+[W]` | `[Alt]+[W]` | None |
| 1346  | `[Alt]+[F4]` | `[Ctrl]+[X]` | `[Alt]+[X]` | None |
| 1356  | None | `[Ctrl]+[Z]` | `[Alt]+[Z]` | None |
| 246   | `[PgUp]` | `[Ctrl]+[PgUp]` | `[Alt]+[PgUp]` | None |
| 1256  | `[PgDn]` | `[Ctrl]+[PgDn]` | `[Alt]+[PgDn]` | None |
| 12456 | Say all from the system caret | None | None | None |
| 45    | `[Home]` | `[Ctrl]+[Home]` | `[Alt]+[Home]` | None |
| 2346  | `[Esc]` | `[Ctrl]+[Esc]` | `[Alt]+[Esc]` | None |
| 3456  | `[Delete]` | `[Ctrl]+[Delete]` | `[Alt]+[Delete]` | None |
| 1246  | `[End]` | `[Ctrl]+[End]` | `[Alt]+[End]` | None |
| 146   | `[`&darr;`]` | `[Ctrl]+[`&darr;`]` | `[Alt]+[`&darr;`]` | `[Ctrl]+[Alt]+[`&darr;`]` |
| 12346 | `[App]` | None | None | None |
| 12356 | `[NVDA]+[F9]` | None | None | None |
| 23456 | `[NVDA]+[F10]` | None | None | None |
| 16    | `[Shift]+[Tab]` | `[Ctrl]+[Shift]+[Tab]` | `[Alt]+[Shift]+[Tab]` | None |
| 346   | `[`&uarr;`]` | `[Ctrl]+[`&uarr;`]` | `[Alt]+[`&uarr;`]` | `[Ctrl]+[Alt]+[`&uarr;`]` |
| 34    | `[Tab]` | `[Ctrl]+[Tab]` | `[Alt]+[Tab]` | None |
| 126   | `[`&larr;`]` | `[Ctrl]+[`&larr;`]` | `[Alt]+[`&larr;`]` | `[Ctrl]+[Alt]+[`&larr;`]` |
| 345   | `[`&rarr;`]` | `[Ctrl]+[`&rarr;`]` | `[Alt]+[`&rarr;`]` | `[Ctrl]+[Alt]+[`&rarr;`]` |
| 456   | Switch between IME alphanumeric and native input conversion modes | None | None | None |
| 2     | Move the review cursor to the previous character of the current navigator object and speak it | `[F1]` | Switch to the previous review mode | `[Win]+[A]` |
| 23    | Report the character of the current navigator object where the review cursor is situated | `[F2]` | Move the navigator object to the first object inside it | `[Win]+[B]` |
| 25    | Move the review cursor to the next character of the current navigator object and speak it | `[F3]` | None | `[Win]+[X]` |
| 256   | Move the review cursor to the previous word of the current navigator object and speak it | `[F4]` | Move the navigator object to the previous object | `[Win]+[D]` |
| 26    | Speak the word of the current navigator object where the review cursor is situated | `[F5]` | Report the current navigator object | None |
| 235   | Move the review cursor to the next word of the current navigator object and speak it | `[F6]` | Move the navigator object to the next object | None |
| 2356  | Move the review cursor to the previous line of the current navigator object and speak it | `[F7]` | Switch to the next review mode | None |
| 236   | Report the line of the current navigator object where the review cursor is situated | `[F8]` | Move the navigator object to the object containing it | None |
| 35    | Move the review cursor to the next line of the current navigator object and speak it | `[F9]` | None | `[Win]+[I]` |
| 356   | None | `[F10]` | Perform the default action on the current navigator object | None |
| 5     | Click the left mouse button once at the current mouse position | `[F11]` | Move the mouse pointer to the current navigator object | None |
| 56    | Read from the review cursor up to the end of the current text, moving the review cursor as it goes | `[F12]` | None | None |
| 3     | None | None | Report information about the location of the text or object at the review cursor | `[Win]+[Tab]` |
| 36    | None | None | Set the navigator object to the current focus, and the review cursor to the position of the caret inside it, if possible | Open the control panel |
| 6     | Click the right mouse button once at the current mouse position | None | Set the navigator object to the current object under the mouse pointer and speak it | `[Win]+[T]` |
| None | Braille space | `[Win]+[Space]` | `[Alt]+[Space]` | `[Win]+[Shift]+[Space]` |

#### Functions without Any Predefined Input Gesture

##### Force NVDA to show the current braille message indefinitely
Most users configure NVDA to automatically dismiss the current braille message within a few seconds. If it is necessary to read some message carefully, then the user can execute this function through a self-defined input gesture. The message will stay on the braille display as if the "Show indefinitely" checkbox in the NVDA preference settings were checked. Thus, it is suggested to bind the function to a handy gesture, which may be completed within a few seconds.

##### Copy the braille patterns on the braille display to the clipboard in BRF format
##### Copy the braille patterns on the braille display to the clipboard in NABCC format
The two functions are variants of "Copy the braille patterns on the braille display to the clipboard." The default, triggered by NVDA+Win+PrintScreen, outputs the result in Unicode braille patterns. Here is some brief instruction for all the mentioned formats.

- [Unicode Braille Pattern](https://en.wikipedia.org/wiki/Braille_Patterns): The set of characters that are displayed as 8 braille dots.
- [Braille ASCII](https://en.wikipedia.org/wiki/Braille_ASCII): The representation to express the braille patterns consisting of dot 1 to dot 6 with ASCII characters adopted by the braille documents with .brf extension.
- [North American Braille Computer Code (NABCC)](https://brltty.app/doc/Manual-BRLTTY/English/BRLTTY-14.html): See the reference web page. Note that only the braille patterns corresponding to characters 0 to 127 can be successfully copied.

##### Translate the clipboard content into Unicode braille patterns
##### Translate the clipboard content into braille in BRF format
##### Translate the clipboard content into braille in NABCC format
Translate the textual clipboard content into the specified format, and write it back into the clipboard. If the clipboard contains data in the other format, e.g. moving or copying a file, then these functions do not work.

### Options

#### Automatically enable braille keyboard simulation when NVDA starts

If checked, braille keyboard simulation is enabled automatically when NVDA starts.

#### Report braille buffer changes

If checked, every change of the braille buffer and dot numbers received from the numpad will be reported during input.

#### The key shortcut to toggle IME alphanumeric/native input

It determines the key command sent by the addon when the user presses dots 4, 5, and 6 along with the braille space. To keep the behavior consistent, the default is left shift.

Note: Windows XP users, please configure the default input conversion mode of New Phonetic IME to native if you would like to use `[Ctrl]+[Space]` to switch between United States Keyboard Layout and New Phonetic IME.

#### Prevent redundant announcement of the composition string change

If checked, the addon will try to prevent redundant announcement of the composition string change. Take Microsoft Phonetic IME for an example. The typed bopomofo symbols during composition are displayed in the composition edit, and thus are announced. The feature enables the users to skip this announcement process. However, if the composition results in a bopomofo symbol, then it may be incorrectly determined not to be announced.

#### Never show the input conversion mode update message indefinitely

The IME input conversion mode update message sometimes pops up. If the option to show messages indefinitely is checked, then the useless message will hinder the user from reading important content through the braille display. To deal with the inconvenience, check this option. When the update message appears, the message timeout will be used as if the option to show messages indefinitely were not checked.

#### Use Full-keyboard input manner as the default with NVDA Braille Input

If checked, Full-keyboard input manner is the default to work with NVDA Braille Input. In other words, "Full-keyboard NVDA Braille Input" is the default input mode.

Remark: The option is an extension from "Disable braille keyboard simulation by default in IME alphanumeric mode" of the version earlier than 2.3. It was "Use the ASCII mode as the default on IME alphanumeric input" in the versions earlier than 2.7.

#### "Braille Keys" and "Ignored Keys"
Users can determine positions of braille dots, braille space, and ignored (reserved) keys for braille keyboard simulation in BrlIMEHelper settings dialog. Braille keyboard simulation is automatically disabled when either of the "Braille Keys" or the "Ignored Keys" edit control is focused. Exact 9 braille keys are required, but number of ignored keys is unlimited. If a key appears in both options, "Braille Keys" takes precedence. After entering all key positions by single computer keyboard strokes, `[Apply]` or `[OK]` button press is necessary to take effect. Occasionally, the "Braille Keys" option may not fully work, because simultaneous transmission of some key commands is unsupported by internal design of your computer (or notebook) keyboard. Please change your configuration to find a set of feasible braille keys.

#### Free all non-braille keys during braille keyboard simulation in IME alphanumeric input mode
If checked, all keys, except the braille keys, are ignored during braille keyboard simulation in IME alphanumeric input mode.

#### Keyboard Mapping

The user must keep the option consistent with the keyboard mapping configuration in IME native input conversion mode to ensure that the addon should work. Note that the custom keyboard mapping is not supported currently.

#### Allow dot-by-dot braille input via numpad during braille keyboard simulation
If checked, the user can input braille cells dot by dot via the numpad with Num Lock on.

#### Indication of manual/automatic toggle of braille keyboard simulation
The two options determines indication of toggle of braille keyboard simulation. Particularly, automatic toggling may occur after change of foreground window and/or options of the addon.

#### Consistent braille keyboard simulation toggle state for all processes
If checked, there is only one single state of braille keyboard simulation toggle, which is the behavior of all versions earlier than 2.0. Otherwise, the addon logs state of each process independently. A user who allows different IMEs for different windows may uncheck this option to reduce times of toggling braille keyboard simulation. Note that all toggle states of processes become the default state of NVDA starting if this option is changed from unchecked to checked.

#### Behavior of the simulated braille keyboard
The computer keyboard can emulate braille input from both the current working braille display and "No braille". When conflict happens, the precedence is determined by this option. On default, gestures provided by the addon take precedence.

### Remarks

1. In IME alphanumeric input conversion mode, the effect of the braille input is determined by NVDA's braille input translation table.
2. The original NVDA behavior of dot 7, dot 8, and dot 7 + dot 8 is preserved in both modes.
3. The addon do not influence other buttons on a braille display, such as buttons for scrolling and positioning.
4. Users may manage all above shortcuts via NVDA input gestures dialog and BrlIMEHelper settings dialog.
5. If no composed character is spoken after composition completion, then IME may get stuck by unreasonable (phonetic) input.

## Issues and ways of development

- Known bugs:
    * NVDA braille does not reflect immediately as user input in "Braille Keys" and "Ignored Keys" edit controls.
    * Under some circumstances, the addon cannot successfully update the user configuration.
    * Using the Microsoft Japanese IME and Full-keyboard input manner, the key-up message of Caps Lock disappears from the sequence: Caps Lock down, Shift down, Caps Lock up, Shift up.
- Possible improvements in the future:
    * Allow users to customize the default state of the addon.
    * Allow users to customize dot patterns of symbols, and/or to load dot patterns from braille translation tables.
    * Allow the addon to work with other IMEs.

## Contributors
- Bo-Cheng Jhan &lt;<school510587@yahoo.com.tw>&gt;
- 黃偉豪 &lt;<hurt.nzsmr@gmail.com>&gt;

## Acknowledgement
- BrlIMEHelper has been sponsored by [Taiwan Visually Impaired People Association](https://www.twvip.org) &lt;<vipastaiwan@gmail.com>&gt; from 2020/01/01 to 2021/12/31, hereby express our sincere appreciation.

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
* Add "Keyboard Mapping" option corresponding to the keyboard mapping option of Microsoft Phonetic IME.
* Allow braille input of rhymes with ⡼ prefix.

### Version 2.0
* Allow dot-by-dot braille input via numpad keys.
* Add feedback manners of audio and none for indication of braille keyboard simulation toggle.
* Allow independent state of braille keyboard simulation toggle for each process.
* Modify keyboard shortcut NVDA+X to NVDA+Ctrl+6.
* Add specification for all options into readme.md.
* Code refactoring.

### Version 2.1
* Add various braille gestures to enhance efficiency for users who use virtual braille keyboard.
* Abandon use of NVDA winVersion API to avoid compatibility issue caused by API update in NVDA 2021.1.
* Add "The key shortcut to toggle IME alphanumeric/native mode" option.
* Avoid gettext warning in keyboard.py.
* Update files obtained from AddonTemplate.
* Various corrections and improvements of this documentation.

### Version 2.2
* Implement quick switch between two braille input translation tables, the original and the Unicode braille, by dots 1, 3, 6 + space.
* Allow ⡀ and ⢀ during Unicode BRL input by the computer keyboard.
* Dismiss NVDA braille message properly even if "Show messages indefinitely" option is enabled.
* Avoid deprecated usage of "collections" module, "collections.abc" instead.
* Implement "print screen" for the braille display.

### Version 2.3
* Assign different key shortcuts to two modes of the "copy braille display content" feature.
* Add the feature to force NVDA to show the current message indefinitely without the default gesture.
* Load keyboard-symbol mappings of IMEs from JSON files.
* On installation, ask the user whether to automatically change the input translation table to "English (U.S.) 8 dot computer braille".
* Adopt the new rule to determine the addon version string.
* The design of the braille input and the general input modes, and implementation in IME alphanumeric input.

### Version 2.4
* Support NVDA version 2023.1.
* Add "The format to copy the braille display content" option.
* Code refactoring, and to separate the data from the code files.
* Add the msctf module, which may contribute to development of the oncoming features.

### Version 2.5
* Support NVDA version 2023.3.
* Replace "The format to copy the braille display content" option with 3 individual scripts.
* Add scripts to translate the clipboard content into braille patterns.
* Improve the input mode inference rules.

### Version 2.6
* Interrupt braille composition on conversion mode update and input language change.
* Add the "Prevent redundant announcement of the composition string change" option.
* Add the "Never show the input conversion mode update message indefinitely" option.
* Fix the behavior of braille composition during the browse mode.
* Add the "Report braille buffer changes" option.
* Improve representation of the addon state, and change the gesture to show it.
* Improve the dot-by-dot braille input feature.
* Perform the original NVDA braille input during IME candidate selection.
* Add the internal code braille feature.
* Enable full-shape character input via the IME.

### Version 2.7
* Support NVDA version 2025.1.
* Rename/Rewrite the manners of braille input: "9-key" and "full-keyboard" input manners.
* The feature of 9-key NVDA braille input is preserved even if no recognized bopomofo IME is found during the load time.
* Add the input mode information into the input conversion mode update message.
* Solve the issue that the keyboard layout cannot be lookuped in the secure desktop.
* Other code refactoring and documentation adjustment.
