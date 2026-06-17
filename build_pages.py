import os

pages_content = {}

pages_content['violations.html'] = """{% extends "base.html" %}
{% block header_title %}Violations Management{% endblock %}
{% block header_subtitle %}Comprehensive list of all detected traffic violations{% endblock %}

{% block content %}
<!-- Filters Section -->
<section class="bg-[#1a2030] border border-[#262f44] rounded-xl p-4 mb-6 flex flex-wrap items-end gap-4">
    <div class="flex-1 min-w-[150px]">
        <label for="filter-type" class="block text-[11px] text-slate-400 mb-1.5 ml-1">Filter by Type</label>
        <div class="relative">
            <select id="filter-type" class="w-full bg-[#111623] border border-[#262f44] text-slate-200 text-xs rounded-lg block p-2.5 appearance-none focus:outline-none focus:border-blue-500">
                <option value="">All Violations</option>
                <option value="no_helmet">No Helmet</option>
                <option value="overloading">Overloading</option>
                <option value="no_plate">No License Plate</option>
            </select>
            <i class="fa-solid fa-chevron-down absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs pointer-events-none"></i>
        </div>
    </div>
    
    <div class="flex-1 min-w-[150px]">
        <label for="filter-status" class="block text-[11px] text-slate-400 mb-1.5 ml-1">Filter by Status</label>
        <div class="relative">
            <select id="filter-status" class="w-full bg-[#111623] border border-[#262f44] text-slate-200 text-xs rounded-lg block p-2.5 appearance-none focus:outline-none focus:border-blue-500">
                <option value="">All Status</option>
                <option value="pending">Pending</option>
                <option value="processed">Processed</option>
                <option value="dismissed">Dismissed</option>
            </select>
            <i class="fa-solid fa-chevron-down absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs pointer-events-none"></i>
        </div>
    </div>

    <div class="flex items-center gap-3 ml-auto mt-2 xl:mt-0">
        <button id="refresh-btn" class="bg-[#2563eb] hover:bg-blue-600 text-white text-xs font-semibold py-2.5 px-4 rounded-lg transition-colors flex items-center gap-2">
            <i class="fa-solid fa-arrows-rotate"></i> Refresh Now
        </button>
    </div>
</section>

<!-- Violations Table -->
<section class="bg-[#1a2030] border border-[#262f44] rounded-xl flex flex-col overflow-hidden flex-1 min-h-[500px]">
    <div class="px-5 py-4 border-b border-[#262f44] flex justify-between items-center bg-[#1e2536]">
        <h2 class="text-sm font-bold text-white flex items-center gap-2">
            <i class="fa-solid fa-table-list text-blue-500"></i> All Violations Database
        </h2>
        <div class="bg-[#123675] border border-[#1e489a] text-blue-200 text-[10px] font-bold px-2.5 py-1.5 rounded flex items-center gap-1.5">
            <i class="fa-solid fa-database text-blue-400"></i> Production Data
        </div>
    </div>
    
    <div class="overflow-x-auto h-full overflow-y-auto">
        <table class="w-full text-xs text-left text-slate-300">
            <thead class="text-[10px] text-slate-400 uppercase bg-[#141a29] border-b border-[#262f44] sticky top-0 z-10">
                <tr>
                    <th scope="col" class="px-5 py-3 font-semibold">ID</th>
                    <th scope="col" class="px-5 py-3 font-semibold">Time</th>
                    <th scope="col" class="px-5 py-3 font-semibold">Type</th>
                    <th scope="col" class="px-5 py-3 font-semibold">Description</th>
                    <th scope="col" class="px-5 py-3 font-semibold">Plate #</th>
                    <th scope="col" class="px-5 py-3 font-semibold">Conf.</th>
                    <th scope="col" class="px-5 py-3 font-semibold">Status</th>
                    <th scope="col" class="px-5 py-3 font-semibold text-right">Actions</th>
                </tr>
            </thead>
            <tbody id="violations-tbody" class="divide-y divide-[#262f44]">
                <tr class="loading-row">
                    <td colspan="8" class="px-5 py-12 text-center text-slate-500">
                        <div class="flex flex-col items-center justify-center gap-3">
                            <i class="fa-solid fa-spinner fa-spin text-2xl text-blue-500 mb-2"></i>
                            <p>Loading database records...</p>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</section>
{% endblock %}
"""

