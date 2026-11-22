"""Order-first flow. One function per step; each ends with a read-back check.

Steps implemented so far: open_new_order, fill_header.
"""
import logging
import time

from . import ui
from .validate import fakturama_date

log = logging.getLogger("fakturama_bot")


def _editor_count(win):
    """How many unsaved order editors are open. Counted by TAB TITLE, not by a field inside the editor: the fields
    of an editor are invisible whenever another tab is active (a second order was once opened by mistake, E32)."""
    return sum(1 for t in win.descendants(control_type="TabItem")
               if t.window_text().lstrip("*") == "New Order" and t.rectangle().top < 250)


def activate_order_tab(win):
    """Bring the open (unsaved) order editor to the front and make sure the editor panel is maximized."""
    tabs = [t for t in win.descendants(control_type="TabItem")
            if t.window_text().lstrip("*") == "New Order" and t.rectangle().top < 250]
    if len(tabs) != 1:
        ui.fail(f"Expected exactly one open order editor, found {len(tabs)}")
    tabs[0].click_input()
    time.sleep(0.8)
    ensure_editor_maximized(win)


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


def ensure_editor_maximized(win):
    """Maximize the editor panel only if it is not maximized yet (its button is named 'Maximize' when it is not,
    'Restore' when it is), so a repeated call never toggles it back."""
    buttons = [b for b in win.descendants(control_type="Button")
               if b.window_text() in ("Maximize", "Restore") and b.rectangle().top > 100 and b.rectangle().width() > 0]
    if not buttons:
        ui.fail("Editor maximize button not found")
    top = min(buttons, key=lambda b: b.rectangle().top)
    if top.window_text() == "Maximize":
        ui.click(top)
        time.sleep(1.2)


def open_debtor_from_list(win, title):
    """Open the first row of the Debtors list (a double-click inside the table body) and wait for its editor.
    `title` is the editor's title, 'Company, First Last'. Only meant for a short list (one or two debtors)."""
    from pywinauto.keyboard import send_keys
    send_keys("{ESC}")
    nav = [n for n in win.descendants(control_type="Text")
           if n.window_text() == "Debtors" and n.rectangle().left < 400 and n.rectangle().width() > 0]
    if not nav:
        ui.fail("The 'Debtors' entry of the navigation panel is not visible")
    nav[0].click_input(double=True)
    time.sleep(2.2)
    panes = [d for d in win.descendants(control_type="Pane")
             if d.rectangle().width() == 552 and d.rectangle().height() > 300 and d.is_visible()]
    if not panes:
        ui.fail("The Debtors list table was not found")
    panes[-1].click_input(double=True, coords=(100, 38))
    return ui.wait_until(lambda: next((d for d in win.descendants(control_type="Pane") if d.window_text() == title), None),
                         10, what=f"editor {title!r}")


def _open_tab(editor, name):
    ui.click(ui.find_by_name(editor, name, "TabItem"))


ROLE_NAMES = ("Invoice addr.", "Delivery addr.")


def _fill_address(editor, a, email=None, phone=None):
    """Fill the address tab that is currently ACTIVE (UIA shows only the active tab's fields):
    optional 'additional name', Street, ZIP / City, Country, optional e-mail and phone."""
    if a.get("name"):
        ui.set_text(ui.find_by_name(editor, "additional name", "Edit"), a["name"])
    ui.set_text(ui.find_by_name(editor, "Street", "Edit"), a["street"])
    zip_box, city_box = ui.edits_after_label(editor, "ZIP - City", 2)
    ui.set_text(zip_box, a["zip"])
    ui.set_text(city_box, a["city"])
    select_in_combo(ui.find_by_name(editor, "Country", "ComboBox"), a["country"])
    if email:
        ui.set_text(ui.find_by_name(editor, "E-Mail", "Edit"), email)
    if phone:
        ui.set_text(ui.find_by_name(editor, "Telephone", "Edit"), phone)


