# Invento Print

Prints URY KOTs and bills on printers connected to the restaurant's laptop, through
[QZ Tray](https://qz.io). The page at `/kot-printer` checks for work every 3 seconds. KOTs print
automatically for every order type, and bills print when staff click print in the POS.

## How it behaves

- **Printer choice:** choose a KOT printer and a bill printer from those installed in Windows. They can be the same printer, and you can change them at any time. Nothing prints until both are chosen.
- **Nothing is lost:** a ticket only counts as printed once QZ Tray accepts it. If the page, QZ Tray or the internet goes down, unprinted KOTs from the last 12 hours and bills from the last 2 hours print when it recovers.
- **Bills need the page running:** if the page hasn't checked in during the last 30 seconds, the POS shows an error, and the bill stays unprinted.
- **First use:** only KOTs created after the page is first opened on a computer are printed.
- **Reprints:** URY's KOT reprint creates a new KOT, so it prints here marked `REPRINT`.
- **Language:** tickets print English text only. Other characters print as `?`.

## Server setup

Create a signing certificate, once per site. Keep the private key on the server only.

```bash
cd ~/frappe-bench
```

```bash
mkdir -p sites/SITE/private/qz && chmod 700 sites/SITE/private/qz
```

```bash
openssl req -x509 -newkey rsa:2048 -nodes -days 3650 -subj "/CN=Invento KOT Printing/O=Invento" -keyout sites/SITE/private/qz/private-key.pem -out sites/SITE/private/qz/digital-certificate.pem
```

```bash
chmod 600 sites/SITE/private/qz/private-key.pem
```

```bash
bench --site SITE set-config qz_private_key qz/private-key.pem
```

```bash
bench --site SITE set-config qz_cert "$(cat sites/SITE/private/qz/digital-certificate.pem)"
```

Then send the POS's bills to the laptop page, using your POS Profile's name:

```bash
bench --site SITE execute invento_print.setup.enable_laptop_bills --kwargs '{"pos_profile":"PROFILE"}'
```

This adds a placeholder printer called `Laptop Thermal Printer` to the POS Profile. To go back to the browser's print dialog, remove that row from the POS Profile's printer table.

The bill header uses the company name, phone and tax ID, and the POS Profile's company address.

## Laptop setup

1. Check both printers can print a Windows test page.
2. Install QZ Tray from <https://qz.io/download>.
3. Copy the site's `digital-certificate.pem` to `C:\Program Files\QZ Tray\override.crt`, then restart QZ Tray. This stops the "Allow" prompt on each print. One laptop trusts one certificate at a time.
4. Open `/kot-printer`, log in, choose the printers and paper width, and test each printer.
5. Keep that page open during service, ideally in its own browser window.
