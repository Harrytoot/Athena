import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ErrorBoundary } from "@/components/ErrorBoundary";

function ThrowError({ message }: { message?: string }) {
  throw new Error(message || "test error");
}

const origConsole = console.error;
beforeEach(() => {
  console.error = vi.fn();
});
afterAll(() => {
  console.error = origConsole;
});

describe("ErrorBoundary", () => {
  it("renders children normally", () => {
    render(
      <ErrorBoundary>
        <div>正常内容</div>
      </ErrorBoundary>,
    );
    expect(screen.getByText("正常内容")).toBeInTheDocument();
  });

  it("renders fallback when child throws", () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>,
    );
    expect(screen.getByText("页面发生错误")).toBeInTheDocument();
    expect(screen.getByText("test error")).toBeInTheDocument();
  });

  it("renders custom fallback when provided", () => {
    render(
      <ErrorBoundary fallback={<div>自定义降级</div>}>
        <ThrowError />
      </ErrorBoundary>,
    );
    expect(screen.getByText("自定义降级")).toBeInTheDocument();
  });

  it("shows unknown error text as heading", () => {
    render(
      <ErrorBoundary>
        <ThrowError message="something broke" />
      </ErrorBoundary>,
    );
    expect(screen.getByText("页面发生错误")).toBeInTheDocument();
    expect(screen.getByText("something broke")).toBeInTheDocument();
  });
});