pages_content['live_capture.html'] = """{% extends "base.html" %}
{% block header_title %}Live Capture & Processing{% endblock %}
{% block header_subtitle %}Process offline videos or connect to live camera streams{% endblock %}

{% block content %}
<section class="bg-[#1a2030] border border-[#262f44] rounded-xl p-6 mb-6 h-full flex flex-col">
    <h2 class="text-lg font-bold text-white mb-6 border-b border-[#262f44] pb-4">Detection Input Source</h2>
    
    <div class="flex flex-col sm:flex-row gap-6 mb-8">
        <!-- Offline Tab -->
        <div class="flex-1" id="mode-offline">
            <input type="radio" name="capture-mode" id="offline-mode" value="offline" checked class="peer hidden">
            <label for="offline-mode" class="cursor-pointer flex items-center gap-4 p-5 rounded-xl border-2 border-[#262f44] bg-[#111623] peer-checked:border-blue-500 peer-checked:bg-[#152344] transition-colors relative">
                <div class="w-12 h-12 rounded-lg bg-blue-500 flex items-center justify-center text-white text-xl shadow-inner">
                    <i class="fa-solid fa-folder-open"></i>
                </div>
                <div class="flex-1">
                    <span class="block font-semibold text-white text-base">Offline Processing</span>
                    <span class="block text-sm text-slate-400 mt-1">Upload & analyze video files locally</span>
                </div>
                <div class="w-5 h-5 rounded-full border-2 border-slate-500 peer-checked:border-blue-500 flex items-center justify-center ml-auto">
                    <div class="w-2.5 h-2.5 rounded-full bg-blue-500 hidden peer-checked:block"></div>
                </div>
            </label>
        </div>
        <!-- Online Tab -->
        <div class="flex-1" id="mode-online">
            <input type="radio" name="capture-mode" id="online-mode" value="online" class="peer hidden">
            <label for="online-mode" class="cursor-pointer flex items-center gap-4 p-5 rounded-xl border-2 border-[#262f44] bg-[#111623] peer-checked:border-blue-500 peer-checked:bg-[#152344] transition-colors relative">
                <div class="w-12 h-12 rounded-lg bg-purple-700 flex items-center justify-center text-white text-xl shadow-inner">
                    <i class="fa-solid fa-video"></i>
                </div>
                <div class="flex-1">
                    <span class="block font-semibold text-white text-base">Live Capture</span>
                    <span class="block text-sm text-slate-400 mt-1">Connect to IP Camera or Webcam</span>
                </div>
                <div class="w-5 h-5 rounded-full border-2 border-slate-500 peer-checked:border-blue-500 flex items-center justify-center ml-auto">
                    <div class="w-2.5 h-2.5 rounded-full bg-blue-500 hidden peer-checked:block"></div>
                </div>
            </label>
        </div>
    </div>

    <!-- Upload Box (Offline) -->
    <div id="upload-area" class="video-section border-2 border-dashed border-[#3a4663] bg-[#141a29] rounded-xl p-16 flex-1 flex flex-col items-center justify-center text-center cursor-pointer hover:border-blue-500 hover:bg-[#152344] transition-colors" onclick="document.getElementById('video-input').click()">
        <div class="w-20 h-20 rounded-full bg-blue-500 mx-auto flex items-center justify-center text-white text-4xl mb-6 shadow-xl shadow-blue-500/20">
            <i class="fa-solid fa-cloud-arrow-up"></i>
        </div>
        <h3 class="text-xl font-bold text-white">Click or drag to upload video for analysis</h3>
        <p class="text-sm text-slate-400 mt-2">Supports MP4, AVI, MKV up to 500MB</p>
        <input type="file" id="video-input" accept="video/*" class="hidden">
    </div>
    
    <div id="processing-status" class="mt-4 bg-[#111623] border border-[#262f44] p-6 rounded-lg" style="display:none;">
        <div class="flex justify-between items-center mb-4">
            <p id="status-message" class="text-sm font-semibold text-slate-300 flex items-center gap-2">
                <i class="fa-solid fa-gear fa-spin text-blue-500"></i> AI Model Processing Video...
            </p>
            <p id="progress-text" class="text-sm font-bold text-blue-400">0%</p>
        </div>
        <div class="w-full bg-[#1e2536] rounded-full h-2.5">
            <div class="bg-blue-500 h-2.5 rounded-full transition-all duration-300" style="width: 0%" id="progress-fill"></div>
        </div>
    </div>

    <!-- Live Capture Controls -->
    <div id="online-capture-controls" class="flex-1 flex flex-col" style="display:none;">
        <div class="flex flex-col sm:flex-row gap-4 mb-6">
            <div class="flex-1 relative">
                <label class="block text-xs text-slate-400 mb-2 font-bold uppercase tracking-wider">Stream URL or Device ID</label>
                <input type="text" id="direct-stream-url" placeholder="0 for Webcam, or http://192.168.1.5:8080/video" class="w-full bg-[#111623] border border-[#262f44] text-slate-200 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500">
            </div>
            <div class="flex items-end pb-0">
                <button class="bg-[#1e2536] hover:bg-[#2a3449] text-slate-300 border border-[#262f44] text-sm font-semibold py-3 px-6 rounded-lg transition-colors" onclick="dashboard.saveDirectCameraConfig()">
                    <i class="fa-solid fa-floppy-disk mr-2"></i> Save Config
                </button>
            </div>
        </div>
        
        <div class="bg-[#111623] border border-[#262f44] rounded-lg p-6 flex flex-col items-center flex-1 justify-center relative overflow-hidden">
            <!-- Camera Feed Box -->
            <div class="relative w-full max-w-3xl aspect-video bg-black rounded-lg border-2 border-[#262f44] mb-6 flex flex-col items-center justify-center overflow-hidden">
                <i id="camera-placeholder-icon" class="fa-solid fa-video-slash text-6xl text-slate-700"></i>
                <img id="camera-feed" class="absolute inset-0 w-full h-full object-cover" style="display:none;" alt="Live Feed">
                
                <!-- Status Overlay -->
                <div id="live-capture-status" class="absolute top-4 left-4 bg-black/60 backdrop-blur-md border border-white/10 p-3 rounded-lg z-10" style="display:none;">
                    <div class="flex items-center gap-2 mb-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span>
                        <p id="capture-status-text" class="text-xs font-bold text-white uppercase tracking-wide">Rec</p>
                    </div>
                    <div class="flex flex-col gap-1 text-[10px] text-white">
                        <span>Frames: <strong id="frames-count" class="text-blue-400">0</strong></span>
                        <span>Violations: <strong id="capture-violations-count" class="text-rose-400">0</strong></span>
                    </div>
                </div>
            </div>
            
            <div class="flex gap-4">
                <button id="start-capture-btn" class="bg-[#2563eb] hover:bg-blue-600 text-white font-bold py-3 px-8 rounded-lg transition-colors text-sm shadow-lg shadow-blue-500/30 flex items-center gap-2">
                    <i class="fa-solid fa-play"></i> Start Stream
                </button>
                <button id="stop-capture-btn" class="bg-[#1e2536] hover:bg-[#2a3449] text-rose-400 border border-[#262f44] font-bold py-3 px-8 rounded-lg transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2" disabled>
                    <i class="fa-solid fa-stop"></i> Stop Stream
                </button>
            </div>
        </div>
    </div>
</section>
{% endblock %}
"""

