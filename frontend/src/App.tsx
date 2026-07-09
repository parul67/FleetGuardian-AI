import { useEffect, useMemo, useRef, useState } from "react";

type Telemetry = {
  speed: number;
  rpm: number;
  heading: string;
  fuel: number;
  location: string;
};

type LiveAlert = {
  event?: string;
  alert?: string;
  driver_id?: number;
  vehicle_id?: number;
  severity?: string;
};

type VideoPayload = {
  image?: string;
  metrics?: {
    speed?: number;
    rpm?: number;
    eye_aspect_ratio?: number;
    phone_confidence?: number;
    seatbelt?: boolean;
    lane_departure?: boolean;
  };
  risk_level?: string;
};

const metricDefaults: Telemetry = {
  speed: 62,
  rpm: 2100,
  heading: "North-East",
  fuel: 74,
  location: "Sector 12",
};

const fallbackAlerts: LiveAlert[] = [
  {
    event: "critical",
    alert: "Drowsiness detected - immediate driver attention required",
    driver_id: 1,
    vehicle_id: 1,
    severity: "high",
  },
  {
    event: "warning",
    alert: "Lane drift rising - route correction suggested",
    driver_id: 1,
    vehicle_id: 1,
    severity: "medium",
  },
  {
    event: "notice",
    alert: "Seatbelt status stable - telemetry capture active",
    driver_id: 1,
    vehicle_id: 1,
    severity: "low",
  },
];

const MOVING_SPEED_THRESHOLD = 5;

