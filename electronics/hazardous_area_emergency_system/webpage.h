#ifndef WEBPAGE_H
#define WEBPAGE_H

#include <Arduino.h>

const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HazardGuard C3 // Hazardous Area Emergency System</title>
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: rgba(20, 27, 45, 0.85);
      --card-border: #1e293b;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --accent: #00f2fe;
      --accent-glow: rgba(0, 242, 254, 0.25);
      --green: #10b981;
      --yellow: #f59e0b;
      --red: #ef4444;
      --red-glow: rgba(239, 68, 68, 0.4);
      --radius: 14px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 18px; min-height: 100vh; line-height: 1.5; }
    .container { max-width: 1100px; margin: 0 auto; }

    /* Header */
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      padding-bottom: 18px;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 20px;
    }
    .brand-title { font-size: 1.5rem; font-weight: 800; letter-spacing: 0.5px; display: flex; align-items: center; gap: 10px; }
    .brand-badge { background: #0284c7; color: #fff; font-size: 0.72rem; padding: 3px 8px; border-radius: 6px; font-weight: 700; }
    .sub-title { font-size: 0.82rem; color: var(--text-muted); font-weight: 400; }
    .header-meta { display: flex; align-items: center; gap: 10px; font-size: 0.85rem; }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.4px;
      text-transform: uppercase;
    }
    .badge-normal { background: rgba(16, 185, 129, 0.15); color: var(--green); border: 1px solid var(--green); }
    .badge-warning { background: rgba(245, 158, 11, 0.15); color: var(--yellow); border: 1px solid var(--yellow); }
    .badge-danger { background: rgba(239, 68, 68, 0.25); color: var(--red); border: 1px solid var(--red); animation: pulseAlert 1.2s infinite; }
    .pulse-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }

    @keyframes pulseAlert {
      0%, 100% { box-shadow: 0 0 10px var(--red-glow); transform: scale(1); }
      50% { box-shadow: 0 0 24px rgba(239, 68, 68, 0.7); transform: scale(1.02); }
    }

    /* Main Threat Banner */
    .threat-banner {
      border-radius: var(--radius);
      padding: 16px 22px;
      margin-bottom: 22px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 14px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      transition: all 0.3s ease;
    }
    .threat-banner.normal { border-left: 6px solid var(--green); }
    .threat-banner.warning { border-left: 6px solid var(--yellow); background: rgba(245, 158, 11, 0.08); }
    .threat-banner.danger { border-left: 6px solid var(--red); background: rgba(239, 68, 68, 0.12); box-shadow: 0 0 20px var(--red-glow); }
    .threat-text h3 { font-size: 1.15rem; font-weight: 700; margin-bottom: 4px; }
    .threat-text p { font-size: 0.85rem; color: var(--text-muted); }

    /* Sensor Cards Grid */
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 18px;
      position: relative;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    .card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .card-title { font-size: 0.82rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); }
    .card-icon { font-size: 1.3rem; }
    .card-value { font-size: 2.1rem; font-weight: 800; letter-spacing: -0.5px; color: #fff; margin-bottom: 4px; }
    .card-unit { font-size: 0.95rem; font-weight: 500; color: var(--text-muted); margin-left: 4px; }
    .card-sub { font-size: 0.8rem; color: var(--text-muted); display: flex; justify-content: space-between; margin-top: 8px; }

    /* Progress bar */
    .bar-bg { width: 100%; height: 8px; background: #1e293b; border-radius: 4px; overflow: hidden; margin-top: 10px; }
    .bar-fill { height: 100%; border-radius: 4px; width: 0%; transition: width 0.4s ease, background-color 0.4s ease; }

    /* Controls & Actions Section */
    .control-panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 20px;
      margin-bottom: 24px;
    }
    .panel-title { font-size: 1rem; font-weight: 700; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
    .mode-buttons { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 18px; }
    .btn-mode {
      flex: 1;
      min-width: 140px;
      background: #1e293b;
      border: 1px solid #334155;
      color: #e2e8f0;
      padding: 10px 14px;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      transition: all 0.2s ease;
    }
    .btn-mode.active {
      background: #0284c7;
      border-color: #38bdf8;
      color: #fff;
      box-shadow: 0 0 14px rgba(2, 132, 199, 0.4);
    }
    .btn-mode:hover:not(.active) { background: #334155; }
    .mode-desc { font-size: 0.7rem; font-weight: 400; opacity: 0.8; }

    .action-row { display: flex; gap: 12px; flex-wrap: wrap; }
    .btn-action {
      flex: 1;
      min-width: 150px;
      padding: 12px 18px;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 700;
      cursor: pointer;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.2s ease;
    }
    .btn-trip { background: #dc2626; color: #fff; box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3); }
    .btn-trip:hover { background: #b91c1c; }
    .btn-reset { background: #059669; color: #fff; box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3); }
    .btn-reset:hover { background: #047857; }
    .btn-siren { background: #475569; color: #fff; }
    .btn-siren:hover { background: #64748b; }

    /* Threshold tuning */
    .thresh-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-top: 18px; }
    .thresh-item { background: #111827; padding: 12px; border-radius: 8px; border: 1px solid #1f2937; }
    .thresh-label { font-size: 0.75rem; color: var(--text-muted); margin-bottom: 6px; display: block; }
    .thresh-input { width: 100%; background: #1f2937; border: 1px solid #374151; color: #fff; padding: 8px 10px; border-radius: 6px; font-size: 0.9rem; }

    /* Terminal Event Log */
    .log-panel {
      background: #050811;
      border: 1px solid var(--card-border);
      border-radius: var(--radius);
      padding: 16px;
    }
    .log-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .log-title { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.5px; }
    .log-box {
      background: #02040a;
      border: 1px solid #111827;
      border-radius: 6px;
      height: 160px;
      overflow-y: auto;
      padding: 10px;
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      font-size: 0.78rem;
      color: #94a3b8;
    }
    .log-line { margin-bottom: 4px; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 2px; }
    .log-ts { color: #64748b; margin-right: 8px; }
    .log-alert { color: #f87171; font-weight: 600; }
    .log-warn { color: #fbbf24; }
    .log-ok { color: #34d399; }
    .log-act { color: #38bdf8; font-weight: 600; }

    footer { text-align: center; margin-top: 25px; font-size: 0.78rem; color: #475569; }
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <header>
      <div>
        <div class="brand-title">
          <span>🚨 HAZARDGUARD C3</span>
          <span class="brand-badge">SHAKTHIKULANGARA STEM</span>
        </div>
        <div class="sub-title">Smart Multi-Hazard Emergency & Safety Automation Platform (ESP32-C3)</div>
      </div>
      <div class="header-meta">
        <div id="modePill" class="badge badge-normal">HOUSEHOLD MODE</div>
        <div id="statusBadge" class="badge badge-normal">
          <span class="pulse-dot"></span>
          <span id="statusText">SYSTEM ARMED</span>
        </div>
      </div>
    </header>

    <!-- Master Threat Status Banner -->
    <div id="threatBanner" class="threat-banner normal">
      <div class="threat-text">
        <h3 id="bannerTitle">All Monitored Parameters Normal</h3>
        <p id="bannerDesc">Atmospheric combustible gas, ambient heat, and perimeter clearance within safety margins.</p>
      </div>
      <div id="uptimeDisplay" style="font-size: 0.85rem; color: var(--text-muted);">Uptime: 00:00:00</div>
    </div>

    <!-- Live Telemetry Grid -->
    <div class="grid">
      <!-- Gas Sensor Card -->
      <div class="card">
        <div class="card-head">
          <span class="card-title">Gas & Vapor (MQ-2/135)</span>
          <span class="card-icon">🛢️</span>
        </div>
        <div class="card-value">
          <span id="gasRaw">0</span><span class="card-unit">ADC</span>
        </div>
        <div class="bar-bg">
          <div id="gasBar" class="bar-fill" style="width: 0%; background: var(--green);"></div>
        </div>
        <div class="card-sub">
          <span>Est: <b id="gasPpm">0</b> ppm</span>
          <span>Alarm: <b id="gasThreshVal">1900</b></span>
        </div>
      </div>

      <!-- Temperature & Humidity Card -->
      <div class="card">
        <div class="card-head">
          <span class="card-title">Thermal Monitor (DHT11)</span>
          <span class="card-icon">🌡️</span>
        </div>
        <div class="card-value">
          <span id="tempVal">0.0</span><span class="card-unit">°C</span>
        </div>
        <div class="bar-bg">
          <div id="tempBar" class="bar-fill" style="width: 0%; background: var(--green);"></div>
        </div>
        <div class="card-sub">
          <span>Humidity: <b id="humidityVal">0</b>%</span>
          <span>Alarm: <b id="tempThreshVal">52.0</b>°C</span>
        </div>
      </div>

      <!-- Ultrasonic Clearance / Tank Sump Card -->
      <div class="card">
        <div class="card-head">
          <span id="usTitle" class="card-title">Perimeter / Tank (HC-SR04)</span>
          <span class="card-icon">📏</span>
        </div>
        <div class="card-value">
          <span id="distVal">0</span><span class="card-unit">cm</span>
        </div>
        <div class="bar-bg">
          <div id="distBar" class="bar-fill" style="width: 0%; background: var(--green);"></div>
        </div>
        <div class="card-sub">
          <span id="distSub">Clearance: <b id="distStatus">SAFE</b></span>
          <span>Danger: &lt; <b id="distThreshVal">30</b> cm</span>
        </div>
      </div>

      <!-- Emergency Relay State Card -->
      <div class="card">
        <div class="card-head">
          <span class="card-title">Safety Actuator Relay</span>
          <span class="card-icon">⚡</span>
        </div>
        <div class="card-value" id="relayStateText" style="font-size: 1.7rem; color: var(--green);">
          SAFE (IDLE)
        </div>
        <div class="bar-bg">
          <div id="relayBar" class="bar-fill" style="width: 0%; background: var(--green);"></div>
        </div>
        <div class="card-sub">
          <span>Load: Exhaust Fan / Gas Solenoid</span>
          <span id="relayTrigger">Auto Supervised</span>
        </div>
      </div>
    </div>

    <!-- Mode Selector & Controls -->
    <div class="control-panel">
      <div class="panel-title">🛡️ Environment Protection Profiles</div>
      <div class="mode-buttons">
        <button id="btnMode0" class="btn-mode active" onclick="setMode(0)">
          <span>🏠 Household Mode</span>
          <span class="mode-desc">Kitchen LPG leak & fire supervision</span>
        </button>
        <button id="btnMode1" class="btn-mode" onclick="setMode(1)">
          <span>🏨 Hotel Mode</span>
          <span class="mode-desc">Boiler overheat & commercial gas leak</span>
        </button>
        <button id="btnMode2" class="btn-mode" onclick="setMode(2)">
          <span>🏭 Industrial Mode</span>
          <span class="mode-desc">Machinery intrusion & toxic effluent</span>
        </button>
      </div>

      <div class="panel-title" style="margin-top: 18px;">⚡ Emergency Response & Testing</div>
      <div class="action-row">
        <button class="btn-action btn-trip" onclick="tripRelay(1)">
          ⚠️ TRIP RELAY (EMERGENCY VENT)
        </button>
        <button class="btn-action btn-reset" onclick="tripRelay(0)">
          ✅ RESET RELAY & ALARMS
        </button>
        <button id="btnAudioSiren" class="btn-action btn-siren" onclick="toggleWebSiren()">
          🔊 TEST AUDIO SIREN
        </button>
      </div>

      <!-- Live Threshold Tuning -->
      <div class="thresh-grid">
        <div class="thresh-item">
          <label class="thresh-label">Gas Alarm Limit (ADC):</label>
          <input type="number" id="inGasAlarm" class="thresh-input" min="300" max="4000" step="50">
        </div>
        <div class="thresh-item">
          <label class="thresh-label">Temp Fire Alarm (°C):</label>
          <input type="number" id="inTempAlarm" class="thresh-input" min="20" max="90" step="1">
        </div>
        <div class="thresh-item">
          <label class="thresh-label">Ultrasonic Breach Limit (cm):</label>
          <input type="number" id="inDistLimit" class="thresh-input" min="5" max="250" step="5">
        </div>
        <div class="thresh-item" style="display:flex; align-items:flex-end;">
          <button class="btn-action btn-reset" style="width:100%; height:38px; font-size:0.8rem;" onclick="saveThresholds()">
            💾 Apply Thresholds
          </button>
        </div>
      </div>
    </div>

    <!-- Live Event Log -->
    <div class="log-panel">
      <div class="log-head">
        <span class="log-title">Telemetry & Hazard Event Journal</span>
        <button onclick="clearLogUI()" style="background:none; border:none; color:var(--text-muted); font-size:0.75rem; cursor:pointer;">Clear Log</button>
      </div>
      <div id="logBox" class="log-box">
        <div class="log-line"><span class="log-ts">[00:00:00]</span> <span class="log-ok">SYSTEM READY:</span> HazardGuard C3 online. Listening on Wi-Fi interface.</div>
      </div>
    </div>

    <footer>
      Shakthikulangara School STEM Lab • Electronics & IoT Engineering Project • ESP32-C3
    </footer>
  </div>

  <script>
    let audioCtx = null;
    let sirenOsc1 = null;
    let sirenOsc2 = null;
    let sirenGain = null;
    let isSirenPlaying = false;
    let lastRelayState = -1;
    let lastHazardLevel = -1;

    // Web Audio Siren Generator (Runs purely client-side without external media files!)
    function toggleWebSiren() {
      if (isSirenPlaying) {
        stopWebSiren();
      } else {
        startWebSiren();
      }
    }

    function startWebSiren() {
      try {
        if (!audioCtx) {
          audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
          audioCtx.resume();
        }

        sirenOsc1 = audioCtx.createOscillator();
        sirenOsc2 = audioCtx.createOscillator();
        sirenGain = audioCtx.createGain();

        sirenOsc1.type = 'sawtooth';
        sirenOsc2.type = 'sine';

        // Warble frequency modulation
        const now = audioCtx.currentTime;
        sirenOsc1.frequency.setValueAtTime(750, now);
        sirenOsc2.frequency.setValueAtTime(800, now);

        sirenGain.gain.setValueAtTime(0.18, now);

        // LFO warble
        let modTimer = setInterval(() => {
          if (!isSirenPlaying || !audioCtx) {
            clearInterval(modTimer);
            return;
          }
          const t = audioCtx.currentTime;
          sirenOsc1.frequency.linearRampToValueAtTime(1100, t + 0.25);
          sirenOsc1.frequency.linearRampToValueAtTime(700, t + 0.5);
        }, 500);

        sirenOsc1.connect(sirenGain);
        sirenOsc2.connect(sirenGain);
        sirenGain.connect(audioCtx.destination);

        sirenOsc1.start();
        sirenOsc2.start();
        isSirenPlaying = true;
        document.getElementById('btnAudioSiren').innerText = '🔇 STOP AUDIO SIREN';
        document.getElementById('btnAudioSiren').style.background = '#dc2626';
      } catch (e) {
        console.warn('AudioContext error:', e);
      }
    }

    function stopWebSiren() {
      if (sirenOsc1) { sirenOsc1.stop(); sirenOsc1.disconnect(); sirenOsc1 = null; }
      if (sirenOsc2) { sirenOsc2.stop(); sirenOsc2.disconnect(); sirenOsc2 = null; }
      isSirenPlaying = false;
      document.getElementById('btnAudioSiren').innerText = '🔊 TEST AUDIO SIREN';
      document.getElementById('btnAudioSiren').style.background = '#475569';
    }

    function logMessage(level, text) {
      const logBox = document.getElementById('logBox');
      const now = new Date().toTimeString().split(' ')[0];
      const div = document.createElement('div');
      div.className = 'log-line';
      let tagClass = 'log-ok';
      if (level === 'ALERT') tagClass = 'log-alert';
      if (level === 'WARN') tagClass = 'log-warn';
      if (level === 'ACT') tagClass = 'log-act';
      div.innerHTML = `<span class="log-ts">[${now}]</span> <span class="${tagClass}">${level}:</span> ${text}`;
      logBox.appendChild(div);
      logBox.scrollTop = logBox.scrollHeight;
    }

    function clearLogUI() {
      document.getElementById('logBox').innerHTML = '';
    }

    // REST API calls
    function tripRelay(state) {
      fetch('/api/relay?state=' + state)
        .then(r => r.json())
        .then(data => {
          logMessage('ACT', state === 1 ? 'Emergency Relay Manually TRIPPED!' : 'Relay Disengaged / Alarms Reset.');
          fetchTelemetry();
        })
        .catch(e => console.error(e));
    }

    function setMode(modeIdx) {
      fetch('/api/mode?mode=' + modeIdx)
        .then(r => r.json())
        .then(data => {
          updateModeUI(modeIdx);
          logMessage('ACT', `Switched to Mode: ${data.modeName}`);
          fetchTelemetry();
        })
        .catch(e => console.error(e));
    }

    function updateModeUI(modeIdx) {
      [0, 1, 2].forEach(i => {
        const btn = document.getElementById('btnMode' + i);
        if (btn) btn.className = (i === modeIdx) ? 'btn-mode active' : 'btn-mode';
      });
      const names = ['HOUSEHOLD MODE', 'HOTEL MODE', 'INDUSTRIAL MODE'];
      document.getElementById('modePill').innerText = names[modeIdx] || 'CUSTOM';
    }

    function saveThresholds() {
      const g = document.getElementById('inGasAlarm').value;
      const t = document.getElementById('inTempAlarm').value;
      const d = document.getElementById('inDistLimit').value;
      fetch(`/api/setThresholds?gas=${g}&temp=${t}&dist=${d}`)
        .then(r => r.json())
        .then(data => {
          logMessage('ACT', `Thresholds updated: Gas=${g}, Temp=${t}°C, Dist=${d}cm`);
          fetchTelemetry();
        })
        .catch(e => console.error(e));
    }

    // Live Telemetry Poller
    function fetchTelemetry() {
      fetch('/api/data')
        .then(r => r.json())
        .then(d => {
          // Uptime
          const sec = d.uptime;
          const h = String(Math.floor(sec / 3600)).padStart(2, '0');
          const m = String(Math.floor((sec % 3600) / 60)).padStart(2, '0');
          const s = String(sec % 60).padStart(2, '0');
          document.getElementById('uptimeDisplay').innerText = `Uptime: ${h}:${m}:${s}`;

          // Mode
          updateModeUI(d.mode);

          // Gas
          document.getElementById('gasRaw').innerText = d.gasRaw;
          document.getElementById('gasPpm').innerText = d.gasPpm;
          document.getElementById('gasThreshVal').innerText = d.gasAlarmThresh;
          const gasPercent = Math.min(100, Math.round((d.gasRaw / 4095) * 100));
          const gasBar = document.getElementById('gasBar');
          gasBar.style.width = gasPercent + '%';
          gasBar.style.background = (d.gasRaw >= d.gasAlarmThresh) ? 'var(--red)' : (d.gasRaw >= d.gasWarnThresh ? 'var(--yellow)' : 'var(--green)');

          // Temperature
          document.getElementById('tempVal').innerText = d.temp.toFixed(1);
          document.getElementById('humidityVal').innerText = Math.round(d.humidity);
          document.getElementById('tempThreshVal').innerText = d.tempAlarmThresh.toFixed(1);
          const tempPercent = Math.min(100, Math.max(0, Math.round((d.temp / 80) * 100)));
          const tempBar = document.getElementById('tempBar');
          tempBar.style.width = tempPercent + '%';
          tempBar.style.background = (d.temp >= d.tempAlarmThresh) ? 'var(--red)' : (d.temp >= d.tempWarnThresh ? 'var(--yellow)' : 'var(--green)');

          // Ultrasonic Distance & Clearance
          document.getElementById('distVal').innerText = d.distance;
          document.getElementById('distThreshVal').innerText = d.distThresh;
          const distBar = document.getElementById('distBar');
          const distPercent = Math.min(100, Math.round((d.distance / 150) * 100));
          distBar.style.width = distPercent + '%';
          if (d.distance <= d.distThresh && d.distance > 0) {
            distBar.style.background = 'var(--red)';
            document.getElementById('distStatus').innerText = 'BREACHED!';
            document.getElementById('distStatus').style.color = 'var(--red)';
          } else {
            distBar.style.background = 'var(--green)';
            document.getElementById('distStatus').innerText = 'SAFE';
            document.getElementById('distStatus').style.color = 'var(--green)';
          }

          // Relay State
          const relayText = document.getElementById('relayStateText');
          const relayBar = document.getElementById('relayBar');
          if (d.relayActive) {
            relayText.innerText = 'TRIPPED (ACTIVE)';
            relayText.style.color = 'var(--red)';
            relayBar.style.width = '100%';
            relayBar.style.background = 'var(--red)';
            document.getElementById('relayTrigger').innerText = d.relayReason || 'Hazard Tripped';
          } else {
            relayText.innerText = 'ARMED (IDLE)';
            relayText.style.color = 'var(--green)';
            relayBar.style.width = '20%';
            relayBar.style.background = 'var(--green)';
            document.getElementById('relayTrigger').innerText = 'Standby Safe';
          }

          // Threat Banner & Status Badge
          const banner = document.getElementById('threatBanner');
          const statusBadge = document.getElementById('statusBadge');
          const statusText = document.getElementById('statusText');
          const bannerTitle = document.getElementById('bannerTitle');
          const bannerDesc = document.getElementById('bannerDesc');

          if (d.hazardLevel === 2) { // CRITICAL ALARM
            banner.className = 'threat-banner danger';
            statusBadge.className = 'badge badge-danger';
            statusText.innerText = 'CRITICAL EMERGENCY';
            bannerTitle.innerText = '🚨 EMERGENCY HAZARD ACTIVE!';
            bannerDesc.innerText = d.activeHazards || 'Immediate action required! Safety actuator triggered.';

            // Play siren if not already
            if (!isSirenPlaying && d.relayActive) {
              startWebSiren();
            }
          } else if (d.hazardLevel === 1) { // WARNING
            banner.className = 'threat-banner warning';
            statusBadge.className = 'badge badge-warning';
            statusText.innerText = 'CAUTION WARNING';
            bannerTitle.innerText = '⚠️ Elevated Sensor Reading';
            bannerDesc.innerText = d.activeHazards || 'Pre-alert condition detected. Monitor zone.';
          } else { // NORMAL
            banner.className = 'threat-banner normal';
            statusBadge.className = 'badge badge-normal';
            statusText.innerText = 'SYSTEM ARMED';
            bannerTitle.innerText = 'All Monitored Parameters Normal';
            bannerDesc.innerText = 'Atmospheric combustible gas, ambient heat, and perimeter clearance within safety margins.';
            if (isSirenPlaying && !d.relayActive) {
              stopWebSiren();
            }
          }

          // Sync input fields if not focused
          if (document.activeElement.id !== 'inGasAlarm') document.getElementById('inGasAlarm').value = d.gasAlarmThresh;
          if (document.activeElement.id !== 'inTempAlarm') document.getElementById('inTempAlarm').value = d.tempAlarmThresh;
          if (document.activeElement.id !== 'inDistLimit') document.getElementById('inDistLimit').value = d.distThresh;

          // Detect state transitions for logging
          if (lastHazardLevel !== -1 && lastHazardLevel !== d.hazardLevel) {
            if (d.hazardLevel === 2) logMessage('ALERT', 'CRITICAL EMERGENCY: ' + d.activeHazards);
            else if (d.hazardLevel === 1) logMessage('WARN', 'WARNING: ' + d.activeHazards);
            else logMessage('OK', 'All hazards resolved. Conditions safe.');
          }
          lastHazardLevel = d.hazardLevel;

          if (lastRelayState !== -1 && lastRelayState !== d.relayActive) {
            if (d.relayActive) logMessage('ALERT', 'Actuator Relay TRIPPED: ' + (d.relayReason || 'Auto safety shutoff'));
            else logMessage('OK', 'Actuator Relay Returned to IDLE/Standby.');
          }
          lastRelayState = d.relayActive;
        })
        .catch(err => {
          console.warn('Telemetry poll error:', err);
        });
    }

    // Auto poll every 800ms
    setInterval(fetchTelemetry, 800);
    fetchTelemetry();
  </script>
</body>
</html>
)rawliteral";

#endif // WEBPAGE_H