pages_content['analytics.html'] = """{% extends "base.html" %}
{% block header_title %}Analytics & Intelligence{% endblock %}
{% block header_subtitle %}Advanced statistics and detection trends{% endblock %}

{% block scripts %}
{{ super() }}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    // Initialize dummy charts for analytics page
    document.addEventListener('DOMContentLoaded', function() {
        const ctx1 = document.getElementById('trendChart').getContext('2d');
        new Chart(ctx1, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Helmet Violations',
                    data: [12, 19, 15, 25, 22, 30, 28],
                    borderColor: '#8b5cf6',
                    tension: 0.4,
                    borderWidth: 3
                }, {
                    label: 'Overloading',
                    data: [5, 8, 4, 10, 7, 15, 12],
                    borderColor: '#f59e0b',
                    tension: 0.4,
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#94a3b8' } } },
                scales: {
                    y: { grid: { color: '#262f44' }, ticks: { color: '#94a3b8' } },
                    x: { grid: { color: '#262f44' }, ticks: { color: '#94a3b8' } }
                }
            }
        });

        const ctx2 = document.getElementById('typeChart').getContext('2d');
        new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: ['No Helmet', 'Overloading', 'No Plate'],
                datasets: [{
                    data: [65, 25, 10],
                    backgroundColor: ['#8b5cf6', '#f59e0b', '#ef4444'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 20 } } }
            }
        });
    });
</script>
{% endblock %}

{% block content %}
<!-- Stats Grid -->
<section class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
    <!-- Total -->
    <div class="bg-[#0f213b] border border-[#1e3a8a] rounded-xl p-4 flex items-center gap-4">
        <div class="w-14 h-14 rounded-xl bg-[#1a498b] flex flex-shrink-0 items-center justify-center text-white text-2xl shadow-inner">
            <i class="fa-solid fa-clipboard-list"></i>
        </div>
        <div>
            <h3 class="text-[11px] font-bold text-slate-300 uppercase tracking-widest mb-1">Total Violations</h3>
            <p class="text-2xl font-bold text-white leading-none mb-1" id="stat-total">0</p>
            <p class="text-[10px] text-slate-400">All time recorded</p>
        </div>
    </div>
    <!-- 24h -->
    <div class="bg-[#0f2d1e] border border-[#065f46] rounded-xl p-4 flex items-center gap-4">
        <div class="w-14 h-14 rounded-xl bg-[#127236] flex flex-shrink-0 items-center justify-center text-white text-2xl shadow-inner">
            <i class="fa-solid fa-clock-rotate-left"></i>
        </div>
        <div>
            <h3 class="text-[11px] font-bold text-slate-300 uppercase tracking-widest mb-1">Last 24 Hours</h3>
            <p class="text-2xl font-bold text-white leading-none mb-1" id="stat-24h">0</p>
            <p class="text-[10px] text-slate-400">Violations detected</p>
        </div>
    </div>
    <!-- Helmet -->
    <div class="bg-[#291742] border border-[#4c1d95] rounded-xl p-4 flex items-center gap-4">
        <div class="w-14 h-14 rounded-xl bg-[#5d2192] flex flex-shrink-0 items-center justify-center text-white text-2xl shadow-inner">
            <i class="fa-solid fa-helmet-safety"></i>
        </div>
        <div>
            <h3 class="text-[11px] font-bold text-slate-300 uppercase tracking-widest mb-1">No Helmet</h3>
            <p class="text-2xl font-bold text-white leading-none mb-1" id="stat-helmet">0</p>
            <p class="text-[10px] text-slate-400">Violations detected</p>
        </div>
    </div>
    <!-- Overloading -->
    <div class="bg-[#331c0e] border border-[#78350f] rounded-xl p-4 flex items-center gap-4">
        <div class="w-14 h-14 rounded-xl bg-[#b05e15] flex flex-shrink-0 items-center justify-center text-white text-2xl shadow-inner">
            <i class="fa-solid fa-triangle-exclamation"></i>
        </div>
        <div>
            <h3 class="text-[11px] font-bold text-slate-300 uppercase tracking-widest mb-1">Overloading</h3>
            <p class="text-2xl font-bold text-white leading-none mb-1" id="stat-overload">0</p>
            <p class="text-[10px] text-slate-400">Violations detected</p>
        </div>
    </div>
</section>

<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <div class="lg:col-span-2 bg-[#1a2030] border border-[#262f44] rounded-xl p-6">
        <h3 class="text-sm font-bold text-white mb-6">7-Day Violation Trends</h3>
        <div class="h-80 w-full">
            <canvas id="trendChart"></canvas>
        </div>
    </div>
    <div class="bg-[#1a2030] border border-[#262f44] rounded-xl p-6">
        <h3 class="text-sm font-bold text-white mb-6">Violation Breakdown</h3>
        <div class="h-64 w-full">
            <canvas id="typeChart"></canvas>
        </div>
        <div class="mt-6 pt-6 border-t border-[#262f44] text-center">
            <p class="text-xs text-slate-400">Highest compliance gap: <strong class="text-purple-400">Helmet Usage</strong></p>
        </div>
    </div>
</div>
{% endblock %}
"""