function App() {
  const videoSocketRef = useRef<WebSocket | null>(null);
  const alertsSocketRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [frame, setFrame] = useState("");
  const [riskLevel, setRiskLevel] = useState("NORMAL");
  const [telemetry, setTelemetry] = useState<Telemetry>(metricDefaults);
  const [liveAlerts, setLiveAlerts] = useState<LiveAlert[]>(fallbackAlerts);
  const [status, setStatus] = useState("Connecting to backend...");
  const [metrics, setMetrics] = useState<VideoPayload["metrics"]>({});
  const [driverId] = useState(1);
  const [vehicleId] = useState(1);
  const [tripId] = useState(1);
  const webcamRef = useRef<HTMLVideoElement | null>(null);
  const webcamStreamRef = useRef<MediaStream | null>(null);
  const [showWebcam, setShowWebcam] = useState(false);

  useEffect(() => {
    const wsUrl = "ws://127.0.0.1:8000/ws/video";
    const alertWsUrl = "ws://127.0.0.1:8000/ws/alerts";

    const videoSocket = new WebSocket(wsUrl);
    videoSocketRef.current = videoSocket;

    videoSocket.onopen = () => {
      setConnected(true);
      setStatus("Live stream connected");
      videoSocket.send(
        JSON.stringify({
          action: "start_stream",
          driver_id: driverId,
          vehicle_id: vehicleId,
          trip_id: tripId,
        })
      );
    };

    videoSocket.onmessage = (event) => {
      try {
        const data: VideoPayload = JSON.parse(event.data);
        if (data.image) setFrame(data.image);
        if (data.metrics) {
          setMetrics(data.metrics);
          setTelemetry((current) => ({
            speed: data.metrics?.speed ?? current.speed,
            rpm: Math.max(1200, Math.round((data.metrics?.speed ?? current.speed) * 34)),
            heading: current.heading,
            fuel: Math.max(18, current.fuel - 0.1),
            location: current.location,
          }));
        }
        if (data.risk_level) setRiskLevel(data.risk_level);
      } catch {
        // ignore malformed payloads
      }
    };

    videoSocket.onerror = () => setStatus("Video stream error");
    videoSocket.onclose = () => {
      setConnected(false);
      setStatus("Video stream disconnected");
    };

    const alertSocket = new WebSocket(alertWsUrl);
    alertsSocketRef.current = alertSocket;
    alertSocket.onopen = () => {
      alertSocket.send(JSON.stringify({ action: "listen" }));
    };
    alertSocket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as LiveAlert;
        setLiveAlerts((current) => [payload, ...current].slice(0, 6));
      } catch {
        // ignore
      }
    };

    return () => {
      try {
        videoSocket.send(JSON.stringify({ action: "stop_stream" }));
      } catch {
        // ignore
      }
      videoSocket.close();
      alertSocket.close();
    };
  }, [driverId, tripId, vehicleId]);

  const kpis = useMemo(
    () => [
      { label: "Driver speed", value: `${telemetry.speed.toFixed(0)} km/h` },
      { label: "Engine RPM", value: telemetry.rpm.toLocaleString() },
      { label: "Fuel level", value: `${telemetry.fuel.toFixed(0)}%` },
      { label: "Risk level", value: riskLevel },
    ],
    [riskLevel, telemetry]
  );

  const currentAlert = liveAlerts[0] ?? fallbackAlerts[0];
  const alertCounts = useMemo(
    () => ({
      critical: liveAlerts.filter((item) => item.event === "critical").length,
      warning: liveAlerts.filter((item) => item.event === "warning").length,
      notice: liveAlerts.filter((item) => item.event === "notice").length,
    }),
    [liveAlerts]
  );

  useEffect(() => {
    const isMoving = telemetry.speed >= MOVING_SPEED_THRESHOLD;
    if (!isMoving) {
      if (webcamStreamRef.current) {
        webcamStreamRef.current.getTracks().forEach((track) => track.stop());
        webcamStreamRef.current = null;
      }
      setShowWebcam(false);
      return;
    }

    let active = true;
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "user" }, audio: false })
      .then((stream) => {
        if (!active) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        webcamStreamRef.current = stream;
        setShowWebcam(true);
        if (webcamRef.current) {
          webcamRef.current.srcObject = stream;
        }
      })
      .catch(() => {
        setShowWebcam(false);
      });

    return () => {
      active = false;
    };
  }, [telemetry.speed]);

  return (
    <div className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <header className="topbar">
        <div>
          <p className="eyebrow">FleetGuardian AI</p>
          <h1>Real-time driver movement and vehicle telemetry</h1>
        </div>
        <div className={`live-badge ${connected ? "live" : "idle"}`}>
          <span />
          {status}
        </div>
      </header>

      <main className="dashboard live-dashboard">
        <section className="card alert-banner">
          <div>
            <p className="section-label">Live incident</p>
            <h2>{currentAlert.alert}</h2>
            <p>
              {String(currentAlert.event ?? "alert").toUpperCase()} | Driver #{currentAlert.driver_id ?? driverId} | Vehicle #{currentAlert.vehicle_id ?? vehicleId}
            </p>
          </div>
          <div className="alert-stats">
            <div>
              <strong>{alertCounts.critical}</strong>
              <span>Critical</span>
            </div>
            <div>
              <strong>{alertCounts.warning}</strong>
              <span>Warning</span>
            </div>
            <div>
              <strong>{alertCounts.notice}</strong>
              <span>Notice</span>
            </div>
          </div>
        </section>

        <section className="hero card live-hero">
          <div className="video-shell">
            {showWebcam ? (
              <div className="stacked-feed">
                <video ref={webcamRef} autoPlay playsInline muted className="video-frame webcam-frame" />
                {frame ? <img src={frame} alt="Live driver feed" className="video-overlay" /> : null}
                <div className="feed-badge">Webcam active while vehicle is moving</div>
              </div>
            ) : frame ? (
              <img src={frame} alt="Live driver feed" className="video-frame" />
            ) : (
              <div className="video-placeholder">
                <div className="pulse-ring" />
                <p>Waiting for live video frames...</p>
                <small>The webcam opens automatically while the vehicle is moving.</small>
              </div>
            )}
          </div>

          <div className="telemetry-panel">
            <div className="card-header">
              <div>
                <p className="section-label">Telemetry</p>
                <h3>Vehicle status</h3>
              </div>
              <span className="badge">Driver #{driverId}</span>
            </div>

            <div className="telemetry-grid">
              {kpis.map((item) => (
                <article className="card kpi-card telemetry-card" key={item.label}>
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </article>
              ))}
            </div>

            <div className="signal-panel">
              <div>
                <span>Heading</span>
                <strong>{telemetry.heading}</strong>
              </div>
              <div>
                <span>Location</span>
                <strong>{telemetry.location}</strong>
              </div>
              <div>
                <span>Lane/phone</span>
                <strong>
                  {metrics?.lane_departure ? "Lane departure" : "Lane stable"} /{" "}
                  {metrics?.phone_confidence ? `${Math.round((metrics.phone_confidence ?? 0) * 100)}%` : "0%"}
                </strong>
              </div>
            </div>
          </div>
        </section>

        <section className="content-grid live-grid">
          <article className="card chart-card">
            <div className="card-header">
              <div>
                <p className="section-label">Driver movement</p>
                <h3>Risk and motion snapshot</h3>
              </div>
              <span className="badge">Trip #{tripId}</span>
            </div>

            <div className="movement-map">
              <div className="route route-1" />
              <div className="route route-2" />
              <div className="vehicle-dot" />
              <div className="movement-label north">N</div>
              <div className="movement-label east">E</div>
              <div className="movement-label west">W</div>
              <div className="movement-label south">S</div>
            </div>
          </article>

          <article className="card timeline-card">
            <div className="card-header">
              <div>
                <p className="section-label">Alerts</p>
                <h3>Live safety events</h3>
              </div>
            </div>

            <div className="timeline">
              {liveAlerts.map((item, index) => (
                <div className={`timeline-item timeline-${item.event ?? "notice"}`} key={`${item.event ?? "alert"}-${index}`}>
                  <span>{item.event ?? "alert"}</span>
                  <div>
                    <strong>{item.alert ?? "Live alert"}</strong>
                    <p>
                      Driver #{item.driver_id ?? driverId} • Vehicle #{item.vehicle_id ?? vehicleId}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </article>
        </section>
      </main>
    </div>
  );
}

export default App;
