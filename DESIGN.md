---
name: Silent Type
description: Neutral native Windows controls with restrained teal accents.
colors:
  background: "#f4f5f6"
  surface: "#ffffff"
  ink: "#172026"
  muted: "#53616a"
  accent: "#087e8b"
  accent-dark: "#06616b"
  edge: "#c9d0d4"
  button-hover: "#e1ecee"
  error: "#8b3535"
  success: "#14783d"
  working: "#805900"
  recents-row: "#242e35"
  recents-hover: "#34434d"
  recents-muted: "#b8c5cc"
  recents-accent: "#8ed8dc"
typography:
  title:
    fontFamily: Segoe UI
    fontSize: 22pt
    fontWeight: 700
  section:
    fontFamily: Segoe UI
    fontSize: 11pt
    fontWeight: 700
  body:
    fontFamily: Segoe UI
    fontSize: 10pt
    fontWeight: 400
  phrase:
    fontFamily: Segoe UI
    fontSize: 11pt
    fontWeight: 400
  indicator:
    fontFamily: Segoe UI
    fontSize: 12pt
    fontWeight: 400
  recents-body:
    fontFamily: Segoe UI Variable Text, Segoe UI
    fontSize: 13px
    fontWeight: 400
  recents-label:
    fontFamily: Segoe UI Variable Display, Segoe UI
    fontSize: 11px
    fontWeight: 700
rounded:
  recents-shell: 20px
  recents-row: 11px
  recents-digit: 12px
spacing:
  window-inset: 24px
  popup-inset: 16px
  control-gap: 8px
  section-gap: 12px
components:
  button:
    padding: 8px 12px
    textColor: "{colors.ink}"
  button-primary:
    backgroundColor: "{colors.accent-dark}"
    textColor: "{colors.surface}"
    padding: 8px 12px
  button-primary-hover:
    backgroundColor: "{colors.accent}"
  history-selected:
    backgroundColor: "{colors.accent-dark}"
    textColor: "{colors.surface}"
    height: 32px
  phrase-review:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    padding: 10px 12px
  recents-row:
    backgroundColor: "{colors.recents-row}"
    textColor: "{colors.surface}"
    rounded: "{rounded.recents-row}"
    height: 38px
  recents-row-hover:
    backgroundColor: "{colors.recents-hover}"
---

# Design System: Silent Type

## Overview

Silent Type uses light gray settings, dark text, white reading surfaces and restrained teal actions. The tray recovery popup uses a dark counterpart. The user approved this neutral restyle without SRC branding or a new visual concept.

The implementation is Windows Tk/ttk with the clam theme, a custom Canvas popup and a native status window. These files describe the implemented desktop system; they do not specify a web interface. The locally rendered shushing emoji remains the application icon.

## Colors

Primary accent-dark identifies manual recording and selected history. Accent supplies the active primary-button state and focus color. The popup uses the lighter recents-accent for shortcut digits and its log action.

Background, surface, ink, muted and edge establish the settings hierarchy. The popup reuses ink as its shell and muted as its outline, with separate row, hover and subdued-text colors. Error, success and working are the shared theme's semantic status colors; status also has text.

## Typography

Settings use Segoe UI with a bold title, bold sections and regular body copy. The full selected phrase uses the slightly larger phrase role. Tk positive font sizes are points, so these must not be treated as CSS pixels.

The popup prefers Segoe UI Variable Text and Segoe UI Variable Display, falling back to Segoe UI. Its negative Tk font sizes are pixel sizes multiplied by system DPI scale. Shortcut numerals use 12px bold and secondary header text uses 11px regular at base scale. No custom line-height or letter spacing is set.

## Layout

Settings use a single vertical column with the window-inset on all sides. The camera row stretches its selector between its label and preview button. Instruction and help labels update their wrap length with the body width. The history list expands or contracts; the full-phrase review box, action row and warning remain reserved at the bottom.

The reviewed settings sizes are 780 by 760 and 700 by 720. Preserve access to the window's own controls at both sizes. Camera preview opens in a separate, nonresizable native window with its own Stop camera button; it does not consume the settings history area.

The popup is 430px wide at base scale with a 26px header, 38px rows, 5px row gaps and 24px shortcut chips. Dimensions multiply by system DPI scale. It sits near the pointer and clamps to screen bounds. Long phrases are measured and ellipsized on one line; copying retains the complete phrase.

The status strip centers at the top of the active display's work area. Its preferred width is 400px, reduced for narrower work areas. Text wraps inside 16px horizontal insets and height grows from a 48px minimum.

## Elevation & Depth

The app adds no shadows. Settings use native control relief, separators and contrasting reading surfaces. The popup uses tonal rows and an outlined shell. Window-manager decoration is platform controlled.

## Shapes

Settings retain ttk control geometry and the bordered rectangular phrase field. Do not apply the popup's corner radii to native controls. Popup corners are smooth Canvas polygons; Windows transparent-color keying removes the background outside the shell. Its key color is an implementation detail, never a visible palette color.

## Components

### Buttons and camera selector

Manual recording uses the primary button. Copy, Clear history, Hide and preview use the standard button. Standard buttons have a pale active background and muted disabled text; primary buttons have edge-colored disabled text. The camera selector is readonly with 6px padding. Native theme rendering can override some requested field colors.

### History and phrase review

The two-column list has 32px rows, bold headings and a vertical scrollbar. Its selected row uses teal with white text. The separate disabled text widget wraps the full selected phrase and has a one-pixel border and focus highlight. Copy selected is disabled without a valid selection; Clear history is disabled when empty. The empty list prompts recording. Clearing requires a native confirmation dialog.

### Recent phrases popup

Rows support explicit mouse release on the pressed row and physical digit shortcuts. Hover changes row tone and pointer cursor. The full-log action has an L shortcut. Escape or focus loss dismisses the popup. The empty state has no copy action. This Canvas interface is not evidence of full screen-reader support.

### Status indicator

The status window stays above other windows without taking focus or mouse clicks. It uses white Segoe UI text; callers supply the status background. It must not interrupt typing or acquire foreground focus.

## Do's and Don'ts

- Do preserve native workflows, visible status text and complete phrase recovery.
- Do reserve enough height for review and action controls at the minimum reviewed settings size.
- Do keep actual UI behavior in Tk/ttk and Windows APIs; the design sidecar contains no substitute HTML controls.
- Don't introduce SRC colors, typography or branding.
- Don't turn the tray utility into a new visual concept or website.
- Don't infer untested scaling, accessibility or application compatibility guarantees from the reviewed screenshots.
