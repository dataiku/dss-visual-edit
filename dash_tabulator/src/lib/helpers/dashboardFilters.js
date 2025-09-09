export const extractFilterValues = (filter) => {
    const includedValues = filter.selectedValues
        ? Object.keys(filter.selectedValues).filter(key => filter.selectedValues[key])
        : [];
    const excludedValues = filter.excludedValues
        ? Object.keys(filter.excludedValues).filter(key => filter.excludedValues[key])
        : [];
    return { includedValues, excludedValues };
}