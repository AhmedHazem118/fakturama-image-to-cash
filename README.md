# Fakturama Image-to-Cash Automation

Take-home project for TJM Labs. A Python robot that reads an order image with a vision model, validates it, and drives the Fakturama desktop application through Microsoft UI Automation (UIA) to create the master data and the Order.

**This is a partial implementation.** The image reading, the validation, and the first part of the flow (Order header, payment method, Debtor, VAT, products, adding the products to the Order) are built and were verified step by step on the real application. Several steps the task asks for are **not** built or only partly met, and the whole chain has not yet been run end to end on the task's example image. Everything skipped is listed below with the reason and the next step.

The Part 1 design document is in [docs/Design_Doc_Fakturama.docx](docs/Design_Doc_Fakturama.docx).

## Status

Step numbers refer to the task document.

| Step | Status |
|---|---|
| 1.1, 1.2 Read the order image into JSON (Gemini vision, fixed schema, model fallback) | Done: matches the answer key for the task's example image |
| Validate (line totals, sums, VAT, dates, payment rules), 15 unit tests | Done |
| 1.3 to 1.8 Open a New Order, Date, Cust.Ref., price mode Net, VAT mode | Done, verified on screen |
| 2.1 to 2.4 Select the Debtor from the Order (reads the dialog table, exact match, native row selection) | Done, the Invoice address box is verified; the Delivery address is not compared yet |
| 2.5 to 2.7, 2.9, 2.11 Create the Debtor (company, contact, billing address, alias, Net) | Done, record reopened and every field compared |
| 2.8 Address roles: Invoice role on the Main address, Delivery role or a second delivery address | **Not done** |
| 2.10 Payment method (select or create) | Partly: created with the default payment code; the required code mapping (for example Bank Transfer = Credit transfer) is **not done** |
| 2.12, 2.13 Back to the Order and select the new Debtor | Done |
| 3.2, 3.3 Select a Product from the Order by exact SKU (verified by Total Net and the Items grid, offline OCR fallback) | Done |
| 3.4 to 3.6 VAT (look up, create with code S) | Partly: reused by name only; the value and the code are not compared |
| 3.7 to 3.12 Create the Product (gross = net x (1 + VAT/100), cost 0, stock 0) and select it | Done |
| 3.13 to 3.16 Quantity, discount and line price on each order line | **Not done** |
| 3.1, 3.17 Loop over every item | **Not done** (the step functions exist, the loop does not) |
| 4.1 to 4.3 Confirm addresses, lines and totals against the image | Partly |
| 4.4 to 4.7 Save the Order, check Data > Documents, create the linked Invoice | **Not started** |
| 5.1 to 5.6 Invoice: payment method, PAID date and value, save, verify | **Not started** |
| Check before create for products | **Not done**: re-running creates duplicate products |
| One-command runner and run report | **Not started** (each step has its own script in `tools/`) |
| Annotated screenshots or a short recording | **Not included yet** |

## Requirements

- Windows 10 or 11, a screen of 1920 x 1080 (positions inside tables are derived from measured control sizes at this layout).
- Fakturama 2.2.1 with the **English** user interface, open, main window not minimized, using a **new, empty data folder** (File > Select Workspace). The create steps are not idempotent yet.
- Python 3.12.
- A Gemini API key (free tier works). Use synthetic data only: free-tier inputs may be used by the provider.

## Setup

```powershell
pip install -r requirements.txt
[Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "<your key>", "User")   # then restart the terminal
```

Optional: `GEMINI_MODEL` puts your own model first. If the preferred model is overloaded, retired or stalls, the extractor tries the next one in `DEFAULT_MODELS` (`gemini-3.8-flash`, `gemini-3-flash-preview`, `gemini-3.1-flash-lite`) and logs which one answered.

## Run

From the project folder:

```powershell
python -m unittest discover -s tests -t . -v                  # validator tests, no Fakturama and no key needed
python -m tools.try_extract samples/task_example_order.png    # reads the task's example image with Gemini and compares it to the answer key
python -m tools.try_header                                    # opens a New Order and fills the header, reading each value back
python -m tools.try_select_product CHR-ERG-01                 # adds a product to the open, maximized order and verifies it
```

