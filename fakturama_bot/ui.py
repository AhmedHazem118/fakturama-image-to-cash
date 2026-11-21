"""UI layer: small, dumb helpers around pywinauto (UIA backend).

No business logic here. Every helper either returns something we can check
or raises UIError with a screenshot saved, so the flow never continues after
a silent failure.
"""
import logging
import time
from pathlib import Path

from pywinauto import Desktop

log = logging.getLogger("fakturama_bot")
SHOTS = Path("run_output/screenshots")


class UIError(Exception):
    """Something on screen was not as expected. Stop and look at the screenshot."""


# ---------------------------------------------------------------- waiting
def wait_until(condition, timeout=10.0, interval=0.3, what="condition"):
    """Poll `condition()` until it returns something truthy, or raise UIError.

    Used instead of time.sleep(): as fast as the app allows, with a safety limit.
    """
    end = time.time() + timeout
    last_error = None
    while time.time() < end:
        try:
            result = condition()
            if result:
                return result
        except Exception as e:  # control not there yet: keep waiting
            last_error = e
        time.sleep(interval)
    raise UIError(f"Timed out after {timeout}s waiting for: {what} ({last_error})")


def wait_stable(read_state, timeout=10.0, interval=0.4, what="list"):
    """Wait until `read_state()` returns the same value twice in a row.
    Good for search results that load asynchronously."""
    previous = [object()]

    def check():
        current = read_state()
        same = current == previous[0]
        previous[0] = current
        return same

    return wait_until(check, timeout, interval, f"{what} to stop changing")


# ---------------------------------------------------------------- windows
def main_window():
    """The Fakturama main window (found by title, never by position)."""
    # Anchored on "Fakturama - " so other windows that merely contain the word
    # (a Word file called Fakturama_Guide.docx) cannot match.
    win = Desktop(backend="uia").window(title_re=r"^Fakturama - .*", control_type="Window")
    wait_until(win.exists, 15, what="Fakturama main window")
    if win.get_show_state() == 2:  # minimized -> bring back
        win.restore()
    win.set_focus()
    return win


def screenshot(name):
    """Save a screenshot of the whole screen for debugging / the README."""
    from PIL import ImageGrab
    SHOTS.mkdir(parents=True, exist_ok=True)
    path = SHOTS / f"{time.strftime('%H%M%S')}_{name}.png"
    ImageGrab.grab().save(path)
    return path


def fail(message):
    shot = screenshot("failure")
    raise UIError(f"{message} (screenshot: {shot})")


# ---------------------------------------------------------------- finding
def find_by_name(scope, title, control_type=None, timeout=8):
    """Strategy 1: find a control by its visible name (and optionally its type)."""
    # Search the descendants (works for a window spec AND for any control wrapper, e.g. one editor).
    # Only visible controls count, so a hidden tab's fields cannot match.
    def look():
        found = [d for d in scope.descendants()
                 if (d.window_text() or "") == title
                 and (control_type is None or d.element_info.control_type == control_type)
                 and d.rectangle().width() > 0]
        if len(found) > 1:
            fail(f"{len(found)} visible controls named {title!r}; refusing to guess")
        return found[0] if found else None

    try:
        return wait_until(look, timeout, what=f"{control_type or 'control'} named {title!r}")
    except UIError:
        fail(f"Control not found by name: {title!r}")


def field_by_label(scope, label, kinds=("Edit", "ComboBox")):
    """Strategy 2: find a field by the Text label next to it.

    UIA lists controls in reading order, so the first Edit/ComboBox after the
    label is the field that belongs to it. Used for fields with no own name (No., Date).
    """
    def look():
        items = scope.descendants()
        for i, item in enumerate(items):
            if item.element_info.control_type == "Text" and (item.window_text() or "").strip() == label:
                for nxt in items[i + 1:i + 8]:
                    if nxt.element_info.control_type in kinds:
                        return nxt
        return None

    try:
        return wait_until(look, 8, what=f"field labelled {label!r}")
    except UIError:
        fail(f"Field not found by label: {label!r}")


def edits_after_label(scope, label, n=2):
    """Strategy 2 for ONE label with SEVERAL unnamed boxes (e.g. 'First Name Last Name',
    'ZIP - City'): the next n Edit controls after the label, left to right."""
    items = scope.descendants()
    for i, item in enumerate(items):
        if item.element_info.control_type == "Text" and (item.window_text() or "").strip() == label:
            edits = [x for x in items[i + 1:i + 8] if x.element_info.control_type == "Edit"][:n]
            if len(edits) == n:
                return sorted(edits, key=lambda c: c.rectangle().left)
    fail(f"Expected {n} boxes after label {label!r}")


def icons_after_label(scope, label, n=2):
    """Strategy 2 for unnamed icons: the Image controls right after a label,
    in reading order (e.g. the two icons beside 'Addresses': upper = select
    existing contact, lower = green + new contact)."""
    items = scope.descendants()
    for i, item in enumerate(items):
        if item.element_info.control_type == "Text" and (item.window_text() or "").strip() == label:
            icons = [x for x in items[i + 1:i + 8] if x.element_info.control_type == "Image"]
            return sorted(icons[:n], key=lambda c: c.rectangle().top)
    fail(f"Label not found: {label!r}")


# ---------------------------------------------------------------- acting
def read_value(ctrl):
    """Current text of a field. Tries the UIA value first, then the visible text."""
    try:
        value = ctrl.get_value()
        if value is not None:
            return value.strip()
    except Exception:
        pass
    return (ctrl.window_text() or "").strip()


def set_text(ctrl, value, same=None):
    """Type `value` into a field, then READ IT BACK to confirm it stuck.
    `same(shown, value)` can replace the exact comparison (money fields reformat what you type)."""
    ctrl.click_input()
    # Safety guard: if the field is off-screen or covered, the click lands elsewhere and we would
    # overwrite another field (this happened with ZIP/Street, see E15). No focus -> do not type.
    try:
        wait_until(ctrl.has_keyboard_focus, 2, 0.1, what="field to get keyboard focus")
    except UIError:
        fail(f"Field did not get focus after click; refusing to type {value!r} (off-screen or covered?)")
    ctrl.type_keys("^a{BACKSPACE}", set_foreground=False)
    # In pywinauto's key language + ^ % ~ ( ) { } are commands (+ = Shift). Escape them so that
    # data like "+49 40 123" is typed literally (E16).
    literal = "".join("{" + c + "}" if c in "+^%~(){}" else c for c in str(value))
    ctrl.type_keys(literal, with_spaces=True, set_foreground=False)
    # The field's value can lag behind the keystrokes, so wait for it to match.
    try:
        wait_until(lambda: (same or (lambda a, b: a == str(b)))(read_value(ctrl), value), 4, 0.2, what=f"field to show {value!r}")
    except UIError:
        fail(f"Typed {value!r} but the field shows {read_value(ctrl)!r}")
    actual = read_value(ctrl)
    log.info("set %r", value)
    return actual


def click(ctrl):
    ctrl.click_input()


def same_money(shown, value):
    """True if the field text (e.g. '$59.50', '1,234.50 EUR') equals `value` as a number."""
    from decimal import Decimal, InvalidOperation
    cleaned = "".join(ch for ch in str(shown) if ch.isdigit() or ch in ".-")
    try:
        return Decimal(cleaned) == Decimal(str(value))
    except InvalidOperation:
        return False
