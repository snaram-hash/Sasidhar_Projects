let currentBorrowerId = null;
let currentBorrowerName = "None Selected";

// Charts holders
let creditChartInstance = null;
let varianceChartInstance = null;

// Tab switcher
document.querySelectorAll(".nav-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
        
        btn.classList.add("active");
        const tabId = btn.getAttribute("data-tab");
        document.getElementById(tabId).classList.add("active");
    });
});

// Toast popup function
function showToast(message, isError = false) {
    const toast = document.getElementById("toast");
    toast.innerText = message;
    toast.style.borderColor = isError ? "var(--color-red)" : "var(--color-blue)";
    toast.classList.remove("hidden");
    
    setTimeout(() => {
        toast.classList.add("hidden");
    }, 4000);
}

// Format numbers
function formatCurrency(val) {
    if (val === null || val === undefined) return "Rs. --";
    return "Rs. " + parseFloat(val).toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

// Fetch borrowers
async function loadBorrowers() {
    try {
        const res = await fetch("/api/borrowers");
        const list = await res.json();
        
        // Body table
        const tbody = document.getElementById("borrowers-table-body");
        tbody.innerHTML = "";
        
        // Global Select option
        const select = document.getElementById("borrower-select-global");
        const uploadSelect = document.getElementById("document-borrower-select");
        const bulkSelect = document.getElementById("bulk-borrower-select");
        
        select.innerHTML = '<option value="">-- Select Borrower --</option>';
        uploadSelect.innerHTML = '<option value="">-- Choose Borrower --</option>';
        if (bulkSelect) bulkSelect.innerHTML = '<option value="">-- Choose Borrower --</option>';
        
        if (list.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No borrowers onboarded yet.</td></tr>';
            return;
        }
        
        list.forEach(b => {
            // Populate select
            const opt = document.createElement("option");
            opt.value = b.id;
            opt.innerText = `${b.company_name} (ID: ${b.id})`;
            select.appendChild(opt.cloneNode(true));
            uploadSelect.appendChild(opt.cloneNode(true));
            if (bulkSelect) bulkSelect.appendChild(opt);
            
            // Populate table row
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${b.id}</td>
                <td><strong>${b.company_name}</strong></td>
                <td>${b.pan}</td>
                <td>${b.gstin}</td>
                <td>${b.industry}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        showToast("Failed to fetch borrowers list.", true);
    }
}

// Change Active Borrower
document.getElementById("borrower-select-global").addEventListener("change", async (e) => {
    const bId = e.target.value;
    if (!bId) {
        currentBorrowerId = null;
        currentBorrowerName = "None Selected";
        document.getElementById("current-borrower-name").innerText = "None Selected";
        clearDashboard();
        return;
    }
    
    currentBorrowerId = parseInt(bId);
    // Find name
    const opt = e.target.options[e.target.selectedIndex];
    currentBorrowerName = opt.innerText.split(" (ID:")[0];
    document.getElementById("current-borrower-name").innerText = currentBorrowerName;
    
    showToast(`Context switched to: ${currentBorrowerName}`);
    
    // Refresh Documents for this borrower
    await loadDocuments();
    // Load Dashboard details if populated
    await refreshDashboard();
});

// Clear Dashboard displays
function clearDashboard() {
    document.getElementById("kpi-sales").innerText = "Rs. --";
    document.getElementById("kpi-credits").innerText = "Rs. --";
    document.getElementById("kpi-cibil").innerText = "--";
    document.getElementById("kpi-risk").innerText = "--";
    
    if (creditChartInstance) creditChartInstance.destroy();
    if (varianceChartInstance) varianceChartInstance.destroy();
}

// Fetch documents
async function loadDocuments() {
    if (!currentBorrowerId) return;
    try {
        const res = await fetch(`/api/documents?borrower_id=${currentBorrowerId}`);
        const docs = await res.json();
        
        const tbody = document.getElementById("documents-table-body");
        tbody.innerHTML = "";
        
        if (docs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No documents registered for this borrower.</td></tr>';
            return;
        }
        
        docs.forEach(d => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${d.id}</td>
                <td><strong>${d.file_name}</strong></td>
                <td><span class="status-badge passed">${d.file_type}</span></td>
                <td>${d.financial_year || 'N/A'}</td>
                <td>
                    <button class="action-icon-btn" onclick="parseDocument(${d.id})">
                        <i class="fa-solid fa-wand-magic-sparkles"></i> Extract Data
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        showToast("Failed to fetch documents list.", true);
    }
}

// Parse document
async function parseDocument(docId) {
    showToast("Triggering data extraction...");
    try {
        const res = await fetch("/api/extract", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ borrower_id: currentBorrowerId, document_id: docId })
        });
        const out = await res.json();
        if (out.success) {
            showToast("Document successfully parsed and extracted!");
            await refreshDashboard();
        } else {
            showToast(out.error || "Failed to extract document.", true);
        }
    } catch (err) {
        showToast("Server error during extraction.", true);
    }
}

// Onboard Form submit
document.getElementById("onboard-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
        company_name: document.getElementById("company_name").value,
        pan: document.getElementById("pan").value,
        gstin: document.getElementById("gstin").value,
        industry: document.getElementById("industry").value,
        constitution: document.getElementById("constitution").value
    };
    
    try {
        const res = await fetch("/api/borrowers", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const out = await res.json();
        if (out.success) {
            showToast("Borrower onboarded successfully!");
            document.getElementById("onboard-form").reset();
            await loadBorrowers();
        } else {
            showToast(out.error || "Failed to onboard borrower.", true);
        }
    } catch (err) {
        showToast("Server error during onboarding.", true);
    }
});

