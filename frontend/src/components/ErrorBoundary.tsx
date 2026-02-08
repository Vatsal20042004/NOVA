
import React from 'react';

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean, error: Error | null }> {
    constructor(props: { children: React.ReactNode }) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error) {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error("Uncaught error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{ padding: '20px', textAlign: 'center' }}>
                    <h1>Something went wrong.</h1>
                    <p style={{ color: 'red' }}>{this.state.error && this.state.error.toString()}</p>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
