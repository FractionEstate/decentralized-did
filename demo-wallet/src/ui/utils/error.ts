import { AnyAction, ThunkDispatch } from "@reduxjs/toolkit";
import { RootState } from "../../store";
import { setToastMsg, showGenericError } from "../../store/reducers/stateCache";
import { ToastMsgType } from "../globals/types";
import { Agent } from "../../core/agent/agent";

const showError = (
  message: string,
  error: unknown,
  dispatch?: ThunkDispatch<RootState, undefined, AnyAction>,
  toastMessage?: ToastMsgType
) => {
  // eslint-disable-next-line no-console
  console.error(`${message}:`, error);

  if (!dispatch) return;

  if (error instanceof Error && error.message === Agent.KERIA_CONNECTION_BROKEN)
    return;

  // Filter out NotFoundError - it's an expected storage initialization issue
  if (error instanceof Error && error.name === 'NotFoundError') {
    return;
  }

  if (toastMessage) {
    dispatch(setToastMsg(toastMessage));
  } else {
    dispatch(showGenericError(true));
  }
};

export { showError };