// Ingest/Upload Form submit
document.getElementById("upload-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
        borrower_id: parseInt(document.getElementById("document-borrower-select").value),
        file_type: document.getElementById("document-type-select").value,
        financial_year: document.getElementById("document-fy").value,
        file_path: document.getElementById("document-filepath").value
    };
    
    try {
        const res = await fetch("/api/documents", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const out = await res.json();
        if (out.success) {
            showToast("Document registered and uploaded successfully!");
            document.getElementById("upload-form").reset();
            if (payload.borrower_id === currentBorrowerId) {
                await loadDocuments();
            }
        } else {
            showToast(out.error || "Ingestion failed.", true);
        }
    } catch (err) {
        showToast("Server connection failed.", true);
    }
});

// Bulk Folder Form submit
document.getElementById("bulk-folder-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
        borrower_id: parseInt(document.getElementById("bulk-borrower-select").value),
        folder_path: document.getElementById("bulk-folderpath").value
    };
    
    showToast("Scanning folder and ingesting documents...");
    try {
        const res = await fetch("/api/ingest_folder", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const out = await res.json();
        if (out.success) {
            showToast(`Successfully ingested ${out.data.length} documents from folder!`);
            document.getElementById("bulk-folder-form").reset();
            if (payload.borrower_id === currentBorrowerId) {
                await loadDocuments();
            }
        } else {
            showToast(out.error || "Bulk ingestion failed.", true);
        }
    } catch (err) {
        showToast("Server connection failed during bulk upload.", true);
    }
});

// Run Reconciliation
document.getElementById("trigger-reconciliation-btn").addEventListener("click", async () => {
    if (!currentBorrowerId) {
        showToast("Please choose an active borrower first.", true);
        return;
    }
    showToast("Running validation checks...");
    try {
        const res = await fetch(`/api/reconcile?borrower_id=${currentBorrowerId}&fy=FY24`);
        const rep = await res.json();
        
        const box = document.getElementById("reconciliation-results-box");
        box.innerHTML = `
            <div class="panel-header-action">
                <h4>Validation Status:</h4>
                <span class="status-badge ${rep.status.toLowerCase()}">${rep.status}</span>
            </div>
        `;
        
        for (const [name, check] of Object.entries(rep.checks)) {
            const card = document.createElement("div");
            card.className = "check-card";
            card.innerHTML = `
                <div class="check-card-header">
                    <h4>${name.toUpperCase().replace("_", " ")}</h4>
                    <span class="status-badge ${check.status.toLowerCase()}">${check.status}</span>
                </div>
                <p>${check.message}</p>
            `;
            box.appendChild(card);
        }
    } catch (err) {
        showToast("Reconciliation trigger failed.", true);
    }
});

// Run Policy Engine Evaluation
document.getElementById("trigger-policy-btn").addEventListener("click", async () => {
    if (!currentBorrowerId) {
        showToast("Please select an active borrower first.", true);
        return;
    }
    showToast("Running Lending Policy Engine...");
    try {
        const res = await fetch(`/api/policy?borrower_id=${currentBorrowerId}&fy=FY24`);
        const result = await res.json();
        
        const box = document.getElementById("policy-results-box");
        box.innerHTML = `
            <div class="panel-header-action">
                <h4>Assigned Risk Tier: <strong>${result.risk_tier}</strong></h4>
                <span class="status-badge ${result.risk_tier.toLowerCase() === 'high' ? 'failed' : 'passed'}">${result.risk_tier} RISK</span>
            </div>
            <p class="neutral-text">Engine Scorecard rating: <strong>${result.score.toFixed(1)}/100.0</strong></p>
        `;
        
        for (const [r_code, rule] of Object.entries(result.rules)) {
            const card = document.createElement("div");
            card.className = "check-card";
            card.innerHTML = `
                <div class="check-card-header">
                    <h4>${r_code} - ${rule.name}</h4>
                    <span class="status-badge ${rule.status.toLowerCase() === 'passed' ? 'passed' : 'failed'}">${rule.status}</span>
                </div>
                <p>Calculated Value: <strong>${rule.value.toFixed(2)}</strong> (Limit threshold: ${rule.threshold}) | Triggered alert: ${rule.flag}</p>
            `;
            box.appendChild(card);
        }
        await refreshDashboard();
    } catch (err) {
        showToast("Policy engine evaluation crashed.", true);
    }
});

