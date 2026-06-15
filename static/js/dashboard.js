// Dashboard JavaScript
class ViolationDashboard {
    constructor() {
        this.violations = [];
        this.stats = {};
        this.autoRefreshEnabled = true;
        this.refreshRate = 10000;
        this.refreshInterval = null;
        this.filterType = '';
        this.filterStatus = '';
        this.init();
    }

    init() {
        this.attachEventListeners();
        this.setupModeSwitching();
        this.setupCameraControls();   // ✅ CAMERA BUTTONS
        this.setupVideoUpload();      // ✅ OFFLINE UPLOAD
        this.loadConfig();
        this.loadData();
        this.startAutoRefresh();
    }

    // ==========================
    // BASIC BUTTONS
    // ==========================
    attachEventListeners() {
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn)
            refreshBtn.addEventListener('click', () => this.loadData());

        const autoBtn = document.getElementById('auto-refresh-toggle');
        if (autoBtn) {
            autoBtn.addEventListener('click', () => {
                this.autoRefreshEnabled = !this.autoRefreshEnabled;
                autoBtn.textContent =
                    `Auto Refresh: ${this.autoRefreshEnabled ? 'ON' : 'OFF'}`;
                this.autoRefreshEnabled
                    ? this.startAutoRefresh()
                    : clearInterval(this.refreshInterval);
            });
        }

