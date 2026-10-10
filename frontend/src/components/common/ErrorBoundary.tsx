import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, LayoutDashboard, Terminal } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  onReset?: () => void;
  onReturnHome?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('MessWise Uncaught Render Exception in ErrorBoundary:', error, errorInfo);
    this.setState({ errorInfo });
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  private handleReturnHome = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReturnHome) {
      this.props.onReturnHome();
    } else {
      window.location.hash = '';
    }
  };

  public render() {
    if (this.state.hasError) {
      const { fallbackTitle = 'Page Display Issue Encountered' } = this.props;
      const errorMessage = this.state.error?.message || 'An unexpected rendering error occurred.';
      const componentStack = this.state.errorInfo?.componentStack;

      return (
        <div className="my-8 mx-auto max-w-3xl rounded-3xl border border-red-300 bg-[var(--surface)] p-8 shadow-xl dark:border-red-800/80 dark:bg-[#11261F]">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-red-100 text-red-700 dark:bg-red-950/90 dark:text-red-300">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <div className="flex-1">
              <span className="text-[11px] font-bold uppercase tracking-wider text-red-700 dark:text-red-300">
                Resilience Recovery System
              </span>
              <h2 className="mt-1 font-display text-xl font-extrabold text-[var(--text-primary)]">
                {fallbackTitle}
              </h2>
              <p className="mt-2 text-xs leading-relaxed text-[var(--text-secondary)] font-medium">
                MessWise caught an unexpected rendering issue before it could cause a blank screen. You can retry loading this view, return to the Command Center, or inspect the diagnostic details below.
              </p>

              <div className="mt-4 rounded-xl border border-red-200 bg-red-50/70 p-3.5 text-xs text-red-900 dark:border-red-900/60 dark:bg-red-950/50 dark:text-red-200 font-mono">
                {errorMessage}
              </div>

              {/* Action Buttons with Guaranteed Contrast & No Black Hover */}
              <div className="mt-6 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={this.handleRetry}
                  className="btn-primary"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  Retry View
                </button>
                <button
                  type="button"
                  onClick={this.handleReturnHome}
                  className="btn-secondary"
                >
                  <LayoutDashboard className="h-3.5 w-3.5" />
                  Return to Command Center
                </button>
              </div>

              {/* Collapsible Technical Details */}
              <details className="mt-6 border-t border-[var(--border)] pt-4 text-xs text-[var(--text-secondary)]">
                <summary className="cursor-pointer font-semibold flex items-center gap-1.5 text-[var(--text-primary)] hover:underline">
                  <Terminal className="h-3.5 w-3.5" />
                  Diagnostic Technical Trace
                </summary>
                <pre className="mt-3 max-h-48 overflow-auto rounded-xl bg-stone-900 p-3 font-mono text-[11px] text-emerald-300">
                  {this.state.error?.stack || errorMessage}
                  {componentStack && `\n\nComponent Hierarchy:${componentStack}`}
                </pre>
              </details>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