// Generate Excel CAM Workbook
document.getElementById("generate-cam-btn").addEventListener("click", async () => {
    if (!currentBorrowerId) {
        showToast("No borrower context set.", true);
        return;
    }
    showToast("Building CAM Excel workbook...");
    try {
        const res = await fetch("/api/generate_cam", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ borrower_id: currentBorrowerId, fy: "FY24" })
        });
        const out = await res.json();
        if (out.success) {
            showToast("Excel CAM Workbook generated!");
            document.getElementById("cam-export-path-display").innerText = "Generated: " + out.path;
        } else {
            showToast(out.error || "CAM export failed.", true);
        }
    } catch (err) {
        showToast("CAM Generation failed.", true);
    }
});

// Generate HTML Dashboard Web report
document.getElementById("generate-dashboard-btn").addEventListener("click", async () => {
    if (!currentBorrowerId) {
        showToast("No borrower context set.", true);
        return;
    }
    showToast("Compiling HTML Dashboard report...");
    try {
        const res = await fetch("/api/generate_dashboard", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ borrower_id: currentBorrowerId })
        });
        const out = await res.json();
        if (out.success) {
            showToast("HTML Web Dashboard Compiled!");
            document.getElementById("dashboard-export-path-display").innerText = "Generated: " + out.path;
        } else {
            showToast(out.error || "Dashboard compilation failed.", true);
        }
    } catch (err) {
        showToast("Dashboard compilation failed.", true);
    }
});

// Refresh Dashboard details (graphs and KPIs)
async function refreshDashboard() {
    if (!currentBorrowerId) return;
    try {
        // Query policy to fetch latest scores
        const polRes = await fetch(`/api/policy?borrower_id=${currentBorrowerId}&fy=FY24`);
        const pol = await polRes.json();
        
        // Query validation to fetch values
        const valRes = await fetch(`/api/reconcile?borrower_id=${currentBorrowerId}&fy=FY24`);
        const val = await valRes.json();
        
        // Write KPIs
        if (val && val.checks && val.checks.audited_financials && val.checks.audited_financials.status === "PASSED" || val.status) {
            // Find Audited Sales
            const salesCard = document.getElementById("kpi-sales");
            const creditCard = document.getElementById("kpi-credits");
            
            // To fetch financials, we run custom GETs
            // In val_service we get messages: e.g. "GST-declared sales (Rs. 101,000.00)..."
            // For convenience, we extract figures from report messages or directly query
            // Let's set some default labels
        }
        
        document.getElementById("kpi-cibil").innerText = pol.rules.R004.value;
        document.getElementById("kpi-risk").innerText = pol.risk_tier.toUpperCase();
        
        // Handle Risk icon color
        const kpiRiskIcon = document.getElementById("kpi-risk-icon");
        kpiRiskIcon.className = "kpi-icon " + (pol.risk_tier.toLowerCase() === 'high' ? 'red' : 'green');
        
        // Draw credit chart using Chart.js
        if (creditChartInstance) creditChartInstance.destroy();
        const ctxCredit = document.getElementById("creditChart").getContext("2d");
        
        // Let's mock a simple monthly data for AU bank statement credits
        creditChartInstance = new Chart(ctxCredit, {
            type: "bar",
            data: {
                labels: ["Apr 24", "May 24", "Jun 24", "Jul 24", "Aug 24", "Sep 24", "Oct 24", "Nov 24", "Dec 24", "Jan 25", "Feb 25", "Mar 25"],
                datasets: [{
                    label: "Deposits / Inflows (Lakhs)",
                    data: [12.5, 14.8, 11.2, 18.4, 22.1, 19.5, 23.4, 25.1, 28.3, 31.2, 33.1, 35.5],
                    backgroundColor: "rgba(59, 130, 246, 0.4)",
                    borderColor: "var(--color-blue)",
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { grid: { color: "rgba(255,255,255,0.03)" }, ticks: { color: "var(--text-secondary)" } },
                    x: { grid: { color: "rgba(255,255,255,0.03)" }, ticks: { color: "var(--text-secondary)" } }
                }
            }
        });
        
        // Draw variance chart
        if (varianceChartInstance) varianceChartInstance.destroy();
        const ctxVar = document.getElementById("varianceChart").getContext("2d");
        
        varianceChartInstance = new Chart(ctxVar, {
            type: "radar",
            data: {
                labels: ["GST Sales", "Bank Credits", "ITR Income", "Audited Sales", "Net Worth"],
                datasets: [{
                    label: "Reconciled Proportions (Scale-offset)",
                    data: [85, 95, 82, 90, 80],
                    fill: true,
                    backgroundColor: "rgba(16, 185, 129, 0.2)",
                    borderColor: "var(--color-green)",
                    pointBackgroundColor: "var(--color-green)",
                    pointBorderColor: "#fff"
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: "var(--text-primary)" } } }
            }
        });
        
    } catch (err) {
        // Safe skip if data not fully loaded
    }
}

// Initial Boot
window.onload = async () => {
    await loadBorrowers();
};
