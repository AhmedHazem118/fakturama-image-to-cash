"""Order-first flow. One function per step; each ends with a read-back check.

Steps implemented so far: open_new_order, fill_header.
"""
import logging

from . import ui
from .validate import fakturama_date

log = logging.getLogger("fakturama_bot")


def _editor_count(win):
    return sum(1 for d in win.descendants()
               if d.element_info.control_type == "Edit" and d.window_text() == "Cust.Ref.")


def open_new_order(win):
    """Steps 1.3 / 1.4: click Order, wait for the New Order editor. Leave No. unchanged."""
    if _editor_count(win):
        # A second editor tab would make every label ambiguous. Refuse instead of guessing.
        ui.fail("An order editor is already open. Close it (answer No to saving) and rerun.")
    ui.click(ui.find_by_name(win, "Create: New Order", "Button"))
    ui.wait_until(lambda: _editor_count(win) == 1, 10, what="New Order editor to open")
    number = ui.read_value(ui.field_by_label(win, "No."))
    if not number:
        ui.fail("The editor opened but no order number was proposed")
    log.info("New Order opened, proposed No. %s", number)
    return number


def _price_mode_combo(win):
    """The dropdown right of the Date field (Gross / Net). It has no name, so find it by position
    relative to the Date field: same row, to the right."""
    date_box = ui.field_by_label(win, "Date")
    row_top = date_box.rectangle().top
    for c in win.descendants():
        if (c.element_info.control_type == "ComboBox" and abs(c.rectangle().top - row_top) < 15
                and c.rectangle().left > date_box.rectangle().right):
            return c
    ui.fail("Price mode dropdown (Gross/Net) not found next to the Date field")


def select_in_combo(combo, text):
    """Choose an entry in a dropdown, then read it back."""
    combo.select(text)
    try:
        ui.wait_until(lambda: combo.selected_text() == text, 4, 0.2, what=f"dropdown to show {text!r}")
    except ui.UIError:
        ui.fail(f"Dropdown shows {combo.selected_text()!r}, expected {text!r}")


