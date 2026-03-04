import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="info-box">
          <div className="info-box-title">Något gick fel</div>
          <p>Ett fel uppstod vid rendering av denna sektion.</p>
          <pre style={{ fontSize: 12, whiteSpace: "pre-wrap", color: "#B91E2B", marginTop: 8 }}>
            {this.state.error.message}
          </pre>
          <button
            className="toggle-btn"
            style={{ marginTop: 12 }}
            onClick={() => this.setState({ error: null })}
          >
            Försök igen
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
