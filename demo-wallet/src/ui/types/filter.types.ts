/**
 * Shared filter types for credentials and identifiers
 * Both use the same filter structure: All, Individual, Group
 */
enum FilterType {
    All = "all",
    Individual = "individual",
    Group = "group",
}

// Legacy aliases for backward compatibility during migration
// TODO: Remove these aliases once all code is updated to use FilterType
type CredentialsFilters = FilterType;
type IdentifiersFilters = FilterType;

export { FilterType };
export type { CredentialsFilters, IdentifiersFilters };