def _same_address(debtor):
    """True when there is no separate delivery address (task step 2.8: then the Main address also gets the
    Delivery role and no second address is created)."""
    d = debtor.get("delivery")
    if not d:
        return True
    same_lines = all((d.get(k) or "").strip() == (debtor.get(k) or "").strip() for k in ("street", "zip", "city", "country"))
    name = (d.get("name") or "").strip()
    return same_lines and name in ("", (debtor.get("company") or "").strip())


def _role_boxes(win):
    return {c.window_text(): c for c in win.descendants(control_type="CheckBox") if (c.window_text() or "") in ROLE_NAMES}


def _open_role_popup(win, editor):
    """The small '>' button beside 'address type' opens a popup with two checkboxes (probe: D42)."""
    edit = ui.edits_after_label(editor, "address type", 1)[0]
    er = edit.rectangle()
    btn = next((b for b in editor.descendants(control_type="Button")
                if (b.window_text() or "") == "" and abs(b.rectangle().top - er.top) < 6 and b.rectangle().left >= er.right - 6), None)
    if btn is None:
        ui.fail("The button beside 'address type' was not found (is the address row visible?)")
    ui.click(btn)
    return ui.wait_until(lambda: _role_boxes(win) or None, 5, what="address role popup")


def set_roles(win, editor, invoice, delivery):
    """Tick/untick 'Invoice addr.' and 'Delivery addr.' for the ACTIVE address tab and verify the result."""
    from pywinauto.keyboard import send_keys
    _open_role_popup(win, editor)
    want = {"Invoice addr.": bool(invoice), "Delivery addr.": bool(delivery)}
    for name, wanted in want.items():
        box = _role_boxes(win)[name]
        if bool(box.get_toggle_state()) != wanted:
            box.click_input()
            time.sleep(0.5)
    got = {n: bool(b.get_toggle_state()) for n, b in _role_boxes(win).items()}
    send_keys("{ESC}")
    time.sleep(0.4)
    if got != want:
        ui.fail(f"Address roles are {got}, expected {want}")
    log.info("address roles set: %s", got)


def read_roles(win, editor):
    from pywinauto.keyboard import send_keys
    _open_role_popup(win, editor)
    got = {n: bool(b.get_toggle_state()) for n, b in _role_boxes(win).items()}
    send_keys("{ESC}")
    time.sleep(0.4)
    return got


def add_second_address(win, editor, delivery):
    """'+' adds the tab 'additional address #1'; fill it and give it the Delivery role only."""
    ui.click(ui.find_by_name(editor, "+", "Button"))
    ui.wait_until(lambda: any(t.window_text() == "additional address #1" for t in editor.descendants(control_type="TabItem")),
                  6, what="the tab 'additional address #1'")
    _fill_address(editor, delivery)
    set_roles(win, editor, invoice=False, delivery=True)


def fill_debtor(editor, debtor, payment=None, win=None):
    """Fill the identity, the Main address (Invoice role, plus Delivery role when there is no separate delivery
    address), a second delivery address when the image has a different one, and the Miscellaneous tab.
    Reads every field back. Does NOT save. The editor panel must be maximized."""
    win = win or ui.main_window()
    ui.set_text(ui.find_by_name(editor, "Company", "Edit"), debtor["company"])
    first, last = ui.edits_after_label(editor, "First Name Last Name", 2)
    ui.set_text(first, debtor["first_name"])
    ui.set_text(last, debtor["last_name"])

    _open_tab(editor, "Addresses")
    _fill_address(editor, debtor, email=debtor.get("email"), phone=debtor.get("phone"))
    same = _same_address(debtor)
    set_roles(win, editor, invoice=True, delivery=same)
    if not same:
        add_second_address(win, editor, debtor["delivery"])
        _open_tab(editor, "Main address")          # leave the main address showing

    _open_tab(editor, "Miscellaneous")
    ui.set_text(ui.find_by_name(editor, "Alias name", "Edit"), debtor["alias"])
    select_in_combo(ui.field_by_label(editor, "Net or Gross", ("ComboBox",)), "Net")
    if payment:
        pay_combo = ui.find_by_name(editor, "Payment", "ComboBox")
        options = _dropdown_items(pay_combo)
        log.info("Payment dropdown offers: %s", options)
        if payment not in options:
            ui.fail(f"Payment method {payment!r} not in the dropdown {options}")
        select_in_combo(pay_combo, payment)
    discount = ui.read_value(ui.find_by_name(editor, "Discount", "Edit"))
    if discount != "0%":
        ui.fail(f"Debtor discount is {discount!r}, expected the default 0%")
    log.info("Debtor form filled: %s (separate delivery address: %s)", debtor["company"], not same)


