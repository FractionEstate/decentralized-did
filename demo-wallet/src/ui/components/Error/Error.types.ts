import { AlertProps } from "../common/Alert/Alert.types";

type CommonErrorAlertProps = Pick<
  AlertProps,
  "isOpen" | "setIsOpen" | "actionConfirm" | "dataTestId"
>;

export type { CommonErrorAlertProps };
