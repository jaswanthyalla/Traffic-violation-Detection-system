import os

pages = {
    'violations.html': ('Violations', 'View and manage all traffic violations'),
    'live_capture.html': ('Live Capture', 'Real-time camera feed and detection'),
    'analytics.html': ('Analytics', 'System analytics and statistics'),
    'reports.html': ('Reports', 'Generate and download reports'),
    'devices.html': ('Devices', 'Manage connected cameras and devices'),
    'settings.html': ('Settings', 'System configuration and preferences'),
    'users.html': ('Users', 'Manage user accounts and permissions'),
    'alerts.html': ('Alerts', 'System alerts and notifications'),
    'logs.html': ('Logs', 'System logs and audit trails')
}

template = '''{{% extends "base.html" %}}

{{% block header_title %}}{title}{{% endblock %}}
{{% block header_subtitle %}}{subtitle}{{% endblock %}}

{{% block content %}}
<section class="bg-[#1a2030] border border-[#262f44] rounded-xl flex flex-col overflow-hidden p-12 text-center h-[500px] justify-center">
    <div class="flex flex-col items-center justify-center gap-4">
        <div class="w-16 h-16 rounded-2xl bg-[#111623] border border-[#262f44] flex items-center justify-center text-blue-500 mb-2 shadow-inner">
            <i class="fa-solid fa-screwdriver-wrench text-3xl"></i>
        </div>
        <h2 class="text-2xl font-bold text-white">{title} Module</h2>
        <p class="text-slate-400 max-w-md">This module is currently under development. The full feature set will be available in an upcoming update.</p>
        <a href="{{{{ url_for('index') }}}}" class="mt-6 bg-[#2563eb] hover:bg-blue-600 text-white font-medium py-2.5 px-6 rounded-lg transition-colors flex items-center gap-2">
            <i class="fa-solid fa-arrow-left"></i> Back to Dashboard
        </a>
    </div>
</section>
{{% endblock %}}
'''

for filename, (title, subtitle) in pages.items():
    filepath = os.path.join('frontend', 'templates', filename)
    with open(filepath, 'w') as f:
        f.write(template.format(title=title, subtitle=subtitle))
    print(f'Created {filename}')