pages_content['reports.html'] = """{% extends "base.html" %}
{% block header_title %}System Reports{% endblock %}
{% block header_subtitle %}Export and download violation data{% endblock %}

{% block content %}
<section class="bg-[#1a2030] border border-[#262f44] rounded-xl p-6 h-full">
    <div class="flex justify-between items-center mb-8">
        <h2 class="text-lg font-bold text-white">Available Reports</h2>
        <button class="bg-[#2563eb] hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-lg transition-colors text-sm flex items-center gap-2">
            <i class="fa-solid fa-plus"></i> Generate Custom Report
        </button>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Report Card 1 -->
        <div class="bg-[#111623] border border-[#262f44] rounded-lg p-5 flex flex-col">
            <div class="flex items-start justify-between mb-4">
                <div class="w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center text-red-500">
                    <i class="fa-solid fa-file-pdf text-xl"></i>
                </div>
                <span class="text-[10px] font-bold px-2 py-1 bg-[#1e2536] text-slate-400 rounded">Today</span>
            </div>
            <h3 class="text-sm font-bold text-white mb-1">Daily Summary Report</h3>
            <p class="text-xs text-slate-400 mb-4 flex-1">Complete summary of all violations detected today across all camera nodes.</p>
            <button class="w-full bg-[#1e2536] hover:bg-[#2a3449] border border-[#262f44] text-white text-xs font-semibold py-2 rounded transition-colors">
                <i class="fa-solid fa-download mr-1"></i> Download PDF
            </button>
        </div>

        <!-- Report Card 2 -->
        <div class="bg-[#111623] border border-[#262f44] rounded-lg p-5 flex flex-col">
            <div class="flex items-start justify-between mb-4">
                <div class="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center text-green-500">
                    <i class="fa-solid fa-file-csv text-xl"></i>
                </div>
                <span class="text-[10px] font-bold px-2 py-1 bg-[#1e2536] text-slate-400 rounded">Auto-Generated</span>
            </div>
            <h3 class="text-sm font-bold text-white mb-1">Weekly Helmet Audit</h3>
            <p class="text-xs text-slate-400 mb-4 flex-1">Raw CSV export of all helmet violations for data analysis and citation mailing.</p>
            <button class="w-full bg-[#1e2536] hover:bg-[#2a3449] border border-[#262f44] text-white text-xs font-semibold py-2 rounded transition-colors">
                <i class="fa-solid fa-download mr-1"></i> Download CSV
            </button>
        </div>
        
        <!-- Report Card 3 -->
        <div class="bg-[#111623] border border-[#262f44] rounded-lg p-5 flex flex-col">
            <div class="flex items-start justify-between mb-4">
                <div class="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-500">
                    <i class="fa-solid fa-file-contract text-xl"></i>
                </div>
                <span class="text-[10px] font-bold px-2 py-1 bg-[#1e2536] text-slate-400 rounded">Archive</span>
            </div>
            <h3 class="text-sm font-bold text-white mb-1">Monthly Analytics</h3>
            <p class="text-xs text-slate-400 mb-4 flex-1">Executive summary of traffic trends, accuracy rates, and operational status.</p>
            <button class="w-full bg-[#1e2536] hover:bg-[#2a3449] border border-[#262f44] text-white text-xs font-semibold py-2 rounded transition-colors">
                <i class="fa-solid fa-download mr-1"></i> Download PDF
            </button>
        </div>
    </div>
</section>
{% endblock %}
"""