def _address_tab_names(editor):
    return [t.window_text() for t in editor.descendants(control_type="TabItem")
            if t.window_text() == "Main address" or t.window_text().startswith("additional address")]


def read_debtor(win, editor):
    """Everything fill_debtor wrote, read back from an open Debtor editor (used to verify a saved record).
    Addresses are keyed by their ROLE ('invoice' / 'delivery'): after a save and reopen Fakturama may list the
    address tabs in a different order, so tab position must never be trusted (E30)."""
    out = {"company": ui.read_value(ui.find_by_name(editor, "Company", "Edit"))}
    first, last = ui.edits_after_label(editor, "First Name Last Name", 2)
    out["first_name"], out["last_name"] = ui.read_value(first), ui.read_value(last)

    def read_tab():
        zip_box, city_box = ui.edits_after_label(editor, "ZIP - City", 2)
        return {"name": ui.read_value(ui.find_by_name(editor, "additional name", "Edit")),
                "street": ui.read_value(ui.find_by_name(editor, "Street", "Edit")),
                "zip": ui.read_value(zip_box), "city": ui.read_value(city_box),
                "country": ui.find_by_name(editor, "Country", "ComboBox").selected_text().strip(),
                "email": ui.read_value(ui.find_by_name(editor, "E-Mail", "Edit")),
                "phone": ui.read_value(ui.find_by_name(editor, "Telephone", "Edit")),
                "roles": read_roles(win, editor)}

    _open_tab(editor, "Addresses")
    time.sleep(0.5)
    out["tabs"] = {}
    for tab in _address_tab_names(editor):
        _open_tab(editor, tab)
        time.sleep(0.4)
        out["tabs"][tab] = read_tab()
    out["invoice"] = next((a for a in out["tabs"].values() if a["roles"].get("Invoice addr.")), None)
    out["delivery"] = next((a for a in out["tabs"].values() if a["roles"].get("Delivery addr.")), None)
    _open_tab(editor, "Miscellaneous")
    out["alias"] = ui.read_value(ui.find_by_name(editor, "Alias name", "Edit"))
    out["net_gross"] = ui.field_by_label(editor, "Net or Gross", ("ComboBox",)).selected_text().strip()
    out["payment"] = ui.find_by_name(editor, "Payment", "ComboBox").selected_text().strip()
    return out


def check_debtor(read, debtor, payment, soft=("email",)):
    """Compare a read-back debtor with the extracted one, address by ROLE. Returns (errors, warnings).
    Fields listed in `soft` produce a warning instead of an error (an optional field the application may not keep)."""
    errors, warnings = [], []

    def eq(label, got, want, field=None):
        if (got or "").strip() != (want or "").strip():
            msg = f"{label}: saved {got!r}, expected {want!r}"
            (warnings if field in soft else errors).append(msg)

    eq("company", read["company"], debtor["company"])
    eq("first name", read["first_name"], debtor["first_name"])
    eq("last name", read["last_name"], debtor["last_name"])
    inv, dlv = read["invoice"], read["delivery"]
    if inv is None:
        errors.append("no address has the Invoice role")
    else:
        for k in ("street", "zip", "city", "country", "email", "phone"):
            eq(f"invoice {k}", inv[k], debtor.get(k), field=k)
    same = _same_address(debtor)
    if same:
        if dlv is not inv and dlv is not None:
            errors.append("a separate delivery address exists although billing and delivery are identical")
        if inv is not None and not inv["roles"].get("Delivery addr."):
            errors.append("the address does not carry the Delivery role")
    else:
        d = debtor["delivery"]
        if dlv is None or dlv is inv:
            errors.append("the separate delivery address (Delivery role) is missing")
        else:
            for k in ("street", "zip", "city", "country"):
                eq(f"delivery {k}", dlv[k], d.get(k))
            eq("delivery additional name", dlv["name"], d.get("name"))
    eq("alias", read["alias"], debtor["alias"])
    eq("net or gross", read["net_gross"], "Net")
    eq("payment", read["payment"], payment)
    return errors, warnings


