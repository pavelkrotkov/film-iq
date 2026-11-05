// User-entered values are separate from the source-listed year and director.
const SPECS = [
  {key: "year", name: "POC Year", type: "number"},
  {key: "genre", name: "POC Genre", type: "text"},
];

function validValue(key, value) {
  return typeof value === "string" && (value === "" ||
    (key === "year" ? /^[1-9][0-9]{0,3}$/.test(value) : !!value.trim()));
}

export function storedMetadata(definitions, rows) {
  return Object.fromEntries(SPECS.map(({key, name, type}) => {
    const matches = Array.isArray(definitions) ? definitions.filter((item) => item?.name === name) : [];
    const definition = matches.length === 1 && matches[0].type === type && typeof matches[0].id === "string" && matches[0].id ? matches[0] : null;
    const values = definition && Array.isArray(rows) ? rows.filter((item) => item?.fieldId === definition.id) : [];
    const value = values.length === 0 ? "" : values[0]?.value;
    const editable = !!definition && values.length <= 1 && validValue(key, value);
    return [key, {fieldId: editable ? definition.id : null, value: editable ? value : "", editable}];
  }));
}

export function metadataChanges(baseline, draft, edited) {
  const updates = [];
  for (const {key, name} of SPECS) {
    const field = baseline?.[key];
    if (!edited?.[key]) continue;
    if (!field?.editable || !field.fieldId) throw new Error(`${name} is unavailable or invalid. This draft is unsaved; copy it before reloading.`);
    const value = key === "year" ? draft[key].trim() : draft[key];
    if (!validValue(key, value)) throw new Error(key === "year" ? "Release year must be an integer from 1 to 9999." : "Genre cannot contain only whitespace.");
    if (value !== field.value) updates.push({fieldId: field.fieldId, value, name});
  }
  return updates;
}
