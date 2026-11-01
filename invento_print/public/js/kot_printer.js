(function () {
	const API = "/api/method/invento_print.api.";
	const URY_PRINT = "/api/method/ury.ury.api.ury_print.";
	const POLL_MS = 3000;
	const MAX_HISTORY = 30;
	const SETTINGS_KEY = "invento_kot_printer";

	const csrfToken = document.body.dataset.csrf;
	const elements = {
		status: document.getElementById("status"),
		title: document.getElementById("status-title"),
		detail: document.getElementById("status-detail"),
		kotPrinter: document.getElementById("kot-printer"),
		billPrinter: document.getElementById("bill-printer"),
		width: document.getElementById("width"),
		testKot: document.getElementById("test-kot"),
		testBill: document.getElementById("test-bill"),
		history: document.getElementById("history"),
		empty: document.getElementById("empty"),
	};

	const settings = loadSettings();
	const printedNotSaved = new Map();
	let busy = false;
	let refused = false;

	function loadSettings() {
		let saved = {};
		try {
			saved = JSON.parse(localStorage.getItem(SETTINGS_KEY)) || {};
		} catch (error) {
			saved = {};
		}
		// Only KOTs created after first use are printed, so turning this on mid-service
		// doesn't reprint the whole day. After that, a reopened page catches up on what it missed.
		saved.since = saved.since || document.body.dataset.now;
		saved.width = saved.width || "48";
		return saved;
	}

	function saveSettings() {
		try {
			localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
		} catch (error) {
			setStatus("warn", "Settings not saved", "This browser is blocking saved settings.");
		}
	}

	function setStatus(state, title, detail) {
		elements.status.dataset.state = state;
		elements.title.textContent = title;
		elements.detail.textContent = detail;
	}

	async function call(url, params, method) {
		const options = {
			method: method || "GET",
			headers: { Accept: "application/json", "X-Frappe-CSRF-Token": csrfToken },
			credentials: "same-origin",
		};
		let target = url;
		if (options.method === "POST") {
			options.headers["Content-Type"] = "application/json";
			options.body = JSON.stringify(params || {});
		} else if (params) {
			target += "?" + new URLSearchParams(params);
		}
		const response = await fetch(target, options);
		if (response.status === 401 || response.status === 403) {
			throw new Error("Please log in again.");
		}
		if (!response.ok) {
			throw new Error("The server returned an error (" + response.status + ").");
		}
		return (await response.json()).message;
	}

	qz.security.setCertificatePromise(function (resolve, reject) {
		call(URY_PRINT + "qz_certificate").then(resolve, reject);
	});
	qz.security.setSignatureAlgorithm("SHA512");
	qz.security.setSignaturePromise(function (toSign) {
		return function (resolve, reject) {
			call(URY_PRINT + "signature_promise", { toSign: toSign }, "POST").then(resolve, reject);
		};
	});

	async function connect() {
		if (qz.websocket.isActive()) return;
		await qz.websocket.connect({ retries: 1, delay: 1 });
		await loadPrinters();
	}

	// Always an explicit choice: falling back to the Windows default could quietly send
	// tickets somewhere like Microsoft Print to PDF while the page still says Ready.
	function fillPrinterList(select, printers, chosen) {
		select.replaceChildren(
			new Option("Choose a printer", ""),
			...printers.map(function (name) {
				return new Option(name, name);
			})
		);
		select.disabled = false;
		select.value = printers.includes(chosen) ? chosen : "";
	}

	async function loadPrinters() {
		const printers = await qz.printers.find();
		fillPrinterList(elements.kotPrinter, printers, settings.kotPrinter);
		fillPrinterList(elements.billPrinter, printers, settings.billPrinter);
		elements.testKot.disabled = false;
		elements.testBill.disabled = false;
	}

	function printerFor(kind) {
		return kind === "bill" ? elements.billPrinter.value : elements.kotPrinter.value;
	}

	function printRaw(printer, ticket) {
		const config = qz.configs.create(printer);
		return qz.print(config, [{ type: "raw", format: "command", flavor: "base64", data: ticket }]);
	}

	function addHistory(label) {
		elements.empty.hidden = true;
		const row = document.createElement("li");
		const name = document.createElement("span");
		const time = document.createElement("span");
		name.textContent = label;
		time.textContent = new Date().toLocaleTimeString();
		row.append(name, time);
		elements.history.prepend(row);
		while (elements.history.children.length > MAX_HISTORY) {
			elements.history.lastElementChild.remove();
		}
	}

	async function saveMarks() {
		for (const [key, ticket] of Array.from(printedNotSaved)) {
			await call(API + "mark_printed", { kind: ticket.kind, id: ticket.id, printer: ticket.printer }, "POST");
			printedNotSaved.delete(key);
		}
	}

	async function printPending() {
		const tickets = await call(API + "get_pending_tickets", { since: settings.since, width: settings.width });
		for (const ticket of tickets) {
			const key = ticket.kind + ":" + ticket.id;
			// Already on paper, and only the save failed: printing it again would duplicate the ticket.
			if (printedNotSaved.has(key)) continue;
			const printer = printerFor(ticket.kind);
			await printRaw(printer, ticket.ticket);
			printedNotSaved.set(key, { kind: ticket.kind, id: ticket.id, printer: printer });
			addHistory(ticket.label);
			await saveMarks();
		}
	}

	async function tick() {
		if (busy || refused) return;
		busy = true;
		try {
			await connect();
			if (!elements.kotPrinter.value || !elements.billPrinter.value) {
				setStatus("bad", "Choose your printers", "Nothing prints until both a KOT and a bill printer are chosen.");
				return;
			}
			await saveMarks();
			await printPending();
			const detail =
				elements.kotPrinter.value === elements.billPrinter.value
					? "KOTs and bills print to " + elements.kotPrinter.value
					: "KOTs print to " + elements.kotPrinter.value + ", bills to " + elements.billPrinter.value;
			setStatus("ok", "Ready", detail);
		} catch (error) {
			if (isRefused(error)) {
				// Trying again every few seconds would reopen QZ Tray's pop-up forever.
				refused = true;
				setStatus("bad", "QZ Tray was blocked", "Refresh this page and click Allow in the QZ Tray pop-up.");
			} else {
				setStatus("bad", "Printing has stopped", describeError(error));
			}
		} finally {
			busy = false;
		}
	}

	function isRefused(error) {
		return /blocked|rejected|denied/i.test((error && error.message) || String(error));
	}

	function describeError(error) {
		if (!qz.websocket.isActive()) {
			return "QZ Tray isn't running on this computer. Start it and this page will reconnect.";
		}
		return (error && error.message) || String(error);
	}

	async function printTest(select, button) {
		if (!select.value) {
			setStatus("bad", "Choose a printer first", "Pick a printer from the list, then test it.");
			return;
		}
		button.disabled = true;
		try {
			await connect();
			const ticket = await call(API + "get_test_ticket", { printer: select.value, width: settings.width });
			await printRaw(select.value, ticket);
			addHistory("Test - " + select.value);
		} catch (error) {
			setStatus("bad", "Test print failed", describeError(error));
		} finally {
			button.disabled = false;
		}
	}

	function start() {
		elements.width.value = settings.width;
		elements.kotPrinter.addEventListener("change", function () {
			settings.kotPrinter = elements.kotPrinter.value;
			saveSettings();
		});
		elements.billPrinter.addEventListener("change", function () {
			settings.billPrinter = elements.billPrinter.value;
			saveSettings();
		});
		elements.width.addEventListener("change", function () {
			settings.width = elements.width.value;
			saveSettings();
		});
		elements.testKot.addEventListener("click", function () {
			printTest(elements.kotPrinter, elements.testKot);
		});
		elements.testBill.addEventListener("click", function () {
			printTest(elements.billPrinter, elements.testBill);
		});
		saveSettings();

		// Browsers slow normal timers in background tabs to about once a minute. Worker timers
		// keep their pace, so tickets still print promptly when this page isn't the active tab.
		const timer = new Worker(
			URL.createObjectURL(new Blob(["setInterval(function(){postMessage(0)}," + POLL_MS + ")"]))
		);
		timer.onmessage = tick;
		tick();
	}

	// A second open tab would print everything twice, so only one tab may run at a time.
	navigator.locks.request("invento-kot-printer", { ifAvailable: true }, function (lock) {
		if (!lock) {
			setStatus("warn", "Already open", "This page is open in another tab. Use that tab to print.");
			return undefined;
		}
		start();
		return new Promise(function () {});
	});
})();