        const settingsBtn = document.getElementById("settings-btn");
        if (settingsBtn) {
            settingsBtn.addEventListener("click", () => {
                document.getElementById("settings-modal").style.display = "block";
            });
        }
    }

    // ==========================
    // ONLINE / OFFLINE SWITCH
    // ==========================
    setupModeSwitching() {
        const offlineBtn = document.getElementById("mode-offline");
        const onlineBtn = document.getElementById("mode-online");

        const uploadSection = document.querySelector(".video-section");
        const onlineSection = document.getElementById("online-capture-controls");

        offlineBtn.addEventListener("click", async () => {
            uploadSection.style.display = "block";
            onlineSection.style.display = "none";

            // 🔥 STOP CAMERA FIRST
            try {
                await fetch("/api/camera/stop", { method: "POST" });
            } catch (e) {
                console.error("Camera stop failed", e);
            }

            this.updateCaptureMode("offline");
            this.updateCameraView("offline");
        });

        onlineBtn.addEventListener("click", async () => {
            uploadSection.style.display = "none";
            onlineSection.style.display = "block";

            this.updateCaptureMode("online");

            // 🔥 START CAMERA

            this.updateCameraView("online");
        });
    }
    async updateCaptureMode(mode) {
        try {
            await fetch("/api/config", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ capture_mode: mode })
            });
        } catch (err) {
            console.error("Capture mode error", err);
        }
    }
    updateCameraView(mode) {
        const cam = document.getElementById("camera-feed");
        if (!cam) return;

        if (mode === "online") {
            // ❌ don't auto show here
            cam.style.display = "none";
            cam.src = "";
        } else {
            cam.style.display = "none";
            cam.src = "";
        }
    }

    // ==========================
    // CAMERA START / STOP
    // ==========================
    setupCameraControls() {
        const startBtn = document.getElementById("start-capture-btn");
        const stopBtn = document.getElementById("stop-capture-btn");

        if (!startBtn || !stopBtn) return;



        startBtn.addEventListener("click", async () => {
            try {
                const res = await fetch("/api/camera/start", { method: "POST" });
                const data = await res.json();

                if (data.success) {

                    const cam = document.getElementById("camera-feed");
                    const onlineSection = document.getElementById("online-capture-controls");

                    // 🔥 Ensure section visible
                    if (onlineSection) {
                        onlineSection.style.display = "block";
                    }
                    // 🔥 ADD THESE LINES HERE
                    cam.style.width = "700px";
                    cam.style.height = "500px";
                    cam.style.border = "2px solid red";


                    // 🔥 Force reload stream
                    cam.src = "";
                    setTimeout(() => {
                        cam.src = "/video_feed?" + new Date().getTime();
                    }, 200);

                    cam.style.display = "block";

                    startBtn.disabled = true;
                    stopBtn.disabled = false;

                } else {
                    alert(data.error || "Camera failed");
                }

            } catch (err) {
                console.error(err);
            }
        });
        stopBtn.addEventListener("click", async () => {
            await fetch("/api/camera/stop", { method: "POST" });

            const cam = document.getElementById("camera-feed");
            cam.style.display = "none";
            cam.src = "";

            startBtn.disabled = false;
            stopBtn.disabled = true;
        });
    }

    // ==========================
    // OFFLINE VIDEO UPLOAD
    // ==========================
    setupVideoUpload() {
        const uploadArea = document.getElementById("upload-area");
        const videoInput = document.getElementById("video-input");

        if (!uploadArea || !videoInput) return;

        uploadArea.addEventListener("click", () => {
            videoInput.click();
        });

        videoInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (!file) return;
            this.uploadVideo(file);
        });
    }

    async uploadVideo(file) {
        const formData = new FormData();
        formData.append("file", file);

        const status = document.getElementById("processing-status");
        const msg = document.getElementById("status-message");

        if (status) status.style.display = "block";
        if (msg) msg.textContent = "Uploading video...";

        try {
            const res = await fetch("/api/videos/upload", {
                method: "POST",
                body: formData
            });

            const data = await res.json();

            if (data.success) {
                msg.textContent = "Processing started...";

                // Start polling for status
                this.pollVideoStatus(data.video_id);

            } else {
                alert(data.error);
            }

        } catch (err) {
            alert("Upload failed");
            status.style.display = "none";
        }
    }

    async pollVideoStatus(videoId) {
        const statusDiv = document.getElementById("processing-status");
        const msg = document.getElementById("status-message");
        const progressFill = document.getElementById("progress-fill");
        const progressText = document.getElementById("progress-text");

        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/video/status/${videoId}`);
                const data = await res.json();

                if (data.success) {
                    const status = data.status;

                    if (progressFill) progressFill.style.width = `${status.progress}%`;
                    if (progressText) progressText.textContent = `${status.progress}%`;
                    if (msg) msg.textContent = status.message;

                    if (status.status === 'completed') {
                        clearInterval(interval);
                        msg.textContent = "Processing Complete!";
                        setTimeout(() => {
                            statusDiv.style.display = "none";
                        }, 3000);

                        // REFRESH DATA AND SCREENSHOTS
                        this.loadData();
                        alert("Video processing complete! Screenshots are now available.");
                    } else if (status.status === 'error') {
                        clearInterval(interval);
                        msg.textContent = "Error: " + status.message;
                        alert("Processing failed: " + status.message);
                    }
                }
            } catch (err) {
                console.error("Polling error", err);
            }
        }, 1000);
    }

    // ==========================
    // DATA
    // ==========================
    async loadConfig() {
        try {
            const res = await fetch('/api/config');
            const data = await res.json();

            const mode = data.config.capture_mode;

            const urlInput = document.getElementById("stream-url");
            const devInput = document.getElementById("webcam-device");
            const directUrlInput = document.getElementById("direct-stream-url");
            if (urlInput) urlInput.value = data.config.stream_url || "";
            if (devInput && data.config.webcam_device !== undefined) devInput.value = data.config.webcam_device;

            if (directUrlInput) {
                directUrlInput.value = data.config.stream_url || (data.config.webcam_device === 0 ? "0" : data.config.webcam_device);
            }

            const uploadSection = document.querySelector(".video-section");
            const onlineSection = document.getElementById("online-capture-controls");

            if (mode === "online") {
                uploadSection.style.display = "none";
                onlineSection.style.display = "block";
                this.updateCameraView("online");
            } else {
                uploadSection.style.display = "block";
                onlineSection.style.display = "none";
                this.updateCameraView("offline");
            }

        } catch (err) {
            console.error("Config load error", err);
        }
    }

    async loadData() {
        try {
            const vRes = await fetch('/api/violations?limit=100');
            const vData = await vRes.json();

            if (vData.success) {
                this.violations = vData.violations;
                const tbody = document.getElementById("violations-tbody");
                if (tbody) {
                    if (this.violations.length === 0) {
                        tbody.innerHTML = '<tr class="loading-row"><td colspan="8">No violations recorded</td></tr>';
                    } else {
                        tbody.innerHTML = this.violations.map(v => {
                            // SQLite saves UTC without 'Z', so we append 'Z' to tell JS it's UTC
                            const tsStr = v.timestamp.replace(' ', 'T') + 'Z';
                            const time = new Date(tsStr).toLocaleString();
                            const statusClass = `status-${v.status}`;
                            const typeClass = `type-${v.violation_type}`;

                            // Check for screenshot
                            const screenshotBtn = v.screenshot_path
                                ? `<img src="/api/screenshot/${v.screenshot_path.split('/').pop()}" alt="Proof" style="width: 80px; height: auto; border-radius: 4px; cursor: pointer; border: 1px solid #ddd;" onclick="window.open(this.src, '_blank')" title="Click to enlarge">`
                                : '<span style="color:#ccc; font-size:0.8rem">No Proof</span>';
                            const deleteBtn = v.screenshot_path
                                ? `<button class="action-btn btn-delete-table" onclick="dashboard.deleteScreenshot('${v.screenshot_path.split('/').pop()}')" title="Delete Proof">🗑️</button>`
                                : '';

                            return `
                                <tr>
                                    <td>${v.id}</td>
                                    <td class="timestamp">${time}</td>
                                    <td><span class="type-badge ${typeClass}">${v.violation_type}</span></td>
                                    <td>${v.description || '-'}</td>
                                    <td>${v.plate_number || 'Unknown'}</td>
                                    <td class="confidence">${(v.confidence * 100).toFixed(0)}%</td>
                                    <td><span class="status-badge ${statusClass}">${v.status}</span></td>
                                    <td class="actions">
                                        ${screenshotBtn}
                                        ${deleteBtn}
                                    </td>
                                </tr>
                            `;
                        }).join('');
                    }
                }
            }

            const sRes = await fetch('/api/stats');
            const sData = await sRes.json();

            if (sData.success) {
                this.stats = sData.stats;
                document.getElementById("stat-total").textContent = this.stats.total || 0;
                document.getElementById("stat-24h").textContent = this.stats.last_24h || 0;
            }

            document.getElementById("last-update").textContent =
                "Last updated: " + new Date().toLocaleTimeString();

        } catch {
            document.getElementById("system-status").textContent = "● OFFLINE";
        }
    }

    async deleteScreenshot(filename) {
        if (!confirm("Are you sure you want to delete this screenshot?")) return;

        try {
            const res = await fetch(`/api/screenshot/${filename}`, { method: 'DELETE' });
            const data = await res.json();

            if (data.success) {
                this.loadData(); // Refresh table
            } else {
                alert("Failed to delete: " + data.error);
            }
        } catch (err) {
            console.error("Delete error:", err);
            alert("Error deleting screenshot");
        }
    }

    async saveSettings() {
        const streamUrl = document.getElementById("stream-url")?.value;
        const webcamDevice = document.getElementById("webcam-device")?.value;

        try {
            const res = await fetch("/api/config", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    stream_url: streamUrl,
                    webcam_device: webcamDevice
                })
            });
            const data = await res.json();
            if (data.success) {
                alert("Settings saved! If camera is running, please stop and start it to apply the new camera.");
                document.getElementById('settings-modal').style.display = 'none';
            } else {
                alert("Failed to save settings");
            }
        } catch (err) {
            console.error("Error saving settings:", err);
            alert("Error saving settings");
        }
    }

    async saveDirectCameraConfig() {
        const inputVal = document.getElementById("direct-stream-url").value.trim();
        let streamUrl = null;
        let webcamDevice = 0;

        if (inputVal.startsWith("http") || inputVal.startsWith("rtsp")) {
            streamUrl = inputVal;
        } else {
            webcamDevice = parseInt(inputVal) || 0;
        }

        try {
            await fetch("/api/config", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    stream_url: streamUrl,
                    webcam_device: webcamDevice
                })
            });
            alert("Camera Saved! If capture is running, Stop it and then Start it again.");
        } catch (err) {
            console.error(err);
            alert("Error saving camera URL.");
        }
    }

    startAutoRefresh() {
        clearInterval(this.refreshInterval);
        this.refreshInterval = setInterval(() => {
            if (this.autoRefreshEnabled) this.loadData();
        }, this.refreshRate);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.dashboard = new ViolationDashboard();
});