The other scripts in `tools/` (`try_payment`, `try_debtor`, `try_vat`, `try_product`, `try_select_debtor`) are the step-by-step scripts used during development. They expect Fakturama to be in a specific state (for example an editor already open) and are described in their docstrings. A single entry point that runs the whole flow does not exist yet.

`samples/task_example_order.png` is the example order image from the task (synthetic data); `samples/task_example_order.expected.json` is its answer key.

## How it works

Five small layers that only communicate through one data object:

| Layer | File | Job |
|---|---|---|
| Extractor | `fakturama_bot/extract.py` | Image to JSON with a fixed schema; every field may be null so the model never has to invent a value |
| Validator | `fakturama_bot/validate.py` | Decimal arithmetic checks, date normalisation, stop on doubt |
| UI layer | `fakturama_bot/ui.py` | Find controls by name or label, write then read back, wait for conditions, no business logic |
| Vision | `fakturama_bot/vision.py` | Reads tables UIA cannot see: crop the screen, ask the vision model for the rows |
| Flow | `fakturama_bot/flow.py` | One function per business step, each ending with a check |

Principles: names and labels instead of coordinates; write then read back; verify the outcome rather than the action; reopen saved records and compare; wait for conditions with a time limit; stop on doubt with a screenshot instead of guessing.

Findings that shaped the code:

- Forms and dropdowns are readable through UIA. The list tables (Debtors, VATs, Products, the address and product dialogs) and the Items table are custom-drawn and appear as anonymous panes.
- Simulated mouse clicks never selected a row in the selection dialogs. Sending the double-click as a window message to the table's native window (win32 backend) did.
- Fakturama silently dropped an e-mail address ending in `.example`. Saved records are therefore reopened and compared field by field.
- In the product dialog, typing a full SKU adds the product by itself when exactly one product matches, so every add is verified (Total Net grows by the net price, the SKU appears in the grid).
- The toolbar Save acts on the active panel, so the editor's own tab is activated before saving.
- Typed text goes through pywinauto where `+`, `^`, `%`, `~`, `(`, `)`, `{`, `}` are commands, so they are escaped (a phone number `+49` was typed as `$9`).

## Limitations and skipped items

- Not built: address roles and the delivery address, the payment-code mapping, quantity and discount per line, the loop over items, saving the Order, the linked Invoice and the payment status (see Status).
- Not fully idempotent: products are created without first checking whether they exist, and an existing VAT entry or payment method is reused by name only (its value, code or settings are not compared). Use a new, empty data folder.
- The extractor is tested on the task's example image only. Other layouts, photos, rotated or multi-page images, other languages and number formats are untested.
- English user interface and one screen layout assumed.
- The vision read of tables sends a screenshot crop to the model, costs an API call and can time out. Verification of an added product falls back to an offline Windows OCR (weaker: it checks that the SKU is present, not which row). With real customer data this needs a private or paid model.
- Company names in the address dialog are cut off by the column width, so they are matched by prefix and verified in full in the Order afterwards.
- The Fakturama version used here has the Payment dropdown on the Miscellaneous tab of the Debtor editor and fills it when the editor opens, so the payment method is created before the Debtor form is opened (the task creates it while the Debtor editor is open).
- Annotated screenshots and a screen recording are not included yet.

## If you had 3 more hours, what would you do?

1. Close the gaps in the Debtor and payment steps: address roles with a second delivery address, the payment-code mapping, and an exact VAT check (name, value and code).
2. Finish the remaining stages in order: quantity and discount per line, saving the Order with a reopen-and-compare check, then the linked Invoice and paid status.
3. Make re-runs safe: check before create for products and debtors, plus a run report of what was created, reused or skipped, and one entry point that runs the whole flow.
4. Test harder orders: rotated or blurred photos, German number format, missing discount, several pages, an unknown payment method.
5. Add a review queue: when the bot stops, save the extracted data and a screenshot so a person can fix it and resume instead of restarting.
6. Produce annotated screenshots and a short recording of a full run, and add an end-to-end test on a clean Fakturama database.

## Repository layout

```
fakturama_bot/   extract.py, validate.py, ui.py, vision.py, flow.py
tests/           unit tests for the validator and the task example
samples/         the task's example order image and its answer key
tools/           probe scripts (look only) and try scripts (one step each), UIA control dumps
docs/            Part 1 design document
```