def set_date(date_box, iso):
    """The Date field is a segmented control (month / day / year), not a text box.
    Clicking its left edge selects the month segment; typing MMDDYYYY then fills all three
    segments, because each full segment jumps to the next one by itself."""
    mmddyyyy = f"{iso[5:7]}{iso[8:10]}{iso[0:4]}"
    expected = fakturama_date(iso)
    date_box.click_input(coords=(8, date_box.rectangle().height() // 2))
    date_box.type_keys(mmddyyyy, set_foreground=False)
    try:
        ui.wait_until(lambda: ui.read_value(date_box) == expected, 4, 0.2, what=f"date to show {expected!r}")
    except ui.UIError:
        ui.fail(f"Date field shows {ui.read_value(date_box)!r}, expected {expected!r}")


def fill_header(win, order):
    """Steps 1.5 - 1.7: Date, Cust.Ref., price mode Net, VAT stays 'With VAT'."""
    shown_date = fakturama_date(order["order_date"])
    set_date(ui.field_by_label(win, "Date"), order["order_date"])
    ui.set_text(ui.find_by_name(win, "Cust.Ref.", "Edit"), order["external_reference"])
    select_in_combo(_price_mode_combo(win), "Net")

    vat_mode = ui.find_by_name(win, "VAT", "ComboBox").selected_text()
    if vat_mode != "With VAT":
        ui.fail(f"VAT mode is {vat_mode!r}, expected 'With VAT'")
    log.info("Header filled: date=%s ref=%s mode=Net vat=%s", shown_date, order["external_reference"], vat_mode)


# ------------------------------------------------------------------ debtor
def _debtor_editor(win):
    """Scope all debtor lookups to the 'New Debtor' editor so labels like Company/Street
    can never match another open editor."""
    spec = win.child_window(title="New Debtor", control_type="Pane")
    ui.wait_until(spec.exists, 10, what="New Debtor editor")
    return spec.wrapper_object()


def open_new_debtor(win):
    """Menu New > New Debtor (the task's 'New Contact'). Menus are found by name, never by position."""
    from pywinauto.keyboard import send_keys
    send_keys("{ESC}")  # close any menu left open, otherwise the click below would toggle it shut
    ui.click(ui.find_by_name(win, "New", "MenuItem"))
    ui.click(ui.find_by_name(win, "New Debtor", "MenuItem"))
    return _debtor_editor(win)


def toggle_editor_maximized(win):
    """Click the Maximize/Restore button of the editor panel (the upper one below the title bar).
    The Documents panel otherwise covers the bottom half and hides form rows."""
    buttons = [b for b in win.descendants(control_type="Button")
               if b.window_text() in ("Maximize", "Restore") and b.rectangle().top > 100 and b.rectangle().width() > 0]
    if not buttons:
        ui.fail("Editor maximize button not found")
    ui.click(min(buttons, key=lambda b: b.rectangle().top))


def _open_tab(editor, name):
    ui.click(ui.find_by_name(editor, name, "TabItem"))


def fill_debtor(editor, debtor, payment=None):
    """Fill the identity + main address + alias fields, reading each one back. Does NOT save."""
    ui.set_text(ui.find_by_name(editor, "Company", "Edit"), debtor["company"])
    first, last = ui.edits_after_label(editor, "First Name Last Name", 2)
    ui.set_text(first, debtor["first_name"])
    ui.set_text(last, debtor["last_name"])

    _open_tab(editor, "Addresses")
    ui.set_text(ui.find_by_name(editor, "Street", "Edit"), debtor["street"])
    zip_box, city_box = ui.edits_after_label(editor, "ZIP - City", 2)
    ui.set_text(zip_box, debtor["zip"])
    ui.set_text(city_box, debtor["city"])
    select_in_combo(ui.find_by_name(editor, "Country", "ComboBox"), debtor["country"])
    if debtor.get("email"):
        ui.set_text(ui.find_by_name(editor, "E-Mail", "Edit"), debtor["email"])
    if debtor.get("phone"):
        ui.set_text(ui.find_by_name(editor, "Telephone", "Edit"), debtor["phone"])

    _open_tab(editor, "Miscellaneous")
    ui.set_text(ui.find_by_name(editor, "Alias name", "Edit"), debtor["alias"])
    select_in_combo(ui.field_by_label(editor, "Net or Gross", ("ComboBox",)), "Net")
    if payment:
        pay_combo = ui.find_by_name(editor, "Payment", "ComboBox")
        options = pay_combo.item_texts()
        log.info("Payment dropdown offers: %s", options)
        if payment not in options:
            ui.fail(f"Payment method {payment!r} not in the dropdown {options}")
        select_in_combo(pay_combo, payment)
    discount = ui.read_value(ui.find_by_name(editor, "Discount", "Edit"))
    if discount != "0%":
        ui.fail(f"Debtor discount is {discount!r}, expected the default 0%")
    log.info("Debtor form filled: %s", debtor["company"])


# ------------------------------------------------------------ payment term
def close_tab(win, title, discard=False):
    """Select the tab named `title`, then File > Close (Ctrl+W). A menu entry is more robust than aiming
    at the tiny x icon. For an unsaved editor Fakturama asks to save: with discard=True answer No."""
    from pywinauto.keyboard import send_keys
    ui.find_by_name(win, title, "TabItem").click_input()
    send_keys("{ESC}")
    ui.click(ui.find_by_name(win, "File", "MenuItem"))
    close_item = ui.wait_until(
        lambda: next((m for m in win.descendants(control_type="MenuItem") if (m.window_text() or "").startswith("Close	")), None),
        5, what="File > Close entry")
    ui.click(close_item)
    if discard:
        discard_save_prompt(win)


def discard_save_prompt(win):
    """The 'Save Parts' dialog lists the unsaved editors with ticked boxes; OK would SAVE them.
    To discard: untick every box, verify they are unticked, then press OK."""
    def find_dialog():
        return next((d for d in win.descendants(control_type="Window") if d.window_text() == "Save Parts"), None)

    dlg = ui.wait_until(find_dialog, 6, what="'Save Parts' dialog")
    boxes = dlg.descendants(control_type="CheckBox")
    if not boxes:
        ui.fail("'Save Parts' dialog has no checkboxes; refusing to press OK")
    for b in boxes:
        if b.get_toggle_state() == 1:
            b.toggle()
    ui.wait_until(lambda: all(b.get_toggle_state() == 0 for b in boxes), 4, what="all boxes unticked")
    ui.click(ui.find_by_name(dlg, "OK", "Button"))
    ui.wait_until(lambda: find_dialog() is None, 6, what="'Save Parts' dialog to close")


def _save_current(win):
    ui.click(ui.find_by_name(win, "Save the current contents", "Button"))


def create_payment_term(win, name):
    """New > New Term of Payment, set Name, save once, check the tab lost its '*' (= saved)."""
    from pywinauto.keyboard import send_keys
    send_keys("{ESC}")
    ui.click(ui.find_by_name(win, "New", "MenuItem"))
    ui.click(ui.find_by_name(win, "New Term of Payment", "MenuItem"))
    spec = win.child_window(title="New Term of Payment", control_type="Pane")
    ui.wait_until(spec.exists, 10, what="New Term of Payment editor")
    editor = spec.wrapper_object()
    ui.set_text(ui.find_by_name(editor, "Name", "Edit"), name)
    ui.set_text(ui.find_by_name(editor, "Description", "Edit"), name)
    _save_current(win)
    # Saved = the editor tab is now titled with the entry's own name.
    ui.wait_until(lambda: any(t.window_text() == name for t in win.descendants(control_type="TabItem")),
                  8, what=f"tab titled {name!r} (payment term saved)")
    log.info("Payment term created: %s", name)


def save_debtor(win):
    """Save the open New Debtor editor once; success = its tab no longer starts with '*'."""
    _save_current(win)
    ui.wait_until(lambda: not any(t.window_text() == "*New Debtor" for t in win.descendants(control_type="TabItem")),
                  8, what="debtor to be saved")


# ------------------------------------------------------------ select debtor
ADDRESS_COLUMNS = ["No.", "First Name", "Name", "Company", "ZIP", "City"]


def _address_dialog(win):
    return next((d for d in win.descendants(control_type="Window")
                 if "Select the address" in (d.window_text() or "")), None)


def _company_matches(shown, wanted):
    """The Company column is cut off with '...' when it is too wide, so a shortened text counts as a
    match only if it is a prefix of the wanted name. The full name is verified later in the order."""
    shown, wanted = shown.strip(), wanted.strip()
    if shown.endswith("..."):
        return wanted.startswith(shown[:-3].rstrip())
    return shown == wanted


def find_debtor_rows(rows, debtor):
    """Indexes of table rows that match the debtor on First Name, Name, ZIP, City and Company."""
    return [i for i, r in enumerate(rows)
            if r["First Name"].strip() == debtor["first_name"] and r["Name"].strip() == debtor["last_name"]
            and r["ZIP"].strip() == debtor["zip"] and r["City"].strip() == debtor["city"]
            and _company_matches(r["Company"], debtor["company"])]


def select_debtor(win, debtor):
    """Open 'Select the address' (upper icon next to Addresses), search, read the rows with the vision
    fallback, and pick the single exact match. Returns True if selected, False if the debtor does not
    exist (caller then creates it). Several matches = stop for a human."""
    from . import vision
    upper, _lower = ui.icons_after_label(win, "Addresses", 2)
    ui.click(upper)
    dlg = ui.wait_until(lambda: _address_dialog(win), 8, what="'Select the address' dialog")

    def cancel():
        ui.click(ui.find_by_name(dlg, "Cancel", "Button"))

    search = next(e for e in dlg.descendants(control_type="Edit") if e.rectangle().width() == 150)
    ui.set_text(search, debtor["company"])
    body = next(p for p in dlg.descendants(control_type="Pane")
                if p.rectangle().width() == 774 and p.rectangle().height() > 300)
    # The list loads/filters asynchronously: wait until the table's pixels stop changing.
    ui.wait_stable(lambda: vision.region_signature(body.rectangle()), 6, 0.5, what="result list")
    rows = vision.read_table(body.rectangle(), ADDRESS_COLUMNS)
    hits = find_debtor_rows(rows, debtor)
    log.info("address dialog: %d row(s), %d exact match(es)", len(rows), len(hits))
    if not hits:
        cancel()
        return False
    if len(hits) > 1:
        cancel()
        ui.fail(f"{len(hits)} contacts match {debtor['company']!r}; refusing to guess (manual review)")
    r = body.rectangle()
    row_h = 25  # measured on the screen: header ~25px, rows ~25px
    body.click_input(coords=(60, row_h + hits[0] * row_h + row_h // 2))
    ui.click(ui.find_by_name(dlg, "OK", "Button"))
    ui.wait_until(lambda: _address_dialog(win) is None, 6, what="'Select the address' dialog to close")
    # Verify the RESULT, not the click: the order's address box must now show the contact.
    # (A closed dialog does not prove a row was selected: see E21.)
    box = ui.edits_after_label(win, "Addresses", 1)[0]
    shown = ui.read_value(box)
    if debtor["zip"] not in shown or debtor["city"] not in shown:
        ui.fail(f"After selecting, the order's address box shows {shown!r}, not the debtor. "
                "Row selection in the dialog did not take effect; stopping for manual review.")
    if debtor["company"] not in shown:
        ui.fail(f"Address box {shown!r} does not contain the full company name {debtor['company']!r}")
    return True