pages_content['devices.html'] = """{% extends "base.html" %}
{% block header_title %}Connected Devices{% endblock %}
{% block header_subtitle %}Manage IP cameras and edge nodes{% endblock %}

{% block content %}
<section class="bg-[#1a2030] border border-[#262f44] rounded-xl p-6 h-full">
    <div class="flex justify-between items-center mb-6">
        <h2 class="text-lg font-bold text-white">Camera Network</h2>
        <button class="bg-[#2563eb] hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-lg transition-colors text-sm flex items-center gap-2">
            <i class="fa-solid fa-plus"></i> Add Device
        </button>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Device 1 -->
        <div class="bg-[#111623] border border-[#262f44] rounded-xl p-5 flex gap-4 items-center">
            <div class="relative">
                <div class="w-16 h-16 rounded-full bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-500 text-2xl">
                    <i class="fa-solid fa-video"></i>
                </div>
                <span class="absolute bottom-0 right-0 w-4 h-4 bg-emerald-500 border-2 border-[#111623] rounded-full"></span>
            </div>
            <div class="flex-1">
                <h3 class="text-sm font-bold text-white">Main Intersection Cam</h3>
                <p class="text-xs text-slate-400">192.168.1.100:8080</p>
                <div class="flex gap-2 mt-2">
                    <span class="text-[9px] bg-[#1e2536] text-slate-300 px-2 py-0.5 rounded uppercase font-bold tracking-wider">1080p</span>
                    <span class="text-[9px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded uppercase font-bold tracking-wider">Online</span>
                </div>
            </div>
            <button class="w-8 h-8 rounded bg-[#1e2536] hover:bg-[#2a3449] text-slate-300 flex items-center justify-center transition-colors">
                <i class="fa-solid fa-ellipsis-vertical"></i>
            </button>
        </div>

        <!-- Device 2 -->
        <div class="bg-[#111623] border border-[#262f44] rounded-xl p-5 flex gap-4 items-center opacity-70">
            <div class="relative">
                <div class="w-16 h-16 rounded-full bg-slate-500/10 border border-slate-500/30 flex items-center justify-center text-slate-500 text-2xl">
                    <i class="fa-solid fa-video-slash"></i>
                </div>
                <span class="absolute bottom-0 right-0 w-4 h-4 bg-rose-500 border-2 border-[#111623] rounded-full"></span>
            </div>
            <div class="flex-1">
                <h3 class="text-sm font-bold text-white">Highway Node 4</h3>
                <p class="text-xs text-slate-400">10.0.0.55:554</p>
                <div class="flex gap-2 mt-2">
                    <span class="text-[9px] bg-[#1e2536] text-slate-300 px-2 py-0.5 rounded uppercase font-bold tracking-wider">4K</span>
                    <span class="text-[9px] bg-rose-500/20 text-rose-400 border border-rose-500/20 px-2 py-0.5 rounded uppercase font-bold tracking-wider">Offline</span>
                </div>
            </div>
            <button class="w-8 h-8 rounded bg-[#1e2536] hover:bg-[#2a3449] text-slate-300 flex items-center justify-center transition-colors">
                <i class="fa-solid fa-rotate-right"></i>
            </button>
        </div>
    </div>
</section>
{% endblock %}
"""

