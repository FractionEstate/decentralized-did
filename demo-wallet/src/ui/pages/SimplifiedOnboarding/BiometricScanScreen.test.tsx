import { Buffer } from "buffer";
import { render, screen } from "@testing-library/react";
import { act } from "react";
import { BiometricScanScreen } from "./BiometricScanScreen";

describe("BiometricScanScreen", () => {
  const originalBtoa = globalThis.btoa;

  beforeAll(() => {
    if (!globalThis.btoa) {
      globalThis.btoa = (str: string) =>
        Buffer.from(str, "binary").toString("base64");
    }
  });

  afterAll(() => {
    globalThis.btoa = originalBtoa;
  });

  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
    jest.clearAllMocks();
  });

  const flushAllTimers = async (maxIterations = 50) => {
    let iterations = 0;
    while (jest.getTimerCount() > 0) {
      if (iterations++ > maxIterations) {
        throw new Error("Exceeded max timer iterations");
      }
      await act(async () => {
        jest.runOnlyPendingTimers();
      });
    }
  };

  test("auto captures each finger sequentially and notifies completion", async () => {
    const onComplete = jest.fn();
    const onError = jest.fn();

    render(
      <BiometricScanScreen
        fingersToScan={["right-thumb", "right-index", "left-thumb"]}
        onComplete={onComplete}
        onError={onError}
      />
    );

    await flushAllTimers();

    expect(onComplete).toHaveBeenCalledTimes(1);
    const capturedPayload = onComplete.mock.calls[0][0] as string[];
    expect(capturedPayload).toHaveLength(3);
    expect(new Set(capturedPayload).size).toBe(3);
    expect(onError).not.toHaveBeenCalled();
    expect(screen.getByText("Finger 3 of 3")).toBeInTheDocument();
  });
});
