export default function Navbar() {
  return (
    <div style={{ width: "100%", background: "rgba(255,255,255,0.02)", borderBottom: "1px solid rgba(255,255,255,0.03)", padding: "10px 18px", boxSizing: "border-box" }}>
      <div style={{ maxWidth: 980, margin: "0 auto", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ fontWeight: 700 }}>AI Customer Support</div>
        <div style={{ color: "var(--muted)" }}>Real-time AI assistant</div>
      </div>
    </div>
  );
}