pages_content['settings.html'] = """{% extends "base.html" %}
{% block header_title %}System Settings{% endblock %}
{% block header_subtitle %}Configure AI models and system preferences{% endblock %}

{% block content %}
<section class="bg-[#1a2030] border border-[#262f44] rounded-xl overflow-hidden max-w-4xl h-full">
    <div class="flex border-b border-[#262f44]">
        <button class="px-6 py-4 text-sm font-bold text-blue-400 border-b-2 border-blue-500 bg-[#152344]">AI Configuration</button>
        <button class="px-6 py-4 text-sm font-bold text-slate-400 hover:text-white transition-colors">Notifications</button>
        <button class="px-6 py-4 text-sm font-bold text-slate-400 hover:text-white transition-colors">Database</button>
    </div>
    
    <div class="p-8">
        <h3 class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-6">Detection Modules</h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
            <div class="bg-[#111623] border border-[#262f44] p-5 rounded-xl flex items-start gap-4">
                <input type="checkbox" checked class="mt-1 w-5 h-5 rounded bg-[#1e2536] border-[#262f44] text-blue-500 focus:ring-0 focus:ring-offset-0">
                <div>
                    <h4 class="text-sm font-bold text-white mb-1">Helmet Detection (YOLOv8)</h4>
                    <p class="text-xs text-slate-400">Detects riders without helmets on two-wheelers.</p>
                </div>
            </div>
            <div class="bg-[#111623] border border-[#262f44] p-5 rounded-xl flex items-start gap-4">
                <input type="checkbox" checked class="mt-1 w-5 h-5 rounded bg-[#1e2536] border-[#262f44] text-blue-500 focus:ring-0 focus:ring-offset-0">
                <div>
                    <h4 class="text-sm font-bold text-white mb-1">License Plate OCR</h4>
                    <p class="text-xs text-slate-400">Extracts text from detected license plates using EasyOCR.</p>
                </div>
            </div>
            <div class="bg-[#111623] border border-[#262f44] p-5 rounded-xl flex items-start gap-4">
                <input type="checkbox" checked class="mt-1 w-5 h-5 rounded bg-[#1e2536] border-[#262f44] text-blue-500 focus:ring-0 focus:ring-offset-0">
                <div>
                    <h4 class="text-sm font-bold text-white mb-1">Overloading Detection</h4>
                    <p class="text-xs text-slate-400">Flags vehicles with more than 2 passengers.</p>
                </div>
            </div>
        </div>
        
        <h3 class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-6">Accuracy Tuning</h3>
        
        <div class="bg-[#111623] border border-[#262f44] p-6 rounded-xl max-w-xl mb-8">
            <div class="flex justify-between items-center mb-4">
                <div>
                    <h4 class="text-sm font-bold text-white">Base Confidence Threshold</h4>
                    <p class="text-xs text-slate-400 mt-1">Minimum confidence score required to record a violation.</p>
                </div>
                <span class="text-lg font-bold text-blue-400 bg-blue-500/10 px-3 py-1 rounded">45%</span>
            </div>
            <input type="range" min="0" max="100" value="45" class="w-full h-2 bg-[#262f44] rounded-lg appearance-none cursor-pointer accent-blue-500">
            <div class="flex justify-between mt-2 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                <span>More False Positives</span>
                <span>Highly Strict</span>
            </div>
        </div>
        
        <div class="pt-6 border-t border-[#262f44]">
            <button class="bg-[#2563eb] hover:bg-blue-600 text-white font-bold py-2.5 px-8 rounded-lg transition-colors text-sm">
                Save Configurations
            </button>
        </div>
    </div>
</section>
{% endblock %}
"""