# ------------------------------------------------------------ payment term
def close_tab(win, title, discard=False):
    """Select the tab named `title`, then File > Close (Ctrl+W). A menu entry is more robust than aiming
    at the tiny x icon. For an unsaved editor Fakturama asks to save: with discard=True answer No."""
    from pywinauto.keyboard import send_keys
    ui.find_by_name(win, title, "TabItem").click_input()
    send_keys("{ESC}")
    ui.click(ui.find_by_name(win, "File", "MenuItem"))
    close_item = ui.wait_until(
        lambda: next((m for m in win.descendants(control_type="MenuItem") if ((m.window_text() or "") == "Close" or (m.window_text() or "").startswith("Close	"))), None),
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


def _save_current(win, editor_tab=None):
    """Toolbar Save acts on the ACTIVE panel. If a list panel was used last (e.g. the VATs list) it
    would save nothing, so activate the editor's own tab first when its title is known (E23)."""
    if editor_tab:
        ui.find_by_name(win, editor_tab, "TabItem").click_input()
    ui.click(ui.find_by_name(win, "Save the current contents", "Button"))


# Task step 2.10.4: payment code for each extracted payment method.
PAYMENT_CODES = {"Bank Transfer": "Credit transfer", "Credit Card": "Credit card", "SEPA Direct Debit": "SEPA direct debit"}


def _select_loose(combo, text):
    """Select the dropdown entry whose text equals `text` ignoring surrounding spaces (this dropdown's entries
    have a trailing space), then read the selection back."""
    items = _dropdown_items(combo)
    match = next((i for i in items if i.strip() == text), None)
    if match is None:
        ui.fail(f"Dropdown has no entry {text!r}; entries: {items}")
    combo.select(match)
    ui.wait_until(lambda: combo.selected_text().strip() == text, 4, 0.2, what=f"dropdown to show {text!r}")


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
    # Task step 2.10.4: the payment code follows a fixed mapping; an unknown method stops the run.
    wanted_code = PAYMENT_CODES.get(name)
    if wanted_code is None:
        ui.fail(f"Payment method {name!r} has no code mapping (known: {sorted(PAYMENT_CODES)}); manual review")
    _select_loose(ui.field_by_label(editor, "!editorPaymentPaymentcode!", ("ComboBox",)), wanted_code)
    # Task step 2.10.5: cash discount, discount days and net days must be 0 (the defaults); assert, do not assume.
    for label in ("Cash discount", "Discount Days", "Net Days"):
        shown = ui.read_value(ui.find_by_name(editor, label, "Edit"))
        if not ui.same_money(shown, 0):
            ui.fail(f"{label} is {shown!r}, expected 0")
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


def _double_click_row(win, dlg, row_index, row_h):
    """Double-click a row of the dialog's table by sending mouse MESSAGES straight to its native
    window (win32 backend). Real mouse clicks (UIA click_input) never selected the row, but window
    messages do (E21/E22). The table is a custom-drawn canvas, so UIA cannot see rows; position is
    computed from the table's own rectangle, never from the screen."""
    from pywinauto import Application
    app = Application(backend="win32").connect(process=win.element_info.process_id)
    native = next(w for w in app.windows() if dlg.window_text() and dlg.window_text() in w.window_text())
    table = next((c for c in native.descendants()
                  if c.class_name() == "SWT_Window0" and c.rectangle().width() > 600
                  and 380 < c.rectangle().height() < 420), None)
    if table is None:
        ui.fail("Could not find the address table's native window")
    table.double_click(coords=(300, row_h + row_index * row_h + row_h // 2))


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
                if p.rectangle().width() == 774 and 380 < p.rectangle().height() < 420)
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
    row_h = 25  # measured on the screen: header ~25px, rows ~25px
    _double_click_row(win, dlg, hits[0], row_h)
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



# ------------------------------------------------------------------- VAT
def _fill_vat_editor(win, name, percent):
    """Fill the open 'New TAX Rate' editor (Name, Description, Value; VAT code stays the default
    'S (Standard rate)' as in the task's example), save, and prove it saved by the tab's new title."""
    editor = win.child_window(title="New TAX Rate", control_type="Pane").wrapper_object()
    ui.set_text(ui.find_by_name(editor, "Name", "Edit"), name)
    ui.set_text(ui.find_by_name(editor, "Description", "Edit"), name)
    code = ui.find_by_name(editor, "VAT code (E-Invoice)", "ComboBox").selected_text()
    if not code.startswith("S"):
        ui.fail(f"VAT code is {code!r}, expected the default 'S (Standard rate)'")
    value = ui.find_by_name(editor, "Value", "Edit")
    ui.set_text(value, f"{percent}%")
    _save_current(win, "*New TAX Rate")
    ui.wait_until(lambda: any(t.window_text() == name for t in win.descendants(control_type="TabItem")),
                  8, what=f"tab titled {name!r} (VAT saved)")
    log.info("VAT created: %s (%s%%)", name, percent)


def create_vat(win, name, percent):
    from pywinauto.keyboard import send_keys
    send_keys("{ESC}")
    ui.click(ui.find_by_name(win, "New", "MenuItem"))
    ui.click(ui.find_by_name(win, "New VAT", "MenuItem"))
    ui.wait_until(win.child_window(title="New TAX Rate", control_type="Pane").exists, 10, what="New TAX Rate editor")
    _fill_vat_editor(win, name, percent)


# --------------------------------------------------------------- product
def gross_price(net, vat_percent):
    """Gross = net x (1 + VAT/100), 2 decimals (the task's rule). Uses validate's Decimal helper."""
    from decimal import Decimal
    from .validate import gross_price as _gross
    # str() first: Decimal(0.1) would carry binary-float noise, Decimal("0.1") is exact.
    return _gross(Decimal(str(net)), Decimal(str(vat_percent)))


def _fill_product_editor(win, item, vat_description):
    """Fill the open 'New product' editor: Item Number (SKU), Name, Description, Price (gross), VAT.
    Cost price and stock stay at their 0 defaults (task). Saves and proves it by the tab's new title."""
    editor = win.child_window(title="New product", control_type="Pane").wrapper_object()
    ui.set_text(ui.find_by_name(editor, "Item Number", "Edit"), item["sku"])
    ui.set_text(ui.find_by_name(editor, "Name", "Edit"), item["description"])
    ui.set_text(ui.find_by_name(editor, "Description", "Edit"), item["description"])
    gross = gross_price(item["unit_net"], item["vat_percent"])
    ui.set_text(ui.field_by_label(editor, "Price (gross)", ("Edit",)), str(gross), same=ui.same_money)
    select_in_combo(ui.find_by_name(editor, "VAT", "ComboBox"), vat_description)
    cost = ui.read_value(ui.field_by_label(editor, "cost price (net)", ("Edit",)))
    stock = ui.read_value(ui.find_by_name(editor, "Stock", "Edit"))
    if not (ui.same_money(cost, 0) and ui.same_money(stock, 0)):
        ui.fail(f"Cost price {cost!r} / stock {stock!r} are not the expected 0 defaults")
    _save_current(win, "*New product")
    ui.wait_until(lambda: any(t.window_text() == item["description"] for t in win.descendants(control_type="TabItem")),
                  8, what=f"tab titled {item['description']!r} (product saved)")
    log.info("Product created: %s (gross %s, %s)", item["sku"], gross, vat_description)


def _open_new_product(win):
    """Open an empty 'New product' editor. Primary route: the toolbar button 'Create a new product'. The menu
    New > New product failed once with 'command.new.product failed' (E31), so it is only the fallback."""
    from pywinauto.keyboard import send_keys
    send_keys("{ESC}")
    for attempt in ("toolbar", "menu"):
        try:
            if attempt == "toolbar":
                ui.click(ui.find_by_name(win, "Create a new product", "Button", timeout=4))
            else:
                ui.click(ui.find_by_name(win, "New", "MenuItem"))
                ui.click(ui.find_by_name(win, "New product", "MenuItem"))
            ui.wait_until(lambda: any(p.window_text() == "New product" for p in win.descendants(control_type="Pane")),
                          8, what="New product editor")
            return
        except ui.UIError as exc:
            log.warning("opening a new product via the %s failed: %s", attempt, exc)
            send_keys("{ESC}")
    ui.fail("Could not open a New product editor by the toolbar or the menu")


def create_product(win, item, vat_description):
    _open_new_product(win)
    _fill_product_editor(win, item, vat_description)


# ------------------------------------------------- check before create
def _dropdown_items(combo):
    """Entries of a real dropdown (readable by UIA, unlike the list tables)."""
    combo.expand()
    try:
        return [d.window_text() for d in combo.descendants(control_type="ListItem")]
    finally:
        combo.collapse()


def existing_vat_names(win):
    """Names of the VAT entries that exist, read from the VAT dropdown of a throwaway New product form
    (the form is closed again without saving). Name-based only: the percentage of an existing entry is
    NOT compared here (see D32)."""
    from pywinauto.keyboard import send_keys
    _open_new_product(win)
    editor = win.child_window(title="New product", control_type="Pane").wrapper_object()
    names = _dropdown_items(ui.find_by_name(editor, "VAT", "ComboBox"))
    close_tab(win, "New product")
    return names


def existing_payment_names(win):
    """Payment methods that exist, read from the Payment dropdown of a throwaway New Debtor form."""
    editor = open_new_debtor(win)
    _open_tab(editor, "Miscellaneous")
    names = _dropdown_items(ui.find_by_name(editor, "Payment", "ComboBox"))
    close_tab(win, "New Debtor")
    return names


def ensure_vat(win, name, percent):
    """Reuse the VAT entry if its name exists, else create it. Returns 'reused' or 'created'."""
    if name in existing_vat_names(win):
        log.info("VAT %r already exists: reused", name)
        return "reused"
    create_vat(win, name, percent)
    return "created"


def ensure_payment_term(win, name):
    if name in existing_payment_names(win):
        log.info("Payment method %r already exists: reused", name)
        return "reused"
    create_payment_term(win, name)
    return "created"


# ------------------------------------------------------- select a product
PRODUCT_COLUMNS = ["Item No.", "Name", "Description", "Stock", "Price", "VAT"]


def _window_named(win, title):
    return next((d for d in win.descendants(control_type="Window") if d.window_text() == title), None)


def _total_net(win):
    """Order's Total Net as text (a real, readable box; the Items table itself is not)."""
    return ui.read_value(ui.field_by_label(win, "Total Net", ("Edit",)))


ITEM_COLUMNS = ["Pos.", "Qty.", "Item No.", "Picture", "Name", "Description", "VAT", "U.Price", "Discount", "Price"]


def _items_grid_rect(win):
    """Screen rectangle of the Items grid (a custom-drawn canvas, found relative to the 'Items' label)."""
    label = next(t for t in win.descendants(control_type="Text") if (t.window_text() or "").strip() == "Items")
    lr = label.rectangle()
    panes = [p for p in win.descendants(control_type="Pane")
             if p.rectangle().width() > 800 and lr.top - 10 < p.rectangle().top < lr.top + 140 and 100 < p.rectangle().height() < 300]
    if not panes:
        ui.fail("Items grid not found below the 'Items' label")
    return max(panes, key=lambda p: p.rectangle().width() * p.rectangle().height()).rectangle()


def read_items(win, timeout=90):
    """The order lines as shown on screen (vision read of the Items grid): list of {column: text}."""
    from . import vision
    return vision.read_table(_items_grid_rect(win), ITEM_COLUMNS, timeout=timeout)


def _native_items_grid(win):
    from pywinauto import Application
    rect = _items_grid_rect(win)
    app = Application(backend="win32").connect(process=win.element_info.process_id)
    main = next(w for w in app.windows() if w.window_text().startswith("Fakturama - "))
    return next(c for c in main.descendants() if c.class_name() == "SWT_Window0"
                and abs(c.rectangle().width() - rect.width()) < 20 and abs(c.rectangle().height() - rect.height()) < 20)


def delete_last_line(win):
    """Select the first row and press the red x (used to undo a wrong add)."""
    grid = _native_items_grid(win)
    grid.click(coords=(200, 37))
    import time
    time.sleep(0.5)
    ui.click(ui.icons_after_label(win, "Items", 4)[2])


def select_product(win, sku, expected_net, already=0):
    """Add a product to the Order and VERIFY it.
    Opens the 'Select a product' dialog (upper icon next to Items) and types the SKU. Fakturama closes the dialog
    by itself when exactly one product matches (it adds that product). If the dialog stays open, several products
    match: read the rows (vision), require exactly one exact Item No., select it with a native double-click.
    Verification (UIA-readable): Total Net grew by `expected_net`; (vision): the last line's Item No. equals `sku`.
    `already` = how many lines with this SKU were added earlier in this run.
    If the vision service is unavailable, the line check falls back to an offline OCR count (second reader).
    Returns True when the verified line was added, False if the SKU does not exist."""
    import time
    from decimal import Decimal
    from . import vision
    net_before = ui.money_value(_total_net(win))
    ui.click(ui.icons_after_label(win, "Items", 4)[0])
    dlg = ui.wait_until(lambda: _window_named(win, "Select a product"), 8, what="'Select a product' dialog")
    search = next(e for e in dlg.descendants(control_type="Edit") if e.rectangle().width() == 150)
    search.click_input()
    search.type_keys("".join("{" + c + "}" if c in "+^%~(){}" else c for c in sku), set_foreground=False)
    time.sleep(1.5)
    dlg = _window_named(win, "Select a product")
    if dlg is not None:                                   # not auto-added: several matches or none
        body = next(p for p in dlg.descendants(control_type="Pane")
                    if p.rectangle().width() > 600 and 380 < p.rectangle().height() < 420)
        ui.wait_stable(lambda: vision.region_signature(body.rectangle()), 6, 0.5, what="product list")
        rows = vision.read_table(body.rectangle(), PRODUCT_COLUMNS)
        hits = [i for i, r in enumerate(rows) if r["Item No."].strip() == sku]
        log.info("product dialog stayed open: %d row(s), %d exact match(es) for %s", len(rows), len(hits), sku)
        if len(hits) != 1:
            ui.click(ui.find_by_name(dlg, "Cancel", "Button"))
            if not hits:
                return False
            ui.fail(f"{len(hits)} products have Item No. {sku!r}; refusing to guess (manual review)")
        _double_click_row(win, dlg, hits[0], 25)
        ui.wait_until(lambda: _window_named(win, "Select a product") is None, 6, what="'Select a product' dialog to close")
    time.sleep(1.0)
    net_after = ui.money_value(_total_net(win))
    if net_after - net_before != Decimal(str(expected_net)):
        ui.fail(f"Total Net went {net_before} -> {net_after}, expected +{expected_net}: wrong or no product added")
    verified_by = _verify_line(win, sku, already)
    log.info("product %s added and verified (%s)", sku, verified_by)
    return True


def _verify_line(win, sku, already):
    """Prove the last line is `sku`. Primary reader: vision model (reads the last row). If the service fails
    (timeout, HTTP error), fall back to the offline OCR: the SKU must appear `already + 1` times."""
    from . import vision
    from .extract import ExtractionError
    try:
        lines = read_items(win, timeout=30)
    except (ExtractionError, OSError) as exc:
        log.warning("vision unavailable (%s); using offline OCR as the second reader", exc)
        if vision.count_in_ocr(_items_grid_rect(win), sku) >= already + 1:
            return "offline OCR"
        delete_last_line(win)
        ui.fail(f"Could not confirm {sku!r} in the Items grid with either reader; the line was removed again")
    if not lines or lines[-1]["Item No."].strip() != sku:
        got = lines[-1]["Item No."] if lines else None
        delete_last_line(win)
        ui.fail(f"The added line shows Item No. {got!r}, not {sku!r}; the line was removed again (manual review)")
    return "vision"
