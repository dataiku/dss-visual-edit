import { extractFilterValues } from './dashboardFilters'

test('extractFilterValues with single-select event (selectedValues)', () => {
    const filter = {
        selectedValues: { '0092941-00': true }
    };
    const result = extractFilterValues(filter);
    expect(result.includedValues).toEqual(['0092941-00']);
    expect(result.excludedValues).toEqual([]);
});

test('extractFilterValues with multi-select event (excludedValues)', () => {
    const filter = {
        excludedValues: { '0094791-00': true, '0092941-00': true }
    };
    const result = extractFilterValues(filter);
    expect(result.includedValues).toEqual([]);
    expect(result.excludedValues).toEqual(['0094791-00', '0092941-00']);
});

test('extractFilterValues with both selected and excluded values', () => {
    const filter = {
        selectedValues: { '0092941-00': true },
        excludedValues: { '0094791-00': true }
    };
    const result = extractFilterValues(filter);
    expect(result.includedValues).toEqual(['0092941-00']);
    expect(result.excludedValues).toEqual(['0094791-00']);
});

test('extractFilterValues with empty filter', () => {
    const filter = {};
    const result = extractFilterValues(filter);
    expect(result.includedValues).toEqual([]);
    expect(result.excludedValues).toEqual([]);
});