pages_content['users.html'] = """{% extends "base.html" %}
{% block header_title %}User Management{% endblock %}
{% block header_subtitle %}Manage operators and access control{% endblock %}

{% block content %}
<section class="bg-[#1a2030] border border-[#262f44] rounded-xl p-6 h-full">
    <div class="flex justify-between items-center mb-6">
        <h2 class="text-lg font-bold text-white">System Users</h2>
        <button class="bg-[#2563eb] hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-lg transition-colors text-sm flex items-center gap-2">
            <i class="fa-solid fa-user-plus"></i> Add User
        </button>
    </div>
    
    <div class="border border-[#262f44] rounded-lg overflow-hidden">
        <table class="w-full text-sm text-left text-slate-300">
            <thead class="text-xs text-slate-400 uppercase bg-[#141a29] border-b border-[#262f44]">
                <tr>
                    <th scope="col" class="px-6 py-4">Name</th>
                    <th scope="col" class="px-6 py-4">Role</th>
                    <th scope="col" class="px-6 py-4">Status</th>
                    <th scope="col" class="px-6 py-4">Last Login</th>
                    <th scope="col" class="px-6 py-4 text-right">Actions</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-[#262f44] bg-[#111623]">
                <tr>
                    <td class="px-6 py-4 font-bold text-white flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs">AD</div>
                        Authority Admin
                    </td>
                    <td class="px-6 py-4"><span class="bg-purple-500/20 text-purple-400 border border-purple-500/20 px-2 py-1 rounded text-xs font-bold uppercase">Administrator</span></td>
                    <td class="px-6 py-4"><span class="text-emerald-500 font-bold flex items-center gap-2"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Active</span></td>
                    <td class="px-6 py-4 text-slate-400 text-xs">Just now</td>
                    <td class="px-6 py-4 text-right">
                        <button class="text-slate-400 hover:text-white transition-colors"><i class="fa-solid fa-pen"></i></button>
                    </td>
                </tr>
                <tr>
                    <td class="px-6 py-4 font-bold text-white flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs">OP</div>
                        Desk Operator 1
                    </td>
                    <td class="px-6 py-4"><span class="bg-blue-500/20 text-blue-400 border border-blue-500/20 px-2 py-1 rounded text-xs font-bold uppercase">Operator</span></td>
                    <td class="px-6 py-4"><span class="text-emerald-500 font-bold flex items-center gap-2"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Active</span></td>
                    <td class="px-6 py-4 text-slate-400 text-xs">2 hours ago</td>
                    <td class="px-6 py-4 text-right">
                        <button class="text-slate-400 hover:text-white transition-colors"><i class="fa-solid fa-pen"></i></button>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</section>
{% endblock %}
"""

