import { FilterType } from "../../types/filter.types";
import { NotificationFilters } from "../../pages/Notifications/Notification.types";

type AllowedChipFilter =
  | NotificationFilters
  | FilterType;
interface FilterChipProps {
  filter: AllowedChipFilter;
  label: string;
  isActive: boolean;
  onClick: (filter: AllowedChipFilter) => void;
}

export type { AllowedChipFilter, FilterChipProps };
