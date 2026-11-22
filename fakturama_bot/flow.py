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


def create_product(win, item, vat_description):
    from pywinauto.keyboard import send_keys
    send_keys("{ESC}")
    ui.click(ui.find_by_name(win, "New", "MenuItem"))
    ui.click(ui.find_by_name(win, "New product", "MenuItem"))
    ui.wait_until(win.child_window(title="New product", control_type="Pane").exists, 10, what="New product editor")
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
    send_keys("{ESC}")
    ui.click(ui.find_by_name(win, "New", "MenuItem"))
    ui.click(ui.find_by_name(win, "New product", "MenuItem"))
    ui.wait_until(win.child_window(title="New product", control_type="Pane").exists, 10, what="New product editor")
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
