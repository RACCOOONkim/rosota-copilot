(() => {
	// Socket.IO 연결 설정 (재연결 옵션 포함)
	const socket = io({
		path: "/socket.io",
		transports: ["websocket", "polling"],
		reconnection: true,
		reconnectionDelay: 1000,
		reconnectionDelayMax: 5000,
		reconnectionAttempts: Infinity,
		timeout: 20000,
		forceNew: false,
		autoConnect: true,
	});

	// DOM Elements
	const statusDot = document.getElementById("status-dot");
	const statusText = document.getElementById("status-text");
	const topStatusDot = document.getElementById("top-status-dot");
	const topStatusText = document.getElementById("top-status-text");
	const topPort = document.getElementById("top-port");
	const topBaudrate = document.getElementById("top-baudrate");
	const topConnectionInfo = document.getElementById("top-connection-info");
	const topBaudrateInfo = document.getElementById("top-baudrate-info");
	const connectBtn = document.getElementById("connect-btn");
	const disconnectBtn = document.getElementById("disconnect-btn");
	const homeBtn = document.getElementById("home-btn");
	const zeroBtn = document.getElementById("zero-btn");
	const calibrateBtn = document.getElementById("calibrate-btn");
	const estopBtn = document.getElementById("estop-btn");
	const logsEl = document.getElementById("logs");
	const controlModeEl = document.getElementById("control-mode");
	const modeTextEl = document.getElementById("mode-text");
	const speedValueEl = document.getElementById("speed-value");
	const keyboardHintsEl = document.getElementById("keyboard-hints");
	const connTypeEl = document.getElementById("conn-type");
	const portGroup = document.getElementById("port-group");
	const portSelectEl = document.getElementById("conn-port-select");
	const refreshPortsBtn = document.getElementById("refresh-ports-btn");
	const baudrateGroup = document.getElementById("baudrate-group");
	const hostGroup = document.getElementById("host-group");

	// State
	let isConnected = false;
	let currentMode = "joint";
	let speedMultiplier = 1.0;
	let controlRunning = false;
	
	// 키보드 텔레옵 상태
	const pressedKeys = new Set();
	const keyPressTimes = new Map(); // 키를 누른 시간
	let controlLoopInterval = null;
	const CONTROL_LOOP_INTERVAL = 50; // 50ms마다 명령 전송 (20Hz)

	// 번역 데이터 (먼저 선언되어야 함)
	const translations = {
		ko: {
			"menu.tutorial": "튜토리얼",
			"menu.connection": "연결",
			"menu.motor_setup": "모터 설정",
			"menu.calibration": "캘리브레이션",
			"menu.control": "제어",
			"menu.status": "상태",
			"status.disconnected": "연결 안됨",
			"status.connected": "연결됨",
			"status.stopped": "중지됨",
			"status.running": "실행 중",
			"section.tutorial.title": "튜토리얼",
			"section.tutorial.description": "SO Arm 100/101 Quick Start Guide",
			"section.connection.title": "연결",
			"section.connection.description": "로봇 연결 설정 및 관리",
			"section.calibration.title": "캘리브레이션",
			"section.calibration.description": "로봇 캘리브레이션 및 초기 설정",
			"section.control.title": "제어",
			"section.control.description": "키보드로 로봇 제어",
			"section.status.title": "로봇 상태",
			"section.status.description": "실시간 로봇 상태 모니터링",
			"section.motor_setup.title": "모터 설정",
			"section.motor_setup.description": "SO-100 로봇 모터 ID 및 baudrate 설정",
			"card.motor_setup_wizard": "모터 설정 마법사",
			"motor_setup.step1.title": "1단계: 로봇 타입 선택",
			"motor_setup.step1.description": "Follower 또는 Leader 팔을 선택하세요.",
			"motor_setup.step2.title": "2단계: MotorsBus 포트 찾기",
			"motor_setup.step2.description": "MotorsBus에서 USB 케이블을 분리하고 아래 버튼을 클릭하세요.",
			"motor_setup.step3.title": "3단계: 모터 설정",
			"motor_setup.step3.description": "모터를 하나씩 설정하세요. 한 번에 하나의 모터만 연결하세요. 리스트에서 모터를 클릭하여 선택할 수 있습니다.",
			"motor_setup.follower": "Follower 팔",
			"motor_setup.leader": "Leader 팔",
			"motor_setup.find_port": "포트 찾기",
			"motor_setup.port_found": "포트 찾음:",
			"motor_setup.reconnect_cable": "이제 USB 케이블을 다시 연결하세요.",
			"motor_setup.current_motor": "현재 모터:",
			"motor_setup.connect_single_motor": "컨트롤러 보드에 이 모터만 연결되어 있는지 확인하세요.",
			"motor_setup.configure_motor": "모터 설정",
			"motor_setup.check_id": "ID 확인",
			"motor_setup.reset_motor": "모터 ID 초기화",
			"motor_setup.reset_motor_hint": "모터가 이미 설정되어 있다면 '모터 ID 초기화'를 사용하여 ID 1로 리셋한 후 다시 설정하세요.",
			"motor_setup.skip": "건너뛰기",
			"motor_setup.progress": "진행률",
			"motor_setup.reset": "초기화",
			"label.robot_status": "로봇 상태:",
			"label.port": "포트:",
			"label.baudrate": "보드레이트:",
			"label.connection_type": "연결 타입",
			"label.host": "호스트",
			"label.progress": "진행률",
			"label.status": "상태: ",
			"label.current_mode": "현재 제어 모드:",
			"label.speed": "속도:",
			"card.connection_settings": "연결 설정",
			"card.calibration_wizard": "📋 캘리브레이션 마법사",
			"card.quick_actions": "빠른 작업",
			"card.control_mode": "제어 모드",
			"card.keyboard_control": "키보드 제어",
			"card.joint_positions": "조인트 위치",
			"card.system_logs": "📋 시스템 로그",
			"option.serial_usb": "Serial (USB)",
			"option.tcp_ip": "TCP/IP",
			"option.auto_detect": "자동 감지",
			"btn.connect": "연결",
			"btn.disconnect": "연결 해제",
			"btn.refresh": "🔄",
			"btn.start_calibration": "▶ 캘리브레이션 시작",
			"btn.next_step": "다음 단계 →",
			"btn.cancel": "취소",
			"btn.home_position": "홈 포지션",
			"btn.zero_joints": "조인트 제로",
			"btn.run_calibration": "캘리브레이션 실행",
			"btn.open_wizard": "📋 캘리브레이션 마법사 열기",
			"btn.start_control": "▶ 제어 시작",
			"btn.stop_control": "⏹ 제어 중지",
			"btn.emergency_stop": "긴급 정지",
			"btn.clear": "지우기",
			"btn.auto": "자동",
			"tip.auto_detect": "💡 USB 연결 시 자동으로 로봇을 감지하여 연결합니다.",
			"tip.quick_calibration": "빠른 캘리브레이션 작업을 수행합니다.",
			"tip.keyboard_control": "브라우저에 포커스를 두고 키보드로 로봇을 제어하세요.",
			"wizard.ready": "캘리브레이션을 시작할 준비가 되었습니다. 로봇이 연결되어 있고 전원이 켜져 있는지 확인하세요.",
			"mode.joint": "조인트",
			"mode.cartesian": "직교좌표",
			"mode.gripper": "그리퍼",
			"label.mode": "모드",
			"hint.joint1": "조인트 1 ±",
			"hint.joint2": "조인트 2 ±",
			"hint.joint3": "조인트 3 ±",
			"hint.joint4": "조인트 4 ±",
			"hint.joint5": "조인트 5 ±",
			"hint.joint6": "조인트 6 ±",
			"hint.mode_switch": "모드 전환",
			"hint.speed": "속도 ±",
			"hint.estop": "긴급 정지",
			"hint.x": "X ±",
			"hint.y": "Y ±",
			"hint.z": "Z ±",
			"hint.roll": "Roll ±",
			"hint.pitch": "Pitch ±",
			"hint.yaw": "Yaw ±",
			"hint.toggle_gripper": "그리퍼 토글",
		},
		en: {
			"menu.tutorial": "Tutorial",
			"menu.connection": "Connection",
			"menu.motor_setup": "Motor Setup",
			"menu.calibration": "Calibration",
			"menu.control": "Control",
			"menu.status": "Status",
			"status.disconnected": "Disconnected",
			"status.connected": "Connected",
			"status.stopped": "Stopped",
			"status.running": "Running",
			"section.tutorial.title": "Tutorial",
			"section.tutorial.description": "SO Arm 100/101 Quick Start Guide",
			"section.connection.title": "Connection",
			"section.connection.description": "Robot connection settings and management",
			"section.calibration.title": "Calibration",
			"section.calibration.description": "Robot calibration and initial setup",
			"section.control.title": "Control",
			"section.control.description": "Control robot with keyboard",
			"section.status.title": "Robot Status",
			"section.status.description": "Real-time robot status monitoring",
			"section.motor_setup.title": "Motor Setup",
			"section.motor_setup.description": "Configure motor IDs and baudrate for SO-100 robot",
			"card.motor_setup_wizard": "Motor Setup Wizard",
			"motor_setup.step1.title": "Step 1: Select Robot Type",
			"motor_setup.step1.description": "Choose whether you're configuring a follower or leader arm.",
			"motor_setup.step2.title": "Step 2: Find MotorsBus Port",
			"motor_setup.step2.description": "Disconnect the USB cable from your MotorsBus and click the button below.",
			"motor_setup.step3.title": "Step 3: Configure Motors",
			"motor_setup.step3.description": "Configure each motor one by one. Connect only one motor at a time. Click on any motor in the list to select it.",
			"motor_setup.follower": "Follower Arm",
			"motor_setup.leader": "Leader Arm",
			"motor_setup.find_port": "Find Port",
			"motor_setup.port_found": "Port Found:",
			"motor_setup.reconnect_cable": "Please reconnect the USB cable now.",
			"motor_setup.current_motor": "Current Motor:",
			"motor_setup.connect_single_motor": "Make sure only this motor is connected to the controller board.",
			"motor_setup.configure_motor": "Configure Motor",
			"motor_setup.check_id": "Check Motor ID",
			"motor_setup.reset_motor": "Reset Motor ID",
			"motor_setup.reset_motor_hint": "If a motor is already configured, use 'Reset Motor ID' to reset it to ID 1, then configure it again.",
			"motor_setup.skip": "Skip",
			"motor_setup.progress": "Progress",
			"motor_setup.reset": "Reset",
			"label.robot_status": "Robot Status:",
			"label.port": "Port:",
			"label.baudrate": "Baudrate:",
			"label.connection_type": "Connection Type",
			"label.host": "Host",
			"label.progress": "Progress",
			"label.status": "Status: ",
			"label.current_mode": "Current control mode:",
			"label.speed": "Speed:",
			"card.connection_settings": "Connection Settings",
			"card.calibration_wizard": "📋 Calibration Wizard",
			"card.quick_actions": "Quick Actions",
			"card.control_mode": "Control Mode",
			"card.keyboard_control": "Keyboard Control",
			"card.joint_positions": "Joint Positions",
			"card.system_logs": "📋 System Logs",
			"option.serial_usb": "Serial (USB)",
			"option.tcp_ip": "TCP/IP",
			"option.auto_detect": "Auto-detect",
			"btn.connect": "Connect",
			"btn.disconnect": "Disconnect",
			"btn.refresh": "🔄",
			"btn.start_calibration": "▶ Start Calibration",
			"btn.next_step": "Next Step →",
			"btn.cancel": "Cancel",
			"btn.home_position": "Home Position",
			"btn.zero_joints": "Zero Joints",
			"btn.run_calibration": "Run Calibration",
			"btn.open_wizard": "📋 Open Calibration Wizard",
			"btn.start_control": "▶ Start Control",
			"btn.stop_control": "⏹ Stop Control",
			"btn.emergency_stop": "EMERGENCY STOP",
			"btn.clear": "Clear",
			"btn.auto": "Auto",
			"tip.auto_detect": "💡 Automatically detects and connects to the robot when USB is connected.",
			"tip.quick_calibration": "Perform quick calibration tasks.",
			"tip.keyboard_control": "Focus on the browser and control the robot with the keyboard.",
			"wizard.ready": "Ready to start calibration. Make sure the robot is connected and powered on.",
			"mode.joint": "Joint",
			"mode.cartesian": "Cartesian",
			"mode.gripper": "Gripper",
			"label.mode": "Mode",
			"hint.joint1": "Joint 1 ±",
			"hint.joint2": "Joint 2 ±",
			"hint.joint3": "Joint 3 ±",
			"hint.joint4": "Joint 4 ±",
			"hint.joint5": "Joint 5 ±",
			"hint.joint6": "Joint 6 ±",
			"hint.mode_switch": "Mode Switch",
			"hint.speed": "Speed ±",
			"hint.estop": "E-Stop",
			"hint.x": "X ±",
			"hint.y": "Y ±",
			"hint.z": "Z ±",
			"hint.roll": "Roll ±",
			"hint.pitch": "Pitch ±",
			"hint.yaw": "Yaw ±",
			"hint.toggle_gripper": "Toggle Gripper",
		}
	};

	// Keyboard hints mapping (번역 키 사용)
	function getKeyboardHints(mode) {
		const lang = getInitialLanguage();
		const t = (key) => translations[lang]?.[key] || key;
		
		const hints = {
			joint: [
				{ key: "I/K", actionKey: "hint.joint1" },
				{ key: "J/L", actionKey: "hint.joint2" },
				{ key: "U/O", actionKey: "hint.joint3" },
				{ key: "7/9", actionKey: "hint.joint4" },
				{ key: "8/0", actionKey: "hint.joint5" },
				{ key: "Y/H", actionKey: "hint.joint6" },
				{ key: "M", actionKey: "hint.mode_switch" },
				{ key: "+/-", actionKey: "hint.speed" },
				{ key: "Space", actionKey: "hint.estop" },
			],
			cartesian: [
				{ key: "W/S", actionKey: "hint.x" },
				{ key: "A/D", actionKey: "hint.y" },
				{ key: "Q/E", actionKey: "hint.z" },
				{ key: "R/F", actionKey: "hint.roll" },
				{ key: "T/G", actionKey: "hint.pitch" },
				{ key: "Z/X", actionKey: "hint.yaw" },
				{ key: "M", actionKey: "hint.mode_switch" },
				{ key: "+/-", actionKey: "hint.speed" },
				{ key: "Space", actionKey: "hint.estop" },
			],
			gripper: [
				{ key: "C", actionKey: "hint.toggle_gripper" },
				{ key: "M", actionKey: "hint.mode_switch" },
				{ key: "Space", actionKey: "hint.estop" },
			],
		};
		
		return (hints[mode] || hints.joint).map(h => ({
			key: h.key,
			action: t(h.actionKey)
		}));
	}

	// Logging
	let autoScrollEnabled = true;
	
	function log(message, type = "info") {
		if (!logsEl) return;
		const entry = document.createElement("div");
		entry.className = `log-entry ${type}`;
		const timestamp = new Date().toLocaleTimeString();
		entry.textContent = `[${timestamp}] ${message}`;
		logsEl.prepend(entry);
		
		// 자동 스크롤 (최신 로그로) - 활성화된 경우에만
		if (autoScrollEnabled) {
			logsEl.scrollTop = 0;
		}
		
		// 최대 200개 로그 유지
		if (logsEl.children.length > 200) {
			logsEl.removeChild(logsEl.lastChild);
		}
		
		// 콘솔에도 출력 (디버깅)
		console.log(`[${type.toUpperCase()}] ${message}`);
	}
	
	// 로그 패널 컨트롤
	const clearLogsBtn = document.getElementById("clear-logs-btn");
	const toggleLogsBtn = document.getElementById("toggle-logs-btn");
	
	clearLogsBtn?.addEventListener("click", () => {
		if (logsEl) {
			logsEl.innerHTML = "";
			log("Logs cleared", "info");
		}
	});
	
	toggleLogsBtn?.addEventListener("click", () => {
		autoScrollEnabled = !autoScrollEnabled;
		toggleLogsBtn.textContent = autoScrollEnabled ? "Auto" : "Manual";
		toggleLogsBtn.style.background = autoScrollEnabled 
			? "var(--bg-secondary)" 
			: "var(--accent)";
		toggleLogsBtn.style.color = autoScrollEnabled 
			? "var(--text-secondary)" 
			: "white";
		log(`Auto-scroll ${autoScrollEnabled ? "enabled" : "disabled"}`, "info");
	});

	// Update status
	function updateStatus(status, connected = false, connectionInfo = null) {
		isConnected = connected;
		// 상태 번역
		const lang = getInitialLanguage();
		let translatedStatus = status;
		if (status === "Connected" || status === "연결됨") {
			translatedStatus = translations[lang]?.["status.connected"] || status;
		} else if (status === "Disconnected" || status === "연결 안됨") {
			translatedStatus = translations[lang]?.["status.disconnected"] || status;
		}
		statusText.textContent = translatedStatus;
		statusDot.className = "status-dot" + (connected ? " connected" : "");
		
		// Update top status bar
		if (topStatusText) {
			topStatusText.textContent = translatedStatus;
			topStatusText.className = "top-status-value " + (connected ? "connected" : "disconnected");
		}
		if (topStatusDot) {
			topStatusDot.className = "status-dot" + (connected ? " connected" : "");
		}
		
		// Update connection info
		if (connectionInfo) {
			if (topPort && connectionInfo.port) {
				topPort.textContent = connectionInfo.port;
				topConnectionInfo.style.display = "flex";
			}
			if (topBaudrate && connectionInfo.baudrate) {
				topBaudrate.textContent = connectionInfo.baudrate;
				topBaudrateInfo.style.display = "flex";
			}
		} else {
			if (topConnectionInfo) topConnectionInfo.style.display = "none";
			if (topBaudrateInfo) topBaudrateInfo.style.display = "none";
		}
		
		// Enable/disable buttons
		connectBtn.disabled = connected;
		disconnectBtn.disabled = !connected;
		homeBtn.disabled = !connected;
		zeroBtn.disabled = !connected;
		calibrateBtn.disabled = !connected;
	}

	// Update keyboard hints
	function updateKeyboardHints(mode) {
		if (!keyboardHintsEl) return;
		keyboardHintsEl.innerHTML = "";
		const hints = getKeyboardHints(mode);
		hints.forEach(({ key, action }) => {
			const div = document.createElement("div");
			div.className = "key-hint";
			div.innerHTML = `
				<span>${action}</span>
				<span class="key">${key}</span>
			`;
			keyboardHintsEl.appendChild(div);
		});
	}

	// Update joint display
	function updateJointDisplay(joints) {
		for (let i = 0; i < 6; i++) {
			const el = document.getElementById(`joint-${i}`);
			if (el && joints[i] !== undefined) {
				el.textContent = `${joints[i].toFixed(1)}°`;
			}
		}
	}

	// Load available ports
	async function loadPorts() {
		if (!portSelectEl) return;
		try {
			const res = await fetch("/api/ports");
			const json = await res.json();
			if (json.ok && json.ports) {
				const lang = getInitialLanguage();
				const autoDetectText = translations[lang]?.["option.auto_detect"] || "Auto-detect";
				portSelectEl.innerHTML = `<option value="" data-i18n="option.auto_detect">${autoDetectText}</option>`;
				json.ports.forEach(portInfo => {
					const option = document.createElement("option");
					option.value = portInfo.port;
					option.textContent = `${portInfo.port}${portInfo.description ? ` (${portInfo.description})` : ""}`;
					portSelectEl.appendChild(option);
				});
				// 번역 적용
				const autoOption = portSelectEl.querySelector('option[data-i18n="option.auto_detect"]');
				if (autoOption) {
					autoOption.textContent = translations[lang]?.["option.auto_detect"] || "Auto-detect";
				}
			}
		} catch (error) {
			log(`Failed to load ports: ${error.message}`, "error");
		}
	}

	// Refresh ports button
	refreshPortsBtn?.addEventListener("click", async () => {
		await loadPorts();
		log("Ports refreshed", "info");
	});

	// Connection type change
	connTypeEl?.addEventListener("change", (e) => {
		const isSerial = e.target.value === "serial";
		portGroup.style.display = isSerial ? "flex" : "none";
		baudrateGroup.style.display = isSerial ? "flex" : "none";
		hostGroup.style.display = isSerial ? "none" : "flex";
		if (isSerial) {
			loadPorts();
		}
	});

	// Connect button
	connectBtn?.addEventListener("click", async () => {
		const connType = connTypeEl.value;
		const selectedPort = portSelectEl?.value || "";
		const payload = {
			port: connType === "serial" ? (selectedPort || null) : null,
			host: connType === "tcp" ? document.getElementById("conn-host").value : null,
			baudrate: connType === "serial" ? parseInt(document.getElementById("conn-baudrate").value) : null,
		};

		try {
			const res = await fetch("/api/connect", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(payload),
			});
			const json = await res.json();
			if (json.ok && json.details) {
				const d = json.details;
				updateStatus("Connected", true, {
					port: d.port || d.host || "-",
					baudrate: d.baudrate || "-"
				});
				log(`Robot connected: port=${d.port || d.host || "-"}, baud=${d.baudrate || "-"}`, "success");
			} else {
				updateStatus("Connection Failed", false);
				log(`Connection failed: ${json.error || "Unknown error"}`, "error");
				if (json.ports && Array.isArray(json.ports)) {
					log(`Available ports: ${json.ports.map(p => p.port).join(", ") || "(none)"}`, "warning");
				}
			}
		} catch (error) {
			updateStatus("Connection Error", false);
			log(`Connection error: ${error.message}`, "error");
		}
	});

	// Disconnect button
	disconnectBtn?.addEventListener("click", async () => {
		try {
			const res = await fetch("/api/disconnect", { method: "POST" });
			const json = await res.json();
			if (json.ok) {
				updateStatus("Disconnected", false, null);
				log("Robot disconnected", "info");
			}
		} catch (error) {
			log(`Disconnect error: ${error.message}`, "error");
		}
	});

	// 로딩 상태 관리
	function setButtonLoading(button, loading) {
		if (!button) return;
		if (loading) {
			button.disabled = true;
			button.dataset.originalText = button.textContent;
			button.textContent = "⏳ Loading...";
		} else {
			button.disabled = false;
			if (button.dataset.originalText) {
				button.textContent = button.dataset.originalText;
				delete button.dataset.originalText;
			}
		}
	}

	// Home button
	homeBtn?.addEventListener("click", async () => {
		setButtonLoading(homeBtn, true);
		try {
			log("Starting home movement...", "info");
			const res = await fetch("/api/calibration/home", { method: "POST" });
			const json = await res.json();
			if (json.ok) {
				log(json.message || "Home movement completed", "success");
			} else {
				log(`Home failed: ${json.detail || json.error}`, "error");
			}
		} catch (error) {
			log(`Home error: ${error.message}`, "error");
		} finally {
			setButtonLoading(homeBtn, false);
		}
	});

	// Zero button
	zeroBtn?.addEventListener("click", async () => {
		setButtonLoading(zeroBtn, true);
		try {
			log("Starting zero joints...", "info");
			const res = await fetch("/api/calibration/zero", { method: "POST" });
			const json = await res.json();
			if (json.ok) {
				log(json.message || "Joints zeroed successfully", "success");
				if (json.offsets) {
					log(`Offsets: ${json.offsets.map(o => o.toFixed(4)).join(", ")}`, "info");
				}
			} else {
				log(`Zero failed: ${json.detail || json.error}`, "error");
			}
		} catch (error) {
			log(`Zero error: ${error.message}`, "error");
		} finally {
			setButtonLoading(zeroBtn, false);
		}
	});

	// Calibrate button
	calibrateBtn?.addEventListener("click", async () => {
		setButtonLoading(calibrateBtn, true);
		try {
			log("Starting full calibration...", "info");
			const res = await fetch("/api/calibration/run", { method: "POST" });
			const json = await res.json();
			if (json.ok) {
				log(json.message || "Calibration completed", "success");
				if (json.file) {
					log(`Calibration saved to: ${json.file}`, "info");
				}
				if (json.offsets) {
					log(`Final offsets: ${json.offsets.map(o => o.toFixed(4)).join(", ")}`, "info");
				}
			} else {
				log(`Calibration failed: ${json.detail || json.error}`, "error");
			}
		} catch (error) {
			log(`Calibration error: ${error.message}`, "error");
		} finally {
			setButtonLoading(calibrateBtn, false);
		}
	});

	// Start/Stop Control buttons
	const startControlBtn = document.getElementById("start-control-btn");
	const stopControlBtn = document.getElementById("stop-control-btn");
	const controlStatusText = document.getElementById("control-status-text");
	
	startControlBtn?.addEventListener("click", async () => {
		if (!isConnected) {
			log("Cannot start control: robot not connected", "error");
			return;
		}
		
		setButtonLoading(startControlBtn, true);
		try {
			const res = await fetch("/api/control/start", { method: "POST" });
			const json = await res.json();
			if (json.ok) {
				controlRunning = true;
				startControlBtn.disabled = true;
				stopControlBtn.disabled = false;
				const lang = getInitialLanguage();
				controlStatusText.textContent = translations[lang]?.["status.running"] || "Running";
				controlStatusText.style.color = "var(--success)";
				log("Keyboard control started", "success");
				startControlLoop(); // 제어 루프 시작
			} else {
				log(`Failed to start control: ${json.detail || json.message}`, "error");
			}
		} catch (error) {
			log(`Start control error: ${error.message}`, "error");
		} finally {
			setButtonLoading(startControlBtn, false);
		}
	});
	
	stopControlBtn?.addEventListener("click", async () => {
		setButtonLoading(stopControlBtn, true);
		try {
			const res = await fetch("/api/control/stop", { method: "POST" });
			const json = await res.json();
			if (json.ok) {
				controlRunning = false;
				startControlBtn.disabled = false;
				stopControlBtn.disabled = true;
				const lang = getInitialLanguage();
				controlStatusText.textContent = translations[lang]?.["status.stopped"] || "Stopped";
				controlStatusText.style.color = "var(--text-secondary)";
				log("Keyboard control stopped", "info");
				stopControlLoop(); // 제어 루프 중지
			} else {
				log(`Failed to stop control: ${json.detail || json.message}`, "error");
			}
		} catch (error) {
			log(`Stop control error: ${error.message}`, "error");
		} finally {
			setButtonLoading(stopControlBtn, false);
		}
	});

	// E-Stop button
	estopBtn?.addEventListener("click", () => {
		socket.emit("control:key", { key: " ", event_type: "keydown" });
		log("EMERGENCY STOP activated", "error");
	});

	// 키보드 힌트 업데이트 (시각적 피드백)
	function updateKeyVisualFeedback(key, pressed) {
		const keyHints = document.querySelectorAll(".key-hint");
		keyHints.forEach((hint) => {
			const keyEl = hint.querySelector(".key");
			if (keyEl) {
				// 키 텍스트에서 개별 키 추출 (예: "I/K" -> ["i", "k"])
				const keyText = keyEl.textContent.toLowerCase();
				const keys = keyText.split("/").map(k => k.trim());
				
				// 키가 매칭되는지 확인
				let matches = false;
				if (keys.includes(key.toLowerCase())) {
					matches = true;
				} else if (key === "+" && (keyText.includes("+") || keyText.includes("="))) {
					matches = true;
				} else if (key === "-" && keyText.includes("-")) {
					matches = true;
				} else if (key === " " && keyText.includes("space")) {
					matches = true;
				}
				
				if (matches) {
					if (pressed) {
						hint.style.background = "var(--accent)";
						hint.style.color = "white";
						keyEl.style.background = "rgba(255, 255, 255, 0.3)";
						keyEl.style.borderColor = "rgba(255, 255, 255, 0.5)";
						hint.style.transform = "scale(1.05)";
						hint.style.transition = "all 0.1s ease";
					} else {
						hint.style.background = "var(--bg-secondary)";
						hint.style.color = "var(--text-primary)";
						keyEl.style.background = "var(--bg-primary)";
						keyEl.style.borderColor = "var(--border)";
						hint.style.transform = "scale(1)";
					}
				}
			}
		});
	}

	// 키보드 텔레옵 제어 루프
	function startControlLoop() {
		if (controlLoopInterval) {
			console.log("[Frontend] Control loop already running");
			return;
		}
		
		console.log(`[Frontend] Starting control loop. controlRunning=${controlRunning}, isConnected=${isConnected}, socket.connected=${socket.connected}`);
		
		controlLoopInterval = setInterval(() => {
			if (!controlRunning || !isConnected) {
				if (!controlRunning) console.log("[Frontend] Control loop: controlRunning is false");
				if (!isConnected) console.log("[Frontend] Control loop: isConnected is false");
				return;
			}
			
			if (!socket.connected) {
				console.error("[Frontend] Control loop: Socket.IO not connected!");
				return;
			}
			
			// 누른 키가 있으면 명령 전송
			if (pressedKeys.size > 0) {
				// 각 키에 대해 명령 전송
				// 디바운스: 같은 키를 너무 빠르게 보내지 않도록
				const now = Date.now();
				pressedKeys.forEach((key) => {
					const lastSent = keyPressTimes.get(key) || 0;
					// 제어 루프에서는 40ms마다만 보냄 (디바운스 30ms보다 크게)
					if (now - lastSent >= 40) {
						const payload = {
							key: key,
							event_type: "keydown",
							timestamp: now,
						};
						console.log(`[Frontend] Control loop: Emitting key '${key}' (lastSent: ${lastSent}, now: ${now}, diff: ${now - lastSent}ms)`);
						socket.emit("control:key", payload);
						keyPressTimes.set(key, now);
					} else {
						console.log(`[Frontend] Control loop: Key '${key}' debounced (lastSent: ${lastSent}, now: ${now}, diff: ${now - lastSent}ms)`);
					}
				});
			}
		}, CONTROL_LOOP_INTERVAL);
		
		log("Control loop started", "info");
		console.log("[Frontend] Control loop started successfully");
	}

	function stopControlLoop() {
		if (controlLoopInterval) {
			clearInterval(controlLoopInterval);
			controlLoopInterval = null;
			log("Control loop stopped", "info");
		}
		// 모든 키 시각적 피드백 해제
		pressedKeys.forEach((key) => {
			updateKeyVisualFeedback(key, false);
		});
		pressedKeys.clear();
		keyPressTimes.clear();
	}

	// 키 입력 필터링: 무시할 키 목록
	const IGNORED_KEYS = new Set([
		"meta", "control", "alt", "shift", "capslock", "tab", "escape",
		"f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
		"insert", "delete", "home", "end", "pageup", "pagedown",
		"arrowup", "arrowdown", "arrowleft", "arrowright",
		"backspace", "enter", "numlock", "scrolllock",
		// 한글 자모 (한글 입력 모드일 때)
		"ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
		"ㅏ", "ㅑ", "ㅓ", "ㅕ", "ㅗ", "ㅛ", "ㅜ", "ㅠ", "ㅡ", "ㅣ",
		// 기타 특수 문자
		"a", // 'a' 키는 매핑에 없으므로 무시
	]);

	// Keyboard events
	window.addEventListener("keydown", (e) => {
		// 한글 입력 조합 중이면 무시
		if (e.isComposing) {
			return;
		}

		// Prevent default for control keys
		if ([" ", "m", "+", "-", "="].includes(e.key.toLowerCase())) {
			e.preventDefault();
		}

		// Normalize key: e.code를 사용하여 물리적 키 감지 (한글 입력 모드에서도 작동)
		let key = null;
		
		// e.code를 사용하여 물리적 키 매핑 (한글 입력 모드에서도 작동)
		const codeToKey = {
			"KeyI": "i", "KeyK": "k", "KeyJ": "j", "KeyL": "l",
			"KeyU": "u", "KeyO": "o", "KeyY": "y", "KeyH": "h",
			"KeyW": "w", "KeyS": "s", "KeyA": "a", "KeyD": "d",
			"KeyQ": "q", "KeyE": "e", "KeyR": "r", "KeyF": "f",
			"KeyT": "t", "KeyG": "g", "KeyZ": "z", "KeyX": "x",
			"KeyC": "c", "KeyM": "m",
			"Digit7": "7", "Digit8": "8", "Digit9": "9", "Digit0": "0",
			"Space": " ",
			"Equal": "+", "Minus": "-",
		};
		
		if (e.code in codeToKey) {
			key = codeToKey[e.code];
		} else {
			// e.code가 매핑에 없으면 e.key 사용 (fallback)
			key = e.key.toLowerCase();
			if (key === " ") key = " ";
			if (e.key === "+" || e.key === "=") key = "+";
			if (e.key === "-" || e.key === "_") key = "-";
		}

		// 무시할 키 필터링 (로그에도 남기지 않음)
		if (IGNORED_KEYS.has(key)) {
			return;
		}

		// 한글 자모나 특수 문자 필터링 (유니코드 범위 체크)
		if (key.length === 1 && /[\u1100-\u11FF\u3130-\u318F\uAC00-\uD7AF]/.test(key)) {
			return; // 한글 자모/음절 무시
		}

		// 디버깅: 유효한 키 입력만 로그
		console.log(`[Frontend] Keydown event: key='${key}', original='${e.key}', controlRunning=${controlRunning}, isConnected=${isConnected}, socket.connected=${socket.connected}`);
		
		// 키 매핑 확인 (디버깅)
		const validKeys = ["i", "k", "j", "l", "u", "o", "7", "9", "8", "0", "y", "h", "m", " ", "+", "-", "c", "w", "s", "a", "d", "q", "e", "r", "f", "t", "g", "z", "x"];
		if (!validKeys.includes(key)) {
			console.warn(`[Frontend] Key '${key}' is not in valid keys list`);
		}

		// Control이 실행 중일 때만 처리
		if (!controlRunning && !["m", " "].includes(key)) {
			return; // 모드 전환과 E-Stop은 항상 허용
		}

		// Socket.IO 연결 확인
		if (!socket.connected) {
			console.error(`[Frontend] Socket.IO not connected! Cannot send key '${key}'`);
			log(`Socket.IO not connected. Cannot send key: ${key.toUpperCase()}`, "error");
			return;
		}

		// 키 상태 추적
		if (!pressedKeys.has(key)) {
			pressedKeys.add(key);
			updateKeyVisualFeedback(key, true);
			
			// 즉시 명령 전송 (첫 키 입력) - 제어 루프를 기다리지 않고 즉시 전송
			const payload = {
				key: key,
				event_type: "keydown",
				timestamp: Date.now(),
			};
			console.log(`[Frontend] Emitting control:key event (immediate):`, payload);
			console.log(`[Frontend] Socket.IO state: connected=${socket.connected}, id=${socket.id}`);
			
			try {
				socket.emit("control:key", payload);
				console.log(`[Frontend] control:key event emitted successfully for key '${key}'`);
			} catch (error) {
				console.error(`[Frontend] Error emitting control:key event:`, error);
			}
			
			// 제어 루프 디바운스를 위해 시간 기록
			keyPressTimes.set(key, Date.now());
			
			log(`Key pressed: ${key.toUpperCase()}`, "info");
		} else {
			console.log(`[Frontend] Key '${key}' already in pressedKeys, will be sent by control loop`);
		}
	});

	window.addEventListener("keyup", (e) => {
		// 한글 입력 조합 중이면 무시
		if (e.isComposing) {
			return;
		}

		// e.code를 사용하여 물리적 키 매핑 (한글 입력 모드에서도 작동)
		const codeToKey = {
			"KeyI": "i", "KeyK": "k", "KeyJ": "j", "KeyL": "l",
			"KeyU": "u", "KeyO": "o", "KeyY": "y", "KeyH": "h",
			"KeyW": "w", "KeyS": "s", "KeyA": "a", "KeyD": "d",
			"KeyQ": "q", "KeyE": "e", "KeyR": "r", "KeyF": "f",
			"KeyT": "t", "KeyG": "g", "KeyZ": "z", "KeyX": "x",
			"KeyC": "c", "KeyM": "m",
			"Digit7": "7", "Digit8": "8", "Digit9": "9", "Digit0": "0",
			"Space": " ",
			"Equal": "+", "Minus": "-",
		};
		
		let key = null;
		if (e.code in codeToKey) {
			key = codeToKey[e.code];
		} else {
			// e.code가 매핑에 없으면 e.key 사용 (fallback)
			key = e.key.toLowerCase();
			if (key === " ") key = " ";
			if (e.key === "+" || e.key === "=") key = "+";
			if (e.key === "-" || e.key === "_") key = "-";
		}

		// 무시할 키 필터링
		if (IGNORED_KEYS.has(key)) {
			return;
		}

		// 한글 자모 필터링
		if (key.length === 1 && /[\u1100-\u11FF\u3130-\u318F\uAC00-\uD7AF]/.test(key)) {
			return;
		}

		// 키 상태 해제
		if (pressedKeys.has(key)) {
			pressedKeys.delete(key);
			keyPressTimes.delete(key);
			updateKeyVisualFeedback(key, false);
			
			socket.emit("control:key", {
				key: key,
				event_type: "keyup",
				timestamp: Date.now(),
			});
			
			// keyup은 로그에 남기지 않음 (너무 많은 로그 방지)
		}
	});

	// Socket.IO events
	socket.on("connect", () => {
		log("WebSocket connected", "success");
		console.log(`[Frontend] Socket.IO connected. Socket ID: ${socket.id}, connected: ${socket.connected}`);
	});

	socket.on("disconnect", (reason) => {
		log(`WebSocket disconnected: ${reason}`, "warning");
		console.log(`[Frontend] Socket.IO disconnected. Reason: ${reason}, connected: ${socket.connected}`);
		if (reason === "io server disconnect") {
			// 서버가 연결을 끊은 경우 수동으로 재연결
			socket.connect();
		}
	});
	
	socket.on("connect_error", (error) => {
		log(`WebSocket connection error: ${error.message || error}`, "error");
		console.error("[Frontend] Socket.IO connection error:", error);
		console.error("[Frontend] Error details:", {
			message: error.message,
			description: error.description,
			context: error.context,
			type: error.type
		});
	});
	
	socket.on("reconnect", (attemptNumber) => {
		log(`WebSocket reconnected (attempt ${attemptNumber})`, "success");
		console.log(`[Frontend] Socket.IO reconnected after ${attemptNumber} attempts`);
	});
	
	socket.on("reconnect_attempt", (attemptNumber) => {
		console.log(`[Frontend] Socket.IO reconnection attempt ${attemptNumber}`);
	});
	
	socket.on("reconnect_error", (error) => {
		console.error(`[Frontend] Socket.IO reconnection error:`, error);
	});
	
	socket.on("reconnect_failed", () => {
		log("WebSocket reconnection failed", "error");
		console.error("[Frontend] Socket.IO reconnection failed");
	});

	socket.on("server:hello", (data) => {
		log(`Server: ${data.message}`, "info");
	});

	socket.on("state:update", (data) => {
		if (data.joint_positions) {
			updateJointDisplay(data.joint_positions);
		}
		if (data.status) {
			const connectionInfo = data.connection ? {
				port: data.connection.port || data.connection.host || "-",
				baudrate: data.connection.baudrate || "-"
			} : null;
			updateStatus(data.status, data.status === "Connected", connectionInfo);
		}
	});

		socket.on("control:response", (data) => {
		if (data.action === "mode_change") {
			currentMode = data.mode;
			const lang = getInitialLanguage();
			const modeNames = {
				joint: translations[lang]?.["mode.joint"] || "Joint",
				cartesian: translations[lang]?.["mode.cartesian"] || "Cartesian",
				gripper: translations[lang]?.["mode.gripper"] || "Gripper"
			};
			const modeName = modeNames[data.mode] || data.mode.charAt(0).toUpperCase() + data.mode.slice(1);
			controlModeEl.textContent = modeName;
			modeTextEl.textContent = `${modeName} ${translations[lang]?.["label.mode"] || "Mode"}`;
			updateKeyboardHints(data.mode);
			log(`Mode changed to: ${data.mode}`, "info");
		} else if (data.action === "speed_change") {
			speedMultiplier = data.multiplier;
			speedValueEl.textContent = `${speedMultiplier.toFixed(1)}x`;
			log(`Speed: ${speedMultiplier.toFixed(1)}x`, "info");
		} else if (data.action === "estop") {
			log(`E-Stop: ${data.active ? "ACTIVE" : "Released"}`, data.active ? "error" : "warning");
		} else if (data.action === "ignored") {
			// 무시된 키는 로그에 남기지 않음 (너무 많은 로그 방지)
			// 중요한 메시지만 로그에 남김
			if (data.message && data.message.includes("Control not started")) {
				log(data.message, "warning");
			}
			// 기타 무시된 키는 로그에 남기지 않음
		} else if (data.action === "control_started") {
			controlRunning = true;
			if (startControlBtn) startControlBtn.disabled = true;
			if (stopControlBtn) stopControlBtn.disabled = false;
			if (controlStatusText) {
				controlStatusText.textContent = "Running";
				controlStatusText.style.color = "var(--success)";
			}
			log("Keyboard control started", "success");
			startControlLoop(); // 제어 루프 시작
		} else if (data.action === "control_stopped") {
			controlRunning = false;
			if (startControlBtn) startControlBtn.disabled = false;
			if (stopControlBtn) stopControlBtn.disabled = true;
			if (controlStatusText) {
				const lang = getInitialLanguage();
				controlStatusText.textContent = translations[lang]?.["status.stopped"] || "Stopped";
				controlStatusText.style.color = "var(--text-secondary)";
			}
			log("Keyboard control stopped", "info");
			stopControlLoop(); // 제어 루프 중지
		} else if (data.action === "joint_move") {
			if (data.success) {
				log(`Joint ${data.joint} moved: ${data.delta > 0 ? '+' : ''}${data.delta.toFixed(1)}°`, "info");
			} else {
				log(`Joint ${data.joint} move failed`, "error");
			}
		} else if (data.action === "cartesian_move") {
			if (data.success) {
				log(`Cartesian move: axis ${data.axis}`, "info");
			} else {
				log(`Cartesian move failed`, "error");
			}
		}
	});

	socket.on("robot:error", (data) => {
		log(`Robot error: ${data.message}`, "error");
	});

	// 캘리브레이션 로그 수신
	socket.on("calibration:log", (data) => {
		log(data.message || "", data.level || "info");
	});

	// Sidebar menu navigation
	const menuItems = document.querySelectorAll(".menu-item");
	const contentSections = document.querySelectorAll(".content-section");

	menuItems.forEach((item) => {
		item.addEventListener("click", () => {
			const section = item.getAttribute("data-section");
			
			// Update active menu item
			menuItems.forEach((m) => m.classList.remove("active"));
			item.classList.add("active");
			
			// Show corresponding section
			contentSections.forEach((s) => s.classList.remove("active"));
			const targetSection = document.getElementById(`section-${section}`);
			if (targetSection) {
				targetSection.classList.add("active");
			}
		});
	});

	socket.on("robot:auto_connected", (data) => {
		updateStatus("Connected", true, {
			port: data.port || "-",
			baudrate: data.baudrate || "115200"
		});
		log(`Auto-connected to robot on ${data.port}`, "success");
	});

	// 캘리브레이션 마법사
	const wizardCard = document.getElementById("calibration-wizard");
	const showWizardBtn = document.getElementById("show-wizard-btn");
	const wizardStartBtn = document.getElementById("wizard-start-btn");
	const wizardNextBtn = document.getElementById("wizard-next-btn");
	const wizardCancelBtn = document.getElementById("wizard-cancel-btn");
	const wizardStepText = document.getElementById("wizard-step-text");
	const wizardProgressBar = document.getElementById("wizard-progress-bar");
	const wizardInstructionText = document.getElementById("wizard-instruction-text");
	
	let wizardActive = false;
	
	showWizardBtn?.addEventListener("click", () => {
		wizardCard.style.display = "block";
		wizardStartBtn.style.display = "block";
		wizardNextBtn.style.display = "none";
		wizardCancelBtn.style.display = "none";
		wizardStepText.textContent = "Step 0/3";
		wizardProgressBar.style.width = "0%";
		wizardInstructionText.textContent = "Ready to start calibration. Make sure the robot is connected and powered on.";
	});
	
	wizardStartBtn?.addEventListener("click", async () => {
		if (!isConnected) {
			log("Cannot start calibration: robot not connected", "error");
			return;
		}
		
		wizardActive = true;
		wizardStartBtn.style.display = "none";
		wizardNextBtn.style.display = "block";
		wizardCancelBtn.style.display = "block";
		
		// 첫 단계 실행
		await executeWizardStep();
	});
	
	wizardNextBtn?.addEventListener("click", async () => {
		await executeWizardStep();
	});
	
	wizardCancelBtn?.addEventListener("click", async () => {
		if (wizardActive) {
			try {
				await fetch("/api/calibration/wizard/reset", { method: "POST" });
			} catch (e) {
				console.error("Failed to reset wizard:", e);
			}
		}
		wizardActive = false;
		wizardCard.style.display = "none";
		wizardStartBtn.style.display = "block";
		wizardNextBtn.style.display = "none";
		wizardCancelBtn.style.display = "none";
		log("Calibration wizard cancelled", "info");
	});
	
	async function executeWizardStep() {
		if (!wizardActive) return;
		
		setButtonLoading(wizardNextBtn, true);
		try {
			const res = await fetch("/api/calibration/wizard/step", { method: "POST" });
			const json = await res.json();
			
			if (json.ok) {
				const step = json.step || 0;
				const maxSteps = json.max_steps || 3;
				const progress = (step / maxSteps) * 100;
				
				wizardStepText.textContent = `Step ${step}/${maxSteps}`;
				wizardProgressBar.style.width = `${progress}%`;
				wizardInstructionText.textContent = json.message || "";
				
				if (json.status === "success") {
					wizardActive = false;
					wizardNextBtn.style.display = "none";
					wizardCancelBtn.textContent = "Close";
					log("Calibration completed successfully!", "success");
				} else if (json.status === "error") {
					wizardActive = false;
					wizardNextBtn.style.display = "none";
					log(`Calibration error: ${json.message}`, "error");
				}
			} else {
				log(`Calibration step failed: ${json.detail || json.message}`, "error");
				wizardActive = false;
			}
		} catch (error) {
			log(`Calibration step error: ${error.message}`, "error");
			wizardActive = false;
		} finally {
			setButtonLoading(wizardNextBtn, false);
		}
	}

	// Initialize
	updateKeyboardHints("joint");
	loadPorts(); // Load ports on page load
	log("Rosota Copilot initialized", "success");
	
	// 초기 모드 텍스트 번역 적용
	const initialLanguage = getInitialLanguage();
	const modeNames = {
		joint: translations[initialLanguage]?.["mode.joint"] || "Joint",
		cartesian: translations[initialLanguage]?.["mode.cartesian"] || "Cartesian",
		gripper: translations[initialLanguage]?.["mode.gripper"] || "Gripper"
	};
	if (controlModeEl) {
		controlModeEl.textContent = modeNames.joint;
	}
	if (modeTextEl) {
		modeTextEl.textContent = `${modeNames.joint} ${translations[initialLanguage]?.["label.mode"] || "Mode"}`;
	}
	
	// 언어 적용
	applyLanguage(initialLanguage);
	
	// 튜토리얼 페이지 네비게이션
	const tutorialPagePrev = document.getElementById("tutorial-page-prev");
	const tutorialPageNext = document.getElementById("tutorial-page-next");
	const tutorialDots = document.querySelectorAll(".tutorial-dot");
	
	let currentTutorialPage = 1;
	const totalTutorialPages = 3;

	function updateTutorialPage() {
		// 모든 페이지 숨기기
		for (let i = 1; i <= totalTutorialPages; i++) {
			const page = document.getElementById(`tutorial-page-${i}`);
			if (page) {
				page.style.display = "none";
			}
		}

		// 현재 페이지 표시
		const currentPage = document.getElementById(`tutorial-page-${currentTutorialPage}`);
		if (currentPage) {
			currentPage.style.display = "flex";
		}

		// 이전 버튼 표시/숨기기
		if (tutorialPagePrev) {
			tutorialPagePrev.style.display = currentTutorialPage > 1 ? "block" : "none";
		}

		// 다음 버튼 텍스트 변경
		if (tutorialPageNext) {
			if (currentTutorialPage === totalTutorialPages) {
				tutorialPageNext.textContent = "완료";
			} else {
				tutorialPageNext.textContent = "다음 >";
			}
		}

		// 인디케이터 업데이트
		tutorialDots.forEach((dot, index) => {
			if (index + 1 === currentTutorialPage) {
				dot.classList.add("active");
			} else {
				dot.classList.remove("active");
			}
		});
	}

	tutorialPagePrev?.addEventListener("click", () => {
		if (currentTutorialPage > 1) {
			currentTutorialPage--;
			updateTutorialPage();
		}
	});

	tutorialPageNext?.addEventListener("click", () => {
		if (currentTutorialPage < totalTutorialPages) {
			currentTutorialPage++;
			updateTutorialPage();
		} else {
			// 완료 시 연결 섹션으로 이동
			const connectionMenuItem = document.querySelector('[data-section="connection"]');
			if (connectionMenuItem) {
				connectionMenuItem.click();
			}
			localStorage.setItem("rosota_tutorial_seen", "true");
			log("튜토리얼을 완료했습니다. 이제 로봇을 시작할 수 있습니다!", "success");
		}
	});

	// 인디케이터 클릭으로 페이지 이동
	tutorialDots.forEach((dot, index) => {
		dot.addEventListener("click", () => {
			currentTutorialPage = index + 1;
			updateTutorialPage();
		});
	});

	// 초기 페이지 설정
	updateTutorialPage();

	// 첫 실행 시 튜토리얼 섹션으로 이동
	function checkFirstTime() {
		const hasSeenTutorial = localStorage.getItem("rosota_tutorial_seen");
		if (!hasSeenTutorial) {
			setTimeout(() => {
				const tutorialMenuItem = document.querySelector('[data-section="tutorial"]');
				if (tutorialMenuItem) {
					tutorialMenuItem.click();
				}
			}, 1000);
		}
	}
	
	checkFirstTime();

	// 키보드 단축키 가이드 모달
	const shortcutsModal = document.getElementById("shortcuts-modal");
	const shortcutsCloseBtn = document.getElementById("shortcuts-close-btn");
	const shortcutsOverlay = shortcutsModal?.querySelector(".shortcuts-overlay");

	function showShortcutsGuide() {
		if (shortcutsModal) {
			shortcutsModal.style.display = "flex";
		}
	}

	function hideShortcutsGuide() {
		if (shortcutsModal) {
			shortcutsModal.style.display = "none";
		}
	}

	shortcutsCloseBtn?.addEventListener("click", () => {
		hideShortcutsGuide();
	});

	shortcutsOverlay?.addEventListener("click", () => {
		hideShortcutsGuide();
	});

	// Control 섹션에 키보드 가이드 버튼 추가
	const controlSection = document.getElementById("section-control");
	if (controlSection) {
		const keyboardGuideBtn = document.createElement("button");
		keyboardGuideBtn.className = "btn btn-secondary";
		keyboardGuideBtn.textContent = "⌨️ 키보드 가이드";
		keyboardGuideBtn.style.marginTop = "16px";
		keyboardGuideBtn.addEventListener("click", () => {
			showShortcutsGuide();
		});
		
		const keyboardHintsCard = controlSection.querySelector(".card.full-width");
		if (keyboardHintsCard) {
			keyboardHintsCard.appendChild(keyboardGuideBtn);
		}
	}

	// ===== 테마 기능 (처음부터 간단하게) =====
	function getInitialTheme() {
		const saved = localStorage.getItem("rosota_theme");
		return (saved && ["light", "dark", "system"].includes(saved)) ? saved : "light";
	}

	function getSystemTheme() {
		return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
	}

	function applyTheme(theme) {
		const effective = theme === "system" ? getSystemTheme() : theme;
		document.documentElement.setAttribute("data-theme", effective);
		
		const icon = document.getElementById("theme-icon");
		const text = document.getElementById("theme-text");
		if (icon && text) {
			if (theme === "light") {
				icon.textContent = "☀️";
				text.textContent = "Light";
			} else if (theme === "dark") {
				icon.textContent = "🌙";
				text.textContent = "Dark";
			} else {
				icon.textContent = "💻";
				text.textContent = "System";
			}
		}
		
		document.querySelectorAll(".theme-option").forEach(opt => {
			opt.classList.toggle("active", opt.dataset.theme === theme);
		});
	}

	function setTheme(theme) {
		localStorage.setItem("rosota_theme", theme);
		applyTheme(theme);
	}

	// 테마 토글 버튼
	window.toggleThemeDropdown = function(e) {
		if (e) e.preventDefault();
		const dropdown = document.getElementById("theme-dropdown");
		if (dropdown) dropdown.classList.toggle("show");
	};

	// 테마 옵션 클릭
	document.addEventListener("click", (e) => {
		const themeOpt = e.target.closest(".theme-option");
		if (themeOpt) {
			const theme = themeOpt.dataset.theme;
			if (theme) {
				setTheme(theme);
				document.getElementById("theme-dropdown")?.classList.remove("show");
			}
		}
	});

	// 외부 클릭 시 닫기
	document.addEventListener("click", (e) => {
		const dropdown = document.getElementById("theme-dropdown");
		if (dropdown?.classList.contains("show")) {
			if (!e.target.closest("#theme-toggle-btn") && !e.target.closest("#theme-dropdown")) {
				dropdown.classList.remove("show");
			}
		}
	});

	// 초기 테마 적용
	applyTheme(getInitialTheme());

	// ===== 언어 기능 (처음부터 간단하게) =====
	function getInitialLanguage() {
		const saved = localStorage.getItem("rosota_language");
		if (saved && ["ko", "en"].includes(saved)) return saved;
		return navigator.language?.startsWith("ko") ? "ko" : "en";
	}

	function applyLanguage(lang) {
		document.querySelectorAll("[data-i18n]").forEach(el => {
			const key = el.getAttribute("data-i18n");
			if (translations[lang]?.[key]) {
				el.textContent = translations[lang][key];
			}
		});

		const icon = document.getElementById("language-icon");
		const text = document.getElementById("language-text");
		if (icon && text) {
			if (lang === "ko") {
				icon.textContent = "🇰🇷";
				text.textContent = "Kor";
			} else {
				icon.textContent = "🇺🇸";
				text.textContent = "Eng";
			}
		}

		document.querySelectorAll(".language-option").forEach(opt => {
			opt.classList.toggle("active", opt.dataset.lang === lang);
		});

		document.documentElement.setAttribute("lang", lang);

		// 모드 텍스트 업데이트
		if (controlModeEl && currentMode) {
			const modeNames = {
				joint: translations[lang]?.["mode.joint"] || "Joint",
				cartesian: translations[lang]?.["mode.cartesian"] || "Cartesian",
				gripper: translations[lang]?.["mode.gripper"] || "Gripper"
			};
			controlModeEl.textContent = modeNames[currentMode] || "Joint";
		}
		if (modeTextEl && currentMode) {
			const modeNames = {
				joint: translations[lang]?.["mode.joint"] || "Joint",
				cartesian: translations[lang]?.["mode.cartesian"] || "Cartesian",
				gripper: translations[lang]?.["mode.gripper"] || "Gripper"
			};
			modeTextEl.textContent = `${modeNames[currentMode] || "Joint"} ${translations[lang]?.["label.mode"] || "Mode"}`;
		}
		
		if (currentMode) updateKeyboardHints(currentMode);
	}

	function setLanguage(lang) {
		localStorage.setItem("rosota_language", lang);
		applyLanguage(lang);
	}

	// 언어 토글 버튼
	window.toggleLanguageDropdown = function(e) {
		if (e) e.preventDefault();
		const dropdown = document.getElementById("language-dropdown");
		if (dropdown) dropdown.classList.toggle("show");
	};

	// 언어 옵션 클릭
	document.addEventListener("click", (e) => {
		const langOpt = e.target.closest(".language-option");
		if (langOpt) {
			const lang = langOpt.dataset.lang;
			if (lang) {
				setLanguage(lang);
				document.getElementById("language-dropdown")?.classList.remove("show");
			}
		}
	});

	// 외부 클릭 시 닫기
	document.addEventListener("click", (e) => {
		const dropdown = document.getElementById("language-dropdown");
		if (dropdown?.classList.contains("show")) {
			if (!e.target.closest("#language-toggle-btn") && !e.target.closest("#language-dropdown")) {
				dropdown.classList.remove("show");
			}
		}
	});

	// 언어는 이미 Initialize에서 적용됨

	// ========== Motor Setup ==========
	let motorSetupState = {
		robotType: null,
		port: null,
		currentMotorIndex: 0,
		motors: [],
		configuredMotors: new Set()
	};

	// Motor Setup DOM Elements
	const motorSetupFollowerBtn = document.getElementById("motor-setup-follower-btn");
	const motorSetupLeaderBtn = document.getElementById("motor-setup-leader-btn");
	const motorSetupFindPortBtn = document.getElementById("motor-setup-find-port-btn");
	const motorSetupConfigureBtn = document.getElementById("motor-setup-configure-btn");
	const motorSetupCheckIdBtn = document.getElementById("motor-setup-check-id-btn");
	const motorSetupResetMotorBtn = document.getElementById("motor-setup-reset-motor-btn");
	const motorSetupSkipBtn = document.getElementById("motor-setup-skip-btn");
	const motorSetupResetBtn = document.getElementById("motor-setup-reset-btn");
	const motorSetupStep1 = document.getElementById("motor-setup-step-1");
	const motorSetupStep2 = document.getElementById("motor-setup-step-2");
	const motorSetupStep3 = document.getElementById("motor-setup-step-3");
	const motorSetupMotorsList = document.getElementById("motor-setup-motors-list");
	const motorSetupCurrentMotor = document.getElementById("motor-setup-current-motor");
	const motorSetupCurrentMotorName = document.getElementById("motor-setup-current-motor-name");
	const motorSetupPortResult = document.getElementById("motor-setup-port-result");
	const motorSetupPortValue = document.getElementById("motor-setup-port-value");
	const motorSetupProgress = document.getElementById("motor-setup-progress");
	const motorSetupProgressText = document.getElementById("motor-setup-progress-text");
	const motorSetupProgressBar = document.getElementById("motor-setup-progress-bar");
	const motorSetupStatus = document.getElementById("motor-setup-status");
	const motorSetupIdResult = document.getElementById("motor-setup-id-result");
	const motorSetupIdResultText = document.getElementById("motor-setup-id-result-text");

	// Motor Setup: Start (Robot Type Selection)
	if (motorSetupFollowerBtn) {
		motorSetupFollowerBtn.addEventListener("click", async () => {
			await startMotorSetup("follower");
		});
	}

	if (motorSetupLeaderBtn) {
		motorSetupLeaderBtn.addEventListener("click", async () => {
			await startMotorSetup("leader");
		});
	}

	async function startMotorSetup(robotType) {
		try {
			const response = await fetch("/api/setup/start", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ robot_type: robotType })
			});
			const data = await response.json();
			
			if (data.ok) {
				motorSetupState.robotType = robotType;
				motorSetupState.motors = data.motors || [];
				motorSetupState.configuredMotors.clear();
				motorSetupState.currentMotorIndex = 0;
				
				// Show step 2
				motorSetupStep1.style.display = "none";
				motorSetupStep2.style.display = "block";
				
				showMotorSetupStatus("success", `Motor setup started for ${robotType} arm`);
			} else {
				showMotorSetupStatus("error", data.error || "Failed to start motor setup");
			}
		} catch (error) {
			showMotorSetupStatus("error", `Error: ${error.message}`);
		}
	}

	// Motor Setup: Find Port
	if (motorSetupFindPortBtn) {
		motorSetupFindPortBtn.addEventListener("click", async () => {
			try {
				motorSetupFindPortBtn.disabled = true;
				motorSetupFindPortBtn.textContent = "Finding...";
				
				// Get ports before
				const portsBeforeRes = await fetch("/api/setup/ports-before");
				const portsBeforeData = await portsBeforeRes.json();
				
				if (!portsBeforeData.ok) {
					throw new Error("Failed to get ports");
				}
				
			// Try to find port (will try PID first, then disconnect method if needed)
			// Note: If PID method fails, user may need to disconnect USB cable
				const findPortRes = await fetch("/api/setup/find-port", {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({ ports_before: portsBeforeData.ports })
				});
				
				const findPortData = await findPortRes.json();
				
				if (findPortData.ok) {
					motorSetupState.port = findPortData.port;
					motorSetupPortValue.textContent = findPortData.port;
					motorSetupPortResult.style.display = "block";
					
					// Show method used
					const methodText = document.getElementById("motor-setup-port-method");
					if (methodText) {
						if (findPortData.method === "pid") {
							methodText.textContent = "✓ Found automatically (no USB disconnection needed)";
							methodText.style.color = "var(--success)";
						} else {
							methodText.textContent = "Please reconnect the USB cable now.";
							methodText.style.color = "var(--text-secondary)";
						}
					}
					
					// Show step 3
					motorSetupStep2.style.display = "none";
					motorSetupStep3.style.display = "block";
					motorSetupProgress.style.display = "block";
					
					renderMotorsList();
					updateCurrentMotor();
					
					showMotorSetupStatus("success", `Port found: ${findPortData.port} (method: ${findPortData.method || "unknown"})`);
				} else {
					throw new Error(findPortData.detail || "Failed to find port");
				}
			} catch (error) {
				showMotorSetupStatus("error", `Error: ${error.message}`);
			} finally {
				motorSetupFindPortBtn.disabled = false;
				motorSetupFindPortBtn.innerHTML = "<span>Find Port</span>";
			}
		});
	}

	function renderMotorsList() {
		if (!motorSetupMotorsList) return;
		
		motorSetupMotorsList.innerHTML = "";
		
		motorSetupState.motors.forEach((motor, index) => {
			const motorItem = document.createElement("div");
			motorItem.className = "motor-item";
			motorItem.style.cursor = "pointer";
			motorItem.title = `Click to configure ${motor.name} (ID: ${motor.id})`;
			
			if (motorSetupState.configuredMotors.has(motor.id)) {
				motorItem.classList.add("configured");
			}
			if (index === motorSetupState.currentMotorIndex) {
				motorItem.classList.add("current");
			}
			
			motorItem.innerHTML = `
				<div>
					<span class="motor-item-name">${motor.name}</span>
					<span class="motor-item-id"> (ID: ${motor.id})</span>
				</div>
				<span class="motor-item-status ${motorSetupState.configuredMotors.has(motor.id) ? 'configured' : 'pending'}">
					${motorSetupState.configuredMotors.has(motor.id) ? '✓ Configured' : 'Pending'}
				</span>
			`;
			
			// 클릭 이벤트: 해당 모터로 이동
			motorItem.addEventListener("click", () => {
				motorSetupState.currentMotorIndex = index;
				updateCurrentMotor();
			});
			
			motorSetupMotorsList.appendChild(motorItem);
		});
	}

	function updateCurrentMotor() {
		if (motorSetupState.motors.length === 0) return;
		
		// Always update progress first (even if no current motor)
		const progress = (motorSetupState.configuredMotors.size / motorSetupState.motors.length) * 100;
		motorSetupProgressBar.style.width = `${progress}%`;
		motorSetupProgressText.textContent = `${motorSetupState.configuredMotors.size} / ${motorSetupState.motors.length}`;
		
		// Update current motor display
		const currentMotor = motorSetupState.motors[motorSetupState.currentMotorIndex];
		if (!currentMotor) {
			motorSetupCurrentMotor.style.display = "none";
			// Still render motors list to show all configured motors
			renderMotorsList();
			return;
		}
		
		motorSetupCurrentMotorName.textContent = `${currentMotor.name} (ID: ${currentMotor.id})`;
		motorSetupCurrentMotor.style.display = "block";
		
		renderMotorsList();
	}

	// Motor Setup: Configure Motor
	if (motorSetupConfigureBtn) {
		motorSetupConfigureBtn.addEventListener("click", async () => {
			if (!motorSetupState.port || motorSetupState.motors.length === 0) {
				showMotorSetupStatus("error", "Port or motors not set");
				return;
			}
			
			const currentMotor = motorSetupState.motors[motorSetupState.currentMotorIndex];
			if (!currentMotor) {
				showMotorSetupStatus("error", "No motor to configure");
				return;
			}
			
			try {
				motorSetupConfigureBtn.disabled = true;
				motorSetupConfigureBtn.innerHTML = "<span>Configuring...</span>";
				
				const response = await fetch("/api/setup/motor", {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({
						port: motorSetupState.port,
						motor_id: currentMotor.id,
						baudrate: 1000000
					})
				});
				
				const data = await response.json();
				
				if (data.ok) {
					motorSetupState.configuredMotors.add(currentMotor.id);
					showMotorSetupStatus("success", `Motor ${currentMotor.name} (ID: ${currentMotor.id}) configured successfully`);
					
					// Update progress immediately (before moving to next motor)
					updateCurrentMotor();
					
					// Move to next motor
					motorSetupState.currentMotorIndex++;
					if (motorSetupState.currentMotorIndex >= motorSetupState.motors.length) {
						// All motors configured
						showMotorSetupStatus("success", "All motors configured successfully!");
						motorSetupCurrentMotor.style.display = "none";
						// Final progress update to show 6/6
						updateCurrentMotor();
					}
				} else {
					throw new Error(data.detail || "Failed to configure motor");
				}
			} catch (error) {
				showMotorSetupStatus("error", `Error: ${error.message}`);
			} finally {
				motorSetupConfigureBtn.disabled = false;
				motorSetupConfigureBtn.innerHTML = "<span>Configure Motor</span>";
			}
		});
	}

	// Motor Setup: Check Motor ID
	if (motorSetupCheckIdBtn) {
		motorSetupCheckIdBtn.addEventListener("click", async () => {
			if (!motorSetupState.port) {
				showMotorSetupStatus("error", "Port not set. Please find the port first.");
				return;
			}

			try {
				motorSetupCheckIdBtn.disabled = true;
				motorSetupCheckIdBtn.innerHTML = "<span>Checking...</span>";
				motorSetupIdResult.style.display = "none";

				const response = await fetch("/api/setup/check-motor-id", {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({
						port: motorSetupState.port
					})
				});

				const data = await response.json();

				if (data.ok) {
					if (data.warning) {
						// 여러 모터가 감지된 경우
						motorSetupIdResult.style.display = "block";
						motorSetupIdResult.style.background = "rgba(251, 191, 36, 0.1)";
						motorSetupIdResult.style.border = "1px solid var(--warning)";
						motorSetupIdResultText.style.color = "var(--warning)";
						motorSetupIdResultText.textContent = `${data.warning} Detected motors: ${data.motors.map(m => `ID ${m.id} (baudrate: ${m.baudrate})`).join(", ")}`;
					} else if (data.motor_id !== undefined) {
						// 단일 모터가 감지된 경우
						motorSetupIdResult.style.display = "block";
						motorSetupIdResult.style.background = "rgba(34, 197, 94, 0.1)";
						motorSetupIdResult.style.border = "1px solid var(--success)";
						motorSetupIdResultText.style.color = "var(--success)";
						motorSetupIdResultText.textContent = `Motor ID: ${data.motor_id} (Baudrate: ${data.baudrate})`;
					}
				} else {
					throw new Error(data.detail || "Failed to check motor ID");
				}
			} catch (error) {
				motorSetupIdResult.style.display = "block";
				motorSetupIdResult.style.background = "rgba(239, 68, 68, 0.1)";
				motorSetupIdResult.style.border = "1px solid var(--error)";
				motorSetupIdResultText.style.color = "var(--error)";
				motorSetupIdResultText.textContent = `Error: ${error.message}`;
			} finally {
				motorSetupCheckIdBtn.disabled = false;
				motorSetupCheckIdBtn.innerHTML = "<span data-i18n=\"motor_setup.check_id\">Check Motor ID</span>";
				applyLanguage(); // 번역 다시 적용
			}
		});
	}

	// Motor Setup: Reset Motor ID
	if (motorSetupResetMotorBtn) {
		motorSetupResetMotorBtn.addEventListener("click", async () => {
			if (!motorSetupState.port || motorSetupState.motors.length === 0) {
				showMotorSetupStatus("error", "Port or motors not set");
				return;
			}
			
			const currentMotor = motorSetupState.motors[motorSetupState.currentMotorIndex];
			if (!currentMotor) {
				showMotorSetupStatus("error", "No motor to reset");
				return;
			}
			
			if (!confirm(`Reset motor ${currentMotor.name} (ID: ${currentMotor.id}) to ID 1?`)) {
				return;
			}
			
			try {
				motorSetupResetMotorBtn.disabled = true;
				motorSetupResetMotorBtn.innerHTML = "<span>Resetting...</span>";
				
				const response = await fetch("/api/setup/reset-motor", {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({
						port: motorSetupState.port,
						target_id: currentMotor.id,
						reset_to_id: 1,
						baudrate: 1000000
					})
				});
				
				const data = await response.json();
				
				if (data.ok) {
					showMotorSetupStatus("success", `Motor ID reset from ${data.old_id} to ${data.new_id}. You can now configure it again.`);
					// Remove from configured motors if it was configured
					motorSetupState.configuredMotors.delete(currentMotor.id);
					updateCurrentMotor();
				} else {
					throw new Error(data.detail || "Failed to reset motor");
				}
			} catch (error) {
				showMotorSetupStatus("error", `Error: ${error.message}`);
			} finally {
				motorSetupResetMotorBtn.disabled = false;
				motorSetupResetMotorBtn.innerHTML = "<span>Reset Motor ID</span>";
			}
		});
	}

	// Motor Setup: Skip Motor
	if (motorSetupSkipBtn) {
		motorSetupSkipBtn.addEventListener("click", () => {
			motorSetupState.currentMotorIndex++;
			if (motorSetupState.currentMotorIndex >= motorSetupState.motors.length) {
				motorSetupCurrentMotor.style.display = "none";
			} else {
				updateCurrentMotor();
			}
		});
	}

	// Motor Setup: Reset
	if (motorSetupResetBtn) {
		motorSetupResetBtn.addEventListener("click", async () => {
			try {
				await fetch("/api/setup/reset", { method: "POST" });
				motorSetupState = {
					robotType: null,
					port: null,
					currentMotorIndex: 0,
					motors: [],
					configuredMotors: new Set()
				};
				
				motorSetupStep1.style.display = "block";
				motorSetupStep2.style.display = "none";
				motorSetupStep3.style.display = "none";
				motorSetupPortResult.style.display = "none";
				motorSetupCurrentMotor.style.display = "none";
				motorSetupProgress.style.display = "none";
				motorSetupStatus.style.display = "none";
				
				showMotorSetupStatus("info", "Motor setup reset");
			} catch (error) {
				showMotorSetupStatus("error", `Error: ${error.message}`);
			}
		});
	}

	function showMotorSetupStatus(type, message) {
		if (!motorSetupStatus) return;
		
		motorSetupStatus.style.display = "block";
		motorSetupStatus.className = "";
		motorSetupStatus.classList.add(`log-entry`, type);
		motorSetupStatus.textContent = message;
		
		if (type === "success") {
			motorSetupStatus.style.background = "rgba(34, 197, 94, 0.1)";
			motorSetupStatus.style.color = "var(--success)";
		} else if (type === "error") {
			motorSetupStatus.style.background = "rgba(239, 68, 68, 0.1)";
			motorSetupStatus.style.color = "var(--error)";
		} else {
			motorSetupStatus.style.background = "rgba(96, 165, 250, 0.1)";
			motorSetupStatus.style.color = "#60a5fa";
		}
	}
})();
