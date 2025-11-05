
import { FilterType } from "../../types/filter.types";

type StartAnimationSource = "favourite" | "cards" | "none";

// Re-export shared FilterType as IdentifiersFilters for full compatibility
type IdentifiersFilters = FilterType;
const IdentifiersFilters = FilterType;

export type { StartAnimationSource };
export { IdentifiersFilters };