pages_content['alerts.html'] = """{% extends "base.html" %}
{% block header_title %}Alerts & Notifications{% endblock %}
{% block header_subtitle %}Twilio SMS and Call dispatch logs{% endblock %}

{% block content %}
<section class="bg-[#1a2030] border border-[#262f44] rounded-xl p-6 h-full">
    <h2 class="text-lg font-bold text-white mb-6">Dispatch History</h2>
    
    <div class="space-y-4">
        <div class="bg-[#111623] border border-[#262f44] rounded-lg p-4 flex gap-4 items-start">
            <div class="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-500 shrink-0">
                <i class="fa-solid fa-message"></i>
            </div>
            <div>
                <div class="flex items-center gap-3 mb-1">
                    <h3 class="text-sm font-bold text-white">SMS Sent to Vehicle Owner</h3>
                    <span class="text-[10px] text-slate-500">10 mins ago</span>
                </div>
                <p class="text-xs text-slate-400 mb-2">Notice sent for Plate <strong class="text-white">AP30ak5566</strong> regarding No Helmet violation.</p>
                <span class="bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 px-2 py-0.5 rounded text-[10px] font-bold uppercase">Delivered</span>
            </div>
        </div>
        
        <div class="bg-[#111623] border border-[#262f44] rounded-lg p-4 flex gap-4 items-start">
            <div class="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-500 shrink-0">
                <i class="fa-solid fa-phone"></i>
            </div>
            <div>
                <div class="flex items-center gap-3 mb-1">
                    <h3 class="text-sm font-bold text-white">Automated Voice Call</h3>
                    <span class="text-[10px] text-slate-500">1 hour ago</span>
                </div>
                <p class="text-xs text-slate-400 mb-2">Automated warning call dispatched for Overloading.</p>
                <span class="bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 px-2 py-0.5 rounded text-[10px] font-bold uppercase">Answered</span>
            </div>
        </div>
    </div>
</section>
{% endblock %}
"""

pages_content['logs.html'] = """{% extends "base.html" %}
{% block header_title %}System Logs{% endblock %}
{% block header_subtitle %}Live backend debugging and traces{% endblock %}

{% block content %}
<section class="bg-black border border-[#262f44] rounded-xl flex flex-col h-[600px] overflow-hidden shadow-2xl">
    <div class="bg-[#1e2536] border-b border-[#262f44] px-4 py-2 flex justify-between items-center">
        <div class="flex gap-2">
            <div class="w-3 h-3 rounded-full bg-rose-500"></div>
            <div class="w-3 h-3 rounded-full bg-amber-500"></div>
            <div class="w-3 h-3 rounded-full bg-emerald-500"></div>
        </div>
        <span class="text-xs font-mono text-slate-400">output/logs/detection.log</span>
        <button class="text-slate-400 hover:text-white"><i class="fa-solid fa-download"></i></button>
    </div>
    <div class="p-4 font-mono text-xs overflow-y-auto flex-1">
        <div class="text-slate-500 mb-1">[2026-06-15 14:30:10] <span class="text-blue-400">INFO</span> - Initializing detection system...</div>
        <div class="text-slate-500 mb-1">[2026-06-15 14:30:12] <span class="text-blue-400">INFO</span> - Loaded YOLOv8n models successfully.</div>
        <div class="text-slate-500 mb-1">[2026-06-15 14:32:05] <span class="text-amber-400">WARN</span> - Confidence threshold for OCR is below 50%.</div>
        <div class="text-slate-500 mb-1">[2026-06-15 14:45:22] <span class="text-blue-400">INFO</span> - Processed 1500 frames. Violations: 37</div>
        <div class="text-slate-500 mb-1">[2026-06-15 14:50:01] <span class="text-emerald-400">SUCCESS</span> - Recorded violation ID 93 to database.</div>
        <div class="text-slate-500 mb-1 flex items-center"><span class="animate-pulse mr-2 block w-2 h-4 bg-white/50"></span> Waiting for new logs...</div>
    </div>
</section>
{% endblock %}
"""

for filename, content in pages_content.items():
    filepath = os.path.join('frontend', 'templates', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Wrote {filename}')